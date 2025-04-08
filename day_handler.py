
import asyncio
from game_state import game_data
from room_manager import get_room

async def handle_day_phase(room, context, day_number):
    """Handle day phase actions and discussions"""
    if not room or day_number > 100:  # Max 100 days
        return False

    try:
        # Announce day start
        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"☀️ Hari ke-{day_number} dimulai!\n\nPara pemain punya waktu 2 menit untuk berdiskusi."
        )

        # Display alive players
        alive_players = [p for p in room.players if p["is_alive"]]
        player_list = "\n".join([
            f"{'🤖 ' if p.get('is_bot') else '👤 '}{p['name']}"
            for p in alive_players
        ])
        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"Pemain yang masih hidup:\n{player_list}")

        # Wait for discussion time
        await asyncio.sleep(120)  # 2 minutes discussion
        return True

    except Exception as e:
        print(f"Error in day phase: {e}")
        return False
