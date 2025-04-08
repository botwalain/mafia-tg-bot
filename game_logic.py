"""
Game Logic Module
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
#berlinnad
"""

import asyncio
from typing import Dict, List
from game_state import game_data, role_desc
import random

from night_handler import NightHandler
from day_handler import handle_day_phase 
from voting_handler import VotingHandler

voting_handler = VotingHandler()

async def handle_game_loop(room, context):
    """Main game loop handler"""
    try:
        day_number = 1

        while room.phase != "ended" and day_number <= 100:  # Max 100 days
            if room.phase == "night":
                # Handle night phase
                await handle_night_phase(room, context)
                if await check_win_condition(room, context):
                    break
                room.phase = "day"

            elif room.phase == "day":
                # Handle day phase
                await handle_day_phase(room, context, day_number)
                if await check_win_condition(room, context):
                    break
                room.phase = "voting"

            elif room.phase == "voting":
                # Handle voting phase
                await handle_voting_phase(room, context)
                if await check_win_condition(room, context):
                    break
                room.phase = "night"
                day_number += 1

            await asyncio.sleep(1)  # Short delay between phases

    except Exception as e:
        print(f"Error in game loop: {e}")
        try:
            await context.bot.send_message(
                chat_id=room.chat_id,
                text="❌ Terjadi kesalahan dalam permainan. Game dibatalkan."
            )
        except:
            pass
        room.phase = "ended"

async def assign_roles(players: List[dict], mode: str) -> Dict:
    """Assign roles to players based on count and mode"""
    player_count = len(players)
    assigned_roles = {}

    # Calculate role distribution
    mafia_count = max(1, player_count // 4)  # 25% mafia
    special_roles = ["Detektif", "Dokter", "Pengacara"]
    special_count = min(len(special_roles), player_count // 3)

    # Shuffle players and roles
    random.shuffle(players)
    selected_special = random.sample(special_roles, special_count)

    # Assign mafia first
    mafia_players = players[:mafia_count]
    for player in mafia_players:
        assigned_roles[player["id"]] = "Mafia" if len(mafia_players) > 1 else "Boss Mafia"

    # Assign special roles
    for i, player in enumerate(players[mafia_count:mafia_count + special_count]):
        assigned_roles[player["id"]] = selected_special[i]

    # Remaining players are citizens
    for player in players[mafia_count + special_count:]:
        assigned_roles[player["id"]] = "Warga"

    # Additional roles with their descriptions for bots
    role_info = {
        "Boss Mafia": "Pemimpin mafia yang dapat membunuh dan memiliki informasi tentang rekan mafia",
        "Mafia": "Anggota mafia yang dapat membunuh di malam hari",
        "Detektif": "Dapat memeriksa identitas pemain lain setiap malam",
        "Dokter": "Dapat melindungi satu pemain dari serangan malam",
        "Warga": "Penduduk biasa yang harus menemukan mafia",
        "Pengacara": "Dapat melindungi satu pemain dari eksekusi",
        "Kamikaze": "Dapat membawa musuhnya mati bersama",
        "Beruntung": "Memiliki kesempatan kedua untuk hidup"
    }

    # Additional roles that can be duplicated
    extra_roles = ["Mafia", "Warga", "Pengacara", "Kamikaze", "Beruntung"]

    # Add required base roles
    roles = base_roles.copy()

    # Fill remaining slots
    remaining = player_count - len(roles)
    if mode == "random":
        # Double some roles and add random ones
        for _ in range(remaining):
            roles.append(random.choice(extra_roles))
    else:
        # Normal mode - fill with regular citizens
        roles.extend(["Warga"] * remaining)

    # Shuffle roles and assign
    random.shuffle(roles)
    for i, player in enumerate(players):
        assigned_roles[player["id"]] = roles[i]

    if mode == "random" and player_count > 4:
        # Replace some Warga with special roles in random mode
        warga_indices = [i for i, r in enumerate(roles) if r == "Warga"]
        if len(warga_indices) >= 2:
            special_roles = ["Beruntung", "Kamikaze", "Pelacur", "Gelandangan", "Walikota"]
            replace_count = min(len(warga_indices) - 1, len(special_roles))
            for i in range(replace_count):
                roles[warga_indices[i]] = special_roles[i]

    # Shuffle roles and assign
    random.shuffle(roles)
    for i, player in enumerate(players):
        assigned_roles[player["id"]] = roles[i]

    return assigned_roles

async def handle_night_phase(room, context):
    """Handle night phase actions"""
    # Send notifications for important role actions
    for player in room.get_alive_players():
        if player["role"] in ["Detektif", "Dokter", "Mafia", "Boss Mafia"]:
            if player.get("is_bot", False):
                await handle_bot_night_action(player, room, context)
            else:
                role_action = {
                    "Detektif": "🕵️‍ Detektif sedang mencari penjahat...",
                    "Dokter": "👨🏼‍⚕️ Dokter pergi bertugas malam...",
                    "Mafia": "🔪 Mafia memilih korbannya...",
                    "Boss Mafia": "👑 Boss Mafia memilih targetnya..."
                }
                await context.bot.send_message(
                    chat_id=player["id"], # Send PM to player
                    text=role_action[player["role"]]
                )

async def handle_day_phase(room, context, day_number):
    """Handle day phase discussions"""
    # Implementation for day phase - needs further development to include room tagging and join buttons.
    pass

async def handle_voting_phase(room, context):
    """Handle voting phase"""
    # Implementation for voting phase - needs further development to handle voting and results announcement.
    pass

async def check_win_condition(room, context):
    """Check if any team has won"""
    # Implementation for win condition check - needs further development.
    pass


import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from database import save_database, load_database
from game_state import game_data, role_desc, room_state, timer_state
from game_state import GAME_GIFS


async def process_night_actions(context):
    game_data["phase"] = "day"
    # ... (night processing logic)
    save_database(game_data)

async def handle_voting(context, chat_id):
    game_data["phase"] = "voting"
    game_data["votes"] = {}

    # Handle bot voting
    for player in game_data["players"]:
        if player.get("is_bot") and player.get("is_alive"):
            bot_vote = await calculate_bot_vote(player, game_data["players"])
            if bot_vote:
                game_data["votes"][player["id"]] = bot_vote

    await context.bot.send_message(
        chat_id=chat_id,
        text="🗳️ Voting dimulai! Silakan pilih pemain yang mencurigakan."
    )
    save_database(game_data)

async def calculate_bot_vote(bot, players):
    # Smart bot voting logic based on role and observations
    alive_players = [p for p in players if p["is_alive"] and p["id"] != bot["id"]]
    if not alive_players:
        return None

    if bot["role"] == "Mafia":
        # Mafia tries to vote for innocent players
        return random.choice([p["id"] for p in alive_players if p.get("role") != "Mafia"])
    else:
        # Other roles vote based on suspicion level
        suspicious = [p for p in alive_players if p.get("suspicious", 0) > 0]
        if suspicious:
            return max(suspicious, key=lambda x: x.get("suspicious", 0))["id"]
    return random.choice([p["id"] for p in alive_players])

async def start_game(room, context):
    try:
        if not room:
            return False

        if not room.is_joining:
            return False

        total_players = len(room.players)
        if total_players < 4:
            await context.bot.send_message(
                chat_id=room.chat_id,
                text="❌ Room dibatalkan karena kurang pemain!\n"
                     "Silakan buat room baru untuk bermain.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎮 Buat Room Baru", callback_data="create_room")
                ]])
            )
            if room.id in active_rooms:
                del active_rooms[room.id]
            return False

        # Check minimum player requirement
        total_real_players = len([p for p in room.players if not p.get('is_bot', False)])
        total_bots = len([p for p in room.players if p.get('is_bot', False)])

        if total_real_players + total_bots < 4:
            return False #Do not send message here, handled by caller function


        # Start game process
        room.is_joining = False
        room.phase = "night"
        room.current_round = 1 # Added line

        # Assign roles
        roles = await assign_roles(room.players, room.mode)
        player_mentions = []

        # Send roles to players
        for player in room.players:
            player_id = player["id"]
            role = roles[player_id]
            player["role"] = role

            if not player.get("is_bot", False):
                try:
                    await context.bot.send_message(
                        chat_id=player_id,
                        text=f"🎭 Peran kamu: {role}\n\n📜 Deskripsi:\n{role_desc.get(role, '')}"
                    )
                    player_mentions.append(f"@{player['name']}")
                except Exception as e:
                    print(f"Error sending PM to {player_id}: {e}")

        # Start game announcement
        announcement = (
            f"🎮 Permainan dimulai!\n\n"
            f"👥 Pemain ({len(room.players)}):\n"
            f"{chr(10).join(player_mentions)}\n\n"
            f"📱 Cek PM untuk info peran"
        )

        await context.bot.send_message(
            chat_id=room.chat_id,
            text=announcement
        )

        # Update room state
        room.is_joining = False
        room.phase = "night"
        return True

    except Exception as e:
        print(f"Error in start_game: {e}")
        return False
    # Game start announcement
    announcement = (
        f"🌙 Malam telah tiba...\n\n"
        f"👥 Pemain ({len(game_data.get('players',[]))}):\n" #Corrected to access players from game_data
        f"{chr(10).join([player['name'] for player in game_data.get('players',[])])}\n\n" #Corrected to access player names
        f"📱 Cek PM untuk peran dan instruksi kalian\n\n"
        f"💭 Chat telah di-refresh untuk permainan baru"
    )

    # Send night GIF
    await context.bot.send_animation(
        chat_id=update.effective_chat.id,
        animation=GAME_GIFS["night"],
        caption="🌙 Malam hari dimulai..."
    )
    #Send initial PM
    for player in game_data.get('players',[]):
        await send_player_pm(context.bot, player['id'], player['role'])
    save_database(game_data)

async def assign_roles(players, mode):
    """Assign roles to players based on count and mode"""
    player_count = len(players)
    assigned_roles = {}

    # Calculate balanced role counts
    mafia_count = max(1, player_count // 4)  # About 25% are mafia
    special_roles_count = max(2, player_count // 6)  # Special roles like Detektif, Dokter

    # Assign mafia roles first
    mafia_players = random.sample(players, mafia_count)
    for i, player in enumerate(mafia_players):
        assigned_roles[player["id"]] = "Boss Mafia" if i == 0 else "Mafia"

    # Distribute special roles
    remaining_players = [p for p in players if p["id"] not in assigned_roles]
    special_role_players = random.sample(remaining_players, min(special_roles_count, len(remaining_players)))
    special_roles = ["Detektif", "Dokter", "Pengacara"]
    for i, player in enumerate(special_role_players):
        assigned_roles[player["id"]] = special_roles[i % len(special_roles)]

    # Assign remaining players as Warga
    remaining_players = [p for p in players if p["id"] not in assigned_roles]
    for player in remaining_players:
        assigned_roles[player["id"]] = "Warga"

    return assigned_roles

async def send_player_pm(bot, player_id, role):
    #Example PM message
    pm_message = f"Peranmu adalah {role}"

    await bot.send_message(chat_id=player_id, text=pm_message)

async def handle_night_actions(room, context):
    for player in room.get_alive_players():
        role = player["role"]
        if role in ["Detektif", "Dokter", "Mafia", "Boss Mafia"]:
            if player.get("is_bot", False):
                # Handle bot actions
                await handle_bot_night_action(player, room, context)
            else:
                # Send action notification for real players
                role_action = {
                    "Detektif": "🕵️‍ Detektif sedang mencari penjahat...",
                    "Dokter": "👨🏼‍⚕️ Dokter pergi bertugas malam...",
                    "Mafia": "🔪 Mafia memilih korbannya...",
                    "Boss Mafia": "👑 Boss Mafia memilih targetnya..."
                }
                await context.bot.send_message(
                    chat_id=player["id"], # Send PM to player
                    text=role_action[role]
                )

async def handle_bot_night_action(bot, room, context):
    # AI logic for bot actions based on role
    role = bot["role"]
    alive_players = room.get_alive_players()

    if role == "Mafia" or role == "Boss Mafia":
        target = random.choice([p for p in alive_players if p["id"] != bot["id"]])
        room.night_actions[bot["id"]] = {"action": "kill", "target": target["id"]}
    elif role == "Dokter":
        target = random.choice(alive_players)
        room.night_actions[bot["id"]] = {"action": "heal", "target": target["id"]}
    elif role == "Detektif":
        target = random.choice([p for p in alive_players if p["id"] != bot["id"]])
        room.night_actions[bot["id"]] = {"action": "investigate", "target": target["id"]}


# Added function to display alive players
async def display_alive_players(room):
    alive_players = []
    for i, p in enumerate(room.players):
        if p["is_alive"]:
            if p.get("is_bot", False):
                alive_players.append(f"{i+1}. 🤖 {p['name']}")
            else:
                alive_players.append(f"{i+1}. @{p['name']}")

    players_msg = (
        "Pemain hidup:\n" +
        "\n".join(alive_players) +
        "\n\n1 menit tersisa untuk tidur"
    )
    return players_msg

#Further development needed for command handling, room tagging, and join buttons.