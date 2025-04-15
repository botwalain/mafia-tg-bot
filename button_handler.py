from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from room_manager import get_room, get_room_by_player
from game_state import role_desc
from game_logic import assign_roles, handle_night_actions
import random
import asyncio
import time

async def handle_start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game start"""
    try:
        query = update.callback_query
        if not query:
            return

        room_id = int(query.data.split("_")[2])
        room = get_room(room_id)

        if not room or not room.is_joining:
            await query.answer("❌ Room not found or has already started!", show_alert=True)
            return

        if room.creator_id != query.from_user.id:
            await query.answer("❌ Only the room creator can start the game!", show_alert=True)
            return

        if not room.can_start():
            await query.answer("❌ At least 4 players are needed to start!", show_alert=True)
            return

        # Start game
        room.phase = "night"
        room.is_joining = False
        room.current_round = 1

        # Send game start message
        await context.bot.send_message(
            chat_id=room.chat_id,
            text="🎮 At least 4 players are needed to start!The game has started!\n\nThe players will receive their roles via PM..."
        )

        # Assign roles
        roles = await assign_roles(room.players, room.mode)

        # Send roles via PM
        for player in room.players:
            if not player.get("is_bot", False):
                role = roles[player["id"]]
                role_text = role_desc.get(role, "")
                try:
                    await context.bot.send_message(
                        chat_id=player["id"],
                        text=f"🎭 Your role: {role}\n\n📜 Deskripsi:\n{role_text}"
                    )
                except Exception as e:
                    print(f"Error sending PM to {player['id']}: {e}")

        # Display alive players
        alive_players = []
        for p in room.players:
            if p["is_alive"]:
                mention = f"🤖 Bot {p['name']}" if p.get("is_bot", False) else f"👤 @{p['name']}"
                alive_players.append(mention)

        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"👥 The surviving players ({len(alive_players)}):\n" + "\n".join(alive_players)
        )

        # Start night phase
        await handle_night_actions(room, context)

        # Start game loop
        asyncio.create_task(handle_game_loop(room, context))

    except Exception as e:
        print(f"Error in handle_start_game: {e}")
        if update.callback_query:
            await update.callback_query.answer("❌ An error occurred while starting the game!", show_alert=True)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if not query:
            return

        data_parts = query.data.split("_")
        if len(data_parts) < 2:
            return

        action = data_parts[0]

        if action == "join":
            try:
                room_id = int(data_parts[2])
                room = get_room(room_id)

                if not room:
                    await query.answer("❌ Room not found!", show_alert=True)
                    return

                if not room.is_joining:
                    await query.answer("❌ The room has already started!", show_alert=True)
                    return

                player_id = query.from_user.id
                player_name = query.from_user.username or str(player_id)

                # Check if player is already in room
                if any(p["id"] == player_id for p in room.players):
                    await query.answer("⚠️ You have already joined this room!", show_alert=True)
                    return

                result = room.add_player(player_id, player_name)

                if result["success"]:
                    # Single join notification above chat
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text=f"✅ @{player_name} has joined the room!",
                        parse_mode='HTML'
                    )

                    # Single join button if not joined
                    keyboard = []
                    if room.is_joining and not any(p["id"] == player_id for p in room.players):
                        keyboard = [[InlineKeyboardButton("➕ Join", callback_data=f"join_room_{room.id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    # Organized player list
                    player_mentions = []
                    # Admin first
                    for p in room.players:
                        if p.get('is_admin', False):
                            player_mentions.append(f"👑 @{p['name']} (Admin)")
                    # Then normal players
                    for p in room.players:
                        if not p.get('is_admin', False) and not p.get('is_bot', False):
                            player_mentions.append(f"👤 @{p['name']}")
                    # Bots last
                    for p in room.players:
                        if p.get('is_bot', False):
                            player_mentions.append(f"🤖 Bot {p['name']}")

                    time_left = max(0, room.join_timer - (time.time() - room.start_time))
                    await query.message.edit_text(
                        f"📢 Room #{room.id}\n\n"
                        f"👥 Players ({len(room.players)}):\n"
                        f"{chr(10).join(player_mentions)}\n\n"
                        f"⏳ {int(time_left)} seconds remaining",
                        reply_markup=reply_markup
                    )

                    if result["success"]:
                        await query.answer("✅ Successfully joined!", show_alert=True)
            except Exception as e:
                print(f"Error in join action: {e}")
                await query.answer("❌ An error occurred while joining!", show_alert=True)

        if action == "cancel":
            room_id = int(data_parts[2])
            room = get_room(room_id)

            if not room:
                await query.answer("❌ Room not found!", show_alert=True)
                return

            if room.creator_id != query.from_user.id:
                await query.answer("❌ Only the room creator can cancel!", show_alert=True)
                return

            # Cancel room logic
            if room.id in active_rooms:
                del active_rooms[room.id]
                await query.message.edit_text(
                    "🚫 Room canceled.\nPlease create a new room to play.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🎮 Me Again", callback_data="create_room")
                    ]])
                )
            return

        elif action == "start":
            room_id = int(data_parts[1])
            room = get_room(room_id)

            if not room:
                await query.answer("❌ Room not found!", show_alert=True)
                return

            if room.creator_id != query.from_user.id:
                await query.answer("❌ Only the room creator can start the game!", show_alert=True)
                return

            if not room.can_start():
                human_count = len([p for p in room.players if not p.get('is_bot', False)])
                if room.bot_count == 0:
                    await query.answer(f"❌ At least 4 players needed! (Now: {human_count})", show_alert=True)
                else:
                    await query.answer(f"❌ Minimum of 1 player needed and a total of 4 with bots! (Player: {human_count})", show_alert=True)
                return

            # Initialize game state and assign roles
            room.phase = "night"
            room.is_joining = False
            room.current_round = 1

            # Assign roles and send PMs
            from game_logic import assign_roles
            roles = await assign_roles(room.players, room.mode)

            for player in room.players:
                player["role"] = roles[player["id"]]
                if not player.get("is_bot", False):
                    try:
                        from game_state import role_desc
                        role_text = role_desc.get(roles[player["id"]], "")
                        await context.bot.send_message(
                            chat_id=player["id"],
                            text=f"🎭 Your role: {roles[player['id']]}\n\n📜 Description:\n{role_text}"
                        )
                    except Exception as e:
                        print(f"Error sending PM to {player['id']}: {e}")


            # Send night phase message with GIF
            from game_state import GAME_GIFS
            night_msg = (
                "🌃 A terrible night!\n"
                "Only the bravest and most fearless take to the streets. "
                "We will try to count what falls in the morning..."
            )
            await context.bot.send_animation(
                chat_id=room.chat_id,
                animation=GAME_GIFS["night"],
                caption=night_msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # Display alive players
            alive_players = [f"{i+1}. {p['name']}" for i, p in enumerate(room.players) if p["is_alive"]]
            players_msg = (
                "Living player:\n" +
                "\n".join(alive_players) +
                "\n\n 1 minutes left to sleep"
            )
            await context.bot.send_message(chat_id=room.chat_id, text=players_msg)

            # Start night phase for important roles
            await handle_night_actions(room, context)

            # Start game loop
            asyncio.create_task(handle_game_loop(room, context))

        elif query.data.startswith("cancel_room_"):
            try:
                room_id = int(query.data.split("_")[2])
                room = get_room(room_id)

                if not room:
                    await query.answer("❌ Room not found!", show_alert=True)
                    return

                if room.creator_id != query.from_user.id:
                    await query.answer("❌ Only the room creator can cancel the room!", show_alert=True)
                    return

                # Cancel room logic
                if room.id in active_rooms:
                    del active_rooms[room.id]

                    # Clear chat with cancel message
                    await query.message.reply_text("🔄 The chat has been cleared.")

                    # Show cancellation message with option to create new room
                    await query.message.edit_text(
                        "🚫 Room dibatalkan.\n"
                        "Silakan buat room baru untuk bermain.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🎮 Me Again", callback_data="create_room")
                        ]])
                    )

            except Exception as e:
                print(f"Error canceling room: {e}")
                await query.answer("❌ Failed to cancel the room!", show_alert=True)
        elif query.data.startswith("join_room_"):
            try:
                room_id = int(query.data.split("_")[2])
                room = get_room(room_id)

                if not room or not room.is_joining:
                    await query.answer("❌ Room not found or has already started!", show_alert=True)
                    return

                player_id = query.from_user.id
                player_name = query.from_user.username or str(player_id)

                # Check if player is already in room
                if any(p["id"] == player_id for p in room.players):
                    await query.answer("⚠️ You have already joined this room!", show_alert=True)
                    return

                result = room.add_player(player_id, player_name)

                if result["success"]:
                    # Send join notification above chat
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text=f"✅ @{player_name} has joined the room!"
                    )

                    # Only show join button
                    keyboard = [[InlineKeyboardButton("🔗 Join Room", callback_data=f"join_room_{room.id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    # Format players list
                    player_mentions = []
                    for p in room.players:
                        if p.get('is_bot', False):
                            player_mentions.append(f"🤖 Bot {p['name']}")
                        else:
                            player_mentions.append(f"@{p['name']}")

                    time_left = max(0, room.join_timer - (time.time() - room.start_time))

                    await query.message.edit_text(
                        f"📢 Registration is open.\n\n"
                        f"Registered:\n"
                        f"{chr(10).join(player_mentions)}\n\n"
                        f"⏳ {int(time_left)} seconds remaining until the end of registration",
                        reply_markup=reply_markup
                    )
                    await query.answer("✅ Successfully joined!", show_alert=True)
                else:
                    await query.answer(result["message"], show_alert=True)

                if result["success"]:
                    # Show notification above chat
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text=f"📢 Notification: {result['message']}\n👤 @{player_name} has joined!",
                        parse_mode='HTML'
                    )

                    # Update room message with current players
                    player_mentions = room.get_player_mentions()
                    keyboard = await get_room_keyboard(room, player_id)
                    await query.message.edit_text(
                        f"📢 Open room\n\n"
                        f"👥 Players ({len(room.players)}):\n"
                        f"{chr(10).join(player_mentions)}\n\n"
                        f"⏳ Waiting for players to join...",
                        reply_markup=keyboard
                    )
                else:
                    await query.answer(result["message"], show_alert=True)

            except Exception as e:
                print(f"Error joining room: {e}")
                await query.answer("❌ Failed to join the room!", show_alert=True)


        elif query.data.startswith("setup_bot_"):
            try:
                from game_state import BOT_NAMES
                import random

                parts = query.data.split("_")
                room_id = int(parts[2])
                mode = parts[3]
                bot_count = int(parts[4])

                room = get_room(room_id)
                if not room:
                    await query.answer("❌ Room not found!", show_alert=True)
                    return

                if room.creator_id != query.from_user.id:
                    await query.answer("❌ Only the room creator can manage the bot!", show_alert=True)
                    return

                # Setup room with chosen mode and bots
                room.setup(mode, bot_count)

                # Add creator as admin
                room.add_player(query.from_user.id, query.from_user.username or str(query.from_user.id), is_admin=True)

                # Add bots if enabled
                if bot_count > 0:
                    for i in range(bot_count):
                        bot_id = -(room_id * 10 + i)
                        bot_name = random.choice(BOT_NAMES)
                        room.add_player(bot_id, bot_name, is_bot=True)

                # Single join button
                keyboard = [[InlineKeyboardButton("🎮 Join Game", callback_data=f"join_room_{room.id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Clean player list format
                player_list = []
                for p in room.players:
                    if p.get('is_admin', False):
                        player_list.append(f"👑 @{p['name']} (Admin)")
                    elif p.get('is_bot', False):
                        player_list.append(f"🤖 Bot {p['name']}")
                    else:
                        player_list.append(f"👤 @{p['name']}")

                await query.message.edit_text(
                    f"✨ Room #{room.id} dibuat!\n\n"
                    f"🎮 Mode: {mode.title()}\n"
                    f"👥 Player ({len(room.players)}):\n"
                    f"{chr(10).join(player_list)}\n\n"
                    f"⏳ Time for join: 60 second",
                    reply_markup=reply_markup
                )

                # Start room timer
                asyncio.create_task(handle_room_timer(room, query.message, context))

            except Exception as e:
                print(f"Error in setup_bot: {e}")
                await query.answer("❌ An error occurred!", show_alert=True)
        elif query.data.startswith("leave_room_"):
            try:
                room_id = int(query.data.split('_')[2])
                room = get_room(room_id)
                if not room:
                    await query.answer('❌ Room not found!', show_alert=True)
                    return

                player_id = query.from_user.id
                result = room.remove_player(player_id)
                if result['success']:
                    await query.answer('✅ Successfully left the room!', show_alert=True)
                    await context.bot.send_message(
                        chat_id=room.chat_id,
                        text=f'👤 @{query.from_user.username or player_id} has left the room!'
                    )
                    keyboard = await get_room_keyboard(room, query.from_user.id)
                    player_mentions = room.get_player_mentions()
                    await query.message.edit_text(
                        f'📢 Open room\n\n'
                        f'👥 Player ({len(room.players)}):\n'
                        f'{chr(10).join(player_mentions)}\n\n'
                        f'⏳ Waiting for players to join...',
                        reply_markup=keyboard
                    )
                else:
                    await query.answer(result['message'], show_alert=True)
            except Exception as e:
                print(f'Error leaving room: {e}')
                await query.answer('❌ Failed to leave the room!', show_alert=True)

    except Exception as e:
        print(f"Error in handle_callback: {e}")
        await query.answer("❌ An error occurred!", show_alert=True)


async def assign_roles(players, mode):
    available_roles = list(role_desc.keys())
    assigned_roles = {}

    # Ensure at least one Mafia
    mafia_count = max(1, len(players) // 4)
    mafia_players = random.sample(players, mafia_count)

    for player in mafia_players:
        assigned_roles[player["id"]] = "Mafia"

    # Assign remaining roles
    remaining_players = [p for p in players if p["id"] not in assigned_roles]
    remaining_roles = [r for r in available_roles if r != "Mafia"]

    for player in remaining_players:
        role = random.choice(remaining_roles)
        assigned_roles[player["id"]] = role

    return assigned_roles

async def handle_game_loop(room, context):
    from game_logic import handle_night_phase, handle_day_phase, handle_voting_phase, check_win_condition
    from game_state import GAME_GIFS

    try:
        # Clear chat history
        await context.bot.send_message(
            chat_id=room.group_id,
            text="🔄 The game has started!Chat has been refreshed."
        )

        # Initial night phase
        await context.bot.send_animation(
            chat_id=room.group_id,
            animation=GAME_GIFS["night"],
            caption="🌙 The first night begins...\nAll players check PM for instructions on your respective roles!"
        )

        while room.phase != "ended":
            if room.phase == "night":
                await handle_night_phase(room, context)
            elif room.phase == "day":
                await handle_day_phase(room, context)
            elif room.phase == "voting":
                await handle_voting_phase(room, context)

            await check_win_condition(room, context)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in game loop: {e}")

async def get_room_keyboard(room, player_id):
    keyboard = []
    try:
        if room and room.is_joining:
            # Always show join button for non-players
            if not any(p["id"] == player_id for p in room.players):
                keyboard.append([InlineKeyboardButton("➕ Join", callback_data=f"join_room_{room.id}")])
            elif player_id:  # Show leave button for existing players
                keyboard.append([InlineKeyboardButton("❌ Leave", callback_data=f"leave_room_{room.id}")])

        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        print(f"Error creating keyboard: {e}")
        return InlineKeyboardMarkup([[]])

async def handle_room_timer(room, message, context):
    try:
        time_left = room.join_timer
        while time_left > 0 and room.is_joining:
            time_left -= 1
            await asyncio.sleep(1)
            if time_left <= 0:
                await context.bot.send_message(chat_id=room.chat_id, text="Waktu habis! Room akan ditutup.")
                room.is_joining = False
                return
            keyboard = await get_room_keyboard(room, room.creator_id)

            # Format player list with proper order
            player_mentions = []

            # Add real players first
            for p in room.players:
                if not p.get('is_bot', False):
                    player_mentions.append(f"@{p['name']}")

            # Add exactly 3 bots
            bot_count = 0
            for p in room.players:
                if p.get('is_bot', False) and bot_count < 3:
                    player_mentions.append(f"🤖 Bot {p['name']}")
                    bot_count += 1

            await message.edit_text(
                f"📢 Registration is open.\n\n"
                f"Registered:\n"
                f"{chr(10).join(player_mentions)}\n\n"
                f"⏳ {int(time_left)} seconds remaining until the end of registration",
                reply_markup=keyboard
            )

    except Exception as e:
        print(f"Error in room timer: {e}")



active_rooms = {}
BOT_NAMES = ["Bot1", "Bot2", "Bot3", "Bot4", "Bot5", "Bot6"]
