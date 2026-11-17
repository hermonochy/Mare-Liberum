import math

from .geometry import point_in_polygon, nearest_polygon_edge


HARBOUR_BERTH_ANCHOR_DISTANCE = 245.0
HARBOUR_WATER_LENGTH = 360.0
HARBOUR_START_INLAND = -22.0
HARBOUR_BREAKWATER_WIDTH = 14.0
HARBOUR_SIDE_CLEARANCE = 78.0
HARBOUR_ENTRANCE_HALF_WIDTH = 140.0
HARBOUR_FINGER_PIER_WIDTH = 9.0
HARBOUR_FINGER_PIER_END = 174.0


def harbour_frame(port):
    dx = float(port.x) - float(port.shore_x)
    dy = float(port.y) - float(port.shore_y)
    length = max(1.0, math.hypot(dx, dy))
    axis = (dx / length, dy / length)
    perpendicular = (-axis[1], axis[0])
    return axis, perpendicular, length



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
        return sum(point[0] for point in polygon) / len(polygon), sum(point[1] for point in polygon) / len(polygon)
    return cx / (3.0 * area_twice), cy / (3.0 * area_twice)


def _inside_patch(points, polygon):
    if not all(point_in_polygon(point, polygon) or nearest_polygon_edge(point[0], point[1], polygon)[1] <= 2.0
               for point in points):
        return False
    for index, start in enumerate(points):
        end = points[(index + 1) % len(points)]
        for step in (0.25, 0.5, 0.75):
            sample = (start[0] + (end[0] - start[0]) * step,
                      start[1] + (end[1] - start[1]) * step)
            if not point_in_polygon(sample, polygon) and nearest_polygon_edge(sample[0], sample[1], polygon)[1] > 2.0:
                return False
    return True


def position_port_anchor(port, distance=HARBOUR_BERTH_ANCHOR_DISTANCE):
    axis, _, _ = harbour_frame(port)
    port.x = float(port.shore_x) + axis[0] * float(distance)
    port.y = float(port.shore_y) + axis[1] * float(distance)
    return port.x, port.y


def _rectangle_between(start, end, width):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(1.0, math.hypot(dx, dy))
    px = -dy / length * width * 0.5
    py = dx / length * width * 0.5
    return [
        (start[0] + px, start[1] + py),
        (end[0] + px, end[1] + py),
        (end[0] - px, end[1] - py),
        (start[0] - px, start[1] - py),
    ]


def harbour_layout(port, berth_count, berth_spacing, land_polygons=None):
    axis, perpendicular, shore_to_berth = harbour_frame(port)
    berth_half_span = max(0.0, (int(berth_count) - 1) * float(berth_spacing) * 0.5)
    half_width = berth_half_span + HARBOUR_SIDE_CLEARANCE
    start_distance = HARBOUR_START_INLAND
    end_distance = HARBOUR_WATER_LENGTH

    def point(along, across):
        return (
            float(port.shore_x) + axis[0] * along + perpendicular[0] * across,
            float(port.shore_y) + axis[1] * along + perpendicular[1] * across,
        )

    rough_left_start = point(start_distance, -half_width)
    rough_right_start = point(start_distance, half_width)
    land_polygon = None
    if land_polygons:
        land_polygon = min(
            land_polygons,
            key=lambda polygon: nearest_polygon_edge(port.shore_x, port.shore_y, polygon)[1],
        )
    if land_polygon:
        left_coast, _ = nearest_polygon_edge(rough_left_start[0], rough_left_start[1], land_polygon)
        right_coast, _ = nearest_polygon_edge(rough_right_start[0], rough_right_start[1], land_polygon)
        left_start = (left_coast[0] - axis[0] * 6.0, left_coast[1] - axis[1] * 6.0)
        right_start = (right_coast[0] - axis[0] * 6.0, right_coast[1] - axis[1] * 6.0)
    else:
        left_coast = rough_left_start
        right_coast = rough_right_start
        left_start = rough_left_start
        right_start = rough_right_start
    left_end = point(end_distance, -half_width)
    right_end = point(end_distance, half_width)
    walls = [
        _rectangle_between(left_start, left_end, HARBOUR_BREAKWATER_WIDTH),
        _rectangle_between(right_start, right_end, HARBOUR_BREAKWATER_WIDTH),
        _rectangle_between(point(end_distance, -half_width), point(end_distance, -HARBOUR_ENTRANCE_HALF_WIDTH), HARBOUR_BREAKWATER_WIDTH),
        _rectangle_between(point(end_distance, HARBOUR_ENTRANCE_HALF_WIDTH), point(end_distance, half_width), HARBOUR_BREAKWATER_WIDTH),
    ]

    quay = _rectangle_between(left_coast, right_coast, 22.0)
    apron = []
    apron_half_width = 0.0
    apron_depth = 0.0
    if land_polygon:
        centroid = _polygon_centroid(land_polygon)
        inward_x = centroid[0] - float(port.shore_x)
        inward_y = centroid[1] - float(port.shore_y)
        inward_length = max(1.0, math.hypot(inward_x, inward_y))
        inward = (inward_x / inward_length, inward_y / inward_length)
        inward_perpendicular = (-inward[1], inward[0])
        for start_depth in (5.0, 15.0, 25.0, 40.0, 60.0, 80.0):
            best_area_at_start = 0.0
            best_patch_at_start = None
            best_dimensions_at_start = None
            for depth in (60.0, 90.0, 120.0, 160.0):
                for candidate_half_width in (40.0, 60.0, 90.0, 120.0, 160.0):
                    candidate = [
                        (port.shore_x + inward[0] * start_depth - inward_perpendicular[0] * candidate_half_width,
                         port.shore_y + inward[1] * start_depth - inward_perpendicular[1] * candidate_half_width),
                        (port.shore_x + inward[0] * start_depth + inward_perpendicular[0] * candidate_half_width,
                         port.shore_y + inward[1] * start_depth + inward_perpendicular[1] * candidate_half_width),
                        (port.shore_x + inward[0] * (start_depth + depth) + inward_perpendicular[0] * candidate_half_width,
                         port.shore_y + inward[1] * (start_depth + depth) + inward_perpendicular[1] * candidate_half_width),
                        (port.shore_x + inward[0] * (start_depth + depth) - inward_perpendicular[0] * candidate_half_width,
                         port.shore_y + inward[1] * (start_depth + depth) - inward_perpendicular[1] * candidate_half_width),
                    ]
                    area = depth * candidate_half_width * 2.0
                    if area > best_area_at_start and _inside_patch(candidate, land_polygon):
                        best_patch_at_start = candidate
                        best_dimensions_at_start = (candidate_half_width, depth)
                        best_area_at_start = area
            if best_patch_at_start is not None:
                apron = best_patch_at_start
                apron_half_width, apron_depth = best_dimensions_at_start
                break
    if not apron:
        apron = [
            (port.shore_x - axis[0] * 15.0 - perpendicular[0] * 12.0,
             port.shore_y - axis[1] * 15.0 - perpendicular[1] * 12.0),
            (port.shore_x - axis[0] * 15.0 + perpendicular[0] * 12.0,
             port.shore_y - axis[1] * 15.0 + perpendicular[1] * 12.0),
            (port.shore_x - axis[0] * 60.0 + perpendicular[0] * 12.0,
             port.shore_y - axis[1] * 60.0 + perpendicular[1] * 12.0),
            (port.shore_x - axis[0] * 60.0 - perpendicular[0] * 12.0,
             port.shore_y - axis[1] * 60.0 - perpendicular[1] * 12.0),
        ]
        apron_half_width = 12.0
        apron_depth = 45.0

    docks = []
    if int(berth_count) > 1:
        for slot_boundary in range(int(berth_count) - 1):
            across = -berth_half_span + (slot_boundary + 0.5) * float(berth_spacing)
            amount = (across + half_width) / max(1.0, half_width * 2.0)
            start = (left_coast[0] + (right_coast[0] - left_coast[0]) * amount + axis[0] * 25.0,
                     left_coast[1] + (right_coast[1] - left_coast[1]) * amount + axis[1] * 25.0)
            docks.append(_rectangle_between(
                start,
                point(HARBOUR_FINGER_PIER_END, across),
                HARBOUR_FINGER_PIER_WIDTH,
            ))

    berths = []
    for slot in range(int(berth_count)):
        across = (slot - (int(berth_count) - 1) * 0.5) * float(berth_spacing)
        berths.append(point(float(shore_to_berth) + 26.0, across))

    basin = [point(0.0, -half_width + 12.0), point(end_distance, -half_width + 12.0),
             point(end_distance, half_width - 12.0), point(0.0, half_width - 12.0)]
    heads = [point(end_distance, -half_width), point(end_distance, half_width)]
    collision_polygons = walls + docks + [quay]
    return {
        "walls": walls,
        "docks": docks,
        "quay": quay,
        "apron": apron,
        "basin": basin,
        "berths": berths,
        "heads": heads,
        "shore_ends": (left_coast, right_coast),
        "collision_polygons": collision_polygons,
        "axis": axis,
        "perpendicular": perpendicular,
        "half_width": half_width,
        "end_distance": end_distance,
        "shore_to_berth": shore_to_berth,
        "apron_half_width": apron_half_width,
        "apron_depth": apron_depth,
    }


def harbour_wall_contact(x, y, radius, port, berth_count, berth_spacing):
    from .geometry import nearest_polygon_edge

    for polygon in harbour_layout(port, berth_count, berth_spacing)["collision_polygons"]:
        if point_in_polygon((x, y), polygon):
            return True
        _, distance = nearest_polygon_edge(x, y, polygon)
        if distance <= radius:
            return True
    return False
