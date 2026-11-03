from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MISSION_DIR = PROJECT_ROOT / "missions"
WORLD_WIDTH = 3200
WORLD_HEIGHT = 2200
PLAYER_RADIUS = 36
MAX_PLAYER_SPEED = 205.0
PLAYER_HULL = 100
SHIP_CLASSES = {
    "Sloop": {"cost": 0, "hull": 100, "speed": 205.0, "turn": 1.0, "guns": 3, "reload": 1.45, "oar_power": 34.0, "rowers": 12, "description": "A nimble little vessel. A sound first command."},
    "Cutter": {"cost": 650, "hull": 92, "speed": 238.0, "turn": 1.2, "guns": 2, "reload": 1.22, "oar_power": 32.0, "rowers": 12, "description": "Quick through the water and handy for chasing prizes."},
    "Schooner": {"cost": 1250, "hull": 138, "speed": 218.0, "turn": 1.05, "guns": 4, "reload": 1.48, "oar_power": 39.0, "rowers": 16, "description": "A balanced trader-raider with a stronger broadside."},
    "Brigantine": {"cost": 2200, "hull": 188, "speed": 194.0, "turn": 0.9, "guns": 5, "reload": 1.7, "oar_power": 46.0, "rowers": 20, "description": "A sturdy two-masted fighter with plenty of room for guns."},
    "Frigate": {"cost": 3600, "hull": 250, "speed": 176.0, "turn": 0.76, "guns": 7, "reload": 1.95, "oar_power": 54.0, "rowers": 24, "description": "A costly gun platform built to dominate a fleet action."},
}
SHIP_LIVERIES = [
    ("Weathered Pirate", (98, 47, 31), (205, 155, 89), (227, 215, 177)),
    ("Royal Blue", (38, 66, 91), (190, 163, 104), (222, 225, 211)),
    ("Emerald Corsair", (39, 83, 59), (197, 157, 81), (227, 219, 180)),
    ("Blood Red", (104, 35, 34), (204, 155, 90), (231, 210, 184)),
    ("Ivory & Gold", (130, 105, 69), (221, 190, 116), (246, 235, 207)),
]
