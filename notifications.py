from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from game_state import GAME_GIFS # Added import statement

async def send_join_notification(context, chat_id, player_name):
    """Send notification when player joins"""
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ @{player_name} telah bergabung ke room!",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending join notification: {e}")

async def send_timer_notification(context, chat_id, time_left, player_count, mode, room_id):
    """Send timer notification"""
    text = (
        f"⏰ Sisa waktu: {time_left} Detik\n"
        f"👥 Pemain: {player_count}\n"
        f"🎮 Mode: {mode}\n"
        f"🔢 ID Room: {room_id}"
    )
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text
        )
    except Exception as e:
        print(f"Error sending timer notification: {e}")

async def send_game_start_notification(context, chat_id):
    """Send game start notification with GIF"""
    try:
        
        await context.bot.send_animation(
            chat_id=chat_id,
            animation=GAME_GIFS["start"],
            caption="🎮 Game dimulai!\n\nPara pemain akan menerima peran melalui PM..."
        )
    except Exception as e:
        print(f"Error sending game start notification: {e}")

async def send_extend_notification(context, chat_id, seconds):
    """Send notification when timer is extended"""
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⌛ Waktu pendaftaran ditambah {seconds} detik!"
        )
    except Exception as e:
        print(f"Error sending extend notification: {e}")