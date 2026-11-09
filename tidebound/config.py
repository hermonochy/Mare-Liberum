from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MISSION_DIR = PROJECT_ROOT / "missions"
# Authored world coordinates use a compact design grid and are scaled at startup.
MAP_DESIGN_WIDTH = 19000
MAP_DESIGN_HEIGHT = 11000
WORLD_SCALE = 3.2
WORLD_WIDTH = int(MAP_DESIGN_WIDTH * WORLD_SCALE)
WORLD_HEIGHT = int(MAP_DESIGN_HEIGHT * WORLD_SCALE)
PORT_BERTH_COUNT = 9
PORT_BERTH_CENTER_SLOT = PORT_BERTH_COUNT // 2
PORT_BERTH_SPACING = 220.0
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


REGIONAL_PORT_DATA = [
    ("Isla Verde", 3900, 1000, "Windward Reach", "A green volcanic island whose sheltered harbour trades in fruit, rope, and quiet gossip."),
    ("Saint Brigid", 6300, 2600, "Windward Reach", "A small chapel town where fishermen mend their nets and old sailors leave offerings for safe passage."),
    ("Lantern Bay", 8100, 700, "Windward Reach", "A lantern tower watches a busy anchorage used by pilots, smugglers, and coastal traders."),
    ("Port Azure", 5200, 3850, "Windward Reach", "A blue-water roadstead with a crowded market and a reputation for excellent shipwrights."),
    ("Pelican's Rest", 7750, 3900, "Windward Reach", "A quiet fishing haven where the tavern keeper knows every vessel that has crossed the reach."),
    ("Blackwater Reach", 3500, 6750, "Leeward Expanse", "A river-mouth port of tar kilns, shallow bars, and merchants who pay well for dependable captains."),
    ("San Telmo", 5950, 9100, "Leeward Expanse", "A fortified island town with a weather station and a harbour full of hard-working coasters."),
    ("Mariner's Rest", 8350, 6350, "Leeward Expanse", "A generous anchorage for long-haul sailors, with fresh water and a lively chandlery."),
    ("Puerto Cielo", 9600, 8650, "Leeward Expanse", "A hilltop settlement whose white buildings can be seen for miles beyond the reefs."),
    ("Cormorant Quay", 6300, 5050, "Leeward Expanse", "A weather-beaten port on a busy sea lane, famed for its pilots and stubborn harbourmaster."),
    ("Nueva Esperanza", 10400, 1400, "Spanish Main", "A prosperous colonial harbour where silver buyers, customs men, and private agents cross paths."),
    ("Crown's Fall", 13600, 3500, "Spanish Main", "A former royal outpost whose old fort now overlooks a growing community of independent traders."),
    ("Sugarhook", 16200, 800, "Spanish Main", "A sugar island with broad plantations, cane wharves, and a labourers quarter that resents the governor."),
    ("Port de Lune", 11200, 4850, "Spanish Main", "A French-speaking port of chandlers, map sellers, and ship brokers who ask few questions."),
    ("Santa Isabela", 16300, 5150, "Spanish Main", "A grand stone harbour guarding the old silver road and the approaches to the mainland."),
    ("Mermaid's Rest", 17000, 6800, "Outer Antilles", "A remote island anchorage where deep water, warm springs, and old sea tales draw passing crews."),
    ("Stormhaven", 13200, 8900, "Outer Antilles", "A sturdy port built behind a natural breakwater, often crowded when the trade winds turn rough."),
    ("Redoubt", 17800, 4500, "Outer Antilles", "A cliffside settlement with an old signal fort and a watchful militia of local sailors."),
    ("Saint's Refuge", 14800, 9700, "Outer Antilles", "A haven for shipwreck survivors, retired corsairs, and anyone who has earned a second chance."),
    ("Last Light", 18000, 9300, "Outer Antilles", "The farthest charted harbour in the chain, where the western horizon seems to swallow the sun."),
    ("Wreckers' Moon", 2450, 2350, "The Far Shoals", "A crescent island of wreckers, salvagers, and pilots who can read a reef by the colour of its foam."),
    ("Bellweather Cay", 9000, 9650, "The Far Shoals", "A steep green island whose observatory keeps records of storms, tides, and strange lights offshore."),
    ("San Aurelio", 11900, 2450, "The Far Shoals", "A quiet Spanish mission port built around a ruined monastery and an archive of forbidden charts."),
    ("Gallows Key", 14500, 7350, "The Far Shoals", "A remote anchorage where former privateers trade secrets and no flag is trusted for long."),

]

REGIONAL_PORT_FACTIONS = {
    "Isla Verde": "British Crown", "Saint Brigid": "Independent", "Lantern Bay": "British Crown",
    "Port Azure": "Merchant League", "Pelican's Rest": "Independent", "Blackwater Reach": "Merchant League",
    "San Telmo": "Spanish Crown", "Mariner's Rest": "Merchant League", "Puerto Cielo": "Spanish Crown",
    "Cormorant Quay": "British Crown", "Nueva Esperanza": "Spanish Crown", "Crown's Fall": "British Crown",
    "Sugarhook": "Merchant League", "Port de Lune": "French Crown", "Santa Isabela": "Spanish Crown",
    "Mermaid's Rest": "Merchant League", "Stormhaven": "British Crown", "Redoubt": "British Crown",
    "Saint's Refuge": "Independent", "Last Light": "British Crown", "Wreckers' Moon": "Pirate Brotherhood",
    "Bellweather Cay": "Independent", "San Aurelio": "Spanish Crown", "Gallows Key": "Pirate Brotherhood",
}

# Several named ports now share a single large island. Bearings are measured
# clockwise from the east in screen/world coordinates (positive Y points south).
# Every location keeps its own faction, harbour office and mission identity.
MULTI_PORT_ISLAND_GROUPS = [
    {
        "name": "The Windward Grand Isle", "center": (6500, 3700),
        "radius": (1700, 1300),
        "ports": [
            ("Saint Brigid", -115), ("Port Azure", 178),
            ("Pelican's Rest", 8), ("Cormorant Quay", 92),
        ],
    },
    {
        "name": "The Leeward Continent", "center": (7000, 7700),
        "radius": (3100, 2100),
        "ports": [
            ("Blackwater Reach", 178), ("San Telmo", 138),
            ("Mariner's Rest", -82), ("Puerto Cielo", 4),
            ("Bellweather Cay", 68),
        ],
    },
    {
        "name": "The Spanish Main", "center": (13300, 2800),
        "radius": (3000, 1850),
        "ports": [
            ("Nueva Esperanza", -145), ("San Aurelio", -82),
            ("Sugarhook", -25), ("Crown's Fall", 22),
            ("Port de Lune", 158), ("Santa Isabela", 72),
        ],
    },
    {
        "name": "The Outer Antilles", "center": (15700, 7750),
        "radius": (2600, 2700),
        "ports": [
            ("Redoubt", -72), ("Mermaid's Rest", -22),
            ("Last Light", 43), ("Saint's Refuge", 124),
            ("Stormhaven", 178), ("Gallows Key", -137),
            ("Puerto Escondido", 78),
        ],
    },
]

FACTION_PORT_DATA = [
    ("Black Flag Anchorage", 18300, 1450, "Outer Antilles", "A hard-bitten pirate harbour tucked among outer reefs. Captains gather here to bargain, refit, and disappear.", "Pirate Brotherhood"),
    ("King's Sounding", 1050, 8100, "Leeward Expanse", "A remote Royal Navy station with a signal tower, a powder store, and officers who take the Crown's business seriously.", "British Crown"),
    ("Puerto Escondido", 18400, 10600, "Spanish Main", "A Spanish Crown harbour on the far southern route, watched by customs cutters and guarded by an old stone battery.", "Spanish Crown"),
    ("La Compagnie", 1550, 4500, "The Far Shoals", "A French charter-company port where brokers trade in sugar, maps, private contracts, and information from every flag.", "French Crown"),
    ("St Anne's Exchange", 11200, 550, "Windward Reach", "A prosperous merchant harbour run by a league of shipowners. Its warehouses are full, its ledgers exact, and its guards well paid.", "Merchant League"),
    ("Free Sailors' Haven", 10800, 7600, "Leeward Expanse", "A self-governing harbour where independent captains, shipwrights, and refugees vote on local rules beneath a weathered blue flag.", "Independent"),
]

FACTION_COLOURS = {
    "British Crown": (62, 104, 160),
    "Spanish Crown": (183, 61, 48),
    "French Crown": (72, 118, 177),
    "Merchant League": (205, 169, 77),
    "Pirate Brotherhood": (37, 35, 34),
    "Independent": (65, 139, 111),
}

SCATTERED_CAY_ANCHORS = [
    (1450, 5650), (3000, 8700), (4650, 5150), (9250, 1750),
    (9400, 5550), (10300, 7600), (17900, 1850), (11500, 10300),
    (18400, 7200), (6600, 10400), (8700, 4200), (1100, 9400),
    (15100, 5550), (4300, 9600), (9900, 9700), (16600, 10200),
    (2300, 1450), (4200, 2650), (7200, 1800), (8700, 8200),
    (11200, 6500), (12800, 10400), (15400, 2500), (18100, 5600),
]

# ---------------------------------------------------------------------------
# Runtime and presentation settings
# ---------------------------------------------------------------------------
GAME_WINDOW_SIZE = (1280, 800)
GAME_TARGET_FPS = 60
GAME_FRAME_TIME_LIMIT = 0.04
SAVE_FILE_EXTENSION = ".tide"
SAVE_FORMAT_IDENTIFIER = "MARE_LIBERUM_VOYAGE"
SETTINGS_FILE_NAME = "mare_liberum_settings.json"

DEFAULT_TEXT_SCALE = 1.0
MIN_TEXT_SCALE = 0.75
MAX_TEXT_SCALE = 1.5
TEXT_SCALE_STEP = 0.05
FONT_FAMILY = "georgia"
FONT_BASE_SIZES = {
    "normal": 30, "small": 25, "tiny": 21,
    "title": 42, "big": 52, "map": 16, "map_heading": 18,
}
FONT_MIN_SIZES = {
    "normal": 12, "small": 11, "tiny": 10,
    "title": 16, "big": 20, "map": 9, "map_heading": 10,
}
DEFAULT_EFFECTS_VOLUME = 1.0
DEFAULT_AMBIENCE_VOLUME = 1.0
VOLUME_STEP = 0.05

# Audio device and soundscape tuning.
AUDIO_MIXER_OPTIONS = {"frequency": 22050, "size": -16, "channels": 2, "buffer": 512}
AUDIO_CHANNEL_COUNT = 24
AUDIO_LOOP_CHANNELS = ("wind_at_sea", "rolling_waves", "harbour_ambience")
AUDIO_SOUND_NAMES = (
    "wind_at_sea", "rolling_waves", "sails_flapping",
    "cannon_fire", "cannon_impact", "harbour_ambience",
)
AUDIO_INITIAL_SAIL_INTERVAL = (4.0, 8.0)
AUDIO_SAIL_INTERVAL = (5.0, 12.0)
AUDIO_WIND_VOLUME_BASE = 0.13
AUDIO_WIND_VOLUME_RANGE = 0.12
AUDIO_DOCKED_WIND_VOLUME = 0.085
AUDIO_WAVES_UNDERWAY_VOLUME = 0.20
AUDIO_WAVES_DOCKED_VOLUME = 0.13
AUDIO_HARBOUR_AUDIBLE_DISTANCE = 1800.0
AUDIO_HARBOUR_MAX_VOLUME = 0.31
AUDIO_SAIL_SPEED_THRESHOLD = 8.0
AUDIO_SAIL_WIND_THRESHOLD = 0.45


# Initial world layout and new-captain starting state. Coordinates use the design grid
# and are scaled together when the chart is built.
BASE_LAND_POLYGONS = [[(145, 258),
  (290, 170),
  (520, 174),
  (735, 286),
  (820, 465),
  (744, 590),
  (570, 690),
  (355, 700),
  (186, 590),
  (105, 430)],
 [(1328, 260),
  (1458, 146),
  (1662, 105),
  (1853, 204),
  (1930, 362),
  (1812, 497),
  (1590, 520),
  (1400, 421),
  (1306, 340)],
 [(1850, 1170),
  (1910, 1040),
  (2040, 960),
  (2180, 925),
  (2350, 950),
  (2490, 1030),
  (2585, 1160),
  (2550, 1300),
  (2420, 1415),
  (2240, 1460),
  (2050, 1410),
  (1900, 1300)],
 [(2720, 438), (2846, 342), (2990, 420), (3060, 588), (2942, 760), (2770, 730), (2655, 585)],
 [(520, 3600),
  (666, 3485),
  (890, 3520),
  (1060, 3660),
  (1038, 3822),
  (855, 3930),
  (630, 3890),
  (494, 3755)],
 [(1710, 3170),
  (1790, 3110),
  (1900, 3140),
  (1970, 3230),
  (1930, 3345),
  (1820, 3410),
  (1725, 3350),
  (1670, 3255)],
 [(3250, 3500), (3380, 3415), (3540, 3460), (3640, 3600), (3570, 3760), (3410, 3810), (3270, 3710)]]
STARTING_PORT_DATA = [('Port Royal',
  540,
  825,
  540,
  682,
  90.0,
  'A noisy free port of privateers, rum runners, fishwives, and crooked customs men.',
  'Old Caribbean',
  'Independent'),
 ('Tortuga',
  1610,
  605,
  1600,
  487,
  90.0,
  'A lawless harbour tucked beneath green hills. Every tavern has a different account of the truth.',
  'Old Caribbean',
  'Pirate Brotherhood'),
 ('Havana',
  2245,
  810,
  2245,
  938,
  -90.0,
  'A fortified Spanish harbour with high stone walls, merchant galleons, and watchful soldiers.',
  'Old Caribbean',
  'Spanish Crown')]
STARTING_TREASURE_DATA = [('gannet_cay',
  'Gannet Cay',
  [(915, 1450),
   (955, 1385),
   (1025, 1370),
   (1090, 1400),
   (1120, 1465),
   (1090, 1530),
   (1020, 1550),
   (950, 1520)],
  1035,
  1495,
  875,
  1350,
  'The Crooked Palm Chart',
  'Sail east from Port Royal until a low green cay rises beyond the reef. Its crooked palm leans '
  'toward the sunrise. The chart marks the pale beach beneath it.',
  'Three roots drink from one stone. From the crooked palm, take seven paces toward the rising sun. '
  'Which place hides the chest?',
  ['The pale sand beside the split log',
   'The pool beneath the northern cliff',
   'The reef where the gulls circle'],
  0,
  420,
  'A silver sextant'),
 ('widows_key',
  "Widow's Key",
  [(2824, 950),
   (2870, 900),
   (2940, 908),
   (3004, 956),
   (3022, 1027),
   (2974, 1094),
   (2900, 1112),
   (2842, 1068)],
  2930,
  1045,
  2500,
  840,
  "The Widow's Last Key",
  'Run east of the great green island, where the open sea meets a small key watched by two pale rocks. '
  'At sunset the western beach turns the colour of old gold.',
  'The widow keeps her fortune where two white sentries face the western tide. Do not dig beneath the '
  'taller one; seek the sand between them. What marks the right place?',
  ["The black rock at the island's point",
   'The sand between the twin white stones',
   'The mangrove pool behind the beach'],
  1,
  650,
  'A ruby-encrusted ring'),
 ('dead_mans_cay',
  "Dead Man's Cay",
  [(1660, 2350),
   (1715, 2285),
   (1790, 2290),
   (1855, 2350),
   (1850, 2425),
   (1785, 2490),
   (1705, 2480),
   (1650, 2410)],
  1750,
  2390,
  1960,
  2180,
  'The Broken Mast Chart',
  'Sail southwest from Havana, past the southern shadow of the great island. A tiny cay hides there, '
  'with a broken mast lying across its red-sand beach.',
  'A dead mast points no more to sea. When the sun sinks, its shadow touches the only red patch of '
  'sand. Where does the old captain sleep?',
  ['At the foot of the fallen mast',
   "Under the palm at the island's centre",
   'Beside the eastern tide pool'],
  0,
  900,
  'The Black Pearl of Saint Elmo')]
INITIAL_PIRATE_DATA = [(('The Drowned Crown', 2760 * WORLD_SCALE, 1510 * WORLD_SCALE, -130), {'side_choice': 1, 'wander': 4.1})]
STARTING_SHIP_POSITION = (540.0, 825.0)
STARTING_SHIP_HEADING = 90.0
STARTING_PORT_NAME = "Port Royal"
STARTING_SHIP_CLASS = "Sloop"
STARTING_SHIP_NAME = "The Wayward Gull"
STARTING_SHIP_LIVERY = 0
STARTING_SHIP_UPGRADES = {"cannons": 0, "hull": 0, "rigging": 0, "rudder": 0, "cargo": 0}
STARTING_FLEET_ORDER = "follow"
STARTING_RANDOM_SEED = 41
INITIAL_TRAFFIC_COUNT = 7
INITIAL_TRAFFIC_SPAWN_INTERVAL = 20.0
SHIPYARD_TABS = ("Flagship", "Refits", "Fleet", "Repairs", "Name & Colours")
STARTING_CAMERA_ZOOM = 1.0
STARTING_SAIL_SETTING = 0.72
STARTING_WIND = (24.0, 1.0)
STARTING_GOLD = 175
STARTING_JOURNAL = (
    "A battered sloop, a short purse, and a long stretch of blue water. Port Royal is your home for now.",
    "The harbourmaster may know who is hiring. Ask around before putting out to sea.",
)
PORT_GREETING_TEXT = {
    "Port Royal": "The harbourmaster's office is a low, timber building wedged between a rum store and a sailmaker. A brass bell rings as you step inside. A clerk looks up from a ledger; by the window, an old captain with a silver beard folds his charts and watches the sea.",
    "Tortuga": "A tavern keeper wipes a pewter mug and watches you over its rim. Outside, men argue over dice while a schooner is careened on the beach.",
    "Havana": "A uniformed harbour officer waits beneath a portrait of the governor. Beyond the open shutters, bells ring over the crowded anchorage.",
}
PORT_NEWS_TEXT = {
    "Port Royal": "A fisherman says black-sailed vessels have been seen beyond the eastern reefs. The customs men claim it is none of their concern.",
    "Tortuga": "The taverns whisper of Captain Vane, a ruthless privateer who has taken to flying the black flag. His ships are gathering in the cays.",
    "Havana": "The merchants complain that no convoy dares leave harbour. The governor promises safety, but the harbour guns have been loaded for days.",
}

# ---------------------------------------------------------------------------
# Gameplay data tables and shared tuning
# ---------------------------------------------------------------------------
DAY_JOB_BOARD_SIZE = 5

FACTION_NAMES = (
        "British Crown",
        "Spanish Crown",
        "French Crown",
        "Merchant League",
        "Pirate Brotherhood",
        "Independent",
    )

REEF_ANCHORS = [
        (9150, 3450), (9450, 5150), (10850, 5650), (11650, 7050),
        (11650, 8750), (12350, 10150), (2900, 5200), (3150, 8950),
        (7100, 1450), (10100, 1750), (17250, 1150), (18800, 5350),
        (19000, 8650), (14500, 10800), (5200, 10450), (1750, 5650),
        (8500, 10400), (11900, 4450), (1950, 1850), (18300, 10800),
    ]

SHIPWRECK_DATA = [
        ("black_gull", "The Black Gull", 3604.8, 1631.9, 18, "merchant brig", "A merchant brig lost in a winter squall",
         "Her foremast is gone and a broken cargo boom lies across the deck. Several sealed crates still float in the lee of the hull.",
         "A split cargo of lamp oil has soaked the lower deck; a careless spark could ignite it.", 2, 95, 225, "The Black Gull's silver trade seal", 0.25),
        ("widows_promise", "The Widow's Promise", 1158.8, 5834.1, 214, "coastal schooner", "A coastal schooner abandoned decades ago",
         "The schooner's stern is almost intact. Crockery, copper pots and a captain's sea chest are visible beneath the waterline.",
         "The hull is weakened and shifts whenever the swell catches it.", 2, 70, 175, "A miniature ivory ship carved by the captain", 0.18),
        ("saint_elmos_prize", "Saint Elmo's Prize", 846.9, 9963.3, 306, "Spanish treasure barque", "A Spanish barque that vanished with a colonial payroll",
         "A gilded figurehead still clings to the bow. Rumour says the paymaster hid his strongbox below the officers' cabin.",
         "A powder locker lies beneath the stern. The smallest disturbance may set off a violent blast.", 3, 180, 360, "A gold-and-enamel astrolabe", 0.36),
        ("cormorant", "The Cormorant", 10297.7, 4801.5, 128, "merchant galleon", "A deep-draught galleon lost on a calm night",
         "The galleon's cargo decks remain largely sealed. Barrels and trade chests can be seen through a torn hatch.",
         "The wreck sits in a strong cross-current that can drag a small boat against jagged timbers.", 2, 125, 285, "A merchant prince's engraved pocket watch", 0.24),
        ("hms_tyrant", "HMS Tyrant", 12704.9, 5796.5, 42, "Royal Navy frigate", "A Royal Navy frigate lost during an undeclared engagement",
         "The ship's brass fittings and a sealed officer's dispatch case may still be recoverable.",
         "A shattered gun deck is littered with unstable cannon and splintered beams.", 3, 145, 310, "An Admiralty cipher wheel", 0.30),
        ("red_wake", "The Red Wake", 17288.8, 5086.0, 252, "pirate brig", "A feared pirate brig whose crew vanished overnight",
         "The blackened hull carries old boarding marks. A few lockers appear untouched, despite the wreck's reputation.",
         "The surrounding water is thick with broken spars and dangerous undertow.", 2, 115, 260, "The captain's black-ivory pistol crest", 0.27),
        ("la_belladonna", "La Belladonna", 9943.2, 6387.7, 76, "French merchantman", "A French merchantman carrying rare dyes and fine instruments",
         "The stern cabin has collapsed, but the hold contains sealed dye jars and navigational equipment.",
         "The wreck is infested with sharp coral growth and a dense tangle of rigging.", 1, 100, 205, "A rosewood octant with silver inlay", 0.22),
        ("old_hope", "The Old Hope", 586.5, 5500.1, 330, "fishing ketch", "A fishing ketch caught in a sudden squall",
         "This small vessel was no warship, but its crew were known to carry a private savings box for the winter.",
         "The water is shallow and the broken hull is close to the rocks; approach slowly.", 1, 45, 95, "A sailor's carved bone playing set", 0.12),
        ("santa_isidora", "Santa Isidora", 8286.4, 3074.5, 166, "Spanish treasure galleon", "A heavily laden galleon lost during a storm",
         "A line of silver ingots is visible through a rent in the hull. The captain's cabin is buried beneath the collapsed quarterdeck.",
         "The wreck's powder room is partly flooded but not completely safe.", 3, 210, 420, "A silver crown medallion from the lost expedition", 0.38),
        ("mercy_of_lune", "Mercy of Lune", 1024.5, 10404.9, 112, "hospital ship", "A small hospital ship wrecked while carrying supplies between islands",
         "Medical chests and trade goods are still lashed below deck. A sealed surgeon's journal may have survived.",
         "A foul current runs through the wreck, and loose timbers can trap a diver.", 2, 80, 190, "The surgeon's annotated field journal", 0.23),
        ("iron_duke", "The Iron Duke", 4274.6, 3063.6, 290, "armed merchant brig", "An armed merchant brig that fought off raiders before sinking",
         "Some of the gun deck remains intact. The cargo includes shot, tools and a locked pay chest.",
         "A loaded swivel gun is still wedged in the upper deck and may shift without warning.", 2, 135, 275, "A brass maker's plate from a famous shipyard", 0.21),
        ("serpent_dor", "Le Serpent d'Or", 8944.3, 2431.0, 12, "French privateer", "A French privateer whose last prize was never recorded",
         "Her prize room may contain captured jewellery and papers identifying a secret buyer.",
         "The wreck lies in a fast current and its flooded passageways are difficult to navigate.", 2, 150, 295, "A signet ring bearing the mark of a hidden trading house", 0.28),
        ("morning_star", "The Morning Star", 15955.4, 596.2, 196, "mail packet", "A mail packet lost while carrying dispatches between governors",
         "The letter lockers are sealed. The dispatches may be worth more to a scholar than to a fence.",
         "The bow is pinned beneath a heavy spar; removing it could bring the deck down.", 1, 65, 145, "A coded packet addressed to the first cartographer", 0.20),
        ("black_mermaid", "The Black Mermaid", 4009.3, 5394.9, 48, "pirate schooner", "A pirate schooner sunk after a mutiny",
         "The crew's scattered belongings remain aboard. One locked chest bears the initials of a notorious captain.",
         "The wreck is surrounded by tangled chain and jagged boarding hooks.", 2, 105, 250, "A captain's journal naming a forgotten anchorage", 0.31),
        ("san_jorge", "San Jorge", 13535.5, 5126.8, 226, "Spanish naval transport", "A naval transport lost while carrying fortification supplies",
         "The hold contains tools, iron fittings and a sealed dispatch box from the colonial command.",
         "An old magazine has been breached; a sudden impact could scatter burning debris.", 3, 130, 285, "A royal engineer's survey of an uncharted channel", 0.33),
        ("blue_lantern", "The Blue Lantern", 9254.5, 563.4, 84, "merchant schooner", "A merchant schooner whose lantern was seen long after the ship disappeared",
         "The wreck's cabin is remarkably well preserved. Its cargo was modest, but the navigation table may be valuable.",
         "The hull is lodged at an awkward angle and the upper deck can collapse.", 1, 85, 180, "A rare blue-glass tide compass", 0.26),
        ("la_reina", "La Reina de Sal", 14426.1, 292.7, 310, "Spanish treasure ship", "A treasure ship said to have carried the governor's private collection",
         "A heavy iron coffer is visible near the stern. The wreck has resisted generations of salvagers.",
         "The coffer is trapped beneath the gun deck beside a volatile powder store.", 3, 220, 460, "A pearl-inlaid royal seal", 0.40),
        ("northwind", "The Northwind", 11941.8, 10598.2, 154, "whaling brig", "A whaling brig that never returned from the outer waters",
         "Barrels of whale oil and a carpenter's chest remain aboard. The captain kept detailed weather notes.",
         "The wreck is deep and the current pulls strongly beneath the broken keel.", 2, 100, 220, "A whaler's storm journal with unusual current readings", 0.24),
    ]

TRADE_GOODS = [
        {"id": "sugar", "name": "Raw Sugar", "base": 11, "space": 1.0, "description": "Cane sugar for refineries, taverns and the kitchens of the islands."},
        {"id": "rum", "name": "Rum", "base": 24, "space": 1.0, "description": "Casks of island rum. Popular with sailors, taverns and privateers."},
        {"id": "tobacco", "name": "Tobacco", "base": 19, "space": 1.0, "description": "Bales of cured leaf, prized by merchants and colonial factors."},
        {"id": "coffee", "name": "Coffee", "base": 31, "space": 1.0, "description": "Green coffee beans from the warmer upland plantations."},
        {"id": "cocoa", "name": "Cocoa", "base": 28, "space": 1.0, "description": "Cocoa beans and cakes for the growing chocolate trade."},
        {"id": "spices", "name": "Spices", "base": 43, "space": 0.7, "description": "Pepper, nutmeg and other costly aromatics in sealed bales."},
        {"id": "fish", "name": "Salt Fish", "base": 9, "space": 1.0, "description": "Preserved fish, a staple for ships and settlements far from fresh water."},
        {"id": "salt", "name": "Salt", "base": 10, "space": 1.0, "description": "Salt for curing food, preserving hides and provisioning fleets."},
        {"id": "timber", "name": "Ship Timber", "base": 18, "space": 1.5, "description": "Hardwood beams and planking for yards, wharves and repairs."},
        {"id": "rope", "name": "Rope & Hemp", "base": 21, "space": 1.0, "description": "Cordage for rigging, anchors, blocks and dockside work."},
        {"id": "canvas", "name": "Sailcloth", "base": 32, "space": 1.0, "description": "Heavy canvas and sailcloth for merchantmen and warships."},
        {"id": "tools", "name": "Iron Tools", "base": 45, "space": 0.9, "description": "Tools and fittings needed by shipwrights, smiths and builders."},
        {"id": "gunpowder", "name": "Gunpowder", "base": 58, "space": 0.8, "description": "Sealed powder kegs. Valuable, regulated and dangerous cargo."},
        {"id": "silver", "name": "Silver Ingots", "base": 138, "space": 0.35, "description": "Small, heavy ingots from the Spanish silver routes."},
        {"id": "contraband", "name": "Contraband", "base": 82, "space": 0.65, "description": "Unregistered luxury goods. Profitable, but not welcome in every customs house."},
    ]

CARGO_CAPACITY_BY_SHIP = {
        "Sloop": 42.0,
        "Cutter": 34.0,
        "Schooner": 68.0,
        "Brigantine": 104.0,
        "Frigate": 82.0,
    }

TRADE_QUANTITY_OPTIONS = (1, 5, "MAX")

MARKET_TICK_SECONDS = 75.0

FACTION_PRODUCES = {
        "British Crown": {"canvas", "tools", "gunpowder", "rum"},
        "Spanish Crown": {"silver", "sugar", "cocoa", "tobacco"},
        "French Crown": {"coffee", "spices", "canvas", "rum"},
        "Merchant League": {"fish", "salt", "rope", "timber", "sugar"},
        "Pirate Brotherhood": {"contraband", "rum", "gunpowder", "tobacco"},
        "Independent": {"fish", "salt", "timber", "rope"},
    }

FACTION_WANTS = {
        "British Crown": {"sugar", "coffee", "cocoa", "spices", "fish"},
        "Spanish Crown": {"tools", "canvas", "gunpowder", "rope", "coffee"},
        "French Crown": {"sugar", "tobacco", "silver", "fish", "tools"},
        "Merchant League": {"silver", "spices", "coffee", "cocoa", "canvas", "gunpowder"},
        "Pirate Brotherhood": {"rum", "gunpowder", "tools", "silver", "canvas", "fish"},
        "Independent": {"tools", "canvas", "salt", "rum", "cocoa"},
    }

TRAFFIC_ROLES = {
        "merchant": {
            "names": ["Golden Finch", "Grace of Bridgetown", "Three Sisters", "Dawn Trader", "Providence", "Cane Blossom"],
            "types": ["Schooner", "Brigantine", "Frigate"],
            "hull": 7,
            "speed": 58.0,
        },
        "fishing": {
            "names": ["Little Minnow", "Net and Needle", "Morning Catch", "Blue Mackerel", "Sea Lark"],
            "types": ["Sloop", "Cutter"],
            "hull": 4,
            "speed": 66.0,
        },
        "naval patrol": {
            "names": ["HMS Resolute", "HMS Sparrowhawk", "HMS Vigilant", "La Centinela"],
            "types": ["Brigantine", "Frigate"],
            "hull": 9,
            "speed": 61.0,
        },
        "mail packet": {
            "names": ["Swift Dispatch", "King's Letter", "Morning Star", "The Post Boy"],
            "types": ["Cutter", "Schooner"],
            "hull": 5,
            "speed": 78.0,
        },
        "whaler": {
            "names": ["Northern Light", "White Whale", "Moby's Luck", "Harpooner"],
            "types": ["Brigantine", "Schooner"],
            "hull": 8,
            "speed": 48.0,
        },
    }

SHIP_COLLISION_RADII = {
        "Sloop": 52.0,
        "Cutter": 50.0,
        "Schooner": 55.0,
        "Brigantine": 58.0,
        "Frigate": 62.0,
    }

ADMIRAL_NAMES = {
        "naval patrol": ["Admiral Horatio Vale", "Commodore Anne Wycliffe", "Captain-General Mateo Ruiz"],
        "merchant": ["Commodore Elias Harcourt", "Master Mariner Beatrice Shaw", "Captain Tomas Bell"],
        "pirate": ["Black Jack Rourke", "Madame Sabine Voss", "Calico Ned Mercer", "Red Tom Kersey"],
    }

TRADE_GOODS_BY_ID = {good["id"]: good for good in TRADE_GOODS}

