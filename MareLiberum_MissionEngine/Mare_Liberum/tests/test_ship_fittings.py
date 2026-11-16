import unittest

from tidebound.ship_fittings import (
    CANNON_MOUNTS,
    CANNON_TYPES,
    CUSTOMISATION_CATEGORIES,
    DEFAULT_SHIP_CUSTOMISATION,
    HULL_FINISHES,
    HULL_FORMS,
    SAIL_DESIGNS,
    SAIL_TYPES,
    VISUAL_UPGRADES,
    default_ship_customisation,
    normalise_ship_customisation,
    ship_customisation_effects,
    ship_customisation_price,
    ship_fitting_available,
)


class ShipFittingTests(unittest.TestCase):
    def test_every_customisation_category_has_choices(self):
        self.assertEqual(len(CUSTOMISATION_CATEGORIES), 8)
        for key, _, options in CUSTOMISATION_CATEGORIES:
            self.assertIn(key, DEFAULT_SHIP_CUSTOMISATION)
            self.assertTrue(options)
            self.assertIn(DEFAULT_SHIP_CUSTOMISATION[key], options)

    def test_old_or_invalid_save_values_fall_back_to_defaults(self):
        selected = normalise_ship_customisation({"hull_form": "not a hull", "sail_design": "Corsair Mark"})
        self.assertEqual(selected["hull_form"], DEFAULT_SHIP_CUSTOMISATION["hull_form"])
        self.assertEqual(selected["sail_design"], "Corsair Mark")
        self.assertEqual(normalise_ship_customisation(None), default_ship_customisation())

    def test_cannon_types_have_distinct_combat_profiles(self):
        self.assertGreater(CANNON_TYPES["Demi-cannons"]["damage"], CANNON_TYPES["Long Nines"]["damage"])
        self.assertGreater(CANNON_TYPES["Long Nines"]["speed"], CANNON_TYPES["Standard Culverins"]["speed"])
        self.assertGreater(CANNON_TYPES["Swivel Guns"]["reload"], 0)
        self.assertGreater(CANNON_TYPES["Carronades"]["damage"], 1)

    def test_mounting_capabilities_scale_by_ship_class(self):
        self.assertTrue(ship_fitting_available("Sloop", "cannon_mount", "Bow & Stern Chasers"))
        self.assertFalse(ship_fitting_available("Sloop", "cannon_mount", "Rotating Turrets"))
        self.assertFalse(ship_fitting_available("Cutter", "cannon_mount", "Rotating Turrets"))
        self.assertTrue(ship_fitting_available("Brig", "cannon_mount", "Rotating Turrets"))
        self.assertTrue(ship_fitting_available("Frigate", "cannon_mount", "Rotating Turrets"))
        self.assertFalse(ship_fitting_available("Unknown Ship", "cannon_mount", "Broadside Batteries"))

    def test_effects_change_ship_performance_and_profile(self):
        racing = default_ship_customisation()
        racing["hull_form"] = "Racing Keel"
        racing["sail_type"] = "Racing Cut"
        effects = ship_customisation_effects(racing)
        self.assertGreater(effects["speed"], 1.0)
        self.assertEqual(effects["profile"], "fine")
        self.assertLess(effects["cargo"], 1.0)

    def test_customisation_prices_are_non_negative(self):
        for key, _, options in CUSTOMISATION_CATEGORIES:
            for option in options:
                self.assertGreaterEqual(ship_customisation_price(key, option), 0)

    def test_all_visual_catalogues_are_populated(self):
        self.assertGreaterEqual(len(HULL_FORMS), 5)
        self.assertGreaterEqual(len(HULL_FINISHES), 7)
        self.assertGreaterEqual(len(SAIL_DESIGNS), 7)
        self.assertIn("Black Jolly Roger Canvas", SAIL_DESIGNS)
        self.assertEqual(SAIL_DESIGNS["Black Jolly Roger Canvas"]["pattern"], "corsair")
        self.assertGreaterEqual(len(SAIL_TYPES), 4)
        self.assertGreaterEqual(len(VISUAL_UPGRADES), 5)
        self.assertGreaterEqual(len(CANNON_MOUNTS), 3)


if __name__ == "__main__":
    unittest.main()
