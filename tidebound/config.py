from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MISSION_DIR = PROJECT_ROOT / "missions"
# V26 is deliberately a much broader chart. Coordinates authored against the
# original 19,000 x 11,000 chart are multiplied by this factor at startup.
WORLD_SCALE = 3.2
WORLD_WIDTH = int(19000 * WORLD_SCALE)
WORLD_HEIGHT = int(11000 * WORLD_SCALE)
LEGACY_V25_WORLD_SCALE = 1.28
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

