from .ship_fittings import CANNON_TYPES
from .ships import SHIP_CLASSES, max_broadside_guns


def cannon_pair_capacity(ship_type, cannon_upgrade=0):
    stats = SHIP_CLASSES.get(ship_type, SHIP_CLASSES["Sloop"])
    fitted = int(stats.get("guns", 1)) + max(0, int(cannon_upgrade))
    return min(max_broadside_guns(ship_type), max(1, fitted))


def default_cannon_loadout(ship_type, cannon_type="Standard Culverins", cannon_upgrade=0):
    selected = cannon_type if cannon_type in CANNON_TYPES else "Standard Culverins"
    return {selected: cannon_pair_capacity(ship_type, cannon_upgrade)}


def normalise_cannon_loadout(value, ship_type, default_type="Standard Culverins", cannon_upgrade=0):
    capacity = cannon_pair_capacity(ship_type, cannon_upgrade)
    fallback = default_type if default_type in CANNON_TYPES else "Standard Culverins"
    if not isinstance(value, dict):
        return default_cannon_loadout(ship_type, fallback, cannon_upgrade)
    result = {}
    remaining = capacity
    for cannon_type in CANNON_TYPES:
        try:
            count = max(0, int(value.get(cannon_type, 0)))
        except (TypeError, ValueError):
            count = 0
        count = min(count, remaining)
        if count:
            result[cannon_type] = count
            remaining -= count
    if remaining:
        result[fallback] = result.get(fallback, 0) + remaining
    return result


def cannon_loadout_sequence(loadout, ship_type, default_type="Standard Culverins", cannon_upgrade=0):
    selected = normalise_cannon_loadout(loadout, ship_type, default_type, cannon_upgrade)
    return [cannon_type for cannon_type in CANNON_TYPES for _ in range(selected.get(cannon_type, 0))]


def cannon_type_for_gun(loadout, ship_type, gun_index, default_type="Standard Culverins", cannon_upgrade=0):
    sequence = cannon_loadout_sequence(loadout, ship_type, default_type, cannon_upgrade)
    if not sequence:
        return default_type if default_type in CANNON_TYPES else "Standard Culverins"
    return sequence[max(0, min(len(sequence) - 1, int(gun_index)))]


def cannon_replacement_type(loadout, requested_type):
    if requested_type not in CANNON_TYPES:
        return None
    fitted = {name: max(0, int(count)) for name, count in (loadout or {}).items() if name in CANNON_TYPES and int(count) > 0}
    if sum(fitted.values()) <= 0 or fitted.get(requested_type, 0) >= sum(fitted.values()):
        return None
    if requested_type != "Standard Culverins" and fitted.get("Standard Culverins", 0) > 0:
        return "Standard Culverins"
    alternatives = [(count, name) for name, count in fitted.items() if name != requested_type]
    if not alternatives:
        return None
    return max(alternatives)[1]
