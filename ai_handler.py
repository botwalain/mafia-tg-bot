import random
from typing import Dict, List
import os
import google.generativeai as genai

class AIHandler:
    def __init__(self):
        self.personalities = ["joy", "cool", "badass", "suspicious", "friendly"]
        self.role_behaviors = {
            "Mafia": {
                "night_action": "kill",
                "team": "Evil",
                "prompt": "You are the Mafia AI in the MafiosoNnad game. Task: 1) Choose a target to kill 2) Follow the Boss Mafia's instructions 3) Discuss with the team 4) Act suspiciously to confuse the townspeople. Current situation: {situation}",
                "objectives": ["select_target", "follow_boss", "team_discussion", "act_suspicious"],
                "decision_making": {
                    "target_selection": lambda players: random.choice([p for p in players if p["role"] not in ["Mafia", "Boss Mafia"]]),
                    "chat_frequency": 0.7,
                    "voting_strategy": "random_townspeople"
                },
                "chat_styles": {
                    "joy": ["😈 Hehe, who's suspicious?", "🤔 Hmm... {target} seems suspicious"],
                    "cool": ["😎 Don't worry, I know who the Mafia are", "🕶️ {target}'s movements are weird"],
                    "badass": ["💀 Let's just vote {target}", "🔪 I'm sure they're Mafia!"],
                }
            },
            "Townspeople": {
                "night_action": None,
                "team": "Good",
                "prompt": "You are a Townsperson. Task: 1) Find the Mafia through discussion 2) Vote wisely 3) Help the good team. Situation: {situation}",
                "objectives": ["find_mafia", "vote_wisely", "help_town"]
            },
            "Detective": {
                "night_action": "investigate",
                "team": "Good",
                "prompt": "You are a Detective in a social deduction game. Use your investigation results wisely. Current situation: {situation}"
            },
            "Doctor": {
                "night_action": "heal",
                "team": "Good",
                "prompt": "You are a Doctor in a social deduction game. Protect citizens strategically. Current situation: {situation}"
            }
        }
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("AIzaSyA2fmlKKeNqe5GkVW0caA8IzkLg-c0TCFA"))
        self.model = genai.GenerativeModel('gemini-pro')

    def get_night_action(self, bot: Dict, players: List[Dict]) -> Dict:
        role = bot["role"]
        behavior = self.role_behaviors.get(role, self.role_behaviors["Townspeople"])
        
        if not behavior["night_action"]:
            return None
            
        alive_players = [p for p in players if p["id"] != bot["id"] and p["is_alive"]]
        if not alive_players:
            return None
            
        target = random.choice(alive_players)
        return {
            "action": behavior["night_action"],
            "target": target["id"]
        }

    async def get_response(self, room_id: str, message: str, bot_context: Dict) -> str:
        role = bot_context["role"]
        behavior = self.role_behaviors.get(role, self.role_behaviors["Townspeople"])
        
        situation = {
            "role": role,
            "nickname": bot_context["nickname"],
            "alive_players": [p["name"] for p in bot_context["players"]],
            "team": behavior["team"]
        }
        
        prompt = behavior["prompt"].format(situation=str(situation))
        
        try:
            response = await self.model.generate_content(prompt)
            chat_message = response.text[:100]  # Limit length
            return chat_message.strip()
        except:
            # Fallback to basic responses if API fails
            return self.get_role_based_response(role, bot_context["players"])
            
    def get_role_based_response(self, role: str, players: List[Dict]) -> str:
        basic_responses = [
            "Hmm...",
            "We need to be careful",
            "Who's suspicious?",
            "Let's discuss"
        ]
        return random.choice(basic_responses)

    def should_vote(self, bot: Dict, vote_history: List[Dict]) -> bool:
        return True

    def get_vote_target(self, bot: Dict, players: List[Dict], vote_history: List[Dict]) -> int:
        behavior = self.role_behaviors.get(bot["role"])
        alive_players = [p for p in players if p["id"] != bot["id"] and p["is_alive"]]
        
        if not alive_players:
            return None
            
        if behavior["team"] == "Evil":
            town_players = [p for p in alive_players if p.get("role", "Townspeople") != "Mafia"]
            if town_players:
                return random.choice(town_players)["id"]
                
        return random.choice(alive_players)["id"]
