from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from game_state import game_data, role_desc
from room_manager import get_room

async def send_role_pm(player_id, role, context, room_id):
    """Send role PM with appropriate buttons"""
    room = get_room(room_id)
    if not room:
        return

    role_text = role_desc.get(role, "")
    keyboard = []
    
    # Get player list for actions
    player_list = [p for p in room.players if p["is_alive"]]
    buttons = []
    
    # Add role-specific buttons
    if role == "Mafia":
        for p in player_list:
            if not p.get("is_bot", False):
                buttons.append(InlineKeyboardButton(f"🔪 Kill {p['name']}", callback_data=f"kill_{room_id}_{p['id']}"))
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    elif role == "Detective":
        for p in player_list:
            if not p.get("is_bot", False):
                buttons.append(InlineKeyboardButton(f"🔍 Check {p['name']}", callback_data=f"investigate_{room_id}_{p['id']}"))
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    elif role == "Docter":
        for p in player_list:
            if not p.get("is_bot", False):
                buttons.append(InlineKeyboardButton(f"💉 Heal {p['name']}", callback_data=f"heal_{room_id}_{p['id']}"))
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    elif role == "Boss Mafia":
        for p in player_list:
            if not p.get("is_bot", False):
                buttons.append(InlineKeyboardButton(f"👑 Kill {p['name']}", callback_data=f"boss_kill_{room_id}_{p['id']}"))
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=player_id,
        text=f"🎭 Your role: {role}\n\n📜 Description:\n{role_text}",
        reply_markup=reply_markup
    )

async def handle_pm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PM button callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id

    if query.data.startswith("kill_"):
        room_id = int(query.data.split("_")[1])
        # Handle kill action
        pass
    elif query.data.startswith("investigate_"):
        room_id = int(query.data.split("_")[1])
        # Handle investigate action
        pass
    elif query.data.startswith("heal_"):
        room_id = int(query.data.split("_")[1])
        # Handle heal action
        pass
    elif query.data.startswith("boss_kill_"):
        room_id = int(query.data.split("_")[1])
        # Handle boss kill action
        pass
    elif query.data.startswith("lawyer_protect_"):
        room_id = int(query.data.split("_")[1])
        #Handle lawyer protect action
        pass
    elif query.data == "player_ready":
        game_data["waiting_for_roles"].discard(user_id)
        await query.answer("You're ready!")
        await query.edit_message_reply_markup(None)
    elif query.data == "leave_game":
        if user_id in game_data["players"]:
            game_data["players"] = [p for p in game_data["players"] if p["id"] != user_id]
            await query.answer("You left the game")
            await query.message.delete()
