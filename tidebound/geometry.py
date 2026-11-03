import math


def clamp(value, low, high):
    return max(low, min(high, value))


def angle_difference(target, current):
    return (target - current + 180.0) % 360.0 - 180.0


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        if (y1 > y) != (y2 > y):
            crossing = (x2 - x1) * (y - y1) / ((y2 - y1) or 0.000001) + x1
            if x < crossing:
                inside = not inside
    return inside


def closest_point_on_segment(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ax, ay
    amount = clamp(((px - ax) * dx + (py - ay) * dy) / length_sq, 0.0, 1.0)
    return ax + dx * amount, ay + dy * amount


def nearest_polygon_edge(x, y, polygon):
    best_point = None
    best_distance = float("inf")
    for index in range(len(polygon)):
        ax, ay = polygon[index]
        bx, by = polygon[(index + 1) % len(polygon)]
        point = closest_point_on_segment(x, y, ax, ay, bx, by)
        distance = math.hypot(x - point[0], y - point[1])
        if distance < best_distance:
            best_point = point
            best_distance = distance
    return best_point, best_distance


def resolve_land_collision(x, y, vx, vy, radius, polygons):
    collided = False
    for polygon in polygons:
        inside = point_in_polygon((x, y), polygon)
        nearest, distance = nearest_polygon_edge(x, y, polygon)
        if not inside and distance >= radius:
            continue
        collided = True
        nx = nearest[0] - x if inside else x - nearest[0]
        ny = nearest[1] - y if inside else y - nearest[1]
        length = math.hypot(nx, ny)
        if length < 0.001:
            nx, ny, length = 0.0, -1.0, 1.0
        nx /= length
        ny /= length
        x = nearest[0] + nx * (radius + 2.0)
        y = nearest[1] + ny * (radius + 2.0)
        normal_speed = vx * nx + vy * ny
        if normal_speed < 0:
            vx -= 1.48 * normal_speed * nx
            vy -= 1.48 * normal_speed * ny
        vx *= 0.84
        vy *= 0.84
    return x, y, vx, vy, collided


def wrap_text(font, value, width):
    words = value.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if font.size(candidate)[0] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def calculate_propulsion(heading_degrees, wind_degrees, sail_setting, wind_strength, rigging_level, oars_deployed, oar_power, time_seconds):
    heading = math.radians(heading_degrees)
    wind_power = max(0.075, 0.5 + 0.5 * math.cos(heading - math.radians(wind_degrees)))
    sail_thrust = 51.0 * sail_setting * wind_power * wind_strength * (1.0 + rigging_level * 0.10)
    oar_thrust = 0.0
    if oars_deployed:
        stroke_power = 0.90 + 0.10 * (0.5 + 0.5 * math.sin(time_seconds * 8.0))
        oar_thrust = oar_power * 0.30 * stroke_power
    return sail_thrust + oar_thrust, wind_power, sail_thrust, oar_thrust
