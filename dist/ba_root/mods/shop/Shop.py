import _ba
import ba
import os
import json
import random
import string
from datetime import datetime

_bank_data_cache = None  # Global cache variable

# [CACHE LOADER] Called when first accessing bank data
def load_bank_data_from_disk():
    """Load bank data from JSON file and return as dict"""
    print(f"load_bank_data_from_disk() called - Loading bank data from disk...")
    bank_file_path = os.path.join(os.path.dirname(__file__), 'bank.json')
    if os.path.exists(bank_file_path):
        try:
            with open(bank_file_path, 'r') as f:
                full_data = json.load(f)  # [DISK READ] Reading raw JSON data
                
                # Handle different file formats
                if isinstance(full_data, dict) and 'data' in full_data:
                    data = full_data['data']  # New format with metadata
                else:
                    data = full_data  # Old format without metadata
                
                print(f"Loaded {len(data)} accounts from bank.json")
                
                # [DEBUG PRINT] Show first 10 accounts
                print("\nFirst 10 accounts data:")
                accounts_printed = 0
                for account_id, account_data in data.items():
                    if account_id.startswith('_'):  # Skip metadata
                        continue
                    if accounts_printed >= 3:
                        break
                    if isinstance(account_data, dict):
                        print(f"Account {accounts_printed+1}: {account_id}")
                        print(f"  Tickets: {account_data.get('tickets', 0)}")
                        print(f"  Effect: {account_data.get('effect', 'None')}")
                        print(f"  Tag: {account_data.get('tag', 'None')}")
                        print(f"  Password: {account_data.get('password', 'None')}\n")
                        accounts_printed += 1
                
                return data
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
    return {}

# [CACHE SAVER] Called when modifying bank data
def save_bank_data_to_disk():
    """Save current cache state to disk"""
    global _bank_data_cache
    if _bank_data_cache is not None:
        print(f"save_bank_data_to_disk() called - Saving {len(_bank_data_cache)} accounts")
        bank_file_path = os.path.join(os.path.dirname(__file__), 'bank.json')
        with open(bank_file_path, 'w') as f:
            json.dump(_bank_data_cache, f, indent=4)  # [DISK WRITE] Saving cache

# [CACHE GETTER] Main entry point for accessing bank data
def load_bank_data():
    """Get bank data from cache or load from disk if empty"""
    global _bank_data_cache
    if _bank_data_cache is None:
        print("load_bank_data() initializing cache")
        _bank_data_cache = load_bank_data_from_disk()  # [CACHE INIT] First load
    return _bank_data_cache

def update_bank_cache(account_id, data_update):
    """Update the bank cache with new data without saving to disk"""
    global _bank_data_cache
    if _bank_data_cache is None:
        _bank_data_cache = load_bank_data_from_disk()
    
    # Initialize account if not exists
    if account_id not in _bank_data_cache:
        _bank_data_cache[account_id] = {
            "tickets": 200,  # Default starting tickets
            "effect": None,
            "tag": None,
            "password": generate_passcode()
        }
    
    # Special handling for tickets increment
    if 'tickets' in data_update:
        _bank_data_cache[account_id]['tickets'] = _bank_data_cache[account_id].get('tickets', 0) + data_update['tickets']
        # Remove from update dict to avoid double processing
        data_update.pop('tickets')
    
    # Merge remaining updates (non-ticket fields)
    _bank_data_cache[account_id].update(data_update)

# [TAG MANAGER] Called when player joins or tag is checked
def get_player_tag_from_bank(account_id):
    """Return active tag for account or None if expired/missing"""
    global _bank_data_cache 
    if _bank_data_cache is None:  
        _bank_data_cache = load_bank_data()  # [CACHE LOAD] Ensure cache exists
    
    tag_data = _bank_data_cache.get(account_id, {}).get("tag")
    if tag_data and isinstance(tag_data, list) and len(tag_data) == 3:
        tag_text, expiry_time, tag_color = tag_data[0], tag_data[1], tuple(tag_data[2])
        if datetime.now().timestamp() < datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S").timestamp():
            print(f"get_player_tag_from_bank() valid tag for {account_id}")
            return tag_text, tag_color
        else:
            print(f"get_player_tag_from_bank() expired tag for {account_id}")
            update_expired_tag(account_id)  # [TAG CLEANUP] Expired tag
    return None, None

# [TAG UPDATER] Called when tag expires
def update_expired_tag(account_id):
    """Remove expired tag from cache and save to disk"""
    global _bank_data_cache
    print(f"update_expired_tag() processing {account_id}")
    
    clid = get_client_id(account_id)  # [PLAYER LOOKUP] Find online player
    if clid:
        _ba.screenmessage("Your tag has expired.", color=(1.0, 0.2, 0.2), transient=True, clients=[clid])

    if _bank_data_cache and account_id in _bank_data_cache:
        _bank_data_cache[account_id]["tag"] = None  # [CACHE UPDATE] Clear tag
        save_bank_data_to_disk()  # [DISK SYNC] Persist changes

# [PLAYER LOOKUP] Convert account ID to client ID
def get_client_id(account_id):
    """Convert account_id to client_id if player is online"""
    for ros in ba.internal.get_game_roster():
        if ros["account_id"] == account_id:
            return ros["client_id"]
    return None

# [EFFECT MANAGER] Called when player joins or effect is checked
def get_player_effect_from_bank(account_id):
    """Return active effect for account or None if expired/missing"""
    global _bank_data_cache
    if _bank_data_cache is None:
        _bank_data_cache = load_bank_data()  # [CACHE LOAD] Ensure cache exists
    
    effect_data = _bank_data_cache.get(account_id, {}).get("effect")
    if effect_data and isinstance(effect_data, list) and len(effect_data) == 2:
        effect_name, effect_end_period = effect_data
        if datetime.now().timestamp() < datetime.strptime(effect_end_period, "%Y-%m-%d %H:%M:%S").timestamp():
            print(f"get_player_effect_from_bank() valid effect for {account_id}")
            return effect_name
        else:
            print(f"get_player_effect_from_bank() expired effect for {account_id}")
            update_expired_effect(account_id)  # [EFFECT CLEANUP] Expired effect
    return None

# [EFFECT UPDATER] Called when effect expires
def update_expired_effect(account_id):
    """Remove expired effect from cache and save to disk"""
    global _bank_data_cache
    print(f"update_expired_effect() processing {account_id}")
    
    clid = get_client_id(account_id)  # [PLAYER LOOKUP] Find online player
    if clid:
        _ba.screenmessage("Your effect has expired.", color=(1.0, 0.2, 0.2), transient=True, clients=[clid])

    if _bank_data_cache is not None:
        _bank_data_cache.setdefault(account_id, {})["effect"] = None  # [CACHE UPDATE] Clear effect
        save_bank_data_to_disk()  # [DISK SYNC] Persist changes

# [PASSWORD GENERATOR] Called when creating new accounts
def generate_passcode(length=8):
    """Generate random alphanumeric passcode"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# [ACCOUNT CREATOR] Called when new player joins
def add_player_if_not_exists_in_bank(pbid):
    """Add new player with default data if not exists"""
    global _bank_data_cache
    if _bank_data_cache is None:
        _bank_data_cache = load_bank_data()  # [CACHE LOAD] Ensure cache exists

    if pbid not in _bank_data_cache:
        print(f"add_player_if_not_exists_in_bank() creating account {pbid}")
        _bank_data_cache[pbid] = {
            "tickets": 200,
            "effect": None,
            "tag": None,
            "password": generate_passcode()  # [PASSWORD GENERATION] New account
        }
        save_bank_data_to_disk()  # [DISK SYNC] Save new account