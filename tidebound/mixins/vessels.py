from ..common import *


class VesselsMixin:
    def fire_broadside(self, side):
        if self.docked_port or self.conversation or self.journal_open or self.shipyard_open:
            return
        if self.cannon_cooldowns[side] > 0:
            return
        heading = math.radians(self.ship_heading)
        forward = (math.cos(heading), math.sin(heading))
        broadside_angle = heading + side * math.pi / 2
        broadside = (math.cos(broadside_angle), math.sin(broadside_angle))
        stats = self.player_ship_stats()
        gun_count = stats["guns"] + self.upgrades["cannons"]
        spacing = 14.0
        for index in range(gun_count):
            offset = (index - (gun_count - 1) / 2) * spacing
            x = self.ship_x + forward[0] * offset + broadside[0] * 18
            y = self.ship_y + forward[1] * offset + broadside[1] * 18
            vx = broadside[0] * 480 + self.ship_vx * 0.18
            vy = broadside[1] * 480 + self.ship_vy * 0.18
            self.projectiles.append(Cannonball(x, y, vx, vy, 1.45, "player"))
        self.cannon_cooldowns[side] = stats["reload"] * max(0.72, 1.0 - self.upgrades["cannons"] * 0.07)
        self.toast_message("BOOM! Port broadside!" if side < 0 else "BOOM! Starboard broadside!", 1.2)

    def update_player_sailing(self, dt):
        if self.docked_port:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.sail_setting = clamp(self.sail_setting + 0.58 * dt, 0.0, 1.0)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.sail_setting = clamp(self.sail_setting - 0.75 * dt, 0.0, 1.0)
        rudder = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            rudder -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            rudder += 1.0
        speed = math.hypot(self.ship_vx, self.ship_vy)
        stats = self.player_ship_stats()
        turn_rate = (7.0 + min(speed, 170.0) * 0.19) * stats["turn"] * (1.0 + self.upgrades["rudder"] * 0.12)
        self.ship_heading = (self.ship_heading + rudder * turn_rate * dt) % 360.0
        angle = math.radians(self.ship_heading)
        forward = (math.cos(angle), math.sin(angle))
        side = (-forward[1], forward[0])
        thrust, wind_power, sail_thrust, oar_thrust = calculate_propulsion(
            self.ship_heading,
            self.wind_angle,
            self.sail_setting,
            self.wind_strength,
            self.upgrades["rigging"],
            self.oars_deployed,
            stats.get("oar_power", 34.0),
            self.world_time,
        )
        self.ship_vx += forward[0] * thrust * dt
        self.ship_vy += forward[1] * thrust * dt
        forward_speed = self.ship_vx * forward[0] + self.ship_vy * forward[1]
        lateral_speed = self.ship_vx * side[0] + self.ship_vy * side[1]
        lateral_speed *= math.exp(-0.92 * dt)
        forward_speed *= math.exp(-0.115 * dt)
        self.ship_vx = forward[0] * forward_speed + side[0] * lateral_speed
        self.ship_vy = forward[1] * forward_speed + side[1] * lateral_speed
        current_speed = math.hypot(self.ship_vx, self.ship_vy)
        max_speed = stats["speed"] * (1.0 + self.upgrades["rigging"] * 0.08)
        if current_speed > max_speed:
            factor = max_speed / current_speed
            self.ship_vx *= factor
            self.ship_vy *= factor
        self.ship_x += self.ship_vx * dt
        self.ship_y += self.ship_vy * dt
        self.ship_x = clamp(self.ship_x, 24, WORLD_WIDTH - 24)
        self.ship_y = clamp(self.ship_y, 24, WORLD_HEIGHT - 24)
        self.ship_x, self.ship_y, self.ship_vx, self.ship_vy, collided = resolve_land_collision(
            self.ship_x, self.ship_y, self.ship_vx, self.ship_vy, PLAYER_RADIUS, self.collision_land_polygons()
        )
        if collided and not getattr(self, "shore_warning", False):
            self.toast_message("Shore! The hull scrapes the shallows.", 1.7)
            self.shore_warning = True
        if not collided:
            self.shore_warning = False
        self.near_port = None
        nearest_distance = 130.0
        for port in self.ports:
            distance = math.hypot(self.ship_x - port.x, self.ship_y - port.y)
            if distance < nearest_distance:
                nearest_distance = distance
                self.near_port = port

    def spawn_pirate_reinforcement(self):
        names = [
            "The Salt Widow", "The Crimson Gull", "The Ragged Crown", "The Laughing Mary",
            "The Cutlass Rose", "The Storm Petrel", "The Black Marlin", "The Mercy's End",
        ]
        position = None
        for _ in range(240):
            x = self.rng.uniform(150, WORLD_WIDTH - 150)
            y = self.rng.uniform(150, WORLD_HEIGHT - 150)
            if any(point_in_polygon((x, y), polygon) for polygon in self.collision_land_polygons()):
                continue
            if math.hypot(x - self.ship_x, y - self.ship_y) < 720:
                continue
            if any(math.hypot(x - port.x, y - port.y) < 260 for port in self.ports):
                continue
            position = (x, y)
            break
        if position is None:
            return
        x, y = position
        heading = math.degrees(math.atan2(self.ship_y - y, self.ship_x - x))
        name = names[(self.reinforcement_number - 1) % len(names)]
        if self.reinforcement_number > len(names):
            name = f"{name} {self.reinforcement_number}"
        self.pirates.append(
            PirateShip(name, x, y, heading, hull=6, max_hull=6, side_choice=self.rng.choice([-1, 1]), wander=self.rng.random() * 6.0)
        )
        self.reinforcement_number += 1
        self.toast_message("A fresh pirate sail has appeared on the horizon!", 2.8)

    def update_pirates(self, dt):
        if self.docked_port or self.conversation or self.journal_open or self.shipyard_open:
            return
        active_count = sum(not pirate.dead for pirate in self.pirates)
        active_mission = self.active_mission()
        combat_mission_active = bool(active_mission and active_mission.objective_type == "kills")
        reinforcement_delay = 45.0
        if not combat_mission_active and active_count < 2:
            self.reinforcement_timer -= dt
            if self.reinforcement_timer <= 0:
                self.spawn_pirate_reinforcement()
                self.reinforcement_timer = reinforcement_delay
        elif not combat_mission_active:
            self.reinforcement_timer = reinforcement_delay
        for pirate in self.pirates:
            if pirate.dead:
                continue
            pirate.cooldown = max(0.0, pirate.cooldown - dt)
            distance = math.hypot(self.ship_x - pirate.x, self.ship_y - pirate.y)
            dx = self.ship_x - pirate.x
            dy = self.ship_y - pirate.y
            bearing = math.degrees(math.atan2(dy, dx))
            if pirate.objective_target:
                if distance > 430:
                    desired = bearing
                else:
                    side_a = bearing - 90
                    side_b = bearing + 90
                    current_a = abs(angle_difference(side_a, pirate.heading))
                    current_b = abs(angle_difference(side_b, pirate.heading))
                    desired = side_a if current_a <= current_b else side_b
                thrust = 48.0 if distance < 1500 else 31.0
            elif distance < 1100:
                if distance > 430:
                    desired = bearing
                else:
                    side_a = bearing - 90
                    side_b = bearing + 90
                    current_a = abs(angle_difference(side_a, pirate.heading))
                    current_b = abs(angle_difference(side_b, pirate.heading))
                    desired = side_a if current_a <= current_b else side_b
                thrust = 36.0
            else:
                pirate.wander += dt * 0.22
                desired = pirate.heading + math.sin(pirate.wander) * 17.0
                thrust = 18.0
            difference = angle_difference(desired, pirate.heading)
            pirate.heading = (pirate.heading + clamp(difference, -43.0 * dt, 43.0 * dt)) % 360.0
            angle = math.radians(pirate.heading)
            pirate.vx += math.cos(angle) * thrust * dt
            pirate.vy += math.sin(angle) * thrust * dt
            pirate.vx *= math.exp(-0.11 * dt)
            pirate.vy *= math.exp(-0.11 * dt)
            speed = math.hypot(pirate.vx, pirate.vy)
            if speed > 135:
                pirate.vx *= 135 / speed
                pirate.vy *= 135 / speed
            pirate.x += pirate.vx * dt
            pirate.y += pirate.vy * dt
            pirate.x, pirate.y, pirate.vx, pirate.vy, _ = resolve_land_collision(
                pirate.x, pirate.y, pirate.vx, pirate.vy, 30, self.collision_land_polygons()
            )
            if 160 < distance < 560 and pirate.cooldown <= 0:
                self.enemy_fire_if_aligned(pirate, bearing, distance)

    def enemy_fire_if_aligned(self, pirate, bearing, distance):
        choices = []
        for side in (-1, 1):
            aim = (pirate.heading + side * 90.0) % 360.0
            choices.append((abs(angle_difference(bearing, aim)), side))
        alignment, side = min(choices)
        if alignment > 22:
            return
        angle = math.radians(pirate.heading)
        forward = (math.cos(angle), math.sin(angle))
        broadside_angle = angle + side * math.pi / 2
        broadside = (math.cos(broadside_angle), math.sin(broadside_angle))
        for offset in (-16, 0, 16):
            x = pirate.x + forward[0] * offset + broadside[0] * 17
            y = pirate.y + forward[1] * offset + broadside[1] * 17
            vx = broadside[0] * 370 + pirate.vx * 0.14
            vy = broadside[1] * 370 + pirate.vy * 0.14
            self.projectiles.append(Cannonball(x, y, vx, vy, 1.45, "enemy"))
        pirate.cooldown = 2.8 + self.rng.random() * 0.7

    def update_projectiles(self, dt):
        remaining = []
        for ball in self.projectiles:
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt
            ball.life -= dt
            if ball.life <= 0 or ball.x < 0 or ball.y < 0 or ball.x > WORLD_WIDTH or ball.y > WORLD_HEIGHT:
                continue
            if any(point_in_polygon((ball.x, ball.y), polygon) for polygon in self.collision_land_polygons()):
                continue
            if ball.owner in {"player", "fleet"}:
                hit = False
                for pirate in self.pirates:
                    if pirate.dead:
                        continue
                    if math.hypot(ball.x - pirate.x, ball.y - pirate.y) < 25:
                        pirate.hull -= 1
                        hit = True
                        if pirate.hull <= 0:
                            pirate.dead = True
                            self.register_pirate_sunk(pirate)
                        else:
                            self.toast_message(f"Hit {pirate.name}! Hull remaining: {pirate.hull}.", 1.3)
                        break
                if hit:
                    continue
            elif not self.docked_port:
                if math.hypot(ball.x - self.ship_x, ball.y - self.ship_y) < 23:
                    self.player_hull = max(0, self.player_hull - 11)
                    self.toast_message(f"Enemy broadside hit! Hull: {int(100 * self.player_hull / max(1, self.player_max_hull))}%", 1.4)
                    if self.player_hull <= 0:
                        self.player_sunk()
                    continue
                escort_hit = next((escort for escort in self.fleet if escort.hull > 0 and math.hypot(ball.x - escort.x, ball.y - escort.y) < 23), None)
                if escort_hit:
                    escort_hit.hull = max(0, escort_hit.hull - 11)
                    if escort_hit.hull == 0:
                        self.toast_message(f"{escort_hit.name} is disabled! Return to a shipyard for repairs.", 3.2)
                    else:
                        self.toast_message(f"{escort_hit.name} takes a hit. Hull: {escort_hit.hull}/{escort_hit.max_hull}.", 2.0)
                    continue
            remaining.append(ball)
        self.projectiles = remaining

    def player_sunk(self):
        penalty = min(90, self.gold)
        self.gold -= penalty
        port = min(self.ports, key=lambda item: math.hypot(item.x - self.ship_x, item.y - self.ship_y))
        self.ship_x = port.x
        self.ship_y = port.y
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.ship_heading = port.exit_heading
        self.docked_port = port.name
        self.player_hull = max(1, int(self.player_max_hull * 0.55))
        self.projectiles = [ball for ball in self.projectiles if ball.owner != "enemy"]
        self.add_journal(f"Your ship was dismasted and towed to {port.name}. Lost {penalty} gold in repairs.")
        self.toast_message(f"Your ship was nearly sunk. Repairs at {port.name} cost {penalty} gold.", 5.0)

    def update(self, dt):
        self.world_time += dt
        self.toast_time = max(0.0, self.toast_time - dt)
        self.mission_result_timer = max(0.0, self.mission_result_timer - dt)
        self.wind_angle = 24.0 + math.sin(self.world_time * 0.035) * 11.0
        self.wind_strength = 0.92 + math.sin(self.world_time * 0.06) * 0.08
        for side in self.cannon_cooldowns:
            self.cannon_cooldowns[side] = max(0.0, self.cannon_cooldowns[side] - dt)
        if self.conversation or self.journal_open or self.treasure_chart_open or self.shipyard_open:
            return
        self.update_player_sailing(dt)
        self.update_fleet(dt)
        self.update_treasure_discovery()
        self.update_pirates(dt)
        self.update_projectiles(dt)
