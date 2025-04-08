"""
Room Management System
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
"""

import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from game_state import BOT_NAMES, GAME_GIFS, game_data

class Room:
    def __init__(self, creator_id, chat_id):
        self.id = random.randint(10000, 99999)
        self.creator_id = creator_id
        self.chat_id = chat_id
        self.players = []
        self.phase = "setup"
        self.mode = None
        self.bot_count = 0
        self.join_timer = 60
        self.is_joining = True
        self.start_time = time.time()

    def add_player(self, user_id, username, is_bot=False, is_admin=False):
        if any(p["id"] == user_id for p in self.players):
            return False, "⚠️ Sudah bergabung!"

        self.players.append({
            "id": user_id,
            "name": username,
            "role": None,
            "is_bot": is_bot,
            "is_alive": True,
            "is_admin": is_admin
        })
        return True, "✅ Berhasil bergabung!"

    def remove_player(self, user_id):
        self.players = [p for p in self.players if p["id"] != user_id]
        return len(self.players) == 0

    def can_start(self):
        return len(self.players) >= 4

    def setup(self, mode, bot_count=0):
        self.mode = mode
        self.bot_count = min(bot_count, 3) # Maximum 3 bots
        self.is_setup = True
        self.is_joining = True
        self.phase = "waiting"
        self.start_time = time.time()
        self.setup_timeout = time.time() + 60  # 1 minute timeout for setup
        self.game_roles = {}  # Clear any previous roles
        self.buttons_visible = True  # Add flag for button visibility

        # Reset player states
        self.players = []
        # Add creator as first player
        self.add_player(self.creator_id, None, is_admin=True)


        # Add bots immediately after setup
        if self.bot_count > 0:
            from game_state import BOT_NAMES
            for i in range(self.bot_count):
                bot_id = -(1000 + i)
                bot_name = random.choice(BOT_NAMES)
                self.add_player(bot_id, bot_name, is_bot=True)

    def get_player_mentions(self):
        mentions = []

        # First get creator if present
        creator = next((p for p in self.players if p.get('is_admin', False)), None)
        if creator:
            mentions.append(f"@{creator['name']}")

        # Add bots with proper formatting
        for p in self.players:
            if p.get('is_bot', False):
                mentions.append(f"🤖 Bot {p['name']}")

        # Add other real players
        for p in self.players:
            if not p.get('is_bot', False) and not p.get('is_admin', False):
                mentions.append(f"@{p['name']}")

        return mentions

    def get_alive_players(self):
        return [p for p in self.players if p["is_alive"]]


active_rooms = {}

def create_room(creator_id, chat_id):
    room = Room(creator_id, chat_id)
    active_rooms[room.id] = room
    return room

def get_room(room_id):
    return active_rooms.get(room_id)

def save_room_to_db(room):
    try:
        game_data["active_rooms"] = game_data.get("active_rooms", {})
        game_data["active_rooms"][str(room.id)] = {
            "creator_id": room.creator_id,
            "mode": room.mode,
            "players": room.players,
            "bot_count": room.bot_count,
            "created_at": time.time()
        }
        save_database(game_data)
    except Exception as e:
        print(f"Error saving room to database: {e}")

def cleanup_inactive_rooms():
    current_time = time.time()
    if "active_rooms" in game_data:
        for room_id in list(game_data["active_rooms"].keys()):
            room = game_data["active_rooms"][room_id]
            # Remove room if no real players for 30 minutes
            if current_time - room["created_at"] > 1800 and not any(not p.get("is_bot", False) for p in room["players"]):
                del game_data["active_rooms"][room_id]
                if room_id in active_rooms:
                    del active_rooms[room_id]
        save_database(game_data)

def cleanup_user_rooms(user_id, chat_id):
    for room_id in list(active_rooms.keys()):
        room = active_rooms[room_id]
        if (room.creator_id == user_id and room.chat_id == chat_id) or \
           (not room.is_joining and any(p["id"] == user_id for p in room.players)):
            del active_rooms[room_id]

def get_room_by_player(player_id):
    for room_id, room in list(active_rooms.items()):
        if any(p["id"] == player_id for p in room.players):
            return room
    return None

def get_room_by_chat(chat_id):
    for room in active_rooms.values():
        if str(room.chat_id) == str(chat_id):
            return room
    return None

async def get_room_keyboard(room, user_id):
    try:
        if room and room.is_joining:
            # Only show join button if user is not already in room
            if not any(p["id"] == user_id for p in room.players):
                return InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔗 Join Room", callback_data=f"join_room_{room.id}")
                ]])
        return InlineKeyboardMarkup([])
    except Exception as e:
        print(f"Error creating keyboard: {e}")
        return InlineKeyboardMarkup([])

def handle_room_leave(room, player_id):
    room.remove_player(player_id)
    real_players = [p for p in room.players if not p.get('is_bot', False)]

    if len(real_players) == 0:
        if room.id in active_rooms:
            del active_rooms[room.id]
        return True, "🚫 Room dihapus karena hanya berisi bot."
    return False, "✅ Berhasil keluar dari room."

async def handle_room_timer(room, message, context):
    try:
        start_time = time.time()
        reminder_times = [45, 30, 15, 5]
        last_update = 0
        update_interval = 10  # Increased to avoid rate limits

        while time.time() - start_time < room.join_timer and room.is_joining:
            time_left = room.join_timer - (time.time() - start_time)

            # Single join button
            keyboard = []
            if room.is_joining:
                keyboard = [[InlineKeyboardButton("➕ Bergabung", callback_data=f"join_room_{room.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Format player list
            player_list = []
            for p in room.players:
                if p.get('is_admin', False):
                    player_list.append(f"👑 @{p['name']} (Admin)")
                elif p.get('is_bot', False):
                    player_list.append(f"🤖 Bot {p['name']}")
                else:
                    player_list.append(f"👤 @{p['name']}")

            current_time = time.time()
            if current_time - last_update >= update_interval:
                try:
                    await message.edit_text(
                        f"📢 Room #{room.id}\n\n"
                        f"👥 Pemain ({len(room.players)}):\n"
                        f"{chr(10).join(player_list)}\n\n"
                        f"⏳ {int(time_left)} detik tersisa",
                        reply_markup=reply_markup
                    )
                    last_update = current_time
                except Exception as e:
                    if "429" in str(e):
                        await asyncio.sleep(5)  # Longer delay on rate limit

            # Send reminder if needed
            if int(time_left) in reminder_times:
                try:
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text=f"⏰ {int(time_left)} detik tersisa!\n"
                             f"👥 Total Pemain: {len(room.players)}"
                    )
                    reminder_times.remove(int(time_left))
                except Exception as e:
                    print(f"Error sending reminder: {e}")

            # Check if timer ended
            if time_left <= 0:
                total_players = len(room.players)
                real_players = len([p for p in room.players if not p.get('is_bot', False)])

                # Start game if at least 4 players (including bots)
                if total_players >= 4:
                    room.is_joining = False
                    from game_logic import start_game
                    await start_game(room, context)
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text="🎮 Game akan dimulai! Cek PM untuk info peran."
                    )
                else:
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text=f"❌ Room dibatalkan karena kurang pemain\n"
                             f"Minimal 4 pemain (termasuk bot)\n"
                             f"Total pemain: {total_players}\n\n"
                             f"Silakan buat room baru untuk bermain.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🎮 Buat Room Baru", callback_data="create_room")
                        ]])
                    )
                    # Cleanup room
                    if room.id in active_rooms:
                        del active_rooms[room.id]
                break

            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error in room timer: {e}")


def save_database(data):
    # Replace this with your actual database saving logic
    print(f"Saving data to database: {data}")

async def handle_query(update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("start_game_"):
        try:
            room_id = int(query.data.split("_")[2])
            room = get_room(room_id)
            if room and room.can_start():
                #Start Game Logic Here.  This is a placeholder.  You'll need to implement
                #role assignment, game start messages, and game logic.
                await query.message.edit_text("Game Started!")
        except Exception as e:
            print(f"Error starting game: {e}")
            await query.answer("❌ Gagal memulai game!", show_alert=True)

    elif query.data.startswith("join_room_"):
        try:
            room_id = int(query.data.split("_")[2])
            room = get_room(room_id)
            if room and room.is_joining:
                player_id = query.from_user.id
                player_name = query.from_user.username
                result = room.add_player(player_id, player_name)
                if result[0]:
                    await query.message.edit_text(result[1])
                else:
                    await query.answer(result[1], show_alert=True)

        except Exception as e:
            print(f"Error joining room: {e}")
            await query.answer("❌ Gagal bergabung ke room!", show_alert=True)


    elif query.data.startswith("leave_room_"):
        try:
            room_id = int(query.data.split("_")[2])
            room = get_room(room_id)
            player_id = query.from_user.id

            success, message = handle_room_leave(room, player_id)
            if success:
                await query.message.edit_text(message)
            else:
                await query.message.edit_text(message)
        except Exception as e:
            print(f"Error leaving room: {e}")
            await query.answer("❌ Gagal keluar dari room!", show_alert=True)

    elif query.data.startswith("cancel_room_"):
        try:
            room_id = int(query.data.split("_")[2])
            room = get_room(room_id)
            if room:
                if room.id in active_rooms:
                    del active_rooms[room.id]
                await query.message.edit_text("Room dibatalkan!")
        except Exception as e:
            print(f"Error cancelling room: {e}")
            await query.answer("❌ Gagal membatalkan room!", show_alert=True)