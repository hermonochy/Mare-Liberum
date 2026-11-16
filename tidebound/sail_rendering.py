import math

import pygame

from .sail_geometry import (
    clamp_deployment,
    deployed_sail_dimensions,
    gaff_sail_points,
    jib_sail_points,
    lateen_sail_points,
    sail_dimensions,
    square_sail_points,
)


def _point_list(points):
    return tuple((int(x), int(y)) for x, y in points)


def _line(surface, color, start, end, width=1):
    pygame.draw.line(surface, color, (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), max(1, int(width)))


def _blend(first, second, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a + (b - a) * amount) for a, b in zip(first, second))


def _draw_skull_and_crossbones(surface, center, scale, ink, canvas):
    cx, cy = int(center[0]), int(center[1])
    radius = max(2, int(scale * 0.30))
    bone_width = max(1, int(scale * 0.10))
    bone_length = max(4, int(scale * 0.72))
    _line(surface, ink, (cx - bone_length, cy + radius), (cx + bone_length, cy + radius * 2.5), bone_width)
    _line(surface, ink, (cx + bone_length, cy + radius), (cx - bone_length, cy + radius * 2.5), bone_width)
    head_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, int(radius * 1.55))
    pygame.draw.ellipse(surface, ink, head_rect)
    eye_radius = max(1, int(radius * 0.22))
    pygame.draw.circle(surface, canvas, (cx - int(radius * 0.38), cy), eye_radius)
    pygame.draw.circle(surface, canvas, (cx + int(radius * 0.38), cy), eye_radius)
    _line(surface, canvas, (cx - int(radius * 0.20), cy + int(radius * 0.72)), (cx - int(radius * 0.20), cy + int(radius * 1.03)), 1)
    _line(surface, canvas, (cx + int(radius * 0.20), cy + int(radius * 0.72)), (cx + int(radius * 0.20), cy + int(radius * 1.03)), 1)


def _draw_canvas(surface, points, color, seam_color, pattern, sail_type, emblem=False, emblem_ink=None):
    points = _point_list(points)
    shadow = tuple((x + 1, y + 2) for x, y in points)
    canvas_color = _blend(color, (255, 249, 225), 0.10)
    edge_color = _blend(color, (67, 49, 34), 0.43)
    pygame.draw.polygon(surface, (42, 31, 24), shadow)
    pygame.draw.polygon(surface, canvas_color, points)
    pygame.draw.polygon(surface, edge_color, points, 1)
    left = min(point[0] for point in points)
    right = max(point[0] for point in points)
    top = min(point[1] for point in points)
    bottom = max(point[1] for point in points)
    width = max(1.0, right - left)
    height = max(1.0, bottom - top)
    center_x = (left + right) * 0.5
    center_y = (top + bottom) * 0.5
    inner = _blend(color, (255, 255, 242), 0.30)
    seam = _blend(seam_color, (72, 52, 36), 0.10)
    for fraction in (-0.66, -0.33, 0.0, 0.33, 0.66):
        y = center_y + height * fraction * 0.91
        inset = width * (0.06 + abs(fraction) * 0.04)
        _line(surface, inner, (right - inset, y), (left + inset, y), 1)
    for fraction in (0.34, 0.68):
        x = right - width * fraction
        half_height = height * (0.83 - fraction * 0.08)
        _line(surface, seam, (x, center_y - half_height), (x, center_y + half_height), 1)
    if pattern == "stripes":
        for fraction in (-0.52, -0.18, 0.18, 0.52):
            y = center_y + height * fraction * 0.86
            _line(surface, seam_color, (right - 2, y), (left + 2, y), max(1, int(height * 0.035)))
    elif pattern in {"panels", "checks"}:
        _line(surface, seam_color, (right - 2, center_y), (left + 2, center_y), 1)
        if pattern == "checks":
            for fraction in (0.25, 0.75):
                x = right - width * fraction
                _line(surface, seam_color, (x, top + 2), (x, bottom - 2), 1)
    elif pattern == "sunburst":
        for fraction in (-0.48, -0.24, 0.24, 0.48):
            y = center_y + height * fraction
            _line(surface, seam_color, (right - 2, center_y), (left + 2, y), 1)
    if sail_type == "Heavy Weather Canvas":
        for fraction in (0.42, 0.62):
            x = right - width * fraction
            _line(surface, seam_color, (x, top + 2), (x, bottom - 2), 2)
    elif sail_type == "Fine-weave Canvas":
        for fraction in (-0.48, -0.16, 0.16, 0.48):
            y = center_y + height * fraction
            _line(surface, inner, (right - 2, y), (left + 2, y), 1)
    if emblem and width > 13 and height > 10:
        mark_scale = max(6, min(16, int(min(width, height) * 0.43)))
        _draw_skull_and_crossbones(surface, (center_x, center_y), mark_scale, emblem_ink or seam_color, canvas_color)


def _draw_yard(surface, mast_x, center_y, half_span):
    width = max(2, min(4, int(half_span * 0.13)))
    _line(surface, (47, 34, 25), (mast_x, center_y - half_span * 1.04), (mast_x, center_y + half_span * 1.04), width)
    _line(surface, (187, 148, 100), (mast_x + 1, center_y - half_span), (mast_x + 1, center_y + half_span), 1)
    for side in (-1, 1):
        pygame.draw.circle(surface, (89, 62, 39), (int(mast_x), int(center_y + side * half_span * 0.92)), 2)


def _draw_furled_sail(surface, mast_x, center_y, half_span, color, seam):
    half_span = max(3.0, float(half_span))
    _line(surface, (53, 38, 27), (mast_x, center_y - half_span), (mast_x, center_y + half_span), 4)
    _line(surface, _blend(color, (255, 243, 208), 0.20), (mast_x - 2, center_y - half_span * 0.95), (mast_x - 2, center_y + half_span * 0.95), 2)
    for fraction in (-0.65, -0.32, 0.0, 0.32, 0.65):
        y = center_y + half_span * fraction
        _line(surface, seam, (mast_x - 4, y), (mast_x + 1, y), 1)


def _draw_square_sail(surface, mast_x, center_y, depth, half_span, color, seam, pattern, sail_type, phase, emblem=False, emblem_ink=None):
    points = square_sail_points(mast_x, center_y, depth, half_span, phase)
    _draw_canvas(surface, points, color, seam, pattern, sail_type, emblem, emblem_ink)
    _draw_yard(surface, mast_x, center_y, half_span)


def _draw_gaff_sail(surface, mast_x, center_y, depth, half_span, color, seam, pattern, sail_type, phase, emblem=False, emblem_ink=None):
    points = gaff_sail_points(mast_x, center_y, depth, half_span, phase)
    _draw_canvas(surface, points, color, seam, pattern, sail_type, emblem, emblem_ink)
    _draw_yard(surface, mast_x, center_y, half_span * 0.84)
    aft_x = mast_x - depth
    _line(surface, (61, 43, 29), (mast_x - depth * 0.12, center_y - half_span), (aft_x, center_y + half_span * 0.62), 3)
    _line(surface, (182, 145, 98), (mast_x - depth * 0.12 + 1, center_y - half_span * 0.94), (aft_x + 1, center_y + half_span * 0.58), 1)


def _draw_lateen_sail(surface, mast_x, center_y, depth, half_span, color, seam, pattern, sail_type, phase, emblem=False, emblem_ink=None):
    points = lateen_sail_points(mast_x, center_y, depth, half_span, phase)
    _draw_canvas(surface, points, color, seam, pattern, sail_type, emblem, emblem_ink)
    spar_start = (mast_x + depth * 0.14, center_y - half_span)
    spar_end = (mast_x - depth, center_y + half_span)
    _line(surface, (55, 39, 28), spar_start, spar_end, 3)
    _line(surface, (185, 147, 100), (spar_start[0] + 1, spar_start[1]), (spar_end[0] + 1, spar_end[1] - 1), 1)


def _draw_jib(surface, bow_x, center_y, depth, half_span, color, seam, pattern, sail_type, phase):
    points = jib_sail_points(bow_x, center_y, depth, half_span, phase)
    _draw_canvas(surface, points, color, seam, pattern, sail_type)
    _line(surface, (62, 43, 29), (bow_x, center_y - half_span), (bow_x + depth, center_y), 2)


def draw_ship_sails(surface, stats, mast_positions, center_y, half_beam, rig, sail_color, pattern, sail_type, pirate_mark=False, sail_setting=1.0, world_time=0.0):
    if not mast_positions:
        return
    deployment = clamp_deployment(sail_setting)
    full_span, full_depth = sail_dimensions(stats, half_beam, len(mast_positions), sail_type)
    seam = _blend(sail_color, (83, 61, 42), 0.48)
    emblem_ink = (35, 30, 26) if sum(sail_color) > 330 else (236, 225, 192)
    square_rigs = {"brig", "brigantine", "barque", "corvette", "frigate", "ship_of_line", "merchant", "carrack", "galleon", "indiaman"}
    mixed_rigs = {"brigantine", "barque", "merchant", "indiaman"}
    fore_aft_rigs = {"gaff", "sloop", "cutter", "schooner", "yawl"}
    lateen_rigs = {"xebec"}
    emblem_index = min(range(len(mast_positions)), key=lambda index: abs(index - (len(mast_positions) // 2)))
    phase_base = float(world_time) * math.tau
    if deployment <= 0.015:
        for mast_x in mast_positions:
            _draw_furled_sail(surface, mast_x, center_y, full_span, sail_color, seam)
        return
    for index, mast_x in enumerate(mast_positions):
        phase = phase_base + index * 1.31
        mast_factor = 1.0 if len(mast_positions) == 1 else 0.84 + 0.16 * (1.0 - abs(index - (len(mast_positions) - 1) * 0.5) / max(0.5, (len(mast_positions) - 1) * 0.5))
        local_span, local_depth = deployed_sail_dimensions(full_span, full_depth, deployment, mast_factor)
        emblem = index == emblem_index and pirate_mark
        if rig in lateen_rigs:
            _draw_lateen_sail(surface, mast_x, center_y, local_depth * 1.15, local_span, sail_color, seam, pattern, sail_type, phase, emblem, emblem_ink)
        elif rig in fore_aft_rigs or rig in mixed_rigs and index == 0:
            _draw_gaff_sail(surface, mast_x, center_y, local_depth * 1.12, local_span, sail_color, seam, pattern, sail_type, phase, emblem, emblem_ink)
        else:
            _draw_square_sail(surface, mast_x, center_y, local_depth, local_span, sail_color, seam, pattern, sail_type, phase, emblem, emblem_ink)
    headsail_rigs = square_rigs | fore_aft_rigs | mixed_rigs | lateen_rigs
    if rig in headsail_rigs and deployment > 0.035:
        bow_x = max(mast_positions) + float(stats["length"]) * 0.055
        jib_span = deployed_sail_dimensions(full_span, full_depth, deployment, 0.56)[0]
        jib_depth = min(26.0, float(stats["length"]) * 0.12) * deployment
        _draw_jib(surface, bow_x, center_y, max(3.0, jib_depth), jib_span, sail_color, seam, pattern, sail_type, phase_base + 2.7)
