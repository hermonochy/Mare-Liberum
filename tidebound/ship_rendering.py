import math

import pygame

from .config import SHIP_CLASSES, SHIP_LIVERIES


def _points(points):
    return tuple((int(x), int(y)) for x, y in points)


def _draw_polygon(surface, color, points, width=0):
    pygame.draw.polygon(surface, color, _points(points), width)


def _draw_lines(surface, color, closed, points, width=1):
    pygame.draw.lines(surface, color, closed, _points(points), width)


def _draw_line(surface, color, start, end, width=1):
    pygame.draw.line(surface, color, (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), width)


def build_ship_surface(player, allied, rowing, ship_type, faction, player_livery, world_time):
    stats = SHIP_CLASSES.get(ship_type, SHIP_CLASSES["Sloop"])
    length = int(stats["length"])
    beam = int(stats["beam"])
    sail_span = int(stats["sail_span"])
    canvas_width = length + 42
    canvas_height = max(beam + 44, sail_span * 2 + 38)
    center_y = canvas_height // 2
    start_x = 20
    end_x = start_x + length
    surface = pygame.Surface((canvas_width, canvas_height), pygame.SRCALPHA)

    if player:
        _, hull_color, trim_color, sail_color = SHIP_LIVERIES[player_livery]
    elif allied:
        hull_color = (42, 80, 69)
        trim_color = (179, 190, 135)
        sail_color = (191, 220, 202)
    elif faction == "merchant":
        hull_color = (126, 83, 43)
        trim_color = (218, 180, 112)
        sail_color = (222, 211, 176)
    elif faction == "fishing":
        hull_color = (67, 91, 72)
        trim_color = (190, 172, 119)
        sail_color = (202, 191, 153)
    elif faction == "naval patrol":
        hull_color = (39, 60, 86)
        trim_color = (206, 194, 151)
        sail_color = (224, 224, 209)
    elif faction == "mail packet":
        hull_color = (107, 64, 54)
        trim_color = (218, 190, 143)
        sail_color = (220, 222, 200)
    elif faction == "whaler":
        hull_color = (73, 73, 61)
        trim_color = (180, 161, 123)
        sail_color = (170, 181, 169)
    else:
        hull_color = (69, 39, 34)
        trim_color = (165, 92, 65)
        sail_color = (155, 55, 48)

    sail_shadow = tuple(max(0, channel - 43) for channel in sail_color)
    rig = stats["rig"]
    mast_positions = [start_x + int(length * position) for position in stats["masts"]]
    span = min(sail_span, canvas_height // 2 - 12)
    yard_color = (89, 63, 40)
    seam_color = tuple(min(255, channel + 22) for channel in sail_color)

    for mast_index, mast_x in enumerate(mast_positions):
        local_span = int(span * (0.84 if mast_index in (0, len(mast_positions) - 1) else 1.0))
        if rig in {"sloop", "cutter", "gaff", "yawl"}:
            aft = length * (0.16 if rig != "cutter" else 0.21)
            points = [
                (mast_x - 7, center_y - local_span * 0.18),
                (mast_x + aft, center_y - local_span),
                (mast_x + aft * 0.88, center_y + local_span),
                (mast_x - 7, center_y + local_span * 0.18),
            ]
            _draw_polygon(surface, sail_shadow, points)
            inner_points = [
                (mast_x - 3, center_y - local_span * 0.16),
                (mast_x + aft * 0.88, center_y - local_span * 0.86),
                (mast_x + aft * 0.76, center_y + local_span * 0.86),
                (mast_x - 3, center_y + local_span * 0.16),
            ]
            _draw_polygon(surface, sail_color, inner_points)
            _draw_line(surface, seam_color, (mast_x, center_y), (mast_x + aft * 0.88, center_y - local_span * 0.86), 1)
            _draw_line(surface, seam_color, (mast_x, center_y), (mast_x + aft * 0.76, center_y + local_span * 0.86), 1)
        elif rig in {"schooner", "xebec"} or (rig in {"merchant", "brigantine", "barque", "carrack", "galleon", "indiaman"} and mast_index == len(mast_positions) - 1):
            lead = length * (0.13 if rig == "xebec" else 0.16)
            rake = -1 if mast_index % 2 == 0 else 1
            points = [
                (mast_x - lead * 0.35, center_y - local_span * 0.15),
                (mast_x + lead, center_y - local_span),
                (mast_x + lead * 1.18, center_y + local_span * 0.84),
                (mast_x - lead * 0.20, center_y + local_span * 0.12),
            ]
            if rig == "xebec":
                points[1] = (mast_x + lead * 0.72, center_y - local_span * 1.06)
                points[2] = (mast_x + lead * 0.72, center_y + local_span * 1.06)
            _draw_polygon(surface, sail_shadow, points)
            inset = [
                (mast_x - lead * 0.20, center_y - local_span * 0.12),
                (mast_x + lead * 0.86, center_y - local_span * 0.86),
                (mast_x + lead * 1.01, center_y + local_span * 0.73),
                (mast_x - lead * 0.10, center_y + local_span * 0.10),
            ]
            _draw_polygon(surface, sail_color, inset)
            _draw_line(surface, seam_color, (mast_x, center_y), (mast_x + lead, center_y - local_span * 0.88), 1)
            _draw_line(surface, seam_color, (mast_x, center_y), (mast_x + lead * 1.05, center_y + local_span * 0.78), 1)
        else:
            panel_depth = max(15, int(beam * (0.36 if rig == "ship_of_line" else 0.32)))
            width_scale = 1.08 if rig in {"ship_of_line", "galleon", "indiaman"} else 1.0
            yard_span = int(local_span * width_scale)
            points = [
                (mast_x - panel_depth // 2, center_y - yard_span),
                (mast_x + panel_depth // 2, center_y - yard_span * 0.94),
                (mast_x + panel_depth, center_y - yard_span * 0.48),
                (mast_x + panel_depth, center_y + yard_span * 0.48),
                (mast_x + panel_depth // 2, center_y + yard_span * 0.94),
                (mast_x - panel_depth // 2, center_y + yard_span),
            ]
            _draw_polygon(surface, sail_shadow, points)
            inner = [
                (mast_x - panel_depth // 2 + 2, center_y - yard_span * 0.91),
                (mast_x + panel_depth // 2 - 2, center_y - yard_span * 0.85),
                (mast_x + panel_depth - 3, center_y - yard_span * 0.44),
                (mast_x + panel_depth - 3, center_y + yard_span * 0.44),
                (mast_x + panel_depth // 2 - 2, center_y + yard_span * 0.85),
                (mast_x - panel_depth // 2 + 2, center_y + yard_span * 0.91),
            ]
            _draw_polygon(surface, sail_color, inner)
            _draw_line(surface, seam_color, (mast_x, center_y - yard_span * 0.80),
                             (mast_x + panel_depth - 1, center_y - yard_span * 0.39), 1)
            _draw_line(surface, seam_color, (mast_x, center_y + yard_span * 0.80),
                             (mast_x + panel_depth - 1, center_y + yard_span * 0.39), 1)

    half_beam = beam / 2.0
    bow_shoulder, fore_beam, mid_beam, aft_beam, stern_shoulder = stats["hull_profile"]
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
    shadow = [(x + 1, y + 4) for x, y in hull]
    center_x = sum(x for x, _ in hull) / len(hull)
    center_y_hull = sum(y for _, y in hull) / len(hull)
    inset = [(center_x + (x - center_x) * 0.91, center_y_hull + (y - center_y_hull) * 0.84) for x, y in hull]
    deck = [(center_x + (x - center_x) * 0.82, center_y_hull + (y - center_y_hull) * 0.70) for x, y in hull]
    _draw_polygon(surface, (24, 20, 18), shadow)
    _draw_polygon(surface, (42, 29, 23), hull)
    _draw_polygon(surface, hull_color, inset)
    _draw_polygon(surface, (139, 99, 61), deck)
    _draw_lines(surface, trim_color, True, inset, max(2, int(beam * 0.045)))

    deck_top = center_y - half_beam * 0.34
    deck_bottom = center_y + half_beam * 0.34
    plank_start = int(start_x + length * 0.22)
    plank_end = int(start_x + length * 0.86)
    plank_step = max(8, int(length / 17))
    for plank_x in range(plank_start, plank_end, plank_step):
        _draw_line(surface, (157, 116, 72), (plank_x, deck_top + 3), (plank_x + 3, deck_bottom - 3), 1)
    _draw_line(surface, (78, 53, 34), (start_x + length * 0.15, center_y),
                     (end_x - length * 0.09, center_y), 2)

    cabin_x = int(start_x + length * (0.12 if rig in {"galleon", "carrack", "indiaman"} else 0.14))
    cabin_w = max(15, int(length * (0.18 if rig not in {"galleon", "carrack", "indiaman"} else 0.22)))
    cabin_h = max(10, int(beam * (0.30 if rig not in {"galleon", "carrack", "indiaman"} else 0.39)))
    cabin_rect = pygame.Rect(cabin_x, int(center_y - cabin_h / 2), cabin_w, cabin_h)
    pygame.draw.rect(surface, (70, 46, 32), cabin_rect, border_radius=max(2, cabin_h // 5))
    pygame.draw.rect(surface, trim_color, cabin_rect, max(1, int(beam * 0.025)), border_radius=max(2, cabin_h // 5))
    _draw_line(surface, (222, 185, 125), (cabin_rect.left + 4, cabin_rect.top + 3),
                     (cabin_rect.right - 4, cabin_rect.top + 3), 1)
    for window_index in range(3 if cabin_w > 25 else 2):
        window_x = cabin_rect.left + int((window_index + 1) * cabin_w / (4 if cabin_w > 25 else 3))
        pygame.draw.circle(surface, (228, 190, 117), (window_x, cabin_rect.centery), max(1, int(beam * 0.025)))

    if rig in {"galleon", "carrack", "indiaman"}:
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
            _draw_line(surface, (229, 197, 143), (start_x + length * 0.24, gun_deck_y),
                             (end_x - length * 0.10, gun_deck_y), 1)

    gun_count = int(stats["guns"])
    if gun_count > 0:
        gun_start = start_x + length * 0.25
        gun_end = end_x - length * 0.15
        for index in range(gun_count):
            ratio = index / max(1, gun_count - 1)
            gun_x = int(gun_start + (gun_end - gun_start) * ratio)
            for side in (-1, 1):
                gun_y = int(center_y + side * half_beam * 0.39)
                pygame.draw.circle(surface, (39, 29, 22), (gun_x, gun_y), max(2, int(beam * 0.052)))
                pygame.draw.circle(surface, (194, 153, 99), (gun_x, gun_y), max(1, int(beam * 0.026)), 1)

    for mast_x in mast_positions:
        pygame.draw.circle(surface, (48, 33, 24), (mast_x, center_y), max(3, int(beam * 0.075)))
        pygame.draw.circle(surface, (192, 160, 111), (mast_x, center_y), max(1, int(beam * 0.035)))
        _draw_line(surface, yard_color, (mast_x, center_y - span), (mast_x, center_y + span), max(2, int(beam * 0.035)))
        _draw_line(surface, (209, 183, 139), (mast_x - 2, center_y - span + 3),
                         (mast_x - 2, center_y + span - 3), 1)
    if mast_positions:
        _draw_line(surface, (84, 58, 37), (mast_positions[0], center_y), (end_x + 15, center_y), 2)
        _draw_line(surface, (84, 58, 37), (start_x + 5, center_y), (mast_positions[-1], center_y), 1)
        for mast_x in mast_positions:
            _draw_line(surface, (142, 111, 75), (mast_x, center_y - span * 0.72),
                             (mast_positions[-1], center_y), 1)

    _draw_line(surface, (78, 52, 34), (end_x - 2, center_y), (end_x + 18, center_y), 3)
    _draw_line(surface, (203, 169, 119), (end_x + 1, center_y - 2), (end_x + 17, center_y - 2), 1)
    flag_x = mast_positions[-1] if rig in {"barque", "merchant", "carrack", "galleon", "indiaman", "ship_of_line"} else mast_positions[0]
    flag_y = int(center_y - span - 7)
    flag_color = (24, 22, 20) if faction == "pirate" else (225, 218, 183) if allied else (53, 87, 126) if faction == "naval patrol" else (173, 139, 74) if faction == "merchant" else (100, 123, 91) if faction == "fishing" else (158, 62, 49) if faction == "mail packet" else (100, 100, 91)
    _draw_line(surface, (44, 32, 25), (flag_x, flag_y + 4), (flag_x, flag_y - 7), 1)
    _draw_polygon(surface, flag_color, [(flag_x, flag_y - 7), (flag_x + 13, flag_y - 4), (flag_x, flag_y - 1)])
    if player:
        pygame.draw.circle(surface, (48, 37, 29), (cabin_rect.centerx, cabin_rect.centery), max(2, int(beam * 0.07)))
        pygame.draw.circle(surface, (235, 224, 196), (cabin_rect.centerx - 1, cabin_rect.centery - 1), 1)

    if rowing and stats["oar_power"] > 0 and stats["rowers"] >= 8:
        stroke = math.sin(world_time * 8.0) * 3.5
        oar_count = max(4, min(12, int(stats["rowers"] / 3)))
        for index in range(oar_count):
            ratio = index / max(1, oar_count - 1)
            oar_x = int(start_x + length * (0.27 + ratio * 0.52))
            for side in (-1, 1):
                root = (oar_x, int(center_y + side * half_beam * 0.36))
                tip = (int(oar_x + stroke), int(center_y + side * (half_beam + 15)))
                _draw_line(surface, (91, 58, 34), root, tip, 2)
                pygame.draw.ellipse(surface, (156, 116, 68), (tip[0] - 4, tip[1] - 2, 8, 5))

    return surface
