"""
Admin Commands Handler
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
"""

from game_state import ADMIN_ID
from database import add_player_money
from telegram import Update
from telegram.ext import ContextTypes

async def handle_berlin_command(update, context):
    """Super admin command for unlimited access"""
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Command khusus admin!")
        return

    # Add unlimited money
    add_player_money(user_id, 999999)
    await update.message.reply_text("💰 Admin mode activated!")


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    command = update.message.text.split()[0][1:]

    if command == "addmoney":
        # Add money to player
        try:
            target_id = int(update.message.text.split()[1])
            amount = int(update.message.text.split()[2])
            add_player_money(target_id, amount) #Use database function
            await update.message.reply_text(f"Added {amount} coins to player {target_id}")
        except:
            await update.message.reply_text("Usage: /addmoney [player_id] [amount]")

    elif command == "setrole":
        # Force set role for player
        try:
            target_id = int(update.message.text.split()[1])
            role = update.message.text.split()[2]
            game_data["roles"][str(target_id)] = role
            await update.message.reply_text(f"Set role {role} for player {target_id}")
        except:
            await update.message.reply_text("Usage: /setrole [player_id] [role]")