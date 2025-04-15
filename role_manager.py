
from dataclasses import dataclass
from typing import List, Dict
import random

@dataclass
class Role:
    name: str
    team: str
    description: str
    night_action: bool
    special_action: bool
    
class RoleManager:
    def __init__(self):
        self.roles = self._initialize_roles()
        
    def _initialize_roles(self) -> Dict[str, Role]:
        roles = {}
        # Add all roles with their properties
        roles["Villager"] = Role(
            name="Villager",
            team="Good",
            description="👨🏼 A regular villager with no special abilities.",
            night_action=False,
            special_action=False
        )
        # Add all other roles similarly
        return roles
        
    def assign_roles(self, player_count: int, mode: str) -> Dict[str, str]:
        if mode == "normal":
            return self._assign_normal_roles(player_count)
        return self._assign_random_roles(player_count)
