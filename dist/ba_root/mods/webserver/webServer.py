# webserver.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import threading
from typing import Dict, Any, List
import re
import os
import json
import setting

our_settings = setting.get_settings_data()
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
    print(f'Buy Endpoint Hit with data: {data}')  # Log incoming data
    
    try:
        global _bank_data_cache
        
        pbId = data.get('pbId')
        itemName = data.get('itemName')
        price = data.get('price')
        days = data.get('days')
        
        # Validate required fields
        if not all([pbId, itemName, price, days]):
            error_msg = f"Missing required fields. Received: pbId={pbId}, itemName={itemName}, price={price}, days={days}"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Ensure price is a positive number
        try:
            price = int(price)
            if price <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid price value: {price}. Error: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Price must be a positive integer")
        
        # Ensure days is a positive number
        try:
            days = int(days)
            if days <= 0:
                raise ValueError("Days must be positive")
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid days value: {days}. Error: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Days must be a positive integer")
        
        # Load cache if not loaded
        if _bank_data_cache is None:
            print("Loading bank data cache...")
            _bank_data_cache = load_bank_data()
        
        # Initialize account if not exists
        if pbId not in _bank_data_cache:
            print(f"Initializing new account for {pbId}")
            _bank_data_cache[pbId] = {
                "tickets": 200,
                "effect": None,
                "tag": None,
                "password": "default"
            }
        
        # Get current ticket balance (ensure it's an integer)
        current_tickets = int(_bank_data_cache[pbId].get("tickets", 0))
        
        # Check if user has enough tickets
        if current_tickets < price:
            error_msg = f"Insufficient tickets. Current: {current_tickets}, Required: {price}"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Insufficient tickets")
        
        # Calculate new balance (this is where the fix is)
        new_ticket_balance = current_tickets - price
        
        # Calculate expiry date
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare update data
        update_data = {
            "effect": [itemName, expiry_date],
            "tickets": new_ticket_balance
        }
        
        print(f"Updating account {pbId}. Current: {current_tickets}, Deducting: {price}, New Balance: {new_ticket_balance}")
        
        # Update cache and save to disk
        _bank_data_cache[pbId].update(update_data)
        save_bank_data_to_disk()
        
        # Log successful purchase
        print(f"Purchase successful for {pbId}: {itemName} for {price} tickets. New balance: {new_ticket_balance}")
        
        return {
            "success": True,
            "message": f"{itemName} purchased successfully!",
            "user": _bank_data_cache[pbId]
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        error_msg = f"Error in buy endpoint: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/app/bank/buyTag")
async def buy_tag(data: Dict[str, Any]):
    """Handle tag purchases and update bank data"""
    print(f'BuyTag Endpoint Hit with data: {data}')  # Detailed logging
    
    try:
        global _bank_data_cache
        
        pbId = data.get('pbId')
        tagName = data.get('tagName')
        price = data.get('price')
        days = data.get('days')
        color = data.get('color')  # Expecting RGB array [r, g, b]
        
        # Validate required fields
        if not all([pbId, tagName, price, days, color]):
            error_msg = f"Missing required fields. Received: pbId={pbId}, tagName={tagName}, price={price}, days={days}, color={color}"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate price
        try:
            price = int(price)
            if price <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid price value: {price}. Error: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Price must be a positive integer")
        
        # Validate days
        try:
            days = int(days)
            if days <= 0:
                raise ValueError("Days must be positive")
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid days value: {days}. Error: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Days must be a positive integer")
        
        # Validate color format
        if not isinstance(color, list) or len(color) != 3:
            error_msg = f"Invalid color format: {color}. Expected [r,g,b] array"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Color must be RGB array [r,g,b]")
        
        # Validate color values (0-255)
        if not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
            error_msg = f"Invalid color values: {color}. Values must be 0-255"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Color values must be integers 0-255")
        
        # Load cache if not loaded
        if _bank_data_cache is None:
            print("Loading bank data cache...")
            _bank_data_cache = load_bank_data()
        
        # Initialize account if not exists
        if pbId not in _bank_data_cache:
            print(f"Initializing new account for {pbId}")
            _bank_data_cache[pbId] = {
                "tickets": 200,
                "effect": None,
                "tag": None,
                "password": "default"
            }
        
        # Get current tickets (with type conversion)
        current_tickets = int(_bank_data_cache[pbId].get("tickets", 0))
        
        # Check sufficient tickets
        if current_tickets < price:
            error_msg = f"Insufficient tickets. Current: {current_tickets}, Required: {price}"
            print(error_msg)
            raise HTTPException(status_code=400, detail="Insufficient tickets")
        
        # Calculate new balance
        new_ticket_balance = current_tickets - price
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare update
        update_data = {
            "tag": [tagName, expiry_date, color],
            "tickets": new_ticket_balance
        }
        
        print(f"Updating {pbId}. Tickets: {current_tickets} → {new_ticket_balance} (-{price})")
        
        # Apply update
        _bank_data_cache[pbId].update(update_data)
        save_bank_data_to_disk()
        
        print(f"Tag purchase successful: {tagName} for {pbId}")
        
        return {
            "success": True,
            "message": f"{tagName} tag purchased successfully!",
            "user": _bank_data_cache[pbId]
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        error_msg = f"Error in buyTag endpoint: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")

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
    uvicorn.run(app, host=our_settings['fastAPI_webserver_host'], port=our_settings['fastAPI_webserver_port'])

def start_webserver():
    """Start in background thread"""
    thread = threading.Thread(target=run_webserver, daemon=True)
    thread.start()
    print("FastAPI server running on port 3002")