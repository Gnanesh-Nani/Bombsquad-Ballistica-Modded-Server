import _ba
import ba
import os
import json
import random
import string
from datetime import datetime

# Helper function to load the bank data
def load_bank_data():
    bank_file_path = os.path.join(os.path.dirname(__file__), 'bank.json')
    if os.path.exists(bank_file_path):
        try:
            with open(bank_file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
    return {}

# Helper function to save the bank data
def save_bank_data(bank_data):
    bank_file_path = os.path.join(os.path.dirname(__file__), 'bank.json')
    with open(bank_file_path, 'w') as f:
        json.dump(bank_data, f, indent=4)

# Get player's tag from bank.json
def get_player_tag_from_bank(account_id):
    bank_data = load_bank_data()
    tag_data = bank_data.get(account_id, {}).get("tag")
    if tag_data and isinstance(tag_data, list) and len(tag_data) == 3:
        tag_text, expiry_time, tag_color = tag_data[0], tag_data[1], tuple(tag_data[2])

        # Check if the tag has expired
        if datetime.now().timestamp() < datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S").timestamp():
            return tag_text, tag_color
        else:
            update_expired_tag(bank_data, account_id)
    return None, None

# Update the bank data when a tag has expired
def update_expired_tag(bank_data, account_id):
    clid = get_client_id(account_id)
    if clid:
        _ba.screenmessage("Your tag has expired.", color=(1.0, 0.2, 0.2), transient=True, clients=[clid])
    bank_data[account_id]["tag"] = None
    save_bank_data(bank_data)

# Get client ID based on account_id
def get_client_id(account_id):
    for ros in ba.internal.get_game_roster():
        if ros["account_id"] == account_id:
            return ros["client_id"]
    return None

# Get player's effect from bank.json
def get_player_effect_from_bank(account_id):
    bank_data = load_bank_data()
    effect_data = bank_data.get(account_id, {}).get("effect")
    if effect_data and isinstance(effect_data, list) and len(effect_data) == 2:
        effect_name, effect_end_period = effect_data

        # Check if the effect has expired
        if datetime.now().timestamp() < datetime.strptime(effect_end_period, "%Y-%m-%d %H:%M:%S").timestamp():
            return effect_name
        else:
            update_expired_effect(bank_data, account_id)
    return None

# Update the bank data when an effect has expired
def update_expired_effect(bank_data, account_id):
    clid = get_client_id(account_id)
    if clid:
        _ba.screenmessage("Your effect has expired.", color=(1.0, 0.2, 0.2), transient=True, clients=[clid])
    bank_data[account_id]["effect"] = None
    save_bank_data(bank_data)

# Generate a random passcode of the specified length
def generate_passcode(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Add a player to bank.json if they don't already exist
def add_player_if_not_exists_in_bank(pbid):
    bank_data = load_bank_data()
    if pbid not in bank_data:
        bank_data[pbid] = {
            "tickets": 200,  # Default 200 tickets
            "effect": None,
            "tag": None,
            "password": generate_passcode()
        }
        save_bank_data(bank_data)
        print(f"Player {pbid} added with initial values.")
    else:
        print(f"Player {pbid} already exists.")
