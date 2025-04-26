from typing import Dict, Any, List
from pydantic import BaseModel

class GameState(BaseModel):
    player_name: str = ""
    character_class: str = ""
    setting: str = ""
    preferences: Dict[str, Any] = {}
    game_started: bool = False

    # New world data fields
    world_intro: str = ""
    location_intro: str = ""
    npcs: list = []
    main_quest: str = ""
    side_quests: list = []
    inventory: list = []
    current_scene: str = ""
    available_actions: list = []
    selected_action: str = ""
    action_result: str = ""
    new_available_actions: list = []
    last_dice_roll: int = 0
    last_roll_outcome: str = ""
    inventory: List[str] = []
    player_hp: int = 100
    max_hp: int = 100
    experience_points: int = 0
    level: int = 1
    health_points: int = 100
    max_health_points: int = 100


