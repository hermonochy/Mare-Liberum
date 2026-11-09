from ..common import *


class ReefsMixin:
    """Static navigational hazards with readable chart markings and NPC avoidance."""

    REEF_ANCHORS = [
        (9150, 3450), (9450, 5150), (10850, 5650), (11650, 7050),
        (11650, 8750), (12350, 10150), (2900, 5200), (3150, 8950),
        (7100, 1450), (10100, 1750), (17250, 1150), (18800, 5350),
        (19000, 8650), (14500, 10800), (5200, 10450), (1750, 5650),
        (8500, 10400), (11900, 4450), (1950, 1850), (18300, 10800),
    ]

    def make_reef_polygon(self, cx, cy, rx, ry, rotation, seed):
        rng = random.Random(seed)
        points = []
        count = 14
        for index in range(count):
            angle = rotation + math.tau * index / count
            irregularity = 1.0 + 0.10 * math.sin(angle * 3.0 + seed * 0.017) + rng.uniform(-0.055, 0.055)
            points.append((cx + math.cos(angle) * rx * irregularity,
                           cy + math.sin(angle) * ry * irregularity))
        return points

    def add_reefs(self):
        """Place reef patches in navigable channels, safely clear of land and harbours."""
        self.reefs = []
        rng = random.Random(5272026)
        land = list(self.land) + [site.polygon for site in getattr(self, "treasure_sites", [])]
        port_positions = [(port.x, port.y) for port in self.ports]
        names = [
            "The Red Shoals", "Gannet Teeth", "Widowmaker Reef", "The Broken Spit",
            "Pilots' Peril", "The Glass Banks", "Three Sisters Shoal", "The Drowned Garden",
            "Saint Elmo's Teeth", "The Pale Horses", "The Blind Passage", "Copperhead Bank",
            "The Long Coral", "The Wrecker's Table", "The Lantern Shoal", "The Blue Knuckles",
            "The Shattered Shelf", "The Low Crown", "The Needle Rocks", "The Red Anvil",
        ]
        accepted = []

        def clear_candidate(poly, cx, cy, rx, ry):
            # Reef warning zones must not touch land or treasure cays.
            for polygon in land:
                if point_in_polygon((cx, cy), polygon):
                    return False
                _, center_gap = nearest_polygon_edge(cx, cy, polygon)
                if center_gap < max(rx, ry) + 58.0:
                    return False
            # Keep a generous navigable throat around every harbour entrance.
            for px, py in port_positions:
                if math.hypot(cx - px, cy - py) < max(rx, ry) + 330.0:
                    return False
            # Don't let adjacent reef patches merge into one enormous hazard.
            for other in accepted:
                if math.hypot(cx - other.center_x, cy - other.center_y) < rx + other.radius_x + 100.0:
                    return False
            return True

        for index, (anchor_x, anchor_y) in enumerate(self.REEF_ANCHORS):
            chosen = None
            # Try the authored shoal location first, then move within its local
            # passage if the current island/port geometry leaves too little room.
            for attempt in range(260):
                if attempt == 0:
                    cx, cy = float(anchor_x), float(anchor_y)
                else:
                    angle = rng.uniform(0.0, math.tau)
                    spread = 90.0 + 4.0 * attempt
                    cx = anchor_x + math.cos(angle) * rng.uniform(0.0, spread)
                    cy = anchor_y + math.sin(angle) * rng.uniform(0.0, spread * 0.72)
                if not (260.0 < cx < WORLD_WIDTH / WORLD_SCALE - 260.0 and
                        260.0 < cy < WORLD_HEIGHT / WORLD_SCALE - 260.0):
                    continue
                rx = rng.uniform(128.0, 176.0)
                ry = rng.uniform(54.0, 82.0)
                rotation = rng.uniform(-0.42, 0.42)
                polygon = self.make_reef_polygon(cx, cy, rx, ry, rotation, 1800 + index * 91 + attempt)
                if not clear_candidate(polygon, cx, cy, rx, ry):
                    continue
                # Sample the full outline so no sharp reef point clips a coast.
                outline_clear = True
                for edge_index, point in enumerate(polygon):
                    next_point = polygon[(edge_index + 1) % len(polygon)]
                    samples = (point, ((point[0] + next_point[0]) * 0.5, (point[1] + next_point[1]) * 0.5))
                    for sample in samples:
                        if any(point_in_polygon(sample, shore) or nearest_polygon_edge(sample[0], sample[1], shore)[1] < 36.0 for shore in land):
                            outline_clear = False
                            break
                    if not outline_clear:
                        break
                if not outline_clear:
                    continue
                if any(point_in_polygon((px, py), polygon) or nearest_polygon_edge(px, py, polygon)[1] < 260.0
                       for px, py in port_positions):
                    continue
                bounds = (min(x for x, _ in polygon), min(y for _, y in polygon),
                          max(x for x, _ in polygon), max(y for _, y in polygon))
                chosen = Reef(names[index], polygon, cx, cy, rx, ry, bounds)
                break
            if chosen is not None:
                accepted.append(chosen)

        # A second deterministic pass fills gaps if an authored point was too
        # close to a port. It still applies exactly the same coast/port checks.
        filler_attempt = 0
        while len(accepted) < 14 and filler_attempt < 1800:
            filler_attempt += 1
            cx = rng.uniform(700.0, WORLD_WIDTH / WORLD_SCALE - 700.0)
            cy = rng.uniform(700.0, WORLD_HEIGHT / WORLD_SCALE - 700.0)
            rx, ry = rng.uniform(128.0, 168.0), rng.uniform(54.0, 78.0)
            polygon = self.make_reef_polygon(cx, cy, rx, ry, rng.uniform(-0.5, 0.5), 90000 + filler_attempt)
            if not clear_candidate(polygon, cx, cy, rx, ry):
                continue
            if any(point_in_polygon(point, shore) or nearest_polygon_edge(point[0], point[1], shore)[1] < 36.0
                   for shore in land for point in polygon):
                continue
            if any(math.hypot(px - cx, py - cy) < max(rx, ry) + 330.0 for px, py in port_positions):
                continue
            bounds = (min(x for x, _ in polygon), min(y for _, y in polygon),
                      max(x for x, _ in polygon), max(y for _, y in polygon))
            accepted.append(Reef(names[len(accepted) % len(names)], polygon, cx, cy, rx, ry, bounds))

        self.reefs = accepted
        self.reef_damage_notice_timer = 0.0
        return len(self.reefs)

    def reef_clear_at(self, x, y, clearance=75.0):
        """Return True only if a ship-sized spawn point is outside every shoal."""
        for reef in getattr(self, "reefs", []):
            min_x, min_y, max_x, max_y = reef.bounds
            if x < min_x - clearance or x > max_x + clearance or y < min_y - clearance or y > max_y + clearance:
                continue
            if point_in_polygon((x, y), reef.polygon):
                return False
            _, edge_distance = nearest_polygon_edge(x, y, reef.polygon)
            if edge_distance < clearance:
                return False
        return True

    def find_safe_water_position(self, x, y, clearance=100.0, max_radius=1700.0):
        """Find nearby open water for an older saved NPC that now overlaps a new reef."""
        def safe(px, py):
            if not (80.0 < px < WORLD_WIDTH - 80.0 and 80.0 < py < WORLD_HEIGHT - 80.0):
                return False
            if not self.reef_clear_at(px, py, clearance):
                return False
            for polygon in self.collision_land_polygons():
                if point_in_polygon((px, py), polygon):
                    return False
                if nearest_polygon_edge(px, py, polygon)[1] < 65.0:
                    return False
            return True

        if safe(x, y):
            return x, y
        for radius in range(100, int(max_radius) + 1, 90):
            for step in range(32):
                angle = math.tau * step / 32.0
                px = x + math.cos(angle) * radius
                py = y + math.sin(angle) * radius
                if safe(px, py):
                    return px, py
        return None

    def reef_contact(self, x, y, ship_radius=30.0):
        """Return a reef if the vessel's hull overlaps its marked shoal area."""
        for reef in getattr(self, "reefs", []):
            min_x, min_y, max_x, max_y = reef.bounds
            if x < min_x - ship_radius or x > max_x + ship_radius or y < min_y - ship_radius or y > max_y + ship_radius:
                continue
            if point_in_polygon((x, y), reef.polygon):
                return reef
            _, edge_distance = nearest_polygon_edge(x, y, reef.polygon)
            if edge_distance <= ship_radius:
                return reef
        return None

    def apply_reef_damage(self, vessel, dt, kind="npc", ship_radius=30.0):
        x = self.ship_x if kind == "player" else vessel.x
        y = self.ship_y if kind == "player" else vessel.y
        reef = self.reef_contact(x, y, ship_radius)
        if reef is None:
            return False
        speed = (math.hypot(self.ship_vx, self.ship_vy) if kind == "player"
                 else math.hypot(getattr(vessel, "vx", 0.0), getattr(vessel, "vy", 0.0)))
        if kind == "player":
            damage_rate = 1.1 + min(speed, 210.0) * 0.010
            self.player_hull = max(0.0, self.player_hull - damage_rate * dt)
            self.reef_damage_notice_timer = max(0.0, self.reef_damage_notice_timer - dt)
            if self.reef_damage_notice_timer <= 0.0:
                self.toast_message(f"REEF! Coral and rock scrape your hull near {reef.name}.", 2.5)
                self.reef_damage_notice_timer = 2.2
            if self.player_hull <= 0:
                self.player_sunk()
            return True

        max_hull = max(1.0, float(getattr(vessel, "max_hull", 1)))
        if max_hull <= 12:
            damage_rate = 0.10 + min(speed, 145.0) * 0.0015
        else:
            damage_rate = 0.55 + min(speed, 210.0) * 0.0045
        before = getattr(vessel, "hull", 0)
        vessel.hull = max(0.0, before - damage_rate * dt)
        if before > 0 and vessel.hull <= 0:
            self.record_commander_ship_loss(vessel, f"the reef at {reef.name}")
            if isinstance(vessel, PirateShip):
                vessel.dead = True
                self.add_journal(f"{vessel.name} was wrecked on {reef.name}.")
            elif vessel in getattr(self, "traffic_ships", []):
                self.add_journal(f"{vessel.name} was wrecked on {reef.name}.")
            else:
                self.toast_message(f"{getattr(vessel, 'name', 'An escort')} is wrecked on {reef.name}.", 3.0)
        return True

    def reef_avoidance_heading(self, x, y, desired_heading, lookahead=640.0, clearance=125.0):
        """Choose a nearby course that skirts marked reefs instead of blindly crossing them."""
        reefs = getattr(self, "reefs", [])
        if not reefs:
            return desired_heading % 360.0
        best_heading = desired_heading % 360.0
        best_score = float("inf")
        for offset in (0, -18, 18, -36, 36, -56, 56, -78, 78, -105, 105, 180):
            candidate = (desired_heading + offset) % 360.0
            angle = math.radians(candidate)
            dx, dy = math.cos(angle), math.sin(angle)
            score = abs(offset) * 1.35
            for distance in (140.0, 280.0, 420.0, 560.0, lookahead):
                px, py = x + dx * distance, y + dy * distance
                for reef in reefs:
                    min_x, min_y, max_x, max_y = reef.bounds
                    if px < min_x - clearance or px > max_x + clearance or py < min_y - clearance or py > max_y + clearance:
                        continue
                    if point_in_polygon((px, py), reef.polygon):
                        score += 2600.0 + (lookahead - distance) * 0.8
                        continue
                    _, edge_distance = nearest_polygon_edge(px, py, reef.polygon)
                    if edge_distance < clearance:
                        score += (clearance - edge_distance) * 7.0
            if score < best_score:
                best_score, best_heading = score, candidate
        return best_heading

    def apply_reef_course_to_vector(self, vessel, desired_heading, lookahead=640.0):
        return self.reef_avoidance_heading(vessel.x, vessel.y, desired_heading, lookahead)
