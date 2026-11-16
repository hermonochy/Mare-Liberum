import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame is required for game package imports")
class PackageImportTests(unittest.TestCase):
    def test_public_game_imports(self):
        from tidebound import Game
        from tidebound.game import Game as ExplicitGame
        import main

        self.assertIs(Game, ExplicitGame)
        self.assertTrue(callable(main.Game))

    def test_all_game_mixins_are_exported(self):
        from tidebound.mixins import (
            CameraMixin,
            ControlsMixin,
            DayJobsMixin,
            DiplomacyMixin,
            MissionEventsMixin,
            MissionMixin,
            PortMenuMixin,
            ReefsMixin,
            RenderingMixin,
            SaveLoadMixin,
            ShipwreckMixin,
            ShipyardFleetMixin,
            TradeMixin,
            TrafficMixin,
            TreasureMixin,
            VesselsMixin,
        )

        self.assertEqual(len({
            CameraMixin,
            ControlsMixin,
            DayJobsMixin,
            DiplomacyMixin,
            MissionEventsMixin,
            MissionMixin,
            PortMenuMixin,
            ReefsMixin,
            RenderingMixin,
            SaveLoadMixin,
            ShipwreckMixin,
            ShipyardFleetMixin,
            TradeMixin,
            TrafficMixin,
            TreasureMixin,
            VesselsMixin,
        }), 16)


if __name__ == "__main__":
    unittest.main()
