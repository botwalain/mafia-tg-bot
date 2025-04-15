"""
Game State Configuration
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
"""

from database import get_temp_game_data, save_temp_game_data, get_user_stats

# Game info
GAME_NAME = "IBM's Mafia Game Bot"
GAME_CREATOR = "Created by @IBMBotSupport"
GAME_VERSION = "v1.0.0"
ADMIN_ID = 2125687935

# Game assets 
GAME_GIFS = {
    "start": "https://c.tenor.com/SBQWciMEVoAAAAAC/tenor.gif",
    "night": "https://c.tenor.com/LdfTWdNjwmEAAAAd/tenor.gif",
    "day": "https://c.tenor.com/3GgX9XG4fe0AAAAd/tenor.gif",
    "voting": "https://c.tenor.com/IQKTh2BFMt0AAAAC/tenor.gif"
}

# Bot names
BOT_NAMES = ["BenNnadBot", "BenedictNnad", "BeniNnad", "BerlianoNnad", "NnadBot"]

# Game modes
NORMAL_MODE_ROLES = ["Villager", "Mafia", "Doctor", "Detective"]
RANDOM_MODE_ROLES = NORMAL_MODE_ROLES + ["Kamikaze", "Lucky", "Magician", "Sorcerer"]

# Role descriptions
role_desc = {
    "Villager": "👨🏼 A regular villager with no special abilities. Task: Find and expose the mafia through discussion and voting",
    "Mafia": "🔪 A mafia killer. Task: Kill villagers each night and hide your identity.",
    "Doctor": "👨‍⚕️ A healing doctor. Task: Protect one player from the mafia's attack each night.",
    "Detective": "🕵️ A clever detective. Task: Investigate the identity of one player each night.",
    # Add all other roles here from your list
    "Boss Mafia": "👑 You are the Mafia Boss! Lead your mafia and conquer the villagers.",
    "Lawyer": "⚖️ You are the Lawyer! Save a chosen player every night.",
    "Lucky": "🤞🏼 You are the Lucky One! Your first vote has a big impact.",
    "Kamikaze": "💣 You are the Kamikaze! Stay silent, but if you're killed, you can take your killer down with you.",
    "Prostitute": "💋 You are the Prostitute! You can learn the role of one chosen player each night.",
    "Hobo": "🚶 You are the Hobo! No special role, just a regular villager",
    "Mayor": "🏙️ You are the Mayor! You are immune to voting.",
    "Werewolf": "🐺 You are the Werewolf! Kill anyone you want.",
    "Magician": "✨ You are the Magician! Swap roles with another player.",
    "Madman": "🤪 You are the Madman! You can choose to either kill or heal anyone."
}

# Game state management
def get_game_state():
    return get_temp_game_data()

def save_game_state(state):
    save_temp_game_data(state)

# Initialize empty game state
game_state = get_game_state()

# Game state data structure (persistence handled by database functions)
game_data = {
    "phase": None,  # night/day/voting
    "players": [],
    "alive_players": [],
    "roles": {},
    "votes": {},
    "night_actions": {},
    "waiting_for_roles": set(),
    "current_day": 0,
    "group_id": None,
    "vote_time": 60,
    "game_log": [],
    "player_stats": {},  # For achievements and stats
    "active_rooms": {},
    "shop_items": {
        "protection": {"price": 100, "desc": "**One time protection from an attack**"},
        "extra_vote": {"price": 200, "desc": "**Additional one vote during voting**"},
        "role_peek": {"price": 300, "desc": "**See the role of one player**"}
    }
}

room_state = {
    "is_joining": False,
    "players": [],
    "message_id": None,
    "mode": None,
    "join_time": None,
    "last_reminder": None
}

timer_state = {
    "end_time": None,
    "last_extend": {}
}
