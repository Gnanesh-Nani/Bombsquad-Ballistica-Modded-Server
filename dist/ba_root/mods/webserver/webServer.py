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
    _bank_data_cache
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

def hex_to_rgb(color: str) -> List[int]:
    """Convert hex color to RGB list"""
    color = color.lstrip('#')
    if len(color) == 3:
        color = ''.join([c*2 for c in color])
    try:
        return [
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16)
        ]
    except ValueError:
        return [255, 255, 255]

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