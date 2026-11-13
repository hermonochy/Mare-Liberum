import math


def clamp_deployment(value):
    return max(0.0, min(1.0, float(value)))


def deployed_sail_dimensions(full_span, full_depth, deployment, scale=1.0):
    deployment = clamp_deployment(deployment)
    scale = max(0.0, float(scale))
    width_factor = 0.72 + 0.28 * math.sqrt(deployment)
    return float(full_span) * width_factor * scale, max(3.0, float(full_depth) * deployment) * scale


def sail_dimensions(stats, half_beam, mast_count, sail_type):
    profile = stats.get("hull_profile", (0.5, 0.5, 0.5, 0.5, 0.5))
    hull_half_width = max(1.0, float(half_beam) * max(profile))
    span = min(hull_half_width * 0.94, max(hull_half_width * 0.78, float(stats.get("sail_span", hull_half_width * 2.0)) * 0.34))
    length = float(stats["length"])
    mast_spacing = length / max(1, int(mast_count))
    if mast_count == 1:
        depth = min(58.0, max(14.0, length * 0.44))
    else:
        depth = min(48.0, max(12.0, mast_spacing * 0.43))
    if sail_type == "Heavy Weather Canvas":
        depth *= 0.91
        span *= 0.96
    elif sail_type == "Racing Cut":
        depth *= 1.08
        span *= 1.02
    elif sail_type == "Fine-weave Canvas":
        depth *= 1.03
    return span, depth


def square_sail_points(mast_x, center_y, depth, half_span, phase):
    depth = max(3.0, float(depth))
    half_span = max(3.0, float(half_span))
    aft_x = float(mast_x) - depth
    flutter = math.sin(float(phase) * 2.0 + 0.45) * min(1.8, depth * 0.035)
    return (
        (mast_x, center_y - half_span),
        (mast_x - depth * 0.10, center_y - half_span * 0.985),
        (aft_x + flutter * 0.12, center_y - half_span * 0.94),
        (aft_x + flutter * 0.48, center_y - half_span * 0.60),
        (aft_x + flutter, center_y),
        (aft_x + flutter * 0.48, center_y + half_span * 0.60),
        (aft_x + flutter * 0.12, center_y + half_span * 0.94),
        (mast_x - depth * 0.10, center_y + half_span * 0.985),
        (mast_x, center_y + half_span),
    )


def gaff_sail_points(mast_x, center_y, depth, half_span, phase):
    depth = max(3.0, float(depth))
    half_span = max(3.0, float(half_span))
    aft_x = float(mast_x) - depth
    flutter = math.sin(float(phase) * 2.0 + 0.8) * min(1.6, depth * 0.03)
    return (
        (mast_x, center_y - half_span * 0.82),
        (mast_x - depth * 0.12, center_y - half_span),
        (aft_x + flutter, center_y - half_span * 0.62),
        (aft_x + flutter, center_y + half_span * 0.62),
        (mast_x - depth * 0.12, center_y + half_span),
        (mast_x, center_y + half_span * 0.82),
    )


def lateen_sail_points(mast_x, center_y, depth, half_span, phase):
    depth = max(3.0, float(depth))
    half_span = max(3.0, float(half_span))
    flutter = math.sin(float(phase) * 2.0 + 0.35) * min(1.8, depth * 0.035)
    return (
        (mast_x + depth * 0.14, center_y - half_span),
        (mast_x - depth * 0.04, center_y - half_span * 0.78),
        (mast_x - depth * 0.48 + flutter, center_y + half_span * 0.20),
        (mast_x - depth + flutter, center_y + half_span),
        (mast_x - depth * 0.12, center_y + half_span * 0.70),
    )


def jib_sail_points(bow_x, center_y, depth, half_span, phase):
    depth = max(3.0, float(depth))
    half_span = max(2.0, float(half_span))
    flutter = math.sin(float(phase) * 2.0 + 1.2) * min(1.2, depth * 0.03)
    return (
        (bow_x, center_y - half_span),
        (bow_x + depth + flutter, center_y),
        (bow_x, center_y + half_span),
        (bow_x - depth * 0.08, center_y),
    )
