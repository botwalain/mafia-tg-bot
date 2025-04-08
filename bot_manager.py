
from typing import List, Dict
from game_state import BOT_NAMES
import random
from ai_handler import AIHandler

class BotManager:
    def __init__(self):
        self.available_bots = BOT_NAMES.copy()
        self.ai_handler = AIHandler()
        self.bot_nicknames = {}
        self.bot_roles = {}
        
    def generate_bots(self, count: int) -> List[Dict]:
        if count > 3:
            count = 3  # Maximum 3 bots allowed
            
        bots = []
        for i in range(count):
            if not self.available_bots:
                self.available_bots = BOT_NAMES.copy()  # Refill if empty
            bot_name = random.choice(self.available_bots)
            self.available_bots.remove(bot_name)
            bot_id = -(i + 1000)  # Negative IDs for bots
            
            bot = {
                "id": bot_id,
                "name": "MafionnadBot",
                "nickname": f"🤖 {bot_name}",
                "is_bot": True,
                "is_alive": True,
                "vote": None,
                "role": None,
                "ready": True  # Bots are always ready
            }
            
            # Auto-assign role with behavior
            if len(bots) == 0:
                bot["role"] = "Mafia"
                bot["behavior"] = {
                    "night_action": "kill",
                    "strategy": "aggressive",
                    "target_priority": "detektif"
                }
            elif len(bots) == 1:
                bot["role"] = "Detektif"
                bot["behavior"] = {
                    "night_action": "investigate",
                    "strategy": "analytical",
                    "target_priority": "suspicious"
                }
            else:
                bot["role"] = "Warga"
                bot["behavior"] = {
                    "night_action": None,
                    "strategy": "defensive",
                    "target_priority": "voting"
                }
            
            bots.append(bot)
            self.bot_nicknames[bot_id] = bot_name
            
        return bots

    def get_bot_nickname(self, bot_id: int) -> str:
        return f"🤖 {self.bot_nicknames.get(bot_id, 'Bot')}"

    async def handle_bot_chat(self, room_id: str, players: List[Dict], bot: Dict) -> str:
        if not bot["is_alive"]:
            return ""
            
        # Bot understands its role
        role = bot["role"]
        role_info = {
            "Boss Mafia": "Kamu adalah pemimpin mafia. Tugasmu membunuh warga dan melindungi identitas mafia.",
            "Mafia": "Kamu adalah anggota mafia. Berkolaborasi dengan Boss Mafia untuk membunuh warga.",
            "Detektif": "Kamu adalah detektif. Selidiki pemain untuk menemukan mafia.",
            "Dokter": "Kamu adalah dokter. Lindungi pemain dari serangan malam.",
            "Warga": "Kamu adalah warga biasa. Temukan dan eliminasi mafia.",
            "Pengacara": "Kamu adalah pengacara. Lindungi pemain dari eksekusi.",
            "Kamikaze": "Kamu adalah kamikaze. Gunakan kemampuan spesialmu dengan bijak.",
            "Beruntung": "Kamu memiliki kesempatan kedua untuk hidup."
        }
        
        bot["role_info"] = role_info[role]
            
        suspicious_players = [p for p in players if p["id"] != bot["id"] and p["is_alive"]]
        if suspicious_players:
            target = random.choice(suspicious_players)
            
        bot_context = {
            "role": bot["role"],
            "personality": bot["personality"],
            "nickname": self.get_bot_nickname(bot["id"]),
            "players": suspicious_players,
            "target": target["nickname"] if suspicious_players else None,
            "game_phase": game_data.get("phase", ""),
            "discussion_topic": game_data.get("current_topic", ""),
            "votes": game_data.get("votes", {}),
            "behavior": bot.get("behavior", {}),
            "suspicion_level": random.randint(1, 100)  # Random suspicion for dynamic behavior
        }
        
        # Strategic voting and actions
        if bot_context["game_phase"] == "voting":
            if bot_context["suspicion_level"] > 70:
                # Actively accuse others
                bot_context["action"] = "accuse"
            elif bot_context["role"] == "Mafia" and target.get("role") != "Mafia":
                # Mafia tries to eliminate townspeople
                bot_context["action"] = "frame"
        
        # Add contextual awareness
        if bot_context["game_phase"] == "voting":
            suspicious_players = [p for p in bot_context["players"] if p.get("suspicious", 0) > 0]
            bot_context["voting_targets"] = suspicious_players
        
        return await self.ai_handler.get_response(room_id, "", bot_context)
