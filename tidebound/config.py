from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MISSION_DIR = PROJECT_ROOT / "missions"
WORLD_WIDTH = 19000
WORLD_HEIGHT = 11000
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

SCATTERED_CAY_ANCHORS = [
    (1450, 5650), (3000, 8700), (4650, 5150), (9250, 1750),
    (9400, 5550), (10300, 7600), (17900, 1850), (11500, 10300),
    (18400, 7200), (6600, 10400), (8700, 4200), (1100, 9400),
    (15100, 5550), (4300, 9600), (9900, 9700), (16600, 10200),
    (2300, 1450), (4200, 2650), (7200, 1800), (8700, 8200),
    (11200, 6500), (12800, 10400), (15400, 2500), (18100, 5600),
]

