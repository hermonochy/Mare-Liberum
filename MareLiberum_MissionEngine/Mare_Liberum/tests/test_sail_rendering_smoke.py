import sys
import types
import unittest
from unittest.mock import patch

from tidebound.ships import SHIP_CLASSES


class FakeRect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class FakeDraw:
    def __init__(self):
        self.calls = 0

    def _record(self, *args, **kwargs):
        self.calls += 1

    polygon = _record
    line = _record
    ellipse = _record
    rect = _record
    circle = _record


class SailRenderingSmokeTests(unittest.TestCase):
    def test_all_ship_rigs_render_across_deployment_levels(self):
        fake_pygame = types.SimpleNamespace(Rect=FakeRect, draw=FakeDraw())
        with patch.dict(sys.modules, {"pygame": fake_pygame}):
            import importlib
            renderer = importlib.import_module("tidebound.sail_rendering")
            fake_surface = object()
            for ship_type, stats in SHIP_CLASSES.items():
                positions = [20 + stats["length"] * position for position in stats["masts"]]
                for deployment in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0):
                    for pattern in ("plain", "stripes", "panels", "sunburst", "checks", "corsair"):
                        for sail_type in ("Standard Canvas", "Fine-weave Canvas", "Heavy Weather Canvas", "Racing Cut", "Lateen Cut"):
                            renderer.draw_ship_sails(
                                fake_surface,
                                stats,
                                positions,
                                60,
                                stats["beam"] / 2,
                                stats["rig"],
                                (224, 214, 181),
                                pattern,
                                sail_type,
                                True,
                                deployment,
                                deployment * 2.0,
                            )
        self.assertGreater(fake_pygame.draw.calls, 1000)


if __name__ == "__main__":
    unittest.main()
