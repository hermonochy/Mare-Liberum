import math

import pygame

from .config import SHIP_CLASSES, SHIP_LIVERIES
from .sail_rendering import draw_ship_sails
from .ship_fittings import (
    CANNON_MOUNTS,
    FLAG_DESIGNS,
    HULL_FINISHES,
    HULL_FORMS,
    SAIL_DESIGNS,
    VISUAL_UPGRADES,
    normalise_ship_customisation,
    ship_customisation_effects,
)


def _points(points):
    return tuple((int(x), int(y)) for x, y in points)


def _polygon(surface, color, points, width=0):
    pygame.draw.polygon(surface, color, _points(points), width)


def _line(surface, color, start, end, width=1):
    pygame.draw.line(surface, color, (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), max(1, int(width)))


def _blend(first, second, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a + (b - a) * amount) for a, b in zip(first, second))


def _hull_profile(base, profile):
    bow, fore, middle, aft, stern = base
    if profile == "fine":
        return bow * 0.94, fore * 0.94, middle * 0.91, aft * 0.94, stern * 0.92
    if profile == "armoured":
        return bow * 1.04, fore * 1.06, middle * 1.08, aft * 1.06, stern * 1.04
    if profile == "broad":
        return bow * 1.08, fore * 1.12, middle * 1.15, aft * 1.12, stern * 1.08
    if profile == "shallow":
        return bow * 0.91, fore * 0.93, middle * 0.94, aft * 0.93, stern * 0.91
    return base



def _draw_flag(surface, mast_x, flag_y, faction, flag_design):
    design = FLAG_DESIGNS.get(flag_design)
    if design:
        field = design["field"]
        symbol = design["symbol"]
        mark = design["mark"]
    else:
        field = (24, 22, 20) if faction == "pirate" else (225, 218, 183) if faction == "allied" else (53, 87, 126) if faction == "naval patrol" else (173, 139, 74) if faction == "merchant" else (100, 123, 91) if faction == "fishing" else (158, 62, 49) if faction == "mail packet" else (100, 100, 91)
        symbol = (235, 226, 196)
        mark = "none"
    if mark == "none":
        return
    _line(surface, (48, 34, 24), (mast_x, flag_y + 4), (mast_x, flag_y - 8), 1)
    flag = [(mast_x, flag_y - 8), (mast_x + 17, flag_y - 5), (mast_x + 14, flag_y + 1), (mast_x, flag_y - 1)]
    _polygon(surface, field, flag)
    _polygon(surface, _blend(field, (255, 247, 222), 0.24), flag, 1)
    center = (mast_x + 7, flag_y - 3)
    if mark in {"skull", "crossbones"}:
        pygame.draw.circle(surface, symbol, center, 2)
        _line(surface, symbol, (center[0] - 3, center[1] + 4), (center[0] + 3, center[1] + 4), 1)
        if mark == "crossbones":
            _line(surface, symbol, (center[0] - 4, center[1] - 1), (center[0] + 4, center[1] + 5), 1)
            _line(surface, symbol, (center[0] + 4, center[1] - 1), (center[0] - 4, center[1] + 5), 1)
    elif mark == "star":
        pygame.draw.circle(surface, symbol, center, 2)
    elif mark == "cross":
        _line(surface, symbol, (center[0] - 3, center[1]), (center[0] + 3, center[1]), 2)
        _line(surface, symbol, (center[0], center[1] - 3), (center[0], center[1] + 3), 2)
    elif mark == "stripe":
        _line(surface, symbol, (mast_x + 2, flag_y - 4), (mast_x + 12, flag_y - 4), 2)
    elif mark == "diamond":
        _polygon(surface, symbol, [(center[0], center[1] - 4), (center[0] + 3, center[1]), (center[0], center[1] + 4), (center[0] - 3, center[1])])
    elif mark == "anchor":
        _line(surface, symbol, (center[0], center[1] - 4), (center[0], center[1] + 4), 1)
        _line(surface, symbol, (center[0] - 3, center[1] + 1), (center[0] + 3, center[1] + 1), 1)
        pygame.draw.arc(surface, symbol, (center[0] - 4, center[1] + 1, 8, 6), math.pi, math.tau, 1)


def _draw_visual_fittings(surface, style, start_x, end_x, center_y, beam, trim_color):
    if style == "figurehead":
        point = (end_x + 8, center_y)
        _polygon(surface, (189, 146, 78), [(end_x - 2, center_y - 5), (end_x + 10, center_y), (end_x - 2, center_y + 5)])
        pygame.draw.circle(surface, (235, 211, 157), point, max(2, int(beam * 0.045)))
    elif style == "gilded":
        _line(surface, (228, 190, 109), (start_x + 8, center_y - beam * 0.28), (end_x - 2, center_y - beam * 0.28), 2)
        _line(surface, (228, 190, 109), (start_x + 8, center_y + beam * 0.28), (end_x - 2, center_y + beam * 0.28), 2)
        for x in (start_x + beam * 0.34, end_x - beam * 0.34):
            pygame.draw.circle(surface, trim_color, (int(x), int(center_y)), max(2, int(beam * 0.045)))
    elif style == "gallery":
        gallery = pygame.Rect(int(start_x + 4), int(center_y - beam * 0.30), max(12, int(beam * 0.58)), max(9, int(beam * 0.60)))
        pygame.draw.rect(surface, (73, 47, 32), gallery, border_radius=3)
        pygame.draw.rect(surface, trim_color, gallery, 2, border_radius=3)
        for index in range(3):
            window_x = gallery.x + 4 + index * max(3, gallery.width // 4)
            pygame.draw.circle(surface, (229, 194, 126), (window_x, gallery.centery), 1)
    elif style == "lanterns":
        for x in (start_x + beam * 0.52, end_x - beam * 0.42):
            pygame.draw.circle(surface, (242, 199, 105), (int(x), int(center_y - beam * 0.23)), max(2, int(beam * 0.035)))
            pygame.draw.circle(surface, (242, 199, 105), (int(x), int(center_y + beam * 0.23)), max(2, int(beam * 0.035)))
    elif style == "bulwarks":
        _line(surface, (95, 73, 53), (start_x + 10, center_y - beam * 0.39), (end_x - 8, center_y - beam * 0.39), max(2, int(beam * 0.045)))
        _line(surface, (95, 73, 53), (start_x + 10, center_y + beam * 0.39), (end_x - 8, center_y + beam * 0.39), max(2, int(beam * 0.045)))


def build_ship_surface(player, allied, rowing, ship_type, faction, player_livery, world_time, customisation=None):
    stats = SHIP_CLASSES.get(ship_type, SHIP_CLASSES["Sloop"])
    selected = normalise_ship_customisation(customisation) if player or allied else None
    effects = ship_customisation_effects(selected) if selected else None
    length = int(stats["length"] * effects["length"]) if effects else int(stats["length"])
    beam = int(stats["beam"] * effects["beam"]) if effects else int(stats["beam"])
    canvas_width = length + 46
    canvas_height = max(82, beam + 44)
    center_y = canvas_height // 2
    start_x = 20
    end_x = start_x + length
    surface = pygame.Surface((canvas_width, canvas_height), pygame.SRCALPHA)

    if player:
        livery = SHIP_LIVERIES[max(0, min(len(SHIP_LIVERIES) - 1, int(player_livery)))]
        hull_color, trim_color, sail_color = livery[1], livery[2], livery[3]
    elif allied:
        hull_color, trim_color, sail_color = (42, 80, 69), (179, 190, 135), (191, 220, 202)
    elif faction == "merchant":
        hull_color, trim_color, sail_color = (126, 83, 43), (218, 180, 112), (222, 211, 176)
    elif faction == "fishing":
        hull_color, trim_color, sail_color = (67, 91, 72), (190, 172, 119), (202, 191, 153)
    elif faction == "naval patrol":
        hull_color, trim_color, sail_color = (39, 60, 86), (206, 194, 151), (224, 224, 209)
    elif faction == "mail packet":
        hull_color, trim_color, sail_color = (107, 64, 54), (218, 190, 143), (220, 222, 200)
    elif faction == "whaler":
        hull_color, trim_color, sail_color = (73, 73, 61), (180, 161, 123), (170, 181, 169)
    else:
        hull_color, trim_color, sail_color = (69, 39, 34), (165, 92, 65), (201, 188, 158)

    sail_pattern = "plain"
    flag_design = None
    visual_style = "plain"
    hull_profile_style = "balanced"
    if selected:
        hull_finish = HULL_FINISHES[selected["hull_finish"]]
        if hull_finish["hull"] is not None:
            hull_color = hull_finish["hull"]
            trim_color = hull_finish["trim"]
        sail_design = SAIL_DESIGNS[selected["sail_design"]]
        sail_color = sail_design["primary"]
        sail_pattern = sail_design["pattern"]
        flag_design = selected["flag_design"]
        visual_style = VISUAL_UPGRADES[selected["visual_upgrade"]]["style"]
        hull_profile_style = HULL_FORMS[selected["hull_form"]]["profile"]
    else:
        flag_design = None

    half_beam = beam / 2.0
    profile = _hull_profile(stats["hull_profile"], hull_profile_style)
    bow_shoulder, fore_beam, mid_beam, aft_beam, stern_shoulder = profile
    hull = [
        (start_x + length * 0.035, center_y),
        (start_x + length * 0.10, center_y - half_beam * bow_shoulder),
        (start_x + length * 0.27, center_y - half_beam * fore_beam),
        (start_x + length * 0.57, center_y - half_beam * mid_beam),
        (start_x + length * 0.84, center_y - half_beam * aft_beam),
        (start_x + length * 0.96, center_y - half_beam * stern_shoulder),
        (end_x + 7, center_y),
        (start_x + length * 0.96, center_y + half_beam * stern_shoulder),
        (start_x + length * 0.84, center_y + half_beam * aft_beam),
        (start_x + length * 0.57, center_y + half_beam * mid_beam),
        (start_x + length * 0.27, center_y + half_beam * fore_beam),
        (start_x + length * 0.10, center_y + half_beam * bow_shoulder),
    ]
    hull_shadow = [(x + 1, y + 4) for x, y in hull]
    center_x = sum(x for x, _ in hull) / len(hull)
    center_y_hull = sum(y for _, y in hull) / len(hull)
    hull_inset = [(center_x + (x - center_x) * 0.91, center_y_hull + (y - center_y_hull) * 0.84) for x, y in hull]
    deck = [(center_x + (x - center_x) * 0.82, center_y_hull + (y - center_y_hull) * 0.70) for x, y in hull]
    _polygon(surface, (24, 20, 18), hull_shadow)
    _polygon(surface, (42, 29, 23), hull)
    _polygon(surface, hull_color, hull_inset)
    _polygon(surface, (139, 99, 61), deck)
    pygame.draw.lines(surface, trim_color, True, _points(hull_inset), max(2, int(beam * 0.045)))

    deck_top = center_y - half_beam * 0.34
    deck_bottom = center_y + half_beam * 0.34
    plank_start = int(start_x + length * 0.22)
    plank_end = int(start_x + length * 0.86)
    plank_step = max(8, int(length / 17))
    for plank_x in range(plank_start, plank_end, plank_step):
        _line(surface, (157, 116, 72), (plank_x, deck_top + 3), (plank_x + 3, deck_bottom - 3), 1)
    _line(surface, (78, 53, 34), (start_x + length * 0.15, center_y), (end_x - length * 0.09, center_y), 2)

    rig = stats["rig"]
    castle_rigs = {"galleon", "carrack", "indiaman"}
    cabin_x = int(start_x + length * (0.12 if rig in castle_rigs else 0.14))
    cabin_w = max(15, int(length * (0.18 if rig not in castle_rigs else 0.22)))
    cabin_h = max(10, int(beam * (0.30 if rig not in castle_rigs else 0.39)))
    cabin_rect = pygame.Rect(cabin_x, int(center_y - cabin_h / 2), cabin_w, cabin_h)
    pygame.draw.rect(surface, (70, 46, 32), cabin_rect, border_radius=max(2, cabin_h // 5))
    pygame.draw.rect(surface, trim_color, cabin_rect, max(1, int(beam * 0.025)), border_radius=max(2, cabin_h // 5))
    _line(surface, (222, 185, 125), (cabin_rect.left + 4, cabin_rect.top + 3), (cabin_rect.right - 4, cabin_rect.top + 3), 1)
    for window_index in range(3 if cabin_w > 25 else 2):
        window_x = cabin_rect.left + int((window_index + 1) * cabin_w / (4 if cabin_w > 25 else 3))
        pygame.draw.circle(surface, (228, 190, 117), (window_x, cabin_rect.centery), max(1, int(beam * 0.025)))

    if rig in castle_rigs:
        castle_width = max(17, int(length * 0.12))
        castle_height = max(12, int(beam * 0.53))
        castle = pygame.Rect(int(start_x + length * 0.055), int(center_y - castle_height / 2), castle_width, castle_height)
        pygame.draw.rect(surface, (94, 60, 39), castle, border_radius=3)
        pygame.draw.rect(surface, trim_color, castle, 2, border_radius=3)
    if rig == "ship_of_line":
        quarterdeck = pygame.Rect(int(start_x + length * 0.08), int(center_y - beam * 0.31), int(length * 0.21), int(beam * 0.62))
        pygame.draw.rect(surface, (82, 54, 36), quarterdeck, border_radius=3)
        pygame.draw.rect(surface, trim_color, quarterdeck, 2, border_radius=3)
        for gun_deck_y in (center_y - beam * 0.29, center_y + beam * 0.29):
            _line(surface, (229, 197, 143), (start_x + length * 0.24, gun_deck_y), (end_x - length * 0.10, gun_deck_y), 1)

    mast_positions = [start_x + int(length * position) for position in stats["masts"]]
    sail_type = selected["sail_type"] if selected else "Standard Canvas"
    flag_mark = FLAG_DESIGNS.get(flag_design, {}).get("mark")
    pirate_mark = faction == "pirate" or flag_mark in {"skull", "crossbones"} or sail_pattern == "corsair"
    draw_ship_sails(surface, stats, mast_positions, center_y, half_beam, rig, sail_color, sail_pattern, sail_type, pirate_mark)
    for mast_x in mast_positions:
        pygame.draw.circle(surface, (48, 33, 24), (mast_x, center_y), max(3, int(beam * 0.075)))
        pygame.draw.circle(surface, (192, 160, 111), (mast_x, center_y), max(1, int(beam * 0.035)))

    if mast_positions:
        _line(surface, (84, 58, 37), (mast_positions[0], center_y), (end_x + 13, center_y), 2)
        _line(surface, (84, 58, 37), (start_x + 5, center_y), (mast_positions[-1], center_y), 1)
        for mast_x in mast_positions:
            _line(surface, (142, 111, 75), (mast_x, center_y - half_beam * 0.31), (mast_positions[-1], center_y), 1)

    mount_mode = CANNON_MOUNTS[selected["cannon_mount"]]["mode"] if selected else "broadside"
    cannon_type = selected["cannon_type"] if selected else "Standard Culverins"
    cannon_detail = {
        "Standard Culverins": (48, 39, 29),
        "Long Nines": (91, 93, 96),
        "Demi-cannons": (41, 37, 34),
        "Carronades": (107, 76, 49),
        "Swivel Guns": (180, 151, 92),
    }
    cannon_color = cannon_detail[cannon_type]
    if mount_mode == "turrets":
        turret_count = max(2, min(5, int(stats["max_cannons"]) // 6))
        for index in range(turret_count):
            ratio = 0.20 + (0.61 * index / max(1, turret_count - 1))
            turret_x = int(start_x + length * ratio)
            turret_radius = max(3, int(beam * 0.075))
            pygame.draw.circle(surface, (31, 28, 25), (turret_x, center_y), turret_radius + 2)
            pygame.draw.circle(surface, (176, 142, 92), (turret_x, center_y), turret_radius)
            _line(surface, cannon_color, (turret_x, center_y), (turret_x + turret_radius * 2, center_y), max(2, turret_radius // 2))
    else:
        gun_count = max(1, int(stats["guns"]))
        gun_start = start_x + length * 0.25
        gun_end = end_x - length * 0.15
        if mount_mode == "chasers":
            gun_count = max(1, gun_count - 1)
        for index in range(gun_count):
            ratio = index / max(1, gun_count - 1)
            gun_x = int(gun_start + (gun_end - gun_start) * ratio)
            for side in (-1, 1):
                gun_y = int(center_y + side * half_beam * 0.39)
                pygame.draw.circle(surface, cannon_color, (gun_x, gun_y), max(2, int(beam * 0.052)))
                pygame.draw.circle(surface, (194, 153, 99), (gun_x, gun_y), max(1, int(beam * 0.026)), 1)
        if mount_mode == "chasers":
            for gun_x, direction in ((end_x + 1, 1), (start_x + 2, -1)):
                pygame.draw.circle(surface, (37, 30, 25), (gun_x, center_y), max(3, int(beam * 0.065)))
                _line(surface, cannon_color, (gun_x, center_y), (gun_x + direction * max(7, int(beam * 0.24)), center_y), 3)

    _draw_visual_fittings(surface, visual_style, start_x, end_x, center_y, beam, trim_color)
    flag_x = mast_positions[0] if mast_positions else start_x + length * 0.5
    _draw_flag(surface, int(flag_x), int(center_y - half_beam * 0.54), faction, flag_design)

    if rowing and stats["oar_power"] > 0 and stats["rowers"] >= 8:
        stroke = math.sin(world_time * 8.0) * 3.5
        oar_count = max(4, min(12, int(stats["rowers"] / 3)))
        for index in range(oar_count):
            ratio = index / max(1, oar_count - 1)
            oar_x = int(start_x + length * (0.27 + ratio * 0.52))
            for side in (-1, 1):
                root = (oar_x, int(center_y + side * half_beam * 0.36))
                tip = (int(oar_x + stroke), int(center_y + side * (half_beam + 12)))
                _line(surface, (91, 58, 34), root, tip, 2)
                pygame.draw.ellipse(surface, (156, 116, 68), (tip[0] - 4, tip[1] - 2, 8, 5))

    return surface
