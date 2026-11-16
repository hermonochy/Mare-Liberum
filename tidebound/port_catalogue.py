SHIPYARD_CATEGORIES = (
    ("All Ships", None),
    ("Couriers & Scouts", ("Launch", "Cutter", "Yawl")),
    ("Light Warships", ("Sloop", "Xebec")),
    ("Medium Warships", ("Brigantine", "Brig", "Corvette")),
    ("Large Warships", ("Frigate", "Galleon")),
    ("Battleships", ("Ship of the Line",)),
    ("Merchantmen", ("Schooner", "Barque", "Merchantman", "Carrack", "East Indiaman")),
)

OUTFITTER_CATEGORIES = (
    ("All Fittings", None),
    ("Hull", ("hull", "hull_form", "hull_finish")),
    ("Weapons", ("cannons", "cannon_type", "cannon_mount")),
    ("Sails", ("rigging", "sail_design", "sail_type")),
    ("Crew & Oars", ("rowers",)),
    ("Cargo & Handling", ("cargo", "rudder")),
    ("Flags & Colours", ("flag_design",)),
    ("Deck Appearance", ("visual_upgrade",)),
)

SHIPYARD_CATEGORY_BY_CLASS = {
    ship_type: category
    for category, ship_types in SHIPYARD_CATEGORIES
    if ship_types is not None
    for ship_type in ship_types
}

OUTFITTER_CATEGORY_BY_FITTING = {
    fitting_key: category
    for category, fitting_keys in OUTFITTER_CATEGORIES
    if fitting_keys is not None
    for fitting_key in fitting_keys
}


def shipyard_category_for(ship_type):
    return SHIPYARD_CATEGORY_BY_CLASS.get(ship_type, "Other")


def outfitter_category_for(fitting_key):
    return OUTFITTER_CATEGORY_BY_FITTING.get(fitting_key, "Other")


def filter_ship_types(ship_types, category):
    if category == "All Ships":
        return list(ship_types)
    return [ship_type for ship_type in ship_types if shipyard_category_for(ship_type) == category]


def filter_outfitter_items(items, category):
    if category == "All Fittings":
        return list(items)
    return [item for item in items if item.get("group") == category]
