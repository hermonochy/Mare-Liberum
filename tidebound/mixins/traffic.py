from ..common import *


class TrafficMixin:
    TRAFFIC_ROLES = {
        "merchant": {
            "names": ["Golden Finch", "Grace of Bridgetown", "Three Sisters", "Dawn Trader", "Providence", "Cane Blossom"],
            "types": ["Schooner", "Brigantine", "Frigate"],
            "hull": 7,
            "speed": 58.0,
        },
        "fishing": {
            "names": ["Little Minnow", "Net and Needle", "Morning Catch", "Blue Mackerel", "Sea Lark"],
            "types": ["Sloop", "Cutter"],
            "hull": 4,
            "speed": 66.0,
        },
        "naval patrol": {
            "names": ["HMS Resolute", "HMS Sparrowhawk", "HMS Vigilant", "La Centinela"],
            "types": ["Brigantine", "Frigate"],
            "hull": 9,
            "speed": 61.0,
        },
        "mail packet": {
            "names": ["Swift Dispatch", "King's Letter", "Morning Star", "The Post Boy"],
            "types": ["Cutter", "Schooner"],
            "hull": 5,
            "speed": 78.0,
        },
        "whaler": {
            "names": ["Northern Light", "White Whale", "Moby's Luck", "Harpooner"],
            "types": ["Brigantine", "Schooner"],
            "hull": 8,
            "speed": 48.0,
        },
    }

    SHIP_COLLISION_RADII = {
        "Sloop": 52.0,
        "Cutter": 50.0,
        "Schooner": 55.0,
        "Brigantine": 58.0,
        "Frigate": 62.0,
    }

    def initialise_traffic_ships(self, count=6):
        self.traffic_ships = []
        for _ in range(count):
            self.spawn_traffic_ship()

    def choose_traffic_destination(self, exclude=None):
        choices = [port for port in self.ports if port.name != exclude]
        return self.rng.choice(choices) if choices else None

    def spawn_traffic_ship(self):
        if len(self.traffic_ships) >= 18:
            return False
        roles = list(self.TRAFFIC_ROLES)
        weights = [42, 23, 14, 15, 6]
        role = self.rng.choices(roles, weights=weights, k=1)[0]
        profile = self.TRAFFIC_ROLES[role]
        destination = self.choose_traffic_destination()
        if destination is None:
            return False
        position = None
        for _ in range(1400):
            x = self.rng.uniform(260.0, WORLD_WIDTH - 260.0)
            y = self.rng.uniform(260.0, WORLD_HEIGHT - 260.0)
            if math.hypot(x - self.ship_x, y - self.ship_y) < 620.0:
                continue
            if any(point_in_polygon((x, y), polygon) for polygon in self.collision_land_polygons()):
                continue
            if any(nearest_polygon_edge(x, y, polygon)[1] < 86.0 for polygon in self.land):
                continue
            if any(math.hypot(x - port.x, y - port.y) < 190.0 for port in self.ports):
                continue
            if any(math.hypot(x - ship.x, y - ship.y) < 150.0 for ship in self.traffic_ships):
                continue
            if any(ship.hull > 0 and math.hypot(x - ship.x, y - ship.y) < 145.0 for ship in self.fleet):
                continue
            if any(not pirate.dead and math.hypot(x - pirate.x, y - pirate.y) < 150.0 for pirate in self.pirates):
                continue
            position = (x, y)
            break
        if position is None:
            return False
        x, y = position
        heading = math.degrees(math.atan2(destination.y - y, destination.x - x)) % 360.0
        name = self.rng.choice(profile["names"])
        self.traffic_ships.append(
            TrafficShip(
                name=f"{name} {self.traffic_serial}",
                role=role,
                ship_type=self.rng.choice(profile["types"]),
                x=x,
                y=y,
                heading=heading,
                destination=destination.name,
                hull=profile["hull"],
                max_hull=profile["hull"],
                wander=self.rng.random() * math.tau,
            )
        )
        self.traffic_serial += 1
        return True

    def update_traffic_ships(self, dt):
        self.traffic_spawn_timer -= dt
        if self.traffic_spawn_timer <= 0.0:
            self.spawn_traffic_ship()
            self.traffic_spawn_timer = self.rng.uniform(22.0, 36.0)

        land_polygons = self.collision_land_polygons()
        for ship in list(self.traffic_ships):
            if ship.hull <= 0:
                continue
            destination = self.ports_by_name.get(ship.destination)
            if destination is None:
                destination = self.choose_traffic_destination()
                if destination is None:
                    continue
                ship.destination = destination.name
            dx = destination.x - ship.x
            dy = destination.y - ship.y
            distance = math.hypot(dx, dy)
            if distance < 165.0:
                destination = self.choose_traffic_destination(ship.destination)
                if destination is not None:
                    ship.destination = destination.name
                    dx = destination.x - ship.x
                    dy = destination.y - ship.y
                    distance = max(1.0, math.hypot(dx, dy))
            desired = math.degrees(math.atan2(dy, dx))
            difference = angle_difference(desired, ship.heading)
            turn_rate = 25.0 if ship.role == "whaler" else 34.0
            ship.heading = (ship.heading + clamp(difference, -turn_rate * dt, turn_rate * dt)) % 360.0
            heading = math.radians(ship.heading)
            profile = self.TRAFFIC_ROLES[ship.role]
            ship.vx += math.cos(heading) * profile["speed"] * 0.62 * dt
            ship.vy += math.sin(heading) * profile["speed"] * 0.62 * dt
            drag = math.exp(-0.10 * dt)
            ship.vx *= drag
            ship.vy *= drag
            speed = math.hypot(ship.vx, ship.vy)
            maximum = profile["speed"]
            if speed > maximum:
                ship.vx *= maximum / speed
                ship.vy *= maximum / speed
            ship.x += ship.vx * dt
            ship.y += ship.vy * dt
            old_heading = ship.heading
            ship.x, ship.y, ship.vx, ship.vy, collided = resolve_land_collision(
                ship.x, ship.y, ship.vx, ship.vy, self.SHIP_COLLISION_RADII.get(ship.ship_type, 32.0), land_polygons
            )
            if collided:
                ship.heading = (old_heading + self.rng.choice([-1, 1]) * self.rng.uniform(48.0, 82.0)) % 360.0
                ship.vx *= 0.42
                ship.vy *= 0.42

    def _ship_collision_bodies(self):
        bodies = []
        bodies.append({
            "entity": self,
            "x_key": "ship_x", "y_key": "ship_y", "vx_key": "ship_vx", "vy_key": "ship_vy",
            "radius": self.SHIP_COLLISION_RADII.get(self.current_ship, 34.0) + 3.0,
            "mass": max(1.0, self.player_max_hull / 95.0), "player": True,
            "static": bool(self.docked_port),
        })
        for ship in self.fleet:
            if ship.hull > 0:
                bodies.append({
                    "entity": ship, "x_key": "x", "y_key": "y", "vx_key": "vx", "vy_key": "vy",
                    "radius": self.SHIP_COLLISION_RADII.get(ship.ship_type, 32.0),
                    "mass": max(0.9, ship.max_hull / 100.0), "player": False, "static": False,
                })
        for ship in self.pirates:
            if not ship.dead:
                bodies.append({
                    "entity": ship, "x_key": "x", "y_key": "y", "vx_key": "vx", "vy_key": "vy",
                    "radius": self.SHIP_COLLISION_RADII.get(ship.ship_type, 32.0),
                    "mass": max(0.9, ship.max_hull / 6.5), "player": False, "static": False,
                })
        for ship in self.traffic_ships:
            if ship.hull > 0:
                bodies.append({
                    "entity": ship, "x_key": "x", "y_key": "y", "vx_key": "vx", "vy_key": "vy",
                    "radius": self.SHIP_COLLISION_RADII.get(ship.ship_type, 32.0),
                    "mass": max(0.9, ship.max_hull / 6.5), "player": False, "static": False,
                })
        return bodies

    @staticmethod
    def _body_value(body, key):
        return getattr(body["entity"], body[key])

    @staticmethod
    def _set_body_value(body, key, value):
        setattr(body["entity"], body[key], value)

    def resolve_ship_collisions(self, dt=0.04):
        bodies = self._ship_collision_bodies()
        if len(bodies) < 2:
            return
        cell_size = 144.0
        player_bumped = False
        for _ in range(5):
            buckets = {}
            for index, body in enumerate(bodies):
                x = self._body_value(body, "x_key")
                y = self._body_value(body, "y_key")
                cell = (math.floor(x / cell_size), math.floor(y / cell_size))
                buckets.setdefault(cell, []).append(index)
            checked = set()
            for cell, indexes in buckets.items():
                for offset_x in (-1, 0, 1):
                    for offset_y in (-1, 0, 1):
                        neighbour = (cell[0] + offset_x, cell[1] + offset_y)
                        for index_a in indexes:
                            for index_b in buckets.get(neighbour, ()):
                                if index_a >= index_b:
                                    continue
                                pair = (index_a, index_b)
                                if pair in checked:
                                    continue
                                checked.add(pair)
                                a, b = bodies[index_a], bodies[index_b]
                                ax = self._body_value(a, "x_key")
                                ay = self._body_value(a, "y_key")
                                bx = self._body_value(b, "x_key")
                                by = self._body_value(b, "y_key")
                                dx, dy = bx - ax, by - ay
                                distance = math.hypot(dx, dy)
                                minimum = a["radius"] + b["radius"]
                                if distance >= minimum:
                                    continue
                                if distance < 0.001:
                                    angle = (index_a * 2.399963229728653 + index_b) % math.tau
                                    nx, ny, distance = math.cos(angle), math.sin(angle), 0.001
                                else:
                                    nx, ny = dx / distance, dy / distance
                                overlap = minimum - distance + 0.8
                                inverse_a = 0.0 if a["static"] else 1.0 / max(0.25, a["mass"])
                                inverse_b = 0.0 if b["static"] else 1.0 / max(0.25, b["mass"])
                                inverse_total = inverse_a + inverse_b
                                if inverse_total <= 0.0:
                                    continue
                                move_a = overlap * inverse_a / inverse_total
                                move_b = overlap * inverse_b / inverse_total
                                self._set_body_value(a, "x_key", ax - nx * move_a)
                                self._set_body_value(a, "y_key", ay - ny * move_a)
                                self._set_body_value(b, "x_key", bx + nx * move_b)
                                self._set_body_value(b, "y_key", by + ny * move_b)
                                avx = self._body_value(a, "vx_key")
                                avy = self._body_value(a, "vy_key")
                                bvx = self._body_value(b, "vx_key")
                                bvy = self._body_value(b, "vy_key")
                                relative_normal = (bvx - avx) * nx + (bvy - avy) * ny
                                if relative_normal < 0.0:
                                    restitution = 0.58
                                    impulse = -(1.0 + restitution) * relative_normal / inverse_total
                                    avx -= impulse * inverse_a * nx
                                    avy -= impulse * inverse_a * ny
                                    bvx += impulse * inverse_b * nx
                                    bvy += impulse * inverse_b * ny
                                    self._set_body_value(a, "vx_key", avx)
                                    self._set_body_value(a, "vy_key", avy)
                                    self._set_body_value(b, "vx_key", bvx)
                                    self._set_body_value(b, "vy_key", bvy)
                                if a["player"] or b["player"]:
                                    player_bumped = True
        if player_bumped and self.ship_collision_notice_timer <= 0.0:
            self.toast_message("Ships collide! The hulls glance apart and both vessels are knocked off course.", 2.4)
            self.ship_collision_notice_timer = 2.5
        self.ship_collision_notice_timer = max(0.0, self.ship_collision_notice_timer - dt)
