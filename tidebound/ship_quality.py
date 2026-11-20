NPC_TO_PLAYER_DAMAGE_SCALE = 11.0

QUALITY_LIMITS = {
    "weapons": (0.88, 1.14),
    "powder": (0.90, 1.12),
    "crew": (0.88, 1.14),
    "aim": (0.86, 1.14),
    "hull": (0.92, 1.10),
    "maintenance": (0.89, 1.12),
}


def default_ship_quality():
    return {key: 1.0 for key in QUALITY_LIMITS}


def normalise_ship_quality(value=None):
    source = value if isinstance(value, dict) else {}
    result = {}
    for key, (low, high) in QUALITY_LIMITS.items():
        try:
            number = float(source.get(key, 1.0))
        except (TypeError, ValueError):
            number = 1.0
        if not math_is_finite(number):
            number = 1.0
        result[key] = min(high, max(low, number))
    return result


def roll_ship_quality(rng):
    quality = {}
    spreads = {
        "weapons": 0.055,
        "powder": 0.035,
        "crew": 0.055,
        "aim": 0.065,
        "hull": 0.035,
        "maintenance": 0.05,
    }
    for key, (low, high) in QUALITY_LIMITS.items():
        quality[key] = min(high, max(low, rng.gauss(1.0, spreads[key])))
    return quality


def math_is_finite(value):
    return value == value and value not in (float("inf"), float("-inf"))


def ship_damage_quality(quality):
    values = normalise_ship_quality(quality)
    return min(1.20, max(0.82, values["weapons"] * values["powder"]))


def ship_reload_quality(quality):
    values = normalise_ship_quality(quality)
    return min(1.24, max(0.80, 1.0 / (values["crew"] * values["maintenance"])))


def ship_aim_quality(quality):
    values = normalise_ship_quality(quality)
    return min(1.16, max(0.84, values["aim"]))


def ship_hull_quality(quality):
    return normalise_ship_quality(quality)["hull"]


def roll_npc_cannon_type(rng, ship_type, faction="pirate"):
    small_hulls = {"Launch", "Cutter", "Sloop", "Yawl", "Xebec", "Schooner", "Brigantine"}
    if faction in {"naval patrol", "navy", "British Crown", "Spanish Crown", "French Crown"}:
        choices = (("Standard Culverins", 25), ("Long Nines", 30), ("Demi-cannons", 25), ("Carronades", 16), ("Swivel Guns", 4))
    elif faction in {"merchant", "Merchant League", "Independent", "mail packet", "whaler", "fishing"}:
        choices = (("Standard Culverins", 45), ("Long Nines", 12), ("Demi-cannons", 8), ("Carronades", 15), ("Swivel Guns", 20))
    elif ship_type in small_hulls:
        choices = (("Standard Culverins", 30), ("Long Nines", 8), ("Demi-cannons", 8), ("Carronades", 32), ("Swivel Guns", 22))
    else:
        choices = (("Standard Culverins", 30), ("Long Nines", 22), ("Demi-cannons", 22), ("Carronades", 20), ("Swivel Guns", 6))
    return rng.choices([name for name, _ in choices], weights=[weight for _, weight in choices], k=1)[0]


def ship_quality_description(quality):
    values = normalise_ship_quality(quality)
    mean = sum(values.values()) / len(values)
    if mean >= 1.075:
        return "Exceptional"
    if mean >= 1.025:
        return "Well-kept"
    if mean >= 0.975:
        return "Serviceable"
    if mean >= 0.925:
        return "Worn"
    return "Poorly maintained"
