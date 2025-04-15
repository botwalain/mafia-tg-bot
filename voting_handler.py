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
                text="🌙 The night has arrived... Players with special roles, please check your PM!"
            )
            
            # Handle special role actions
            for player in room.get_alive_players():
                if player["role"] in ["Boss Mafia", "Mafia", "Detective", "Doctor"]:
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
            "Detective": "🔍 Choose a player to investigate:",
            "Doctor": "💉 Choose a player to protect:"
        }
        
        if player["role"] in role_prompts:
            await context.bot.send_message(
                chat_id=player["id"],
                text=role_prompts[player["role"]]
            )
    async def process_night_actions(self, room, context):
        # Add night action processing logic here
        pass

class VotingHandler:
    def __init__(self):
        self.ai_handler = AIHandler()

    async def handle_voting_phase(self, room, context):
        """Handle voting phase actions"""
        try:
            # Initialize voting
            room.votes = {}

            # Notify all players
            await context.bot.send_message(
                chat_id=room.chat_id,
                text="🗳️The voting time has started! Please choose the suspicious player."
            )

            # Handle voting actions
            for player in room.get_alive_players():
                if player.get("is_bot"):
                    # Handle bot voting
                    vote = await self.ai_handler.get_vote(player, room.get_alive_players())
                    if vote:
                        room.votes[player["id"]] = vote
                else:
                    # Send voting prompt to real players
                    await self.send_voting_prompt(player, room, context)

            # Wait for votes
            await asyncio.sleep(30)  # 30 seconds for voting

            # Process voting results
            await self.process_voting_results(room, context)
            return True

        except Exception as e:
            print(f"Error in voting phase: {e}")
            return False

    async def send_voting_prompt(self, player, room, context):
        # Add voting prompt logic
        alive_players = room.get_alive_players()
        voting_text = "🗳️ Choose a player to vote.:\n\n"
        for i, p in enumerate(alive_players, 1):
            if p["id"] != player["id"]:
                voting_text += f"{i}. {p['name']}\n"

        await context.bot.send_message(
            chat_id=player["id"],
            text=voting_text
        )

    async def process_voting_results(self, room, context):
        if not room.votes:
            await context.bot.send_message(
                chat_id=room.chat_id,
                text="❌ No one has been voted today."
            )
            return

        # Count votes
        vote_counts = {}
        for voted_id in room.votes.values():
            vote_counts[voted_id] = vote_counts.get(voted_id, 0) + 1

        # Find player with most votes
        most_voted_id = max(vote_counts.items(), key=lambda x: x[1])[0]
        most_voted_player = next(p for p in room.players if p["id"] == most_voted_id)

        # Announce result
        await context.bot.send_message(
            chat_id=room.chat_id,
            text=f"🔨 {most_voted_player['name']} Has been voted out!"
        )

        # Update player state
        most_voted_player["is_alive"] = False
