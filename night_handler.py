
from ai_handler import AIHandler
import asyncio

class NightHandler:
    def __init__(self):
        self.ai_handler = AIHandler()
        
    async def handle_night_phase(self, room, context):
        """Handle night phase actions"""
        try:
            # Initialize night actions
            room.night_actions = {}
            
            # Notify all players
            await context.bot.send_message(
                chat_id=room.chat_id,
                text="🌙 Night has arrived... Players with special roles, please check your PM!"
            )
            
            # Handle special role actions
            for player in room.get_alive_players():
                if player["role"] in ["Boss Mafia", "Mafia", "Detective", "Docter"]:
                    if player.get("is_bot"):
                        # Handle bot night actions
                        action = await self.ai_handler.get_night_action(player, room.get_alive_players())
                        if action:
                            room.night_actions[player["id"]] = action
                    else:
                        # Send action prompt to real players
                        await self.send_night_action_prompt(player, room, context)
                        
            # Wait for actions
            await asyncio.sleep(20)  # 20 seconds for night actions
            
            # Process night actions
            await self.process_night_actions(room, context)
            return True
            
        except Exception as e:
            print(f"Error in night phase: {e}")
            return False
            
    async def send_night_action_prompt(self, player, room, context):
        """Send appropriate action prompt based on role"""
        role_prompts = {
            "Boss Mafia": "🔪 Choose a target to kill:",
            "Mafia": "🔪 Follow the instructions of the Boss Mafia",
            "Detektif": "🔍 Choose a player to investigate:",
            "Dokter": "💉 Choose a player to protect:"
        }
        
        if player["role"] in role_prompts:
            await context.bot.send_message(
                chat_id=player["id"],
                text=role_prompts[player["role"]]
            )
