import json
import os
import logging
from typing import Dict, Any

# Permanent user data file
USER_DB_FILE = "user_database.json"
# Temporary game data file
TEMP_DB_FILE = "temp_game_data.json"

# Default user stats structure
DEFAULT_USER_STATS = {
    "points": 0,
    "level": 1,
    "exp": 0,
    "games_played": 0,
    "wins": 0,
    "achievements": [],
    "items": {},
    "balance": 1000
}

def load_user_data() -> Dict:
    try:
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
        return {"users": {}}
    except Exception as e:
        logging.error(f"Error loading user database: {e}")
        return {"users": {}}

def save_user_data(data: Dict):
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving user database: {e}")

def get_user_stats(user_id: int) -> Dict:
    user_data = load_user_data()
    user_id_str = str(user_id)
    if user_id_str not in user_data["users"]:
        user_data["users"][user_id_str] = DEFAULT_USER_STATS.copy()
        save_user_data(user_data)
    return user_data["users"][user_id_str]

def update_user_stats(user_id: int, updates: Dict):
    user_data = load_user_data()
    user_id_str = str(user_id)
    if user_id_str not in user_data["users"]:
        user_data["users"][user_id_str] = DEFAULT_USER_STATS.copy()
    user_data["users"][user_id_str].update(updates)
    save_user_data(user_data)

def get_temp_game_data() -> Dict:
    try:
        if os.path.exists(TEMP_DB_FILE):
            with open(TEMP_DB_FILE, 'r') as f:
                return json.load(f)
        return {"active_rooms": {}, "current_games": {}}
    except Exception as e:
        logging.error(f"Error loading temp game data: {e}")
        return {"active_rooms": {}, "current_games": {}}

def save_temp_game_data(data: Dict):
    try:
        with open(TEMP_DB_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logging.error(f"Error saving temp game data: {e}")

def add_exp(user_id: int, exp_amount: int):
    user_stats = get_user_stats(user_id)
    user_stats["exp"] += exp_amount

    # Level up logic
    level_threshold = user_stats["level"] * 1000
    if user_stats["exp"] >= level_threshold:
        user_stats["level"] += 1
        user_stats["exp"] -= level_threshold
        user_stats["points"] += 500  # Level up bonus

    update_user_stats(user_id, user_stats)

game_data: Dict[str, Any] = {}


def load_database(data):
    try:
        game_data.update(get_temp_game_data())
    except Exception as e:
        logging.error(f"Error loading database: {e}")

def save_database(data):
    try:
        data_to_save = data.copy()

        # Convert sets to lists for JSON serialization
        if "waiting_for_roles" in data_to_save:
            data_to_save["waiting_for_roles"] = list(data_to_save["waiting_for_roles"])
        if "protected_players" in data_to_save:
            data_to_save["protected_players"] = list(data_to_save["protected_players"])
        if "used_actions" in data_to_save:
            data_to_save["used_actions"] = list(data_to_save["used_actions"])

        save_temp_game_data(data_to_save)
    except Exception as e:
        logging.error(f"Error saving database: {e}")

def update_player_points(player_id: int, points: int):
    try:
        player_id_str = str(player_id)
        if player_id_str not in game_data["player_stats"]:
            game_data["player_stats"][player_id_str] = {
                "points": 0,
                "games": 0,
                "wins": 0,
                "items": {}
            }
        game_data["player_stats"][player_id_str]["points"] += points
        save_database(game_data)
    except Exception as e:
        logging.error(f"Error updating player points: {e}")

def get_player_points(player_id: int) -> int:
    try:
        return game_data["player_stats"].get(str(player_id), {}).get("points", 0)
    except Exception as e:
        logging.error(f"Error getting player points: {e}")
        return 0

def can_afford_item(player_id: int, item_price: int) -> bool:
    try:
        return get_player_points(player_id) >= item_price
    except Exception as e:
        logging.error(f"Error checking if player can afford item: {e}")
        return False

def get_player_stats(player_id: int) -> dict:
    try:
        player_id_str = str(player_id)
        if player_id_str not in game_data["player_stats"]:
            game_data["player_stats"][player_id_str] = {
                "points": 0,
                "games": 0,
                "wins": 0,
                "items": {},
                "achievements": []
            }
        return game_data["player_stats"][player_id_str]
    except Exception as e:
        logging.error(f"Error getting player stats: {e}")
        return {"points": 0, "games": 0, "wins": 0, "items": {}, "achievements": []}