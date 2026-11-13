import itertools
import math


SHIP_CLASSES = {
    "Launch": {
        "cost": 260, "hull": 70, "speed": 246.0, "turn": 1.34, "guns": 1, "max_cannons": 2,
        "reload": 1.05, "oar_power": 31.0, "rowers": 8, "crew": 8, "cargo": 20.0, "length": 88,
        "beam": 28, "hull_profile": (0.16, 0.34, 0.43, 0.32, 0.11), "collision_radius": 42.0, "rig": "gaff", "masts": (0.66,), "sail_span": 22,
        "outfitting": ("hull", "rigging", "rudder"),
        "upgrade_limits": {"hull": 1, "rigging": 2, "rudder": 3},
        "description": "A tiny harbour launch, quick to turn and useful in confined waters, but poorly suited to a stand-up fight."
    },
    "Cutter": {
        "cost": 650, "hull": 92, "speed": 238.0, "turn": 1.2, "guns": 2, "max_cannons": 8,
        "reload": 1.22, "oar_power": 32.0, "rowers": 12, "crew": 28, "cargo": 34.0, "length": 108,
        "beam": 32, "hull_profile": (0.17, 0.36, 0.45, 0.34, 0.12), "collision_radius": 50.0, "rig": "cutter", "masts": (0.65,), "sail_span": 25,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 2, "cannons": 2, "rigging": 3, "rudder": 3, "cargo": 1},
        "description": "A narrow, single-masted dispatch vessel built for speed, pursuit and swift coastal work."
    },
    "Sloop": {
        "cost": 0, "hull": 100, "speed": 205.0, "turn": 1.0, "guns": 3, "max_cannons": 10,
        "reload": 1.45, "oar_power": 34.0, "rowers": 12, "crew": 48, "cargo": 42.0, "length": 122,
        "beam": 38, "hull_profile": (0.20, 0.38, 0.48, 0.38, 0.13), "collision_radius": 52.0, "rig": "sloop", "masts": (0.61,), "sail_span": 29,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 2, "rigging": 3, "rudder": 3, "cargo": 2},
        "description": "A nimble, single-masted raider with a useful broadside and enough hold for a modest prize."
    },
    "Yawl": {
        "cost": 780, "hull": 84, "speed": 224.0, "turn": 1.28, "guns": 2, "max_cannons": 4,
        "reload": 1.18, "oar_power": 30.0, "rowers": 10, "crew": 18, "cargo": 30.0, "length": 102,
        "beam": 31, "hull_profile": (0.18, 0.35, 0.44, 0.34, 0.12), "collision_radius": 47.0, "rig": "yawl", "masts": (0.39, 0.79), "sail_span": 23,
        "outfitting": ("hull", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 2, "rigging": 3, "rudder": 3, "cargo": 1},
        "description": "A light two-masted coaster with shallow draught and excellent handling near reefs and small islands."
    },
    "Xebec": {
        "cost": 1550, "hull": 146, "speed": 230.0, "turn": 1.12, "guns": 4, "max_cannons": 14,
        "reload": 1.34, "oar_power": 48.0, "rowers": 42, "crew": 120, "cargo": 58.0, "length": 151,
        "beam": 40, "hull_profile": (0.16, 0.36, 0.46, 0.36, 0.11), "collision_radius": 55.0, "rig": "xebec", "masts": (0.31, 0.57, 0.81), "sail_span": 31,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 2, "cannons": 3, "rigging": 3, "rudder": 3, "cargo": 1},
        "description": "A long, lean Mediterranean-style vessel with lateen sails, auxiliary oars and exceptional speed."
    },
    "Schooner": {
        "cost": 1250, "hull": 138, "speed": 218.0, "turn": 1.05, "guns": 4, "max_cannons": 14,
        "reload": 1.48, "oar_power": 0.0, "rowers": 0, "crew": 70, "cargo": 68.0, "length": 158,
        "beam": 43, "hull_profile": (0.20, 0.39, 0.47, 0.39, 0.13), "collision_radius": 57.0, "rig": "schooner", "masts": (0.35, 0.72), "sail_span": 32,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 3, "cargo": 2},
        "description": "A long, quick two-masted trader with fore-and-aft sails and a flexible mix of speed and cargo space."
    },
    "Brigantine": {
        "cost": 2200, "hull": 188, "speed": 194.0, "turn": 0.9, "guns": 5, "max_cannons": 16,
        "reload": 1.7, "oar_power": 0.0, "rowers": 0, "crew": 120, "cargo": 104.0, "length": 177,
        "beam": 50, "hull_profile": (0.24, 0.43, 0.50, 0.43, 0.17), "collision_radius": 61.0, "rig": "brigantine", "masts": (0.34, 0.73), "sail_span": 38,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 3, "cargo": 2},
        "description": "A broad, two-masted fighting vessel with a square-rigged foremast and a powerful fore-and-aft aft rig."
    },
    "Brig": {
        "cost": 2950, "hull": 235, "speed": 188.0, "turn": 0.84, "guns": 6, "max_cannons": 18,
        "reload": 1.76, "oar_power": 0.0, "rowers": 0, "crew": 145, "cargo": 118.0, "length": 188,
        "beam": 54, "hull_profile": (0.24, 0.43, 0.50, 0.43, 0.17), "collision_radius": 64.0, "rig": "brig", "masts": (0.33, 0.73), "sail_span": 41,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 3, "cargo": 2},
        "description": "A square-rigged two-masted warship with more gun deck and carrying power than a brigantine."
    },
    "Barque": {
        "cost": 4200, "hull": 310, "speed": 171.0, "turn": 0.72, "guns": 7, "max_cannons": 20,
        "reload": 1.88, "oar_power": 0.0, "rowers": 0, "crew": 190, "cargo": 170.0, "length": 206,
        "beam": 61, "hull_profile": (0.28, 0.45, 0.50, 0.46, 0.21), "collision_radius": 69.0, "rig": "barque", "masts": (0.25, 0.51, 0.79), "sail_span": 45,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 2, "cargo": 3},
        "description": "A large three-masted carrier with square sails forward and efficient fore-and-aft sails aft."
    },
    "Corvette": {
        "cost": 5200, "hull": 340, "speed": 184.0, "turn": 0.82, "guns": 8, "max_cannons": 20,
        "reload": 1.82, "oar_power": 0.0, "rowers": 0, "crew": 210, "cargo": 126.0, "length": 198,
        "beam": 57, "hull_profile": (0.19, 0.39, 0.47, 0.38, 0.13), "collision_radius": 68.0, "rig": "corvette", "masts": (0.25, 0.51, 0.78), "sail_span": 43,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 2, "rigging": 3, "rudder": 3, "cargo": 2},
        "description": "A compact three-masted naval cruiser that trades some endurance for speed and manoeuvrability."
    },
    "Merchantman": {
        "cost": 5100, "hull": 430, "speed": 148.0, "turn": 0.6, "guns": 5, "max_cannons": 14,
        "reload": 2.0, "oar_power": 0.0, "rowers": 0, "crew": 170, "cargo": 270.0, "length": 211,
        "beam": 72, "hull_profile": (0.31, 0.48, 0.50, 0.48, 0.24), "collision_radius": 72.0, "rig": "merchant", "masts": (0.28, 0.57, 0.82), "sail_span": 49,
        "outfitting": ("hull", "cannons", "rigging", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 2, "rigging": 2, "cargo": 3},
        "description": "A capacious merchant vessel with a bluff hull, modest armament and room for a valuable cargo."
    },
    "Carrack": {
        "cost": 6400, "hull": 560, "speed": 132.0, "turn": 0.5, "guns": 7, "max_cannons": 18,
        "reload": 2.08, "oar_power": 0.0, "rowers": 0, "crew": 260, "cargo": 300.0, "length": 221,
        "beam": 77, "hull_profile": (0.32, 0.49, 0.50, 0.49, 0.25), "collision_radius": 76.0, "rig": "carrack", "masts": (0.27, 0.54, 0.81), "sail_span": 53,
        "outfitting": ("hull", "cannons", "rigging", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 2, "rigging": 2, "cargo": 3},
        "description": "An old-fashioned high-sided ocean carrier, slow to turn but exceptionally sturdy and spacious."
    },
    "Galleon": {
        "cost": 9300, "hull": 700, "speed": 125.0, "turn": 0.47, "guns": 9, "max_cannons": 24,
        "reload": 2.12, "oar_power": 0.0, "rowers": 0, "crew": 420, "cargo": 360.0, "length": 237,
        "beam": 82, "hull_profile": (0.31, 0.48, 0.50, 0.47, 0.24), "collision_radius": 82.0, "rig": "galleon", "masts": (0.23, 0.49, 0.77), "sail_span": 57,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 2, "rudder": 1, "cargo": 3},
        "description": "A towering ocean-going galleon with raised castles, a deep hold and a formidable defensive broadside."
    },
    "East Indiaman": {
        "cost": 10800, "hull": 760, "speed": 139.0, "turn": 0.52, "guns": 10, "max_cannons": 26,
        "reload": 2.06, "oar_power": 0.0, "rowers": 0, "crew": 430, "cargo": 410.0, "length": 248,
        "beam": 86, "hull_profile": (0.32, 0.49, 0.50, 0.49, 0.25), "collision_radius": 86.0, "rig": "indiaman", "masts": (0.23, 0.49, 0.77), "sail_span": 60,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 2, "cargo": 3},
        "description": "A very large armed merchant ship, broad in the beam and built to carry expensive cargo across oceans."
    },
    "Frigate": {
        "cost": 6800, "hull": 420, "speed": 176.0, "turn": 0.76, "guns": 12, "max_cannons": 30,
        "reload": 1.95, "oar_power": 0.0, "rowers": 0, "crew": 280, "cargo": 155.0, "length": 254,
        "beam": 66, "hull_profile": (0.18, 0.37, 0.47, 0.37, 0.12), "collision_radius": 82.0, "rig": "frigate", "masts": (0.22, 0.49, 0.77), "sail_span": 52,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 3, "cargo": 2},
        "description": "A long, fine-lined three-masted warship with a full gun deck and room to carry a fleet commander."
    },
    "Ship of the Line": {
        "cost": 18000, "hull": 1120, "speed": 112.0, "turn": 0.36, "guns": 21, "max_cannons": 48,
        "reload": 2.3, "oar_power": 0.0, "rowers": 0, "crew": 720, "cargo": 245.0, "length": 286,
        "beam": 94, "hull_profile": (0.28, 0.47, 0.50, 0.46, 0.21), "collision_radius": 96.0, "rig": "ship_of_line", "masts": (0.20, 0.47, 0.75), "sail_span": 68,
        "outfitting": ("hull", "cannons", "rigging", "rudder", "cargo"),
        "upgrade_limits": {"hull": 3, "cannons": 3, "rigging": 3, "rudder": 2, "cargo": 2},
        "description": "A colossal three-decker, slow to answer the helm but carrying the heaviest broadside on the chart."
    },
}

SHIP_NAME_PREFIXES = (
    "Amber", "Ashen", "Azure", "Battered", "Black", "Blue", "Bold", "Brave", "Bright", "Broken",
    "Burning", "Calm", "Carmine", "Clever", "Copper", "Coral", "Crimson", "Crooked", "Dancing", "Daring",
    "Dawn", "Deep", "Distant", "Drifting", "Dusky", "Emerald", "Endless", "Faithful", "Fallen", "Faraway",
    "Fearless", "Fierce", "Firelit", "First", "Flying", "Forgotten", "Fortunate", "Free", "Golden", "Graceful",
    "Grave", "Grey", "Hidden", "Hollow", "Indigo", "Ivory", "Jade", "Jolly", "Last", "Laughing",
    "Lucky", "Merry", "Midnight", "Misty", "Noble", "Northern", "Old", "Patient", "Pale", "Proud",
    "Quiet", "Ragged", "Raven", "Red", "Restless", "Rising", "Royal", "Ruby", "Sacred", "Sable",
    "Salty", "Scarlet", "Secret", "Shining", "Silent", "Silver", "Solitary", "Southern", "Sovereign", "Starlit",
    "Steady", "Stormy", "Swift", "Tall", "Tattered", "Tempest", "Thrifty", "Wandering", "Warm", "Wayward",
    "Western", "White", "Wild", "Windward", "Worthy", "Yellow", "Zealous", "Starless", "Moonlit", "Sea-worn",
)

SHIP_NAME_SUFFIXES = (
    "Arrow", "Asp", "Badger", "Banshee", "Bastion", "Beacon", "Belle", "Bess", "Blade", "Blessing",
    "Blossom", "Bonny", "Bounty", "Breeze", "Caper", "Caravel", "Carib", "Charm", "Chaser", "Corsair",
    "Crescent", "Crown", "Dancer", "Dart", "Dawn", "Defiant", "Dolphin", "Dove", "Dragon", "Dream",
    "Eagle", "Eclipse", "Endeavour", "Falcon", "Felicity", "Fidelity", "Firefly", "Fortune", "Fox", "Freedom",
    "Gannet", "Gale", "Galleon", "Gambit", "Glory", "Goddess", "Goliath", "Grace", "Gull",
    "Hawk", "Herald", "Hope", "Horizon", "Hound", "Ibis", "Indigo", "Jasmine", "Jester", "Kestrel",
    "Kingfisher", "Kite", "Liberty", "Lily", "Lion", "Lively", "Loyalty", "Maid", "Mariner", "Marlin",
    "Mermaid", "Meridian", "Minstrel", "Mockingbird", "Mongoose", "Morrow", "Nightingale", "Nomad", "Osprey", "Owl",
    "Pelican", "Petrel", "Phoenix", "Pioneer", "Plover", "Privateer", "Providence", "Ranger", "Raven", "Reckoning",
    "Revenge", "Riddle", "Rover", "Sable", "Sailor", "Sally", "Salvation", "Seahorse", "Seeker", "Sentinel",
    "Serpent", "Shamrock", "Shepherd", "Skylark", "Solace", "Sparrow", "Spectre", "Spirit", "Star", "Stingray",
    "Swallow", "Tempest", "Thistle", "Thunder", "Trident", "Triumph", "Turtle", "Vagabond", "Valour", "Venture",
    "Vigilant", "Viper", "Vixen", "Wanderer", "Warrior", "Wave", "Wren", "Zephyr", "Widow", "Whisper",
)


SHIP_NAME_COMBINATIONS = tuple(dict.fromkeys(
    name
    for prefix, suffix in itertools.product(SHIP_NAME_PREFIXES, SHIP_NAME_SUFFIXES)
    if len(name := f"The {prefix} {suffix}") <= 24
))


def max_broadside_guns(ship_type):
    stats = SHIP_CLASSES.get(ship_type, SHIP_CLASSES["Sloop"])
    return max(1, int(stats["max_cannons"]) // 2)


def ship_upgrade_limit(ship_type, upgrade):
    stats = SHIP_CLASSES.get(ship_type, SHIP_CLASSES["Sloop"])
    return max(0, int(stats.get("upgrade_limits", {}).get(upgrade, 0)))


def generate_ship_name(rng, used_names=None):
    used = used_names if used_names is not None else set()
    combinations = SHIP_NAME_COMBINATIONS
    available_count = len(combinations) - len(used.intersection(combinations))
    if available_count <= 0:
        serial = len(used) + 1
        while True:
            candidate = f"Horizon {serial}"
            if candidate not in used:
                used.add(candidate)
                return candidate
            serial += 1
    start = rng.randrange(len(combinations))
    stride = rng.randrange(1, len(combinations))
    while math.gcd(stride, len(combinations)) != 1:
        stride = rng.randrange(1, len(combinations))
    index = start
    for _ in range(len(combinations)):
        candidate = combinations[index]
        if candidate not in used:
            used.add(candidate)
            return candidate
        index = (index + stride) % len(combinations)
    serial = len(used) + 1
    candidate = f"Horizon {serial}"
    while candidate in used:
        serial += 1
        candidate = f"Horizon {serial}"
    used.add(candidate)
    return candidate
