import unittest

from tidebound.ship_armament import (
    cannon_loadout_sequence,
    cannon_pair_capacity,
    cannon_replacement_type,
    cannon_type_for_gun,
    default_cannon_loadout,
    normalise_cannon_loadout,
)
from tidebound.ship_fittings import CANNON_TYPES
from tidebound.ships import SHIP_CLASSES, ROWERS_PER_UPGRADE, ship_upgrade_limit


class ShipArmamentTests(unittest.TestCase):
    def test_every_ship_class_can_row(self):
        for ship_type, stats in SHIP_CLASSES.items():
            self.assertGreater(stats["oar_power"], 0, ship_type)
            self.assertGreaterEqual(stats["rowers"], 8, ship_type)
            self.assertGreaterEqual(stats["rower_capacity"], stats["rowers"], ship_type)
            self.assertEqual("rowers" in stats["outfitting"], stats["rower_capacity"] > stats["rowers"], ship_type)

    def test_hireable_rower_limits_match_hull_capacity(self):
        for ship_type, stats in SHIP_CLASSES.items():
            expected = (stats["rower_capacity"] - stats["rowers"] + ROWERS_PER_UPGRADE - 1) // ROWERS_PER_UPGRADE
            self.assertEqual(ship_upgrade_limit(ship_type, "rowers"), expected, ship_type)

    def test_default_batteries_respect_class_capacity(self):
        for ship_type in SHIP_CLASSES:
            loadout = default_cannon_loadout(ship_type)
            self.assertEqual(sum(loadout.values()), cannon_pair_capacity(ship_type))

    def test_mixed_cannon_pairs_are_preserved(self):
        loadout = normalise_cannon_loadout(
            {"Standard Culverins": 2, "Long Nines": 1, "Demi-cannons": 1}, "Brig"
        )
        self.assertEqual(sum(loadout.values()), cannon_pair_capacity("Brig"))
        self.assertEqual(loadout["Long Nines"], 1)
        self.assertEqual(loadout["Demi-cannons"], 1)
        sequence = cannon_loadout_sequence(loadout, "Brig")
        self.assertEqual(sequence.count("Long Nines"), 1)
        self.assertEqual(sequence.count("Demi-cannons"), 1)
        self.assertEqual(cannon_type_for_gun(loadout, "Brig", 4), "Long Nines")

    def test_cannon_pair_replacement_maintains_total(self):
        loadout = {"Standard Culverins": 3}
        source = cannon_replacement_type(loadout, "Long Nines")
        self.assertEqual(source, "Standard Culverins")
        loadout[source] -= 1
        loadout["Long Nines"] = loadout.get("Long Nines", 0) + 1
        fitted = normalise_cannon_loadout(loadout, "Sloop")
        self.assertEqual(sum(fitted.values()), cannon_pair_capacity("Sloop"))
        self.assertEqual(fitted["Long Nines"], 1)
        self.assertIsNone(cannon_replacement_type({"Long Nines": cannon_pair_capacity("Sloop")}, "Long Nines"))

    def test_frigate_can_carry_thirty_guns(self):
        fitted_pairs = cannon_pair_capacity("Frigate", ship_upgrade_limit("Frigate", "cannons"))
        self.assertEqual(fitted_pairs * 2, SHIP_CLASSES["Frigate"]["max_cannons"])

    def test_cannon_profiles_remain_distinct_for_mixed_batteries(self):
        self.assertLess(CANNON_TYPES["Long Nines"]["damage"], CANNON_TYPES["Demi-cannons"]["damage"])
        self.assertGreater(CANNON_TYPES["Long Nines"]["life"] * CANNON_TYPES["Long Nines"]["speed"],
                           CANNON_TYPES["Demi-cannons"]["life"] * CANNON_TYPES["Demi-cannons"]["speed"])


if __name__ == "__main__":
    unittest.main()
