"""
Bot Commands Handler  
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from game_state import GAME_NAME, GAME_VERSION, GAME_CREATOR, role_desc, game_data, BOT_NAMES
from room_manager import create_room, get_room, get_room_keyboard, active_rooms, get_room_by_player, cleanup_user_rooms
from game_logic import start_game, process_night_actions, handle_voting, assign_roles
from database import save_database
import random
import time
import asyncio

from command_handler import CommandHandler
command_handler = CommandHandler()

# Track last extend time per room
extend_cooldowns = {}

async def denyroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force leave from current room"""
    user_id = update.effective_user.id
    username = update.effective_user.username or str(user_id)
    room = get_room_by_player(user_id)

    if not room:
        await update.message.reply_text("❌ You are not in the room!")
        return

    # Remove player and check result
    was_cancelled = room.remove_player(user_id)

    if was_cancelled:
        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"🚫 Room cancelled because @{username} (host) left."
        )
        if room.id in active_rooms:
            del active_rooms[room.id]
    else:
        # Send leave notification
        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"👋 @{username} has left the room."
        )

        # Update room message if still joining
        if room.is_joining:
            player_list = []
            for p in room.players:
                if p.get('is_bot', False):
                    player_list.append(f"🤖 Bot {p['name']}")
                else:
                    player_list.append(f"👤 @{p['name']}")

            keyboard = await get_room_keyboard(room, None)
            try:
                await context.bot.edit_message_text(
                    chat_id=room.chat_id,
                    message_id=room.message_id,
                    text=f"📢 Room is open.\n\n"
                         f"👥 Total Players: {len(room.players)}\n"
                         f"{chr(10).join(player_list)}",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating room message: {e}")

    await update.message.reply_text("✅ You have left the room.")

command_handler.register_command("denyroom", denyroom)


async def extend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or str(user_id)
    room = get_room_by_player(user_id)

    if not room:
        await update.message.reply_text("❌ You are not in the room!")
        return

    if room.creator_id != user_id:
        await update.message.reply_text("❌ Only the room creator can use /extend!")
        return

    if not room:
        await update.message.reply_text("❌ You are not in the room!")
        return

    if room.creator_id != user_id:
        await update.message.reply_text("❌ Only the host can use /extend!")
        return

    # Add 30 seconds
    room.join_timer += 30

    # Send notification
    await context.bot.send_message(
        chat_id=room.chat_id,
        text=f"⏰ @{username} added +30 seconds to the registration time!"
    )

    if not room:
        await update.message.reply_text("❌ You are not in the room!")
        return

    if not room.is_joining:
        await update.message.reply_text("❌ The room has already started!")
        return

    if room.creator_id != user_id:
        await update.message.reply_text("❌ Only the host can use /extend!")
        return

    if room.creator_id != user_id:
        await update.message.reply_text("❌ Only the room creator can use /extend!")
        return

    if time.time() - room.start_time > room.room_timeout:
        if room.id in active_rooms:
            del active_rooms[room.id]
            await update.message.reply_text("🕐 The room has ended due to exceeding the 2-hour time limit.")
        return

    current_time = time.time()
    last_extend = extend_cooldowns.get(room.id, 0)

    if current_time - last_extend < 15:
        remaining = int(15 - (current_time - last_extend))
        await update.message.reply_text(f"⏳ Wait {remaining} seconds to extend again!")
        return

    room.join_timer += 30
    extend_cooldowns[room.id] = current_time
    await update.message.reply_text("⌛ Registration time extended by 30 seconds!")

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler for /startgame - only usable by room creator"""
    try:
        user_id = update.effective_user.id
        room = get_room_by_player(user_id)

        if not room:
            await update.message.reply_text("❌ You are not in the room!")
            return

        if room.creator_id != user_id:
            await update.message.reply_text("❌ Only the room creator can start the game!")
            return

        if not room.is_joining:
            await update.message.reply_text("❌ The room has already started!")
            return

        # Count both real players and bots for minimum requirement
        total_players = len(room.players)
        if total_players < 4:
            await update.message.reply_text(f"❌ Minimum of 4 players required! (Currently: {total_players})")
            return

        # Start the game
        await start_game(update, context)

    except Exception as e:
        print(f"Error in startgame command: {e}")
        await update.message.reply_text("❌ An error occurred while starting the game!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = f"Welcome to {GAME_NAME} {GAME_VERSION}\n{GAME_CREATOR}"

    chat_type = update.effective_chat.type
    if chat_type == "private":
        # PM Menu
        keyboard = [
            [InlineKeyboardButton("🎮 Join Game", callback_data="join_game")],
            [InlineKeyboardButton("🛍️ Shop", callback_data="shop")],
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("👥 Roles", callback_data="roles")]
        ]
    else:
        # Group Menu  
        keyboard = [
            [InlineKeyboardButton("🎮 Create Room", callback_data="create_room")],
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("🔍 Rules", callback_data="rules")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🎮 Commands:\n"
        "/start - Start the bot\n"
        "/help - Help\n" 
        "/rules - Game rules\n"
        "/roles - List of roles\n"
        "/quitroom - Leave the room\n"
        "/extend - Add time (+30s)\n\n"
        "ℹ️ For more information, use the button below"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, reply_markup=reply_markup)

async def handle_setup_timeout(room, message):
    try:
        await asyncio.sleep(60)  # Wait 1 minute
        if room and not room.is_joining:
            # Clean up room if setup not completed
            if room.id in active_rooms:
                del active_rooms[room.id]
            await message.edit_text(
                "⏰ Room creation time has expired!\n"
                "Please create a new room.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")
                ]])
            )
    except Exception as e:
        print(f"Error in setup timeout: {e}")

async def quit_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    room = get_room_by_player(user_id)
    if room:
        room.remove_player(user_id)
        await update.message.reply_text("You have left the room.")
    else:
        await update.message.reply_text("You are not in a room.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    try:
        if not query:
            return

        # Don't answer query yet - let individual handlers do it
        data = query.data
        if query.data == "main_menu":
            # Cleanup any pending room
            user_id = query.from_user.id
            room = get_room_by_player(user_id)
            if room and not room.is_joining:
                if room.id in active_rooms:
                    del active_rooms[room.id]

            if query.message.chat.type == "private":
                keyboard = [
                    [InlineKeyboardButton("🎮 Create Room", callback_data="create_room")],
                    [InlineKeyboardButton("👥 View Roles", callback_data="roles")],
                    [InlineKeyboardButton("❓ Help", callback_data="help")],
                    [InlineKeyboardButton("🛍️ Shop", callback_data="shop")],
                    [InlineKeyboardButton("📊 Stats", callback_data="stats")]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("🎮 Create Room", callback_data="create_room")],
                    [InlineKeyboardButton("👥 View Roles", callback_data="roles")],
                    [InlineKeyboardButton("❓ Help", callback_data="help")]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await query.message.edit_text("Main Menu:", reply_markup=reply_markup)
            except:
                await query.message.reply_text("Main Menu:", reply_markup=reply_markup)

        elif query.data == "create_room":
            if query.message.chat.type == "private":
                await query.answer("❌ Rooms can only be created in groups!", show_alert=True)
                return

            # Cleanup existing rooms
            cleanup_user_rooms(query.from_user.id, query.message.chat.id)

            # Create new room
            room = create_room(query.from_user.id, query.message.chat.id)
            if not room:
                await query.answer("❌ There is already an active room in this group!", show_alert=True)
                return

            # Add creator as player
            room.add_player(query.from_user.id, query.from_user.username, is_admin=True)
            if not room:
                await query.answer("❌ There is already an active room in this group!", show_alert=True)
                return

            keyboard = [
                [InlineKeyboardButton("👥 Normal Mode", callback_data="mode_normal"),
                 InlineKeyboardButton("🎲 Random Mode", callback_data="mode_random")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"⚙️ Room Settings:\n"
                f"🔢 Room ID: {room.id}\n"
                f"👑 Admin: @{query.from_user.username}\n\n"
                f"Select the game mode:",
                reply_markup=reply_markup
            )

        elif query.data.startswith("select_mode_"):
            parts = query.data.split("_")
            mode = parts[2]
            room_id = int(parts[3])

            room = get_room(room_id)
            if not room or query.from_user.id != room.creator_id:
                await query.answer("❌ Access denied!", show_alert=True)
                return

            keyboard = [
                [InlineKeyboardButton("✅ Yes (3 Bots)", callback_data=f"setup_room_{room_id}_{mode}_3"),
                 InlineKeyboardButton("❌ No", callback_data=f"setup_room_{room_id}_{mode}_0")],
                [InlineKeyboardButton("⬅️ Back", callback_data="create_room")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                f"🤖 Add bots to the room?\n"
                f"Mode: {mode.title()}\n"
                f"🔢 Room ID: {room_id}",
                reply_markup=reply_markup
            )

        elif query.data.startswith("create_room_no_bots_"):
            mode = query.data.split("_")[-1]
            room = create_room(query.from_user.id, mode, 0)
            keyboard = await get_room_keyboard(room, query.from_user.id)
            await query.message.edit_text(
                f"✨ Room successfully created!\n\n"
                f"🎮 Mode: {mode.title()}\n"
                f"🤖 Bots: 0/3\n"
                f"🔢 Room ID: {room.id}\n"
                f"👥 Players: {len(room.players)}/12\n\n"
                f"⏳ Waiting for players...\n"
                f"The room will start in 60 seconds!",
                reply_markup=keyboard
            )
            await handle_room_timer(room, query.message, context)

        elif query.data.startswith("create_room_with_bots_"):
            mode = query.data.split("_")[-1]
            try:
                if query.message.chat.type == "private":
                    await query.answer("❌ Rooms can only be created in groups!", show_alert=True)
                    return

                room = create_room(query.from_user.id, query.message.chat_id, mode, 3)
                if not room:
                    await query.answer("❌ There's already an active room in this group!", show_alert=True)
                    return
                keyboard = []

                is_creator = query.from_user.id == room.creator_id
                is_player = any(p["id"] == query.from_user.id for p in room.players)

                if is_creator:
                    if len(room.players) >= 4:
                        keyboard.append([InlineKeyboardButton("▶️ Start Game", callback_data=f"start_game_{room.id}")])
                    keyboard.append([InlineKeyboardButton("🚫 Cancel Room", callback_data=f"cancel_room_{room.id}")])
                elif not is_player:
                    keyboard.append([InlineKeyboardButton("➕ Join Room", callback_data=f"join_room_{room.id}")])
                else:
                    keyboard.append([InlineKeyboardButton("❌ Leave", callback_data=f"leave_room_{room.id}")])

                reply_markup = InlineKeyboardMarkup(keyboard)
                player_list = []
                for p in room.players:
                    if p.get('is_bot', False):
                        player_list.append(f"🤖 Bot {p['name']}")
                    else:
                        player_list.append(f"👤 @{p['name']}")

                mentions = room.get_player_mentions()
                message = await query.message.edit_text(
                    f"✨ Room successfully created!\n\n"
                    f"🎮 Mode: {mode.title()}\n"
                    f"🤖 AI Players: Yes (3 Bots)\n"
                    f"🔢 Room ID: {room.id}\n"
                    f"👥 Total Players: {len(room.players)}\n"
                    f"{chr(10).join(mentions)}\n\n"
                    f"⏳ {60} seconds remaining\n"
                    f"Type /extend to add 30 more seconds",
                    reply_markup=reply_markup
                )
                await handle_room_timer(room, message, context)
            except Exception as e:
                print(f"Error creating room with bots: {e}")
                await query.answer("❌ Failed to create the room, please try again", show_alert=True)
            await handle_room_timer(room, message, context)

        elif query.data.startswith("select_bots_"):
            bot_count = int(query.data.split("_")[2])
            setup = context.user_data["room_setup"]
            setup["bot_count"] = bot_count

            room = create_room(query.from_user.id, setup["mode"], bot_count)

            # Add creator to room automatically
            creator_result = room.add_player(query.from_user.id, query.from_user.username or str(query.from_user.id), is_admin=True)

            # Add the bots if requested
            if bot_count > 0:
                for i in range(bot_count):
                    bot_id = -(1000 + i)
                    bot_name = random.choice(BOT_NAMES)
                    room.add_player(bot_id, bot_name, is_bot=True)

            keyboard = get_room_keyboard(room, query.from_user.id)
            player_list = room.get_player_mentions()

            await query.message.edit_text(
                f"✨ Room successfully created!\n\n"
                f"🎮 Mode: {setup['mode'].title()}\n"
                f"🔢 Room ID: {room.id}\n"
                f"👥 Players ({len(room.players)}):\n"
                f"{chr(10).join(player_list)}\n\n"
                f"⏳ Waiting for players...\n"
                f"The room will start in 60 seconds!",
                reply_markup=keyboard,
                parse_mode='HTML'
            )

            # Start room timer and reminder system
            asyncio.create_task(handle_room_timer(room, query.message, context))

        elif query.data == "remove_bot":
            room_id = context.user_data.get("current_room_id")
            room = get_room(room_id)

            if room and room.bot_count > 0:
                room.bot_count -= 1
                save_database(game_data)

            keyboard = await get_room_keyboard(room, query.from_user.id)
            await query.message.edit_text(
                f"✨ Room settings:\n\n"
                f"🎮 Mode: {room.mode.title()}\n"
                f"🤖 Bot: {room.bot_count}/3\n"
                f"🔢 Room ID: {room.id}\n"
                f"👥 Players: {len(room.players)}/12\n\n"
                f"⏳ Waiting for players...",
                reply_markup=keyboard
            )

        elif query.data.startswith("cancel_room_"):
            room_id = int(query.data.split("_")[1])
            room = get_room(room_id)

            if not room:
                await query.answer("❌ Room not found!", show_alert=True)
                return

            if room.creator_id != query.from_user.id:
                await query.answer("❌ Only the room creator can cancel the room!", show_alert=True)
                return

            if room.id in active_rooms:
                del active_rooms[room.id]
                await query.message.edit_text(
                    "🚫 Room canceled.\n"
                    "Please create a new room.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")
                    ]])
                )

        elif query.data.startswith("mode_"):
            try:
                mode = query.data.split("_")[1]

                # Get or create room
                room = get_room_by_player(query.from_user.id)
                if not room:
                    room = create_room(query.from_user.id, query.message.chat.id)
                    if not room:
                        await query.answer("❌ There's already an active room in this group!", show_alert=True)
                        return

                # Verify creator permissions
                if room.creator_id != query.from_user.id:
                    await query.answer("❌ Only the room creator can set the mode!", show_alert=True)
                    return

                # Set mode and update keyboard
                room.mode = mode
                room.add_player(query.from_user.id, query.from_user.username, is_admin=True)

                # Create keyboard for bot selection (yes/no)
                keyboard = [
                    [InlineKeyboardButton("✅ Yes (3 Bots)", callback_data=f"setup_bot_{room.id}_{mode}_3"),
                     InlineKeyboardButton("❌ No", callback_data=f"setup_bot_{room.id}_{mode}_0")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="create_room")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(
                    f"🤖 Add AI Players to the room?\n\n"
                    f"🎮 Mode: {mode.title()}\n"
                    f"🔢 Room ID: {room.id}",
                    reply_markup=reply_markup
                )

                # Start timeout timer
                asyncio.create_task(handle_setup_timeout(room, query.message))
            except Exception as e:
                print(f"Error in mode selection: {e}")
                await query.answer("❌ An error occurred, please try again", show_alert=True)

        elif query.data.startswith("setup_bot_"):
            try:
                parts = query.data.split("_")
                room_id = int(parts[2])
                mode = parts[3]
                bot_count = int(parts[4])

                room = get_room(room_id)
                if not room:
                    await query.answer("❌ Room not found!", show_alert=True)
                    return

                if room.creator_id != query.from_user.id:
                    await query.answer("❌ Only the room creator can set up the bots!", show_alert=True)
                    return

                # Setup room with chosen mode and bots
                room.setup(mode, bot_count)

                # Add creator as player first
                creator_result = room.add_player(query.from_user.id, query.from_user.username or str(query.from_user.id), is_admin=True)

                # Add AI players if bot_count > 0
                if bot_count > 0:
                    for i in range(bot_count):
                        bot_id = -(room_id * 10 + i)  # Generate unique bot IDs
                        bot_name = random.choice(BOT_NAMES)
                        room.add_player(bot_id, bot_name, is_bot=True)

                keyboard = await get_room_keyboard(room, query.from_user.id)

                player_mentions = []
                for p in room.players:
                    if p.get('is_bot', False):
                        player_mentions.append(f"🤖 Bot {p['name']}")
                    else:
                        player_mentions.append(f"@{p['name']}")

                await query.message.edit_text(
                    f"✨ Room successfully created!\n\n"
                    f"🎮 Mode: {mode.title()}\n"
                    f"🔢 Room ID: {room.id}\n"
                    f"👥 Players ({len(room.players)}):\n"
                    f"{chr(10).join(player_mentions)}\n\n"
                    f"⏳ Waiting for players...\n"
                    f"The room will start in 60 seconds!",
                    reply_markup=keyboard
                )

                # Start room timer
                asyncio.create_task(handle_room_timer(room, query.message, context))
            except Exception as e:
                print(f"Error in setup_bot: {e}")
                await query.answer("❌ An error occurred, please try again", show_alert=True)

        elif query.data.startswith("create_room_no_bots_"):
            mode = query.data.split("_")[-1]
            try:
                room = create_room(query.from_user.id, mode, 0)
                keyboard = await get_room_keyboard(room, query.from_user.id)
                message = await query.message.edit_text(
                    f"📢 Registration opened\n\n"
                    f"🎮 Mode: {mode.title()}\n"
                    f"🤖 AI Players: No\n"
                    f"🔢 Room ID: {room.id}\n"
                    f"Registered: {', '.join([p['name'] for p in room.players])}\n\n"
                    f"⏳ {60} seconds left until registration ends",
                    reply_markup=keyboard
                )
                asyncio.create_task(handle_room_timer(room, message, context))
            except Exception as e:
                print(f"Error creating room: {e}")
                await query.answer("❌ Failed to create room, please try again", show_alert=True)

        elif query.data.startswith("create_room_with_bots_"):
            mode = query.data.split("_")[-1]
            try:
                if query.message.chat.type == "private":
                    await query.answer("❌ Rooms can only be created in groups!", show_alert=True)
                    return

                room = create_room(query.from_user.id, query.message.chat_id, mode, 3)
                if not room:
                    await query.answer("❌ There is already an active room in this group!", show_alert=True)
                    return
                keyboard = []

                is_creator = query.from_user.id == room.creator_id
                if is_creator:
                    keyboard.append([InlineKeyboardButton("▶️ Start Game", callback_data=f"start_game_{room.id}")])
                    keyboard.append([InlineKeyboardButton("🚫 Cancel Room", callback_data=f"cancel_room_{room.id}")])
                else:
                    keyboard.append([InlineKeyboardButton("➕ Join Room", callback_data=f"join_room_{room.id}")])

                reply_markup = InlineKeyboardMarkup(keyboard)
                player_list = []
                for p in room.players:
                    if p.get('is_bot', False):
                        player_list.append(f"🤖 Bot {p['name']}")
                    else:
                        player_list.append(f"👤 @{p['name']}")

                mentions = room.get_player_mentions()
                message = await query.message.edit_text(
                    f"✨ Room successfully created!\n\n"
                    f"🎮 Mode: {mode.title()}\n"
                    f"🤖 AI Players: Yes (3 Bots)\n"
                    f"🔢 Room ID: {room.id}\n"
                    f"👥 Total Players: {len(room.players)}\n"
                    f"{chr(10).join(mentions)}\n\n"
                    f"⏳ {60} seconds remaining\n"
                    f"Type /extend to add 30 more seconds",
                    reply_markup=reply_markup
                )
                asyncio.create_task(handle_room_timer(room, message, context))
            except Exception as e:
                print(f"Error creating room with bots: {e}")
                await query.answer("❌ Failed to create room, try again", show_alert=True)

        elif query.data == "add_bot":
            room = get_room_by_player(query.from_user.id)
            if room and room.bot_count < 3:
                room.bot_count += 1
                room.setup(room.mode, room.bot_count)

            keyboard = [
                [InlineKeyboardButton("👥 Normal Mode", callback_data="mode_normal"),
                 InlineKeyboardButton("🎲 Random Mode", callback_data="mode_random")],
                [InlineKeyboardButton(f"🤖 Bot: {room.bot_count if room else 0}/3", callback_data="add_bot")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                f"⚙️ Room Settings:\n"
                f"Choose game mode:",
                reply_markup=reply_markup
            )

        elif query.data.startswith("mode_"):
            mode = query.data.split("_")[1]
            bot_count = context.user_data.get("bot_count", 0)
            room = create_room(query.from_user.id, mode, bot_count)
            keyboard = get_room_keyboard(room, query.from_user.id)
            await query.message.edit_text(
                f"✨ Room successfully created!\n\n"
                f"🎮 Mode: {mode.title()}\n"
                f"🤖 Bot: {bot_count}/3\n"
                f"🔢 Room ID: {room.id}\n"
                f"👥 Players: {len(room.players)}/12\n\n"
                f"⏳ Waiting for players...",
                reply_markup=keyboard
            )

        elif query.data == "help":
            help_text = (
                "🎮 How to Play:\n\n"
                "1. Create a room or join a room\n"
                "2. Choose a game mode\n"
                "3. Wait for other players to join\n"
                "4. The game starts when enough players have joined\n\n"
                "❓ For further assistance:\n"
                "/help - Show help\n"
                "/rules - Game rules\n"
                "/roles - List of roles\n"
                "/extend - Add 30 more seconds to the registration time\n"
                "/denyroom - Force leave the room\n\n"
                "💡 Tips:\n"
                "- Use the 'Cancel Room' button to cancel the room\n"
                "- /denyroom can be used if the button does not work"
            )
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(help_text, reply_markup=reply_markup)

        elif query.data == "roles":
            roles_text = "🎭 List of Roles in the Game:\n\n"

            def get_role_name(role_id):
                role_names = {
                    "1": "Townie", "2": "Mafia", "3": "Doctor",
                    "4": "Detective", "5": "Lawyer", "6": "Kamikaze"
                }
                return role_names.get(str(role_id), role_id)

            for role, desc in role_desc.items():
                role_name = get_role_name(role)
                if role == "Mafia":
                    roles_text += "🔪 Mafia:\nTasked with killing townspeople every night. Wins if mafia = townspeople.\n\n"
                elif role == "Townie":
                    roles_text += "👥 Townie:\nTasked with uncovering the mafia through voting.\n\n"
                elif role == "Doctor":
                    roles_text += "👨‍⚕️ Doctor:\nCan protect one player from mafia attacks every night.\n\n"
                elif role == "Detective":
                    roles_text += "🔍 Detective:\nCan check one player's role every night.\n\n"
                elif role == "Lawyer":
                    roles_text += "⚖️ Lawyer:\nCan protect one player from execution voting.\n\n"
                else:
                    roles_text += f"{role}:\n{desc}\n\n"

            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(roles_text, reply_markup=reply_markup)

        elif query.data == "shop":
            from shop_system import get_shop_keyboard, get_player_stats
            stats = get_player_stats(query.from_user.id)
            shop_text = (
                f"💰 Coins: {stats['money']}\n"
                f"💎 Gems: {stats['gems']}\n"
                f"🛡️ Protection: {stats['protection']}\n"
                f"📄 Fake ID: {stats['fake_id']}\n\n"
                f"🛍️ Shop Items:"
            )
            reply_markup = get_shop_keyboard()
            await query.message.edit_text(shop_text, reply_markup=reply_markup)

        elif query.data.startswith("buy_"):
            from shop_system import SHOP_ITEMS
            from database import can_afford_item, update_player_points, get_player_points
            item_id = query.data.split("_")[1]
            item = SHOP_ITEMS[item_id]

            if can_afford_item(query.from_user.id, item["price"]):
                update_player_points(query.from_user.id, -item["price"])
                user_stats = game_data["player_stats"].get(str(query.from_user.id), {})
                if "items" not in user_stats:
                    user_stats["items"] = {}
                if item_id in user_stats["items"]:
                    user_stats["items"][item_id] += 1
                else:
                    user_stats["items"][item_id] = 1
                await query.answer(f"Successfully bought {item['name']}!")
                points = get_player_points(query.from_user.id)
                await query.message.edit_text(f"💰 Points: {points}\n\n🛍️ Shop Items:", reply_markup=get_shop_keyboard())
            else:
                await query.answer("❌ Not enough points!", show_alert=True)

            # Check achievements
            from achievements import check_achievements
            new_achievements = check_achievements(query.from_user.id)
            if new_achievements:
                achievement_text = "\n".join([f"🎉 Earned achievement: {ACHIEVEMENTS[a]['name']}" for a in new_achievements])
                await query.message.reply_text(achievement_text)
            await query.answer("Not enough points!", show_alert=True)


        elif query.data.startswith("start_game_"):
            from button_handler import handle_start_game
            await handle_start_game(update, context)

        elif query.data == "leave_room":
            if update.effective_user.id in [p["id"] for p in game_data["players"]]:
                game_data["players"] = [p for p in game_data["players"] if p["id"] != update.effective_user.id]
                save_database(game_data)
            await start(update, context)

        elif query.data == "extend_time":
            if game_data["phase"] == "voting":
                game_data["vote_time"] += 30
                await query.message.reply_text("Voting time extended by 30 seconds!")
                save_database(game_data)

        elif query.data == "show_rules":
            rules_text = """ 
Game Rules:
1. The game has two phases: Day and Night
2. During Night, special roles perform their actions
3. During Day, all players vote to eliminate suspicious players
4. Mafia wins if they equal or outnumber civilians
5. Civilians win if they eliminate all mafia
            """
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(rules_text, reply_markup=reply_markup)

        elif query.data == "show_roles":
            roles_text = "🎭 List of Roles in the Game:\n\n"

            def get_role_name(role_id):
                role_names = {
                    "1": "Citizen", "2": "Mafia", "3": "Doctor",
                    "4": "Detective", "5": "Lawyer", "6": "Kamikaze"
                }
                return role_names.get(str(role_id), role_id)

            for role, desc in role_desc.items():
                role_name = get_role_name(role)
                if role == "Mafia":
                    roles_text += "🔪 Mafia:\nTasked with killing citizens every night. Wins if the number of mafia = citizens.\n\n"
                elif role == "Citizen":
                    roles_text += "👥 Citizen:\nTasked with revealing the identity of the mafia through voting.\n\n"
                elif role == "Doctor":
                    roles_text += "👨‍⚕️ Doctor:\nCan protect 1 player from mafia attacks each night.\n\n"
                elif role == "Detective":
                    roles_text += "🔍 Detective:\nCan investigate 1 player's role each night.\n\n"
                elif role == "Lawyer":
                    roles_text += "⚖️ Lawyer:\nCan protect 1 player from execution voting.\n\n"
                else:
                    roles_text += f"{role}:\n{desc}\n\n"

            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(roles_text, reply_markup=reply_markup)

        elif query.data == "show_shop":
            from shop_system import get_shop_keyboard, get_player_stats
            stats = get_player_stats(query.from_user.id)
            shop_text = (
                f"💰 Coins: {stats['money']}\n"
                f"💎 Gems: {stats['gems']}\n"
                f"🛡️ Protection: {stats['protection']}\n"
                f"📄 Fake ID: {stats['fake_id']}\n\n"
                f"🛍️ Shop Items:"
            )
            reply_markup = get_shop_keyboard()
            await query.message.edit_text(shop_text, reply_markup=reply_markup)

        elif query.data.startswith("buy_"):
            from shop_system import SHOP_ITEMS
            from database import can_afford_item, update_player_points, get_player_points
            item_id = query.data.split("_")[1]
            item = SHOP_ITEMS[item_id]

            if can_afford_item(query.from_user.id, item["price"]):
                update_player_points(query.from_user.id, -item["price"])
                user_stats = game_data["player_stats"].get(str(query.from_user.id), {})
                if "items" not in user_stats:
                    user_stats["items"] = {}
                if item_id in user_stats["items"]:
                    user_stats["items"][item_id] += 1
                else:
                    user_stats["items"][item_id] = 1
                await query.answer(f"Successfully bought {item['name']}!")
                points = get_player_points(query.from_user.id)
                await query.message.edit_text(f"💰 Points: {points}\n\n🛍️ Shop Items:", reply_markup=get_shop_keyboard())
            else:
                await query.answer("❌ Not enough points!", show_alert=True)

            # Check achievements
            from achievements import check_achievements
            new_achievements = check_achievements(query.from_user.id)
            if new_achievements:
                achievement_text = "\n".join([f"🎉 Gained achievement: {ACHIEVEMENTS[a]['name']}" for a in new_achievements])
                await query.message.reply_text(achievement_text)
            await query.answer("Points tidak cukup!", show_alert=True)

        elif query.data == "show_dev_info":
            dev_info = (
                "🎮 IBM Mafia Game Bot\n\n"
                "👨‍💻 Developer:\n"
                "- @simpshh\n\n"
                "🔧 Features:\n"
                "- Real-time gameplay\n"            "- AI Bots\n"
                "- Multiple roles\n\n"
                "🌟 Special Thanks:\n"
                "- Community supporters\n"
                "- Beta testers\n\n"
                "🎨 Art by: @IBMBotSupport\n"
                "[Insert Promo Image Here]\n\n"
                "✨ Follow us for updates!\n"
                "🔗 t.me/IBMBotSupport"
            )
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(dev_info, reply_markup=reply_markup)

        elif query.data == "show_stats":
            user_id = str(query.from_user.id)
            stats = game_data.get("player_stats", {}).get(user_id, {"wins": 0, "games": 0})
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                f"📊 Your Statistics:\n\n"
                f"🎮 Total Game: {stats['games']}\n"
                f"🏆 Wins: {stats['wins']}\n",
                reply_markup=reply_markup
            )
        elif query.data.startswith("start_game_"):
            from button_handler import handle_start_game
            await handle_start_game(update, context)

        elif query.data == "leave_room":
            if update.effective_user.id in [p["id"] for p in game_data["players"]]:
                game_data["players"] = [p for p in game_data["players"] if p["id"] != update.effective_user.id]
                save_database(game_data)
            await start(update, context)

        elif query.data == "extend_time":
            if game_data["phase"] == "voting":
                game_data["vote_time"] += 30
                await query.message.reply_text("Voting time extended by 30 seconds!")
                save_database(game_data)

        elif query.data == "show_rules":
            rules_text = """
Game Rules:
1. The game has two phases: Day and Night
2. During Night, special roles perform their actions
3. During Day, all players vote to eliminate suspicious players
4. Mafia wins if they equal or outnumber civilians
5. Civilians win if they eliminate all mafia
            """
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(rules_text, reply_markup=reply_markup)

        elif query.data == "show_roles":
            roles_text = "🎭 List of Roles in the Game:\n\n"

            def get_role_name(role_id):
                role_names = {
                    "1": "Townsperson", "2": "Mafia", "3": "Doctor",
                    "4": "Detective", "5": "Lawyer", "6": "Kamikaze"
                }
                return role_names.get(str(role_id), role_id)

            for role, desc in role_desc.items():
                role_name = get_role_name(role)
                if role == "Mafia":
                    roles_text += "🔪 Mafia:\n Tasks to kill townspeople every night. Wins if the number of mafia = townspeople.\n\n"
                elif role == "Townsperson":
                    roles_text += "👥 Townsperson:\n Tasks to reveal the mafia's identity through voting.\n\n"
                elif role == "Docter":
                    roles_text += "👨‍⚕️ Docter:\n Can protect 1 player from a mafia attack every night.\n\n"
                elif role == "Detective":
                    roles_text += "🔍 Detective:\n Can check the role of 1 player every night.\n\n"
                elif role == "Lawyer":
                    roles_text += "⚖️ Lawyer:\n Can protect 1 player from execution voting.\n\n"
                else:
                    roles_text += f"{role}:\n{desc}\n\n"

            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(roles_text, reply_markup=reply_markup)

        elif query.data == "show_shop":
            from shop_system import get_shop_keyboard, get_player_stats
            stats = get_player_stats(query.from_user.id)
            shop_text = (
                f"💰 Coins: {stats['money']}\n"
                f"💎 Gems: {stats['gems']}\n"
                f"🛡️ Protection: {stats['protection']}\n"
                f"📄 Fake ID: {stats['fake_id']}\n\n"
                f"🛍️ Shop Items:"
            )
            reply_markup = get_shop_keyboard()
            await query.message.edit_text(shop_text, reply_markup=reply_markup)

        elif query.data.startswith("buy_"):
            from shop_system import SHOP_ITEMS
            from database import can_afford_item, update_player_points, get_player_points
            item_id = query.data.split("_")[1]
            item = SHOP_ITEMS[item_id]

            if can_afford_item(query.from_user.id, item["price"]):
                update_player_points(query.from_user.id, -item["price"])
                user_stats = game_data["player_stats"].get(str(query.from_user.id), {})
                if "items" not in user_stats:
                    user_stats["items"] = {}
                if item_id in user_stats["items"]:
                    user_stats["items"][item_id] += 1
                else:
                    user_stats["items"][item_id] = 1
                await query.answer(f"Berhasil membeli {item['name']}!")
                points = get_player_points(query.from_user.id)
                await query.message.edit_text(f"💰 Points: {points}\n\n🛍️ Shop Items:", reply_markup=get_shop_keyboard())
            else:
                await query.answer("❌ Insufficient points!", show_alert=True)

            # Check achievements
            from achievements import check_achievements
            new_achievements = check_achievements(query.from_user.id)
            if new_achievements:
                achievement_text = "\n".join([f"🎉 Earned achievement: {ACHIEVEMENTS[a]['name']}" for a in new_achievements])
                await query.message.reply_text(achievement_text)
            await query.answer("Points not enough!", show_alert=True)
        else:
            await command_handler.execute_command(query.data, update, context)
    except Exception as e:
        await query.answer(f"Error: {str(e)}", show_alert=True)

command_handler.register_command("start", start)
command_handler.register_command("help", help_command)
command_handler.register_command("quitroom", quit_room)
command_handler.register_command("extend", extend)
command_handler.register_command("startgame", startgame)

async def handle_room_timer(room, message, context):
    if not room or not room.is_joining:
        return

    try:
        start_time = time.time()
        reminder_times = [45, 30, 15, 5]  # Reminder timestamps

        while time.time() - start_time < room.join_timer and room.is_joining:
            time_left = room.join_timer - (time.time() - start_time)

            # Send reminders
            if int(time_left) in reminder_times:
                await context.bot.send_message(
                    chat_id=room.chat_id,
                    text=f"⏰ {int(time_left)} seconds remaining!\n"
                         f"👥 Total Players: {len(room.players)}"
                )
                reminder_times.remove(int(time_left))

            # Format player list
            player_list = []
            for p in room.players:
                if p.get('is_bot', False):
                    player_list.append(f"🤖 Bot {p['name']}")
                else:
                    player_list.append(f"👤 @{p['name']}")

# Update room message
keyboard = await get_room_keyboard(room, None)  # Pass None to avoid join button for existing players
try:
    await message.edit_text(
        f"✨ Room successfully created!\n\n"
        f"🎮 Mode: {room.mode.title()}\n"
        f"🔢 Room ID: {room.id}\n"
        f"👥 Total Players: {len(room.players)}\n"
        f"{chr(10).join(player_list)}\n\n"
        f"⏳ Time remaining: {int(time_left)} seconds",
        reply_markup=keyboard
    )
except Exception as e:
    print(f"Error updating message: {e}")

# Check if timer ended
if time_left <= 0:
    total_players = len(room.players)

    # Start game if at least 4 players (including bots)
    if total_players >= 4:
        room.is_joining = False
        await start_game(room, context)
    else:
        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"❌ Room cancelled due to insufficient players\n"
                 f"Minimum 4 players (including bots)\n"
                 f"Total players: {total_players}"
        )
    break

await asyncio.sleep(1)
except Exception as e:
    print(f"Error in handle_room_timer: {e}")


async def get_room_keyboard(room, user_id):
    try:
        keyboard = []
        if room.is_joining:
            is_player = any(p["id"] == user_id for p in room.players)
            is_creator = user_id == room.creator_id

            if not is_player:
                keyboard.append([InlineKeyboardButton("➕ Join", callback_data=f"join_room_{room.id}")])
            else:
                keyboard.append([InlineKeyboardButton("❌ Leave", callback_data=f"leave_room_{room.id}")])

            if is_creator:
                keyboard.append([InlineKeyboardButton("▶️ Start Game", callback_data=f"start_game_{room.id}")])
                keyboard.append([InlineKeyboardButton("🚫 Cancel Room", callback_data=f"cancel_room_{room.id}")])

        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        print(f"Error creating keyboard: {e}")
        return None

async def handle_game_loop(room, context):
    while True:
        if room.phase == "night":
            await process_night_actions(room, context)
        elif room.phase == "day":
            await handle_voting(room, context)
        await asyncio.sleep(1)

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        room = get_room_by_player(update.effective_user.id)
        if not room:
            await update.message.reply_text("❌ Room not found!")
            return

        if room.creator_id != update.effective_user.id:
            await update.message.reply_text("❌ Only the room creator can start the game!")
            return

        if len(room.players) < 4:
            await update.message.reply_text("❌ Minimum 4 players required to start the game!")
            return

        # Initialize game state
        room.phase = "night"
        game_data["phase"] = "night"
        game_data["waiting_for_roles"] = set()

        # Assign roles
        assigned_roles = await assign_roles(room.players, room.mode)

        # Send roles via PM and update room state
        player_mentions = []
        for player in room.players:
            player_id = player["id"]
            role = assigned_roles[player_id]
            player["role"] = role

            if not player.get("is_bot", False):
                try:
                    await context.bot.send_message(
                        chat_id=player_id,
                        text=f"🎭 Your role: {role}\n\n📜 Description:\n{role_desc.get(role, 'Secret role')}"
                    )
                    player_mentions.append(f"@{player['name']}")
                except Exception as e:
                    print(f"Error sending PM to {player_id}: {e}")

        # Start game announcement
        announcement = (
            f"🎮 Game started!\n\n"
            f"👥 Players({len(room.players)}):\n"
            f"{', '.join(player_mentions)}\n\n"
            f"📱 Check your PM for role details"
        )

        await update.message.reply_text(announcement)
        room.is_joining = False

        # Start game logic in new thread
        asyncio.create_task(handle_game_loop(room, context))

    except Exception as e:
        print(f"Error starting game: {e}")
        await update.message.reply_text("❌ An error occurred while starting the game!")

async def assign_roles(players, mode):
    available_roles = list(role_desc.keys())
    assigned_roles = {}

    # Ensure at least one Mafia
    mafia_count = max(1, len(players) // 4)
    for i in range(mafia_count):
        player = players[i]
        assigned_roles[player["id"]] = "Mafia"

    # Assign remaining roles
    remaining_players = [p for p in players if p["id"] not in assigned_roles]
    remaining_roles = [r for r in available_roles if r != "Mafia"]

    for player in remaining_players:
        role = random.choice(remaining_roles)
        assigned_roles[player["id"]] = role

    return assigned_roles

async def send_role_pm(player_id, role, context):
    try:
        await context.bot.send_message(chat_id=player_id, text=f"Your role is: {role}")
    except Exception as e:
        print(f"Error sending PM to {player_id}: {e}")
