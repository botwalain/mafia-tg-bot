
"""
MafiosoNnad Bot
Created by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler as TelegramCommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot_commands import *
from game_state import game_data
from database import load_database
from command_handler import CommandHandler

# Initialize logging and command handler
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
command_handler = CommandHandler()

def error_handler(update, context):
    """Handle errors"""
    logger.error(f"Error occurred: {context.error}")

def main():
    from config import BOT_TOKEN, ENCRYPTION_KEY

    try:
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )

        # Register all command handlers
        application.add_handler(TelegramCommandHandler("start", start))
        application.add_handler(TelegramCommandHandler("help", help_command))
        application.add_handler(TelegramCommandHandler("denyroom", denyroom))
        application.add_handler(TelegramCommandHandler("extend", extend))
        application.add_handler(TelegramCommandHandler("startgame", startgame))

        # Add callback query handler
        application.add_handler(CallbackQueryHandler(handle_callback))

        # Add error handler
        application.add_error_handler(error_handler)

        # Load database and start bot
        load_database(game_data)
        print("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
