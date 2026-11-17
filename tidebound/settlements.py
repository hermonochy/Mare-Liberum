import math
import random

from .geometry import point_in_polygon, nearest_polygon_edge


FACTION_SETTLEMENT_PROFILES = {
    "British Crown": {
        "style": "Crown Colonial", "scale": 1.16, "buildings": (31, 39), "layout": "terraced",
        "facades": [(193, 181, 151), (177, 165, 139), (211, 197, 164)],
        "roofs": [(126, 57, 43), (91, 75, 65), (147, 68, 48)], "special": "fort", "walled": True,
    },
    "Spanish Crown": {
        "style": "Spanish Colonial", "scale": 1.22, "buildings": (35, 45), "layout": "plaza",
        "facades": [(211, 187, 143), (196, 166, 119), (229, 211, 171)],
        "roofs": [(157, 66, 43), (181, 81, 48), (121, 57, 44)], "special": "church", "walled": True,
    },
    "French Crown": {
        "style": "French Colonial", "scale": 1.10, "buildings": (28, 37), "layout": "quarter",
        "facades": [(202, 192, 171), (185, 180, 163), (218, 208, 185)],
        "roofs": [(72, 91, 116), (82, 95, 112), (125, 92, 73)], "special": "market", "walled": False,
    },
    "Merchant League": {
        "style": "Merchant Quarter", "scale": 1.28, "buildings": (40, 51), "layout": "warehouse",
        "facades": [(153, 119, 80), (174, 139, 91), (185, 157, 111)],
        "roofs": [(91, 65, 47), (113, 78, 47), (134, 91, 53)], "special": "warehouse", "walled": False,
    },
    "Pirate Brotherhood": {
        "style": "Corsair Haven", "scale": 1.02, "buildings": (24, 33), "layout": "cove",
        "facades": [(115, 91, 68), (91, 72, 58), (143, 111, 77)],
        "roofs": [(55, 52, 46), (91, 55, 41), (73, 45, 38)], "special": "tavern", "walled": True,
    },
    "Independent": {
        "style": "Island Freehold", "scale": 1.08, "buildings": (25, 35), "layout": "organic",
        "facades": [(203, 195, 163), (174, 180, 145), (218, 205, 170)],
        "roofs": [(77, 111, 105), (91, 104, 121), (137, 83, 58)], "special": "market", "walled": False,
    },
}


def _polygon_centroid(polygon):
    area_twice = 0.0
    cx = 0.0
    cy = 0.0
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(index + 1) % len(polygon)]
        cross = x1 * y2 - x2 * y1
        area_twice += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area_twice) < 0.001:
        return sum(p[0] for p in polygon) / len(polygon), sum(p[1] for p in polygon) / len(polygon)
    return cx / (3.0 * area_twice), cy / (3.0 * area_twice)


def _rotated_rectangle(cx, cy, along, across, length, width):
    half_length = length * 0.5
    half_width = width * 0.5
    return [
        (cx + along[0] * a + across[0] * b, cy + along[1] * a + across[1] * b)
        for a, b in ((-half_length, -half_width), (half_length, -half_width),
                     (half_length, half_width), (-half_length, half_width))
    ]


def _ellipse_polygon(cx, cy, along, across, radius_a, radius_b, count, rng, irregularity=0.12):
    points = []
    phase = rng.uniform(0.0, math.tau)
    for index in range(count):
        angle = math.tau * index / count
        wobble = 1.0 + math.sin(angle * 3.0 + phase) * irregularity + rng.uniform(-irregularity * 0.35, irregularity * 0.35)
        a = math.cos(angle) * radius_a * wobble
        b = math.sin(angle) * radius_b * wobble
        points.append((cx + along[0] * a + across[0] * b,
                       cy + along[1] * a + across[1] * b))
    return points


def _footprint_is_buildable(points, polygon, coastal_setback):
    for point in points:
        if not point_in_polygon(point, polygon):
            return False
        if nearest_polygon_edge(point[0], point[1], polygon)[1] < coastal_setback:
            return False
    return True


def _road_curve(start, end, across, rng, polygon, width_factor=1.0):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = max(1.0, math.hypot(dx, dy))
    base_bend = min(52.0, distance * 0.12) * width_factor
    for reduction in (1.0, 0.65, 0.35, 0.0):
        bend = base_bend * reduction
        candidate = [
            start,
            (start[0] + dx * 0.31 + across[0] * bend * rng.uniform(-0.65, 0.65),
             start[1] + dy * 0.31 + across[1] * bend * rng.uniform(-0.65, 0.65)),
            (start[0] + dx * 0.69 - across[0] * bend * rng.uniform(-0.65, 0.65),
             start[1] + dy * 0.69 - across[1] * bend * rng.uniform(-0.65, 0.65)),
            end,
        ]
        if all(point_in_polygon(point, polygon) for point in candidate):
            return candidate
    return [start, end]


def _town_building_kind(profile, rng, index, target_count):
    if index == target_count // 2:
        return profile["special"]
    roll = rng.random()
    if profile["layout"] == "warehouse" and roll < 0.31:
        return "warehouse"
    if roll < 0.12:
        return "shop"
    if roll < 0.19:
        return "tavern"
    return "house"


def build_port_settlements(ports, land_polygons, seed=71931):
    settlements = {}
    if not land_polygons:
        return settlements

    ports_by_island = {}
    port_islands = {}
    for port_index, port in enumerate(ports):
        island_index = min(
            range(len(land_polygons)),
            key=lambda index: nearest_polygon_edge(port.shore_x, port.shore_y, land_polygons[index])[1],
        )
        port_islands[port.name] = island_index
        ports_by_island.setdefault(island_index, []).append(port)

    occupied_by_island = {}
    for port_index, port in enumerate(ports):
        island_index = port_islands[port.name]
        polygon = land_polygons[island_index]
        profile = FACTION_SETTLEMENT_PROFILES.get(port.faction, FACTION_SETTLEMENT_PROFILES["Independent"])
        rng = random.Random(seed + port_index * 7919 + island_index * 131)
        centroid = _polygon_centroid(polygon)
        inward_x = centroid[0] - port.shore_x
        inward_y = centroid[1] - port.shore_y
        inward_length = max(1.0, math.hypot(inward_x, inward_y))
        along = (inward_x / inward_length, inward_y / inward_length)
        across = (-along[1], along[0])
        extent_x = max(x for x, _ in polygon) - min(x for x, _ in polygon)
        extent_y = max(y for _, y in polygon) - min(y for _, y in polygon)
        island_scale = max(1.0, min(extent_x, extent_y) * 0.5)
        sibling_ports = ports_by_island[island_index]
        island_share = min(1.0, 1.35 / max(1.0, math.sqrt(len(sibling_ports))))
        variation = rng.uniform(0.93, 1.13)
        town_scale = max(0.94, min(1.52, profile["scale"] * variation * island_share))
        span = max(340.0, min(890.0, island_scale * 0.62)) * town_scale
        town_depth = max(300.0, min(760.0, island_scale * 0.54)) * town_scale
        inset = min(inward_length * 0.56, max(175.0, town_depth * 0.34))
        center = (port.shore_x + along[0] * inset, port.shore_y + along[1] * inset)
        if not point_in_polygon(center, polygon):
            center = centroid
        coastal_setback = max(42.0, min(82.0, island_scale * 0.065))

        target_count = rng.randint(*profile["buildings"])
        buildings = []
        occupied_buildings = occupied_by_island.setdefault(island_index, [])
        cluster_centers = [(0.0, 0.0)]
        for cluster_index in range(4):
            angle = math.tau * cluster_index / 4.0 + rng.uniform(-0.22, 0.22)
            cluster_centers.append((math.cos(angle) * span * rng.uniform(0.19, 0.27),
                                    math.sin(angle) * town_depth * rng.uniform(0.18, 0.26)))

        attempts = 0
        maximum_attempts = target_count * 70
        while len(buildings) < target_count and attempts < maximum_attempts:
            attempts += 1
            cluster_a, cluster_b = rng.choice(cluster_centers)
            a = cluster_a + rng.gauss(0.0, town_depth * 0.105)
            b = cluster_b + rng.gauss(0.0, span * 0.105)
            if (a / max(1.0, town_depth * 0.49)) ** 2 + (b / max(1.0, span * 0.49)) ** 2 > 1.0:
                continue
            bx = center[0] + along[0] * a + across[0] * b
            by = center[1] + along[1] * a + across[1] * b
            kind = _town_building_kind(profile, rng, len(buildings), target_count)
            size_boost = 1.0
            if kind in {"warehouse", "church", "fort"}:
                size_boost = 1.45
            elif kind in {"shop", "tavern", "market"}:
                size_boost = 1.16
            length = rng.uniform(38.0, 63.0) * town_scale * size_boost
            width = rng.uniform(28.0, 47.0) * town_scale * (1.0 if kind == "house" else 1.14)
            rotation = rng.uniform(-0.55, 0.55)
            rotation += math.atan2(along[1], along[0])
            rotated_along = (math.cos(rotation), math.sin(rotation))
            rotated_across = (-rotated_along[1], rotated_along[0])
            footprint = _rotated_rectangle(bx, by, rotated_along, rotated_across, length, width)
            if not _footprint_is_buildable(footprint, polygon, coastal_setback):
                continue
            radius = max(length, width) * 0.54
            if any(math.hypot(bx - item["center"][0], by - item["center"][1]) < (radius + item["radius"]) * 0.95
                   for item in buildings):
                continue
            if any(math.hypot(bx - item[0], by - item[1]) < (radius + item[2]) * 0.95
                   for item in occupied_buildings):
                continue
            buildings.append({
                "center": (bx, by),
                "footprint": footprint,
                "facade": rng.choice(profile["facades"]),
                "roof": rng.choice(profile["roofs"]),
                "kind": kind,
                "rotation": rotation,
                "radius": radius,
            })
            occupied_buildings.append((bx, by, radius))

        roads = []
        road_start = (port.shore_x + along[0] * 14.0, port.shore_y + along[1] * 14.0)
        roads.append(_road_curve(road_start, center, across, rng, polygon, 1.0))
        for cluster_a, cluster_b in cluster_centers[1:]:
            end = (center[0] + along[0] * cluster_a + across[0] * cluster_b,
                   center[1] + along[1] * cluster_a + across[1] * cluster_b)
            if point_in_polygon(end, polygon):
                roads.append(_road_curve(center, end, across, rng, polygon, 0.65))

        plaza_radius_a = min(68.0, town_depth * 0.11) * town_scale
        plaza_radius_b = min(54.0, span * 0.095) * town_scale
        plaza = _ellipse_polygon(center[0], center[1], along, across,
                                 plaza_radius_a, plaza_radius_b, 9, rng, 0.09)
        if not _footprint_is_buildable(plaza, polygon, coastal_setback * 0.5):
            plaza = []

        town_wall = []
        if profile["walled"]:
            town_wall = _ellipse_polygon(center[0], center[1], along, across,
                                         town_depth * 0.51, span * 0.51, 13, rng, 0.16)
            if not all(point_in_polygon(point, polygon) for point in town_wall):
                town_wall = []

        settlements[port.name] = {
            "port": port.name,
            "island_index": island_index,
            "faction": port.faction,
            "style": profile["style"],
            "layout": profile["layout"],
            "special": profile["special"],
            "walled": bool(town_wall),
            "center": center,
            "along": along,
            "across": across,
            "town_wall": town_wall,
            "shore": (port.shore_x, port.shore_y),
            "roads": roads,
            "plaza": plaza,
            "buildings": buildings,
            "town_scale": town_scale,
            "span": span,
            "depth": town_depth,
            "coastal_setback": coastal_setback,
            "island_polygon": polygon,
        }
    return settlements
