import unittest

from tidebound.port_catalogue import (
    OUTFITTER_CATEGORIES,
    OUTFITTER_CATEGORY_BY_FITTING,
    SHIPYARD_CATEGORIES,
    SHIPYARD_CATEGORY_BY_CLASS,
    filter_outfitter_items,
    filter_ship_types,
)
from tidebound.ship_fittings import CUSTOMISATION_CATEGORIES
from tidebound.ships import SHIP_CLASSES


class PortCatalogueTests(unittest.TestCase):
    def test_every_ship_class_has_exactly_one_shipyard_category(self):
        grouped = [ship_type for _, ship_types in SHIPYARD_CATEGORIES if ship_types for ship_type in ship_types]
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertEqual(set(grouped), set(SHIP_CLASSES))
        self.assertEqual(set(SHIPYARD_CATEGORY_BY_CLASS), set(SHIP_CLASSES))

    def test_shipyard_filter_returns_only_the_selected_role(self):
        all_ships = list(SHIP_CLASSES)
        self.assertEqual(filter_ship_types(all_ships, "All Ships"), all_ships)
        for category, ship_types in SHIPYARD_CATEGORIES:
            if ship_types:
                filtered = filter_ship_types(all_ships, category)
                self.assertEqual(set(filtered), set(ship_types))
                self.assertTrue(all(SHIPYARD_CATEGORY_BY_CLASS[item] == category for item in filtered))

    def test_every_outfitter_entry_belongs_to_a_category(self):
        fitting_keys = {key for key, _, _ in CUSTOMISATION_CATEGORIES}
        upgrade_keys = {"hull", "cannons", "rigging", "rudder", "cargo", "rowers"}
        mapped = set(OUTFITTER_CATEGORY_BY_FITTING)
        self.assertTrue(fitting_keys.issubset(mapped))
        self.assertTrue(upgrade_keys.issubset(mapped))
        self.assertEqual(len({key for _, keys in OUTFITTER_CATEGORIES if keys for key in keys}),
                         sum(len(keys) for _, keys in OUTFITTER_CATEGORIES if keys))

    def test_outfitter_filter_keeps_only_selected_group(self):
        items = [
            {"key": "reinforced", "group": "Hull"},
            {"key": "long_nines", "group": "Weapons"},
            {"key": "canvas", "group": "Sails"},
        ]
        self.assertEqual(filter_outfitter_items(items, "All Fittings"), items)
        self.assertEqual(filter_outfitter_items(items, "Weapons"), [items[1]])
        self.assertEqual(filter_outfitter_items(items, "Flags & Colours"), [])


if __name__ == "__main__":
    unittest.main()
