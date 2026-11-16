import unittest

from tidebound.port_menu_helpers import outfitter_detail_lines


class OutfitterDetailTests(unittest.TestCase):
    def setUp(self):
        self.ship = {"name": "Sea Wraith", "type": "Frigate"}

    def test_upgrade_detail(self):
        lines = outfitter_detail_lines({"kind": "upgrade", "level": 2, "limit": 4, "cost": 900}, self.ship)
        self.assertIn("Current level: 2/4", lines)
        self.assertIn("Next installation: 900 gold", lines)

    def test_cannon_pair_detail_does_not_require_upgrade_fields(self):
        lines = outfitter_detail_lines({"kind": "cannon_pair", "cannon_type": "Long Nines", "source_type": "Standard Culverins", "cost": 2350}, self.ship)
        self.assertIn("Cannon type: Long Nines", lines)
        self.assertIn("Replacement: Standard Culverins", lines)
        self.assertIn("Installation: 2,350 gold", lines)

    def test_customisation_detail_does_not_require_upgrade_fields(self):
        lines = outfitter_detail_lines({"kind": "customisation", "category": "hull_form", "option": "Racing Keel", "cost": 1650}, self.ship)
        self.assertIn("Category: Hull Form", lines)
        self.assertIn("Fitting: Racing Keel", lines)
        self.assertIn("Installation: 1,650 gold", lines)

    def test_installed_customisation_is_reported(self):
        lines = outfitter_detail_lines({"kind": "customisation", "category": "flag_design", "option": "Black Jolly Roger", "installed": True}, self.ship)
        self.assertIn("Already installed", lines)


if __name__ == "__main__":
    unittest.main()
