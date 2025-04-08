
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
                "team": "Jahat",
                "prompt": "Kamu adalah AI Mafia dalam game MafiosoNnad. Tugas: 1) Pilih target untuk dibunuh 2) Ikuti instruksi Boss Mafia 3) Berdiskusi dengan tim 4) Bertindak mencurigakan untuk membingungkan warga. Situasi saat ini: {situation}",
                "objectives": ["select_target", "follow_boss", "team_discussion", "act_suspicious"],
                "decision_making": {
                    "target_selection": lambda players: random.choice([p for p in players if p["role"] not in ["Mafia", "Boss Mafia"]]),
                    "chat_frequency": 0.7,
                    "voting_strategy": "random_townspeople"
                },
                "chat_styles": {
                    "joy": ["😈 Hehe, siapa ya yang mencurigakan?", "🤔 Hmm... {target} kayaknya sus deh"],
                    "cool": ["😎 Tenang aja guys, gw tau siapa mafnya", "🕶️ {target} gerak-geriknya aneh"],
                    "badass": ["💀 Mending kita vote {target} aja", "🔪 Gw yakin dia mafia!"],
                }
            },
            "Warga": {
                "night_action": None,
                "team": "Baik",
                "prompt": "Kamu adalah Warga. Tugas: 1) Cari Mafia melalui diskusi 2) Vote dengan bijak 3) Bantu tim baik. Situasi: {situation}",
                "objectives": ["find_mafia", "vote_wisely", "help_town"]
            },
            "Detektif": {
                "night_action": "investigate",
                "team": "Baik",
                "prompt": "You are a Detective in a social deduction game. Use your investigation results wisely. Current situation: {situation}"
            },
            "Dokter": {
                "night_action": "heal",
                "team": "Baik",
                "prompt": "You are a Doctor in a social deduction game. Protect citizens strategically. Current situation: {situation}"
            }
        }
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    def get_night_action(self, bot: Dict, players: List[Dict]) -> Dict:
        role = bot["role"]
        behavior = self.role_behaviors.get(role, self.role_behaviors["Warga"])
        
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
        behavior = self.role_behaviors.get(role, self.role_behaviors["Warga"])
        
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
            "Kita harus hati-hati",
            "Siapa yang mencurigakan?",
            "Mari kita diskusi"
        ]
        return random.choice(basic_responses)

    def should_vote(self, bot: Dict, vote_history: List[Dict]) -> bool:
        return True

    def get_vote_target(self, bot: Dict, players: List[Dict], vote_history: List[Dict]) -> int:
        behavior = self.role_behaviors.get(bot["role"])
        alive_players = [p for p in players if p["id"] != bot["id"] and p["is_alive"]]
        
        if not alive_players:
            return None
            
        if behavior["team"] == "Jahat":
            town_players = [p for p in alive_players if p.get("role", "Warga") != "Mafia"]
            if town_players:
                return random.choice(town_players)["id"]
                
        return random.choice(alive_players)["id"]
