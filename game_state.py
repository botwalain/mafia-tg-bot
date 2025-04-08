"""
Game State Configuration
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
"""

from database import get_temp_game_data, save_temp_game_data, get_user_stats

# Game info
GAME_NAME = "MafiosoNnad"
GAME_CREATOR = "Created by Berlinnad"
GAME_VERSION = "v1.0.0"
ADMIN_ID = 5136750253

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
NORMAL_MODE_ROLES = ["Warga", "Mafia", "Dokter", "Detektif"]
RANDOM_MODE_ROLES = NORMAL_MODE_ROLES + ["Kamikaze", "Lucky", "Pesulap", "Penyihir"]

# Role descriptions
role_desc = {
    "Warga": "👨🏼 Warga biasa tanpa kemampuan khusus. Tugas: Mencari dan mengungkap mafia melalui diskusi dan voting.",
    "Mafia": "🔪 Mafia pembunuh. Tugas: Membunuh warga tiap malam dan menyembunyikan identitas.",
    "Dokter": "👨‍⚕️ Dokter penyembuh. Tugas: Melindungi satu pemain dari serangan mafia tiap malam.",
    "Detektif": "🕵️ Detektif cerdas. Tugas: Menyelidiki identitas satu pemain tiap malam.",
    # Add all other roles here from your list
    "Boss Mafia": "👑 Kamu adalah Bos Mafia! Pimpin mafiamu dan taklukkan warga.",
    "Pengacara": "⚖️ Kamu adalah Pengacara! Selamatkan pemain yang dipilih setiap malam.",
    "Beruntung": "🤞🏼 Kamu adalah Si Beruntung! Vote pertama memiliki pengaruh besar.",
    "Kamikaze": "💣 Kamu adalah Kamikaze! Jangan bicara, tapi saat dibunuh kamu bisa membawa musuhmu mati bersamamu.",
    "Pelacur": "💋 Kamu adalah Pelacur! Dapat mengetahui peran pemain yang dipilih setiap malam.",
    "Gelandangan": "🚶 Kamu adalah Gelandangan! Tidak memiliki peran khusus, hanya warga biasa.",
    "Walikota": "🏙️ Kamu adalah Walikota! Kamu kebal terhadap vote.",
    "Serigala": "🐺 Kamu adalah Serigala! Bunuh siapapun yang kamu mau.",
    "Pesulap": "✨ Kamu adalah Pesulap! Tukar peran dengan pemain lain.",
    "Gila": "🤪 Kamu adalah Gila! Kamu dapat memilih untuk membunuh siapapun atau menyembuhkan siapapun."
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
        "protection": {"price": 100, "desc": "Satu kali perlindungan dari serangan"},
        "extra_vote": {"price": 200, "desc": "Tambahan satu suara saat voting"},
        "role_peek": {"price": 300, "desc": "Lihat peran satu pemain"}
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