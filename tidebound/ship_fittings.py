DEFAULT_SHIP_CUSTOMISATION = {
    "hull_form": "Balanced Keel",
    "hull_finish": "Use Ship Livery",
    "sail_design": "Natural Canvas",
    "sail_type": "Standard Canvas",
    "flag_design": "Captain's Pennant",
    "cannon_type": "Standard Culverins",
    "cannon_mount": "Broadside Batteries",
    "visual_upgrade": "Plain Finish",
}

HULL_FORMS = {
    "Balanced Keel": {"price": 0, "hull": 1.0, "speed": 1.0, "turn": 1.0, "cargo": 1.0, "profile": "balanced", "length": 1.0, "beam": 1.0, "detail": "A dependable all-round hull with no penalty to handling or carrying capacity."},
    "Racing Keel": {"price": 1650, "hull": 0.94, "speed": 1.08, "turn": 1.08, "cargo": 0.94, "profile": "fine", "length": 1.04, "beam": 0.91, "detail": "Fine underwater lines improve speed and turning, at the cost of some strength and hold volume."},
    "Armoured Keel": {"price": 2350, "hull": 1.18, "speed": 0.93, "turn": 0.92, "cargo": 0.97, "profile": "armoured", "length": 0.99, "beam": 1.06, "detail": "Extra framing and heavier planking improve durability but add weight."},
    "Merchant's Hull": {"price": 1850, "hull": 1.08, "speed": 0.94, "turn": 0.89, "cargo": 1.17, "profile": "broad", "length": 0.98, "beam": 1.15, "detail": "A fuller belly carries more cargo and stores, but responds more slowly."},
    "Shallow-draught Hull": {"price": 1450, "hull": 0.96, "speed": 1.03, "turn": 1.12, "cargo": 0.94, "profile": "shallow", "length": 1.02, "beam": 0.90, "detail": "A lighter, shallower hull is nimble in coastal waters but less forgiving in a fight."},
}

HULL_FINISHES = {
    "Use Ship Livery": {"price": 0, "hull": None, "trim": None},
    "Weathered Oak": {"price": 350, "hull": (105, 66, 41), "trim": (204, 155, 89)},
    "Tarred Black": {"price": 650, "hull": (38, 35, 33), "trim": (176, 145, 104)},
    "Royal Blue": {"price": 850, "hull": (39, 67, 96), "trim": (211, 183, 125)},
    "Spanish Red": {"price": 850, "hull": (116, 42, 36), "trim": (218, 177, 112)},
    "Emerald Green": {"price": 850, "hull": (40, 82, 61), "trim": (204, 174, 104)},
    "Ivory and Gold": {"price": 1250, "hull": (188, 171, 132), "trim": (234, 204, 137)},
    "Copper Sheathing": {"price": 1500, "hull": (91, 99, 78), "trim": (184, 133, 83)},
}

SAIL_DESIGNS = {
    "Natural Canvas": {"price": 0, "primary": (224, 214, 181), "secondary": (181, 166, 129), "pattern": "plain"},
    "Red Racing Stripes": {"price": 700, "primary": (230, 216, 188), "secondary": (164, 55, 43), "pattern": "stripes"},
    "Royal Blue Stripes": {"price": 850, "primary": (224, 224, 206), "secondary": (52, 88, 132), "pattern": "stripes"},
    "Black Panelled": {"price": 950, "primary": (186, 181, 162), "secondary": (39, 39, 39), "pattern": "panels"},
    "Golden Sunburst": {"price": 1250, "primary": (235, 224, 193), "secondary": (181, 127, 49), "pattern": "sunburst"},
    "Corsair Mark": {"price": 1450, "primary": (219, 213, 188), "secondary": (37, 34, 31), "pattern": "corsair"},
    "Black Jolly Roger Canvas": {"price": 1850, "primary": (39, 37, 35), "secondary": (229, 220, 190), "pattern": "corsair"},
    "Emerald Checks": {"price": 1050, "primary": (224, 218, 187), "secondary": (66, 112, 78), "pattern": "checks"},
}

SAIL_TYPES = {
    "Standard Canvas": {"price": 0, "speed": 1.0, "force": 1.0, "turn": 1.0, "detail": "Reliable everyday canvas with balanced speed and handling."},
    "Fine-weave Canvas": {"price": 1850, "speed": 1.055, "force": 1.10, "turn": 1.0, "detail": "Lighter, closely woven cloth catches the wind well and improves acceleration."},
    "Heavy Weather Canvas": {"price": 1450, "speed": 0.965, "force": 0.97, "turn": 0.99, "detail": "Heavy canvas is dependable in rough weather, though it adds weight aloft."},
    "Racing Cut": {"price": 2450, "speed": 1.10, "force": 1.12, "turn": 1.035, "detail": "A lighter racing cut improves top speed and response, but is expensive to maintain."},
    "Lateen Cut": {"price": 2050, "speed": 1.035, "force": 1.04, "turn": 1.10, "detail": "A more responsive cut favours manoeuvrability and ships that work close to the wind."},
}

FLAG_DESIGNS = {
    "Captain's Pennant": {"price": 0, "field": (34, 31, 29), "symbol": (224, 215, 185), "mark": "skull"},
    "Black Jolly Roger": {"price": 700, "field": (27, 27, 27), "symbol": (235, 226, 196), "mark": "crossbones"},
    "Red Privateer": {"price": 650, "field": (145, 42, 34), "symbol": (238, 218, 178), "mark": "star"},
    "Royal Ensign": {"price": 950, "field": (48, 78, 127), "symbol": (234, 223, 186), "mark": "cross"},
    "Merchant Pennant": {"price": 700, "field": (180, 143, 65), "symbol": (55, 48, 34), "mark": "stripe"},
    "Emerald Pennant": {"price": 750, "field": (44, 101, 69), "symbol": (235, 217, 167), "mark": "diamond"},
    "Ivory Pennant": {"price": 1050, "field": (221, 211, 183), "symbol": (91, 59, 37), "mark": "anchor"},
    "No Flag": {"price": 150, "field": (0, 0, 0), "symbol": (0, 0, 0), "mark": "none"},
}

CANNON_TYPES = {
    "Standard Culverins": {"price": 0, "damage": 1, "speed": 480.0, "life": 1.45, "reload": 1.0, "detail": "Balanced range, impact and reload time."},
    "Long Nines": {"price": 2350, "damage": 1, "speed": 610.0, "life": 1.82, "reload": 1.13, "detail": "Long-barrelled guns carry farther and strike at range, but reload more slowly."},
    "Demi-cannons": {"price": 2850, "damage": 2, "speed": 440.0, "life": 1.42, "reload": 1.24, "detail": "Heavy guns inflict greater damage at the cost of slower firing and shorter reach."},
    "Carronades": {"price": 2550, "damage": 2, "speed": 390.0, "life": 0.95, "reload": 0.90, "detail": "Short-barrelled carronades devastate targets at close range and reload quickly."},
    "Swivel Guns": {"price": 1650, "damage": 1, "speed": 520.0, "life": 0.88, "reload": 0.58, "detail": "Light swivel guns fire rapidly at close range but have little reach."},
}

CANNON_MOUNTS = {
    "Broadside Batteries": {"price": 0, "mode": "broadside", "detail": "Traditional port and starboard batteries. Fire with Z and X."},
    "Bow & Stern Chasers": {"price": 1950, "mode": "chasers", "detail": "One gun is reassigned to each end of the ship. Fire forward with Q and aft with E."},
    "Rotating Turrets": {"price": 4250, "mode": "turrets", "detail": "Deck turrets rotate to track nearby hostile vessels. Fire with Z or X to engage the nearest target."},
}

VISUAL_UPGRADES = {
    "Plain Finish": {"price": 0, "style": "plain", "detail": "A clean, practical finish without extra ornament."},
    "Carved Figurehead": {"price": 1250, "style": "figurehead", "detail": "A carved bow figurehead with gilded highlights."},
    "Gilded Rails": {"price": 1850, "style": "gilded", "detail": "Decorative gilded rails and deck fittings."},
    "Stern Gallery": {"price": 1650, "style": "gallery", "detail": "A raised stern gallery with bright windows and trim."},
    "Lanterns and Brass": {"price": 1100, "style": "lanterns", "detail": "Brass lanterns and polished fittings along the deck."},
    "Armoured Bulwarks": {"price": 2150, "style": "bulwarks", "detail": "Raised reinforced bulwarks, adding a little durability but some weight."},
}

CUSTOMISATION_CATEGORIES = (
    ("hull_form", "Hull Form", HULL_FORMS),
    ("hull_finish", "Hull Finish", HULL_FINISHES),
    ("sail_design", "Sail Design", SAIL_DESIGNS),
    ("sail_type", "Sail Type", SAIL_TYPES),
    ("flag_design", "Flag Design", FLAG_DESIGNS),
    ("cannon_type", "Cannon Type", CANNON_TYPES),
    ("cannon_mount", "Cannon Mounting", CANNON_MOUNTS),
    ("visual_upgrade", "Visual Upgrade", VISUAL_UPGRADES),
)


def default_ship_customisation():
    return dict(DEFAULT_SHIP_CUSTOMISATION)


def normalise_ship_customisation(value=None):
    result = default_ship_customisation()
    if isinstance(value, dict):
        for key, _, options in CUSTOMISATION_CATEGORIES:
            selected = value.get(key)
            if selected in options:
                result[key] = selected
    return result


def ship_customisation_option(customisation, category):
    key = category
    selected = normalise_ship_customisation(customisation).get(key)
    catalogues = {name: options for name, _, options in CUSTOMISATION_CATEGORIES}
    return catalogues[key][selected]


def ship_customisation_price(category, option):
    catalogues = {name: options for name, _, options in CUSTOMISATION_CATEGORIES}
    return int(catalogues[category][option]["price"])



def ship_fitting_available(ship_type, category, option):
    from .config import SHIP_CLASSES

    stats = SHIP_CLASSES.get(ship_type)
    catalogues = {key: options for key, _, options in CUSTOMISATION_CATEGORIES}
    if stats is None or category not in catalogues or option not in catalogues[category]:
        return False
    if category == "cannon_mount":
        mode = CANNON_MOUNTS[option]["mode"]
        cannon_limit = int(stats["max_cannons"])
        if mode == "chasers" and cannon_limit < 8:
            return False
        if mode == "turrets" and cannon_limit < 16:
            return False
    return True

def ship_customisation_effects(customisation):
    selection = normalise_ship_customisation(customisation)
    hull = HULL_FORMS[selection["hull_form"]]
    sails = SAIL_TYPES[selection["sail_type"]]
    visual = VISUAL_UPGRADES[selection["visual_upgrade"]]
    return {
        "hull": hull["hull"] * (1.035 if visual["style"] == "bulwarks" else 1.0),
        "speed": hull["speed"] * sails["speed"] * (0.985 if visual["style"] in {"gilded", "gallery"} else 1.0),
        "turn": hull["turn"] * sails["turn"],
        "cargo": hull["cargo"],
        "length": hull["length"],
        "beam": hull["beam"],
        "profile": hull["profile"],
        "sail_force": sails["force"],
    }
