import pygame


def _point_list(points):
    return tuple((int(x), int(y)) for x, y in points)


def _line(surface, color, start, end, width=1):
    pygame.draw.line(surface, color, (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), max(1, int(width)))


def _blend(first, second, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a + (b - a) * amount) for a, b in zip(first, second))


def _sail_shape(mast_x, center_y, depth, span, billow=1.0):
    depth = max(6.0, float(depth))
    span = max(8.0, float(span))
    return [
        (mast_x - depth * 0.92, center_y - span * 0.80),
        (mast_x - depth * 0.77, center_y - span * 0.96),
        (mast_x - depth * 0.18, center_y - span * billow),
        (mast_x + depth * 0.64, center_y - span * 0.96),
        (mast_x + depth * 0.94, center_y - span * 0.80),
        (mast_x + depth * 1.05, center_y - span * 0.37),
        (mast_x + depth * 1.10, center_y),
        (mast_x + depth * 1.05, center_y + span * 0.37),
        (mast_x + depth * 0.94, center_y + span * 0.80),
        (mast_x + depth * 0.64, center_y + span * 0.96),
        (mast_x - depth * 0.18, center_y + span * billow),
        (mast_x - depth * 0.77, center_y + span * 0.96),
        (mast_x - depth * 0.92, center_y + span * 0.80),
        (mast_x - depth, center_y),
    ]


def _draw_skull_and_crossbones(surface, center, scale, ink, canvas):
    cx, cy = int(center[0]), int(center[1])
    radius = max(3, int(scale * 0.30))
    bone_width = max(1, int(scale * 0.12))
    bone_length = max(5, int(scale * 0.78))
    _line(surface, ink, (cx - bone_length, cy + radius), (cx + bone_length, cy + radius * 2.7), bone_width)
    _line(surface, ink, (cx + bone_length, cy + radius), (cx - bone_length, cy + radius * 2.7), bone_width)
    for direction in (-1, 1):
        for offset in (0, 1):
            pygame.draw.circle(
                surface,
                ink,
                (cx + direction * (bone_length - offset), cy + radius + offset * 2),
                max(1, int(scale * 0.07)),
            )
    head_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, int(radius * 1.75))
    pygame.draw.ellipse(surface, ink, head_rect)
    jaw_rect = pygame.Rect(cx - int(radius * 0.72), cy + int(radius * 0.45), int(radius * 1.44), max(2, int(radius * 0.65)))
    pygame.draw.rect(surface, ink, jaw_rect, border_radius=max(1, radius // 4))
    eye_radius = max(1, int(radius * 0.22))
    pygame.draw.circle(surface, canvas, (cx - int(radius * 0.38), cy), eye_radius)
    pygame.draw.circle(surface, canvas, (cx + int(radius * 0.38), cy), eye_radius)
    _line(surface, canvas, (cx - int(radius * 0.22), cy + int(radius * 0.82)), (cx - int(radius * 0.22), cy + int(radius * 1.18)), 1)
    _line(surface, canvas, (cx + int(radius * 0.22), cy + int(radius * 0.82)), (cx + int(radius * 0.22), cy + int(radius * 1.18)), 1)


def _draw_canvas(surface, points, color, seam_color, pattern, sail_type, emblem=False, emblem_ink=None):
    shadow = [(x + 2, y + 3) for x, y in points]
    pygame.draw.polygon(surface, (39, 29, 23), _point_list(shadow))
    pygame.draw.polygon(surface, _blend(color, (255, 248, 220), 0.08), _point_list(points))
    pygame.draw.polygon(surface, _blend(color, (69, 48, 32), 0.36), _point_list(points), 1)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    middle_x = (left + right) / 2
    middle_y = (top + bottom) / 2
    inner = _blend(color, (255, 251, 232), 0.23)
    _line(surface, inner, (left + 3, middle_y), (right - 3, middle_y), 1)
    for fraction in (-0.48, -0.16, 0.16, 0.48):
        seam_x = middle_x + (right - left) * fraction * 0.42
        _line(surface, seam_color, (seam_x, top + 5), (seam_x + 1, bottom - 5), 1)
    for fraction in (-0.48, 0.48):
        reef_y = middle_y + (bottom - top) * fraction
        _line(surface, _blend(color, (98, 72, 49), 0.25), (left + 3, reef_y), (right - 3, reef_y), 1)
    if pattern == "stripes":
        for fraction in (-0.38, 0.0, 0.38):
            stripe_x = middle_x + (right - left) * fraction * 0.42
            _line(surface, seam_color, (stripe_x, top + 5), (stripe_x + 1, bottom - 5), 2)
    elif pattern == "panels":
        _line(surface, seam_color, (left + 3, middle_y), (right - 3, middle_y), 2)
    elif pattern == "sunburst":
        for fraction in (-0.42, -0.2, 0.2, 0.42):
            target_x = middle_x + (right - left) * fraction
            _line(surface, seam_color, (middle_x, middle_y), (target_x, top + 4), 1)
            _line(surface, seam_color, (middle_x, middle_y), (target_x, bottom - 4), 1)
    elif pattern == "checks":
        _line(surface, seam_color, (left + 3, middle_y), (right - 3, middle_y), 2)
        for fraction in (-0.3, 0.3):
            stripe_x = middle_x + (right - left) * fraction * 0.42
            _line(surface, seam_color, (stripe_x, top + 5), (stripe_x + 1, bottom - 5), 2)
    if sail_type == "Heavy Weather Canvas":
        _line(surface, seam_color, (left + 3, middle_y - 2), (right - 3, middle_y - 2), 2)
        _line(surface, seam_color, (left + 3, middle_y + 2), (right - 3, middle_y + 2), 1)
    elif sail_type == "Fine-weave Canvas":
        for fraction in (-0.28, 0.28):
            seam_x = middle_x + (right - left) * fraction * 0.42
            _line(surface, inner, (seam_x, top + 4), (seam_x, bottom - 4), 1)
    if emblem:
        mark_scale = max(11, min(26, int((bottom - top) * 0.36)))
        mark_center = (middle_x + (right - left) * 0.20, middle_y - (bottom - top) * 0.28)
        _draw_skull_and_crossbones(surface, mark_center, mark_scale, emblem_ink or seam_color, color)


def _draw_square_sail(surface, mast_x, center_y, depth, span, color, seam, pattern, sail_type, emblem=False, emblem_ink=None):
    points = _sail_shape(mast_x, center_y, depth, span)
    _draw_canvas(surface, points, color, seam, pattern, sail_type, emblem, emblem_ink)
    yard_half = span * 0.99
    _line(surface, (63, 43, 29), (mast_x, center_y - yard_half), (mast_x, center_y + yard_half), 4)
    _line(surface, (190, 153, 105), (mast_x + 1, center_y - yard_half + 2), (mast_x + 1, center_y + yard_half - 2), 1)
    for end in (-1, 1):
        pygame.draw.circle(surface, (93, 64, 39), (int(mast_x), int(center_y + end * yard_half)), 2)


def _draw_fore_and_aft_sail(surface, mast_x, center_y, depth, span, color, seam, pattern, sail_type, emblem=False, emblem_ink=None):
    points = [
        (mast_x - depth * 1.05, center_y - span * 0.42),
        (mast_x - depth * 0.78, center_y - span * 0.74),
        (mast_x - depth * 0.18, center_y - span * 0.91),
        (mast_x + depth * 0.62, center_y - span * 0.68),
        (mast_x + depth * 0.82, center_y - span * 0.40),
        (mast_x + depth * 0.88, center_y),
        (mast_x + depth * 0.82, center_y + span * 0.40),
        (mast_x + depth * 0.62, center_y + span * 0.68),
        (mast_x - depth * 0.18, center_y + span * 0.91),
        (mast_x - depth * 0.78, center_y + span * 0.74),
        (mast_x - depth * 1.05, center_y + span * 0.42),
        (mast_x - depth * 1.12, center_y),
    ]
    _draw_canvas(surface, points, color, seam, pattern, sail_type, emblem, emblem_ink)
    _line(surface, (63, 43, 29), (mast_x - depth * 0.24, center_y - span * 0.84), (mast_x - depth * 0.24, center_y + span * 0.84), 3)
    _line(surface, (181, 143, 96), (mast_x - depth * 0.24 + 1, center_y - span * 0.78), (mast_x - depth * 0.24 + 1, center_y + span * 0.78), 1)


def _draw_lateen_sail(surface, mast_x, center_y, depth, span, color, seam, pattern, sail_type, emblem=False, emblem_ink=None):
    points = [
        (mast_x - depth * 0.82, center_y - span * 0.88),
        (mast_x + depth * 0.82, center_y - span * 0.97),
        (mast_x + depth * 1.05, center_y + span * 0.74),
        (mast_x - depth * 0.20, center_y + span * 0.98),
        (mast_x - depth * 0.76, center_y + span * 0.66),
    ]
    _draw_canvas(surface, points, color, seam, pattern, sail_type, emblem, emblem_ink)
    _line(surface, (63, 43, 29), (mast_x - depth * 0.78, center_y - span * 0.91), (mast_x + depth * 0.98, center_y + span * 0.82), 3)
    _line(surface, (181, 143, 96), (mast_x - depth * 0.72, center_y - span * 0.85), (mast_x + depth * 0.91, center_y + span * 0.77), 1)


def draw_ship_sails(surface, stats, mast_positions, center_y, half_beam, rig, sail_color, pattern, sail_type, pirate_mark=False):
    if not mast_positions:
        return
    sail_span = float(stats.get("sail_span", half_beam * 1.5))
    mast_spacing = float(stats["length"]) / max(1, len(mast_positions))
    span = min(half_beam * 1.34, max(half_beam * 1.08, sail_span * 0.77))
    if sail_type == "Heavy Weather Canvas":
        span *= 0.94
    elif sail_type == "Racing Cut":
        span *= 1.10
    elif sail_type == "Fine-weave Canvas":
        span *= 1.03
    depth = max(10.0, min(24.0, mast_spacing * 0.22))
    if sail_type == "Racing Cut":
        depth *= 1.13
    elif sail_type == "Heavy Weather Canvas":
        depth *= 0.92
    seam = _blend(sail_color, (82, 61, 43), 0.47)
    emblem_ink = (34, 29, 26) if sum(sail_color) > 330 else (236, 225, 192)
    square_rigs = {"brig", "brigantine", "barque", "corvette", "frigate", "ship_of_line", "merchant", "carrack", "galleon", "indiaman"}
    mixed_rigs = {"brigantine", "barque", "merchant", "indiaman"}
    fore_aft_rigs = {"gaff", "sloop", "cutter", "schooner", "yawl"}
    lateen_rigs = {"xebec"}
    emblem_index = min(range(len(mast_positions)), key=lambda index: abs(index - (len(mast_positions) // 2)))
    for index, mast_x in enumerate(mast_positions):
        is_mizzen = index == len(mast_positions) - 1
        use_fore_aft = rig in fore_aft_rigs or rig in mixed_rigs and is_mizzen
        use_lateen = rig in lateen_rigs
        emblem = pirate_mark and index == emblem_index
        if use_lateen:
            local_depth = min(34.0, max(19.0, mast_spacing * 0.31))
            local_span = min(half_beam * 1.25, span * 1.08)
            _draw_lateen_sail(surface, mast_x, center_y, local_depth, local_span, sail_color, seam, pattern, sail_type, emblem, emblem_ink)
        elif use_fore_aft:
            local_depth = min(42.0, max(19.0, mast_spacing * (0.34 if len(mast_positions) == 1 else 0.31)))
            local_span = min(half_beam * 1.26, span * (1.02 if len(mast_positions) == 1 else 0.90))
            _draw_fore_and_aft_sail(surface, mast_x, center_y, local_depth, local_span, sail_color, seam, pattern, sail_type, emblem, emblem_ink)
        else:
            local_depth = depth * (1.08 if rig == "ship_of_line" else 1.0)
            local_span = span * (1.02 if rig in {"frigate", "ship_of_line", "galleon"} else 0.96)
            if index == 0 and rig in square_rigs:
                local_span *= 0.91
            _draw_square_sail(surface, mast_x, center_y, local_depth, local_span, sail_color, seam, pattern, sail_type, emblem, emblem_ink)
    if rig in {"sloop", "cutter", "schooner", "brigantine", "xebec"}:
        bow_mast = mast_positions[-1]
        jib_depth = min(25.0, max(12.0, (float(stats["length"]) - (bow_mast - min(mast_positions))) * 0.17))
        jib_center_x = bow_mast + jib_depth * 0.88
        jib_span = span * (0.42 if rig in {"sloop", "cutter"} else 0.32)
        jib_points = [
            (bow_mast - 2, center_y - jib_span * 0.72),
            (jib_center_x + jib_depth * 0.42, center_y - jib_span * 0.52),
            (jib_center_x + jib_depth * 0.48, center_y),
            (jib_center_x + jib_depth * 0.42, center_y + jib_span * 0.52),
            (bow_mast - 2, center_y + jib_span * 0.72),
        ]
        _draw_canvas(surface, jib_points, sail_color, seam, pattern, sail_type, False, emblem_ink)
        _line(surface, (63, 43, 29), (bow_mast - 2, center_y - jib_span * 0.72), (jib_center_x + jib_depth * 0.42, center_y + jib_span * 0.52), 2)
