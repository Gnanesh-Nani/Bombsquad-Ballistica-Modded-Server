# webserver.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import threading
from typing import Dict, Any, List
import re
import os
import json

# Import from your existing modules
from shop.Shop import (
    load_bank_data,
    update_bank_cache,
    _bank_data_cache,
    save_bank_data_to_disk
)
from stats.mystats import (
    get_all_stats,
    get_cached_stats,
    get_stats_by_id,
    get_sorted_stats,
    dump_stats
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def format_date(days: int) -> str:
    """Format expiry date as YYYY-MM-DD HH:MM:SS"""
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


# Stats Endpoints
@app.get("/app/stats")
async def get_stats():
    """Get all stats data"""
    return {
        "stats": get_all_stats(),
        "sorted": get_sorted_stats(get_cached_stats()),
        "top_players": get_top_players(3)
    }

@app.get("/app/stats/{account_id}")
async def get_player_stats(account_id: str):
    """Get stats for specific player"""
    stats = get_stats_by_id(account_id)
    if stats is None:
        raise HTTPException(404, detail="Player stats not found")
    return stats

def get_top_players(count: int = 3) -> List[Dict]:
    """Get top players by score"""
    stats = get_cached_stats()
    sorted_entries = sorted(
        stats.values(),
        key=lambda x: x['scores'],
        reverse=True
    )
    return sorted_entries[:count]

@app.post("/app/bank/buy")
async def buy_item(data: Dict[str, Any]):
    """Handle item purchases and update bank data"""
    print('Buy End Point Hitted')
    try:
        global _bank_data_cache  # Access the imported global variable
        
        pbId = data.get('pbId')
        itemName = data.get('itemName')
        price = data.get('price')
        days = data.get('days')
        
        if not all([pbId, itemName, price, days]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Ensure cache is loaded
        if _bank_data_cache is None:
            _bank_data_cache = load_bank_data()
        
        # Initialize account if not exists
        if pbId not in _bank_data_cache:
            _bank_data_cache[pbId] = {
                "tickets": 200,
                "effect": None,
                "tag": None,
                "password": "default"
            }
        
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        update_data = {
            "effect": [itemName, expiry_date],
            "tickets": _bank_data_cache[pbId]["tickets"] - int(price)  # Calculate new ticket count
        }
        
        update_bank_cache(pbId, update_data)
        save_bank_data_to_disk()
        
        return {
            "success": True,
            "message": f"{itemName} purchased successfully!",
            "user": _bank_data_cache[pbId]  # Send updated user data
        }
        
    except Exception as e:
        print(f"Error in buy endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/app/bank/buyTag")
async def buy_tag(data: Dict[str, Any]):
    """Handle tag purchases and update bank data"""
    print('BuyTag End Point Hitted')
    try:
        global _bank_data_cache  # Access the imported global variable
        
        pbId = data.get('pbId')
        tagName = data.get('tagName')
        price = data.get('price')
        days = data.get('days')
        color = data.get('color')  # Expecting RGB array [r, g, b] from frontend
        
        if not all([pbId, tagName, price, days, color]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Validate color format (should be [r, g, b] array)
        if not isinstance(color, list) or len(color) != 3:
            raise HTTPException(status_code=400, detail="Invalid color format")
        
        # Ensure cache is loaded
        if _bank_data_cache is None:
            _bank_data_cache = load_bank_data()
            
        # Initialize account if not exists
        if pbId not in _bank_data_cache:
            _bank_data_cache[pbId] = {
                "tickets": 200,
                "effect": None,
                "tag": None,
                "password": "default"
            }
        
        # Calculate expiry date
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare update data with calculated ticket count
        update_data = {
            "tag": [tagName, expiry_date, color],  # Store the RGB array directly
            "tickets": _bank_data_cache[pbId]["tickets"] - int(price)  # Calculate new ticket count
        }
        
        # Update bank data
        update_bank_cache(pbId, update_data)
        save_bank_data_to_disk()  # Persist changes
        
        return {
            "success": True,
            "message": f"{tagName} purchased successfully!",
            "user": _bank_data_cache[pbId]  # Send updated user data
        }
        
    except Exception as e:
        print(f"Error in buyTag endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/app/bank/removeEffect")
async def remove_effect(data: Dict[str, Any]):
    """Handle effect removal and update bank data"""
    print('Remove Effect End Point Hit')
    try:
        global _bank_data_cache
        
        pbId = data.get('pbId')
        if not pbId:
            raise HTTPException(status_code=400, detail="pbId is required")
        
        # Ensure cache is loaded
        if _bank_data_cache is None:
            _bank_data_cache = load_bank_data()
        
        # Check if user exists
        if pbId not in _bank_data_cache:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only update if there's an effect to remove
        if _bank_data_cache[pbId]["effect"] is not None:
            update_data = {
                "effect": None
            }
            update_bank_cache(pbId, update_data)
            save_bank_data_to_disk()
        
        return {
            "success": True,
            "message": "Effect removed successfully",
            "user": _bank_data_cache[pbId]  # Return updated user data
        }
        
    except Exception as e:
        print(f"Error in removeEffect endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/app/bank/removeTag")
async def remove_tag(data: Dict[str, Any]):
    """Handle tag removal and update bank data"""
    print('Remove Tag End Point Hit')
    try:
        global _bank_data_cache
        
        pbId = data.get('pbId')
        if not pbId:
            raise HTTPException(status_code=400, detail="pbId is required")
        
        # Ensure cache is loaded
        if _bank_data_cache is None:
            _bank_data_cache = load_bank_data()
        
        # Check if user exists
        if pbId not in _bank_data_cache:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only update if there's a tag to remove
        if _bank_data_cache[pbId]["tag"] is not None:
            update_data = {
                "tag": None
            }
            update_bank_cache(pbId, update_data)
            save_bank_data_to_disk()
        
        return {
            "success": True,
            "message": "Tag removed successfully",
            "user": _bank_data_cache[pbId]  # Return updated user data
        }
        
    except Exception as e:
        print(f"Error in removeTag endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Bank Endpoints (existing)
@app.get("/app/bank")
async def get_bank():
    """Get full bank data"""
    print('/app/bank endpoint hitted')
    return load_bank_data()

def run_webserver():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)

def start_webserver():
    """Start in background thread"""
    thread = threading.Thread(target=run_webserver, daemon=True)
    thread.start()
    print("FastAPI server running on port 3002")