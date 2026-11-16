import random
import unittest
from pathlib import Path

from tidebound.mission_system import MissionParser
from tidebound.ships import (
    SHIP_CLASSES,
    SHIP_NAME_COMBINATIONS,
    generate_ship_name,
    max_broadside_guns,
    ship_upgrade_limit,
)


class ShipCatalogueTests(unittest.TestCase):
    def test_catalogue_contains_varied_ship_classes(self):
        self.assertGreaterEqual(len(SHIP_CLASSES), 15)
        lengths = [stats["length"] for stats in SHIP_CLASSES.values()]
        beams = [stats["beam"] for stats in SHIP_CLASSES.values()]
        self.assertGreater(max(lengths), min(lengths) * 2.5)
        self.assertGreater(max(beams), min(beams) * 2.0)
        for stats in SHIP_CLASSES.values():
            self.assertGreater(stats["hull"], 0)
            self.assertGreater(stats["speed"], 0)
            self.assertGreater(stats["cargo"], 0)
            self.assertGreater(stats["max_cannons"], 0)
            self.assertIn("outfitting", stats)
            self.assertIn("upgrade_limits", stats)
            self.assertIn("hull_profile", stats)
            self.assertGreater(stats["crew"], 0)
            self.assertEqual(set(stats["outfitting"]), {key for key, limit in stats["upgrade_limits"].items() if limit > 0})
            self.assertEqual(stats["rowers"] > 0, stats["oar_power"] > 0)
        self.assertGreater(len({stats["hull_profile"] for stats in SHIP_CLASSES.values()}), 8)
        for stats in SHIP_CLASSES.values():
            self.assertGreater(stats["oar_power"], 0)
            self.assertGreaterEqual(stats["rowers"], 8)
            self.assertGreaterEqual(stats["rower_capacity"], stats["rowers"])
        self.assertGreater(ship_upgrade_limit("Frigate", "rowers"), 0)
        self.assertGreater(ship_upgrade_limit("Ship of the Line", "rowers"), 0)

    def test_class_cannon_limits(self):
        self.assertEqual(SHIP_CLASSES["Sloop"]["max_cannons"], 10)
        self.assertEqual(SHIP_CLASSES["Frigate"]["max_cannons"], 30)
        self.assertEqual(max_broadside_guns("Sloop"), 5)
        self.assertEqual(max_broadside_guns("Frigate"), 15)
        for ship_type, stats in SHIP_CLASSES.items():
            self.assertEqual(stats["guns"] + ship_upgrade_limit(ship_type, "cannons"), max_broadside_guns(ship_type))
            self.assertEqual(max_broadside_guns(ship_type) * 2, stats["max_cannons"])

    def test_outfitting_capabilities_are_class_specific(self):
        self.assertEqual(ship_upgrade_limit("Launch", "cannons"), 0)
        self.assertEqual(ship_upgrade_limit("Yawl", "cannons"), 0)
        self.assertEqual(ship_upgrade_limit("Sloop", "cannons"), 2)
        self.assertEqual(ship_upgrade_limit("Frigate", "cannons"), 3)
        self.assertGreater(ship_upgrade_limit("Merchantman", "cargo"), ship_upgrade_limit("Sloop", "cargo"))

    def test_name_pool_and_generation(self):
        self.assertGreaterEqual(len(SHIP_NAME_COMBINATIONS), 1000)
        self.assertLessEqual(max(map(len, SHIP_NAME_COMBINATIONS)), 24)
        used = set()
        rng = random.Random(41)
        generated = [generate_ship_name(rng, used) for _ in range(1000)]
        self.assertEqual(len(set(generated)), 1000)
        self.assertEqual(len(used), 1000)
        self.assertTrue(all(len(name) <= 24 for name in generated))
        exhausted = set(SHIP_NAME_COMBINATIONS)
        fallback = generate_ship_name(rng, exhausted)
        self.assertLessEqual(len(fallback), 24)
        self.assertIn(fallback, exhausted)

    def test_existing_mission_files_still_parse(self):
        mission_dir = Path(__file__).resolve().parents[1] / "missions"
        files = sorted(mission_dir.glob("*.mission"))
        self.assertGreaterEqual(len(files), 70)
        for mission_file in files:
            mission = MissionParser(mission_file).parse()
            self.assertTrue(mission.mission_id)
            self.assertTrue(mission.title)
            self.assertTrue(set(mission.event_config.get("ship_types", [])).issubset(SHIP_CLASSES))


if __name__ == "__main__":
    unittest.main()
