import math
import random
import sys

import pygame

from .config import *
from .ships import generate_ship_name, max_broadside_guns, ship_upgrade_limit
from .ship_fittings import (
    CANNON_MOUNTS, CANNON_TYPES, CUSTOMISATION_CATEGORIES, DEFAULT_SHIP_CUSTOMISATION,
    FLAG_DESIGNS, HULL_FINISHES, HULL_FORMS, SAIL_DESIGNS, SAIL_TYPES, VISUAL_UPGRADES,
    default_ship_customisation, normalise_ship_customisation, ship_customisation_effects,
    ship_customisation_price, ship_fitting_available,
)
from .geometry import *
from .models import *
from .mission_system import ChoiceNode, CommandNode, GotoNode, LabelNode, TextNode, OptionNode, load_missions
from .mission_events import load_mission_events
from .dialogue import Conversation


def fit_text_surface(font, value, color, max_width, max_height):
    """Render a single-line label scaled down just enough to stay in its UI area."""
    rendered = font.render(str(value), True, color)
    max_width = max(1, int(max_width))
    max_height = max(1, int(max_height))
    if rendered.get_width() <= max_width and rendered.get_height() <= max_height:
        return rendered
    ratio = min(max_width / max(1, rendered.get_width()), max_height / max(1, rendered.get_height()), 1.0)
    size = (max(1, int(rendered.get_width() * ratio)), max(1, int(rendered.get_height() * ratio)))
    return pygame.transform.smoothscale(rendered, size)
