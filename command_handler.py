
"""
Command Handler System
Created by @berlinnad 
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

class CommandHandler:
    def __init__(self):
        self._callbacks = {}
        
    async def execute_command(self, command: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute registered command"""
        if command in self._callbacks:
            try:
                return await self._callbacks[command](update, context)
            except Exception as e:
                print(f"Error executing command {command}: {e}")
                if update.callback_query:
                    await update.callback_query.message.reply_text(f"Error: {str(e)}")
        return None

    def register_command(self, command: str, callback):
        """Register new command"""
        self._callbacks[command] = callback
