from ..common import *


class VesselsMixin:
    def spawn_cannon_smoke(self, x, y, direction_x, direction_y, amount=5):
        if not hasattr(self, "cannon_smoke"):
            self.cannon_smoke = []
        for _ in range(amount):
            life = self.rng.uniform(0.45, 0.82)
            self.cannon_smoke.append({
                "x": float(x) + self.rng.uniform(-4.0, 4.0),
                "y": float(y) + self.rng.uniform(-4.0, 4.0),
                "vx": direction_x * self.rng.uniform(12.0, 30.0) + self.rng.uniform(-12.0, 12.0),
                "vy": direction_y * self.rng.uniform(12.0, 30.0) + self.rng.uniform(-12.0, 12.0),
                "life": life, "max_life": life,
                "radius": self.rng.uniform(5.0, 9.0),
                "growth": self.rng.uniform(15.0, 24.0),
            })

    def update_cannon_smoke(self, dt):
        remaining = []
        for puff in getattr(self, "cannon_smoke", []):
            puff["life"] -= dt
            if puff["life"] <= 0.0:
                continue
            puff["x"] += puff["vx"] * dt
            puff["y"] += puff["vy"] * dt
            puff["vx"] *= math.exp(-1.7 * dt)
            puff["vy"] *= math.exp(-1.7 * dt)
            puff["radius"] += puff["growth"] * dt
            remaining.append(puff)
        self.cannon_smoke = remaining[-140:]

    def apply_cannon_recoil(self, vessel, broadside_x, broadside_y, impulse):
        # The flagship stores velocity with ship_ prefixes; NPC hull records
        # use ordinary vx/vy fields.
        if vessel is self:
            self.ship_vx -= broadside_x * impulse
            self.ship_vy -= broadside_y * impulse
        else:
            vessel.vx -= broadside_x * impulse
            vessel.vy -= broadside_y * impulse

    def set_cannon_held(self, side, held):
        if held:
            if self.docked_port or self.conversation or self.journal_open or self.shipyard_open or self.job_board_open or self.world_map_open or getattr(self, "diplomacy_open", False):
                return
            if not self.cannon_held[side]:
                self.cannon_held[side] = True
                if not self.cannon_first_volley_fired[side]:
                    self.fire_broadside(side)
                else:
                    self.ensure_cannon_battery(side)
                    timers = self.cannon_battery_timers[side]
                    rates = self.cannon_battery_rates[side]
                    for index, timer in enumerate(timers):
                        if timer <= 0.0:
                            timers[index] = rates[index] * self.rng.uniform(0.08, 0.58)
        else:
            self.cannon_held[side] = False

    def ensure_cannon_battery(self, side):
        stats = self.player_ship_stats()
        gun_count = stats["guns"] + self.upgrades["cannons"]
        timers = self.cannon_battery_timers[side]
        rates = self.cannon_battery_rates[side]
        base_reload = stats["reload"] * max(0.72, 1.0 - self.upgrades["cannons"] * 0.07)
        while len(timers) < gun_count:
            rate = base_reload * self.rng.uniform(0.84, 1.16)
            rates.append(rate)
            timers.append(self.rng.uniform(0.4, 1.2) * rate if self.cannon_first_volley_fired[side] else 0.0)
        if len(timers) > gun_count:
            del timers[gun_count:]
            del rates[gun_count:]
        return gun_count

    def fire_single_cannon(self, side, gun_index, gun_count, show_effect=False):
        heading = math.radians(self.ship_heading)
        forward = (math.cos(heading), math.sin(heading))
        broadside_angle = heading + side * math.pi / 2
        broadside = (math.cos(broadside_angle), math.sin(broadside_angle))
        spacing = 13.0
        offset = (gun_index - (gun_count - 1) / 2) * spacing
        x = self.ship_x + forward[0] * offset + broadside[0] * 19
        y = self.ship_y + forward[1] * offset + broadside[1] * 19
        vx = broadside[0] * 480 + self.ship_vx * 0.18
        vy = broadside[1] * 480 + self.ship_vy * 0.18
        self.projectiles.append(Cannonball(x, y, vx, vy, 1.45, "player"))
        self.apply_cannon_recoil(self, broadside[0], broadside[1], 12.0 / max(1, gun_count))
        self.spawn_cannon_smoke(x, y, broadside[0], broadside[1], amount=4)
        self.audio.play("cannon_fire", volume=0.30)
        if show_effect:
            self.toast_message("BOOM! Port broadside!" if side < 0 else "BOOM! Starboard broadside!", 1.2)

    def fire_broadside(self, side):
        if self.docked_port or self.conversation or self.journal_open or self.shipyard_open or self.job_board_open or self.world_map_open or getattr(self, "diplomacy_open", False):
            return
        gun_count = self.ensure_cannon_battery(side)
        for index in range(gun_count):
            self.fire_single_cannon(side, index, gun_count, show_effect=False)
            self.cannon_battery_timers[side][index] = self.cannon_battery_rates[side][index] * self.rng.uniform(0.72, 1.28)
        self.cannon_first_volley_fired[side] = True
        self.toast_message("BOOM! The whole port battery fires!" if side < 0 else "BOOM! The whole starboard battery fires!", 1.3)

    def update_player_cannons(self, dt):
        for side in (-1, 1):
            gun_count = self.ensure_cannon_battery(side)
            timers = self.cannon_battery_timers[side]
            rates = self.cannon_battery_rates[side]
            for index in range(gun_count):
                timers[index] = max(0.0, timers[index] - dt)
                if self.cannon_held[side] and timers[index] <= 0.0:
                    self.fire_single_cannon(side, index, gun_count)
                    timers[index] = rates[index] * self.rng.uniform(0.88, 1.16)

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

    def estimated_player_wealth(self):
        flagship_value = SHIP_CLASSES.get(self.current_ship, {}).get("cost", 0)
        escort_value = sum(SHIP_CLASSES.get(ship.ship_type, {}).get("cost", 0) for ship in self.fleet)
        upgrade_value = sum(self.upgrades.values()) * 220
        relic_value = len(self.relics) * 350
        return int(self.gold + flagship_value + escort_value * 0.65 + upgrade_value + relic_value)

    def pirate_reinforcement_interval(self):
        wealth = self.estimated_player_wealth()
        return max(32.0, 112.0 - min(80.0, max(0.0, wealth - 175.0) / 312.5))

    def pirate_reinforcement_group_size(self):
        wealth = self.estimated_player_wealth()
        return 1 + int(wealth >= 7000) + int(wealth >= 18000)

    def spawn_pirate_reinforcement(self):
        names = [
            "The Salt Widow", "The Crimson Gull", "The Ragged Crown", "The Laughing Mary",
            "The Cutlass Rose", "The Storm Petrel", "The Black Marlin", "The Mercy's End",
        ]
        spawned = 0
        group_size = self.pirate_reinforcement_group_size()
        for group_index in range(group_size):
            position = None
            for _ in range(300):
                angle = self.rng.uniform(0.0, math.tau)
                distance = self.rng.uniform(1180.0, 2480.0)
                x = self.ship_x + math.cos(angle) * distance
                y = self.ship_y + math.sin(angle) * distance
                if any(point_in_polygon((x, y), polygon) for polygon in self.collision_land_polygons()):
                    continue
                if math.hypot(x - self.ship_x, y - self.ship_y) < 850:
                    continue
                if any(math.hypot(x - port.x, y - port.y) < 300 for port in self.ports):
                    continue
                occupied = [pirate for pirate in self.pirates if not pirate.dead]
                occupied.extend(self.fleet)
                occupied.extend(getattr(self, "traffic_ships", []))
                if any(math.hypot(x - ship.x, y - ship.y) < 155 for ship in occupied):
                    continue
                if math.hypot(x - self.ship_x, y - self.ship_y) < 720:
                    continue
                position = (x, y)
                break
            if position is None:
                continue
            x, y = position
            heading = math.degrees(math.atan2(self.ship_y - y, self.ship_x - x))
            serial = self.reinforcement_number
            name = names[(serial - 1) % len(names)]
            if serial > len(names):
                name = f"{name} {serial}"
            hull = self.rng.choice([5, 6, 6, 7])
            new_pirate = PirateShip(
                name,
                x,
                y,
                heading,
                hull=hull,
                max_hull=hull,
                side_choice=self.rng.choice([-1, 1]),
                wander=self.rng.random() * 6.0,
                ship_type=self.rng.choice(["Cutter", "Schooner", "Brigantine"]),
            )
            new_pirate.player_attitude = self.npc_relation_label(new_pirate).lower()
            self.pirates.append(new_pirate)
            self.reinforcement_number += 1
            spawned += 1
        if spawned:
            wealth = self.estimated_player_wealth()
            self.toast_message(
                f"{spawned} pirate sail{'s' if spawned != 1 else ''} spotted. Your growing fortune ({wealth:,} gold in assets) is attracting attention!",
                3.8,
            )
        return spawned

    def update_pirates(self, dt):
        # Pirates remain part of the living world while the flagship is berthed
        # or the captain has a harbour panel open. They continue sailing, but
        # will not fire directly at a ship protected by a port's guns.
        active_mission = self.active_mission()
        combat_mission_active = bool(active_mission and active_mission.objective_type == "kills")
        if not combat_mission_active and not self.docked_port:
            self.reinforcement_timer -= dt
            if self.reinforcement_timer <= 0.0:
                self.spawn_pirate_reinforcement()
                self.reinforcement_timer = self.pirate_reinforcement_interval()
        for pirate in self.pirates:
            if pirate.dead:
                continue
            pirate.cooldown = max(0.0, pirate.cooldown - dt)
            npc_target = self._combat_target_for_pirate(pirate)
            if pirate.retreating:
                # Fleet-command logic has already pointed this vessel toward
                # a withdrawal course; preserve it and make way from the fight.
                distance = 9999.0
                bearing = pirate.heading
                desired = pirate.heading
                thrust = 43.0
            elif npc_target is not None and not pirate.objective_target:
                dx = npc_target.x - pirate.x
                dy = npc_target.y - pirate.y
                distance = math.hypot(dx, dy)
                bearing = math.degrees(math.atan2(dy, dx))
                desired = self._broadside_course(bearing, pirate.heading, distance)
                thrust = 39.0 if distance > 480.0 else (20.0 if distance > 285.0 else 27.0)
            else:
                distance = math.hypot(self.ship_x - pirate.x, self.ship_y - pirate.y)
                dx = self.ship_x - pirate.x
                dy = self.ship_y - pirate.y
                bearing = math.degrees(math.atan2(dy, dx))
            if not pirate.retreating and npc_target is None and not pirate.objective_target and getattr(pirate, "player_attitude", "neutral") != "hostile":
                # Neutral and friendly pirate captains leave the player alone;
                # a captain personally attacked by the player remembers the insult.
                pirate.wander += dt * 0.22
                desired = pirate.heading + math.sin(pirate.wander) * 17.0
                thrust = 18.0
            elif not pirate.retreating and npc_target is None and pirate.objective_target:
                if distance > 430:
                    desired = bearing
                else:
                    side_a = bearing - 90
                    side_b = bearing + 90
                    current_a = abs(angle_difference(side_a, pirate.heading))
                    current_b = abs(angle_difference(side_b, pirate.heading))
                    desired = side_a if current_a <= current_b else side_b
                thrust = 48.0 if distance < 1500 else 31.0
            elif not pirate.retreating and npc_target is None and distance < 1100:
                if distance > 430:
                    desired = bearing
                else:
                    side_a = bearing - 90
                    side_b = bearing + 90
                    current_a = abs(angle_difference(side_a, pirate.heading))
                    current_b = abs(angle_difference(side_b, pirate.heading))
                    desired = side_a if current_a <= current_b else side_b
                thrust = 36.0
            elif not pirate.retreating and npc_target is None:
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
            if (npc_target is None and not pirate.retreating and not self.docked_port
                    and 160 < distance < 560 and pirate.cooldown <= 0
                    and (pirate.objective_target or getattr(pirate, "player_attitude", "neutral") == "hostile")):
                self.enemy_fire_if_aligned(pirate, bearing, distance)

    def update_port_defences(self, dt):
        """Harbour guns defend against pirates and captains who have made an enemy of the port."""
        gun_range = 590.0
        reload_seconds = 1.55
        projectile_speed = 525.0
        cooldowns = getattr(self, "port_defence_cooldowns", None)
        if cooldowns is None:
            cooldowns = self.port_defence_cooldowns = {port.name: 0.0 for port in self.ports}
        self.port_defence_notice_timer = max(0.0, getattr(self, "port_defence_notice_timer", 0.0) - dt)
        living_pirates = [pirate for pirate in self.pirates if not pirate.dead]

        for port in self.ports:
            cooldown = max(0.0, cooldowns.get(port.name, 0.0) - dt)
            cooldowns[port.name] = cooldown
            if cooldown > 0.0:
                continue
            # A harbour battery normally engages pirate ships first. Pirate ports
            # protect their own waters, but will still fire on a player who is
            # hostile to the Brotherhood.
            pirate_candidates = []
            if port.faction != "Pirate Brotherhood":
                pirate_candidates = [
                    (math.hypot(pirate.x - port.x, pirate.y - port.y), pirate)
                    for pirate in living_pirates
                ]
                pirate_candidates = [(distance, pirate) for distance, pirate in pirate_candidates if distance <= gun_range]
            target = None
            target_x = target_y = None
            owner = "port"
            if pirate_candidates:
                _, target = min(pirate_candidates, key=lambda item: item[0])
                target_x, target_y = target.x, target.y
            elif not self.docked_port and self.port_attitude(port) == "HOSTILE":
                player_distance = math.hypot(self.ship_x - port.x, self.ship_y - port.y)
                if player_distance <= gun_range:
                    target = self
                    target_x, target_y = self.ship_x, self.ship_y
                    owner = "hostile_port"
            if target is None:
                continue

            aim = math.atan2(target_y - port.y, target_x - port.x)
            for spread in (-0.035, 0.0, 0.035):
                angle = aim + spread
                vx = math.cos(angle) * projectile_speed
                vy = math.sin(angle) * projectile_speed
                self.projectiles.append(Cannonball(
                    port.x + math.cos(angle) * 17.0,
                    port.y + math.sin(angle) * 17.0,
                    vx, vy, 1.45, owner
                ))
            cooldowns[port.name] = reload_seconds
            port_distance = math.hypot(self.ship_x - port.x, self.ship_y - port.y)
            if port_distance < 2400.0:
                self.audio.play("cannon_fire", volume=max(0.05, 0.22 * (1.0 - port_distance / 2800.0)))
            if self.port_defence_notice_timer <= 0.0 and (port.name == self.docked_port or owner == "hostile_port"):
                if owner == "hostile_port":
                    self.toast_message(f"The guns of {port.name} warn you away!", 2.7)
                else:
                    self.toast_message(f"The guns of {port.name} fire on {target.name}!", 2.2)
                self.port_defence_notice_timer = 4.0

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
        self.apply_cannon_recoil(pirate, broadside[0], broadside[1], 8.0)
        self.spawn_cannon_smoke(pirate.x + broadside[0] * 19, pirate.y + broadside[1] * 19,
                                broadside[0], broadside[1], amount=5)
        distance_to_player = math.hypot(pirate.x - self.ship_x, pirate.y - self.ship_y)
        self.audio.play("cannon_fire", volume=max(0.04, 0.27 * (1.0 - distance_to_player / 3000.0)))
        pirate.cooldown = 2.8 + self.rng.random() * 0.7

    def update_projectiles(self, dt):
        remaining = []
        for ball in self.projectiles:
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt
            ball.life -= dt
            if ball.life <= 0:
                continue
            if any(point_in_polygon((ball.x, ball.y), polygon) for polygon in self.collision_land_polygons()):
                continue
            if ball.owner in {"player", "fleet", "port", "npc_navy", "npc_merchant"}:
                hit = False
                for pirate in self.pirates:
                    if pirate.dead:
                        continue
                    if math.hypot(ball.x - pirate.x, ball.y - pirate.y) < 27:
                        if ball.owner in {"player", "fleet"}:
                            source = "your flagship" if ball.owner == "player" else "your escort fleet"
                            self.record_player_attack_on_pirate(pirate, source)
                        pirate.hull -= 1
                        self.audio.play("cannon_impact", volume=0.25)
                        hit = True
                        if pirate.hull <= 0:
                            pirate.dead = True
                            if ball.owner == "port":
                                self.record_commander_ship_loss(pirate, "harbour guns")
                                self.add_journal(f"{pirate.name} was sunk by the harbour guns.")
                                if pirate.name and self.port_defence_notice_timer <= 0.0:
                                    self.toast_message(f"The harbour guns sink {pirate.name}!", 3.0)
                                    self.port_defence_notice_timer = 2.5
                            elif ball.owner in {"npc_navy", "npc_merchant"}:
                                source = "a naval patrol" if ball.owner == "npc_navy" else "an armed merchant"
                                self.record_commander_ship_loss(pirate, source, ball)
                                self.add_journal(f"{pirate.name} was sunk by {source} in an independent sea battle.")
                                self.toast_message(f"{pirate.name} is sunk in an independent sea battle!", 3.0)
                            else:
                                self.record_commander_ship_loss(pirate, "the captain's guns")
                            self.register_pirate_sunk(pirate, by_player=ball.owner in {"player", "fleet"})
                        elif ball.owner not in {"port", "npc_navy", "npc_merchant"}:
                            self.toast_message(f"Hit {pirate.name}! Hull remaining: {pirate.hull}.", 1.3)
                        break
                if hit:
                    continue
                if ball.owner in {"player", "fleet"}:
                    traffic_hit = next((ship for ship in self.traffic_ships if ship.hull > 0 and math.hypot(ball.x - ship.x, ball.y - ship.y) < 27), None)
                    if traffic_hit:
                        self.audio.play("cannon_impact", volume=0.26)
                        source = "Your broadside" if ball.owner == "player" else "Your escort fleet"
                        self.provoke_traffic_ship(traffic_hit, source)
                        traffic_hit.hull = max(0, traffic_hit.hull - 1)
                        if traffic_hit.hull <= 0:
                            self.record_player_sunk_npc(traffic_hit)
                            self.record_commander_ship_loss(traffic_hit, "the player's guns")
                            self.traffic_ships.remove(traffic_hit)
                            self.toast_message(f"Your cannonball sinks the {traffic_hit.role} ship {traffic_hit.name}.", 3.2)
                        elif ball.owner != "player":
                            self.toast_message(f"A ball strikes {traffic_hit.name}!", 1.3)
                        continue
            elif ball.owner == "npc_pirate":
                traffic_hit = next((ship for ship in self.traffic_ships if ship.hull > 0 and math.hypot(ball.x - ship.x, ball.y - ship.y) < 29), None)
                if traffic_hit:
                    self.audio.play("cannon_impact", volume=0.24)
                    traffic_hit.hull = max(0, traffic_hit.hull - 1)
                    if traffic_hit.hull <= 0:
                        self.record_commander_ship_loss(traffic_hit, "pirate guns", ball)
                        self.traffic_ships.remove(traffic_hit)
                        self.add_journal(f"{traffic_hit.name} was sunk by pirate guns in open water.")
                        if self.npc_battle_notice_timer <= 0.0:
                            self.toast_message(f"{traffic_hit.name} is sunk by pirates!", 3.0)
                            self.npc_battle_notice_timer = 3.0
                    continue
            elif not self.docked_port:
                if math.hypot(ball.x - self.ship_x, ball.y - self.ship_y) < 23:
                    self.audio.play("cannon_impact", volume=0.36)
                    self.player_hull = max(0, self.player_hull - 11)
                    self.toast_message(f"Enemy broadside hit! Hull: {int(100 * self.player_hull / max(1, self.player_max_hull))}%", 1.4)
                    if self.player_hull <= 0:
                        self.player_sunk()
                    continue
                escort_hit = next((escort for escort in self.fleet if escort.hull > 0 and math.hypot(ball.x - escort.x, ball.y - escort.y) < 23), None)
                if escort_hit:
                    self.audio.play("cannon_impact", volume=0.28)
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
        self.ship_x, self.ship_y = self.harbour_berth_position(port, 2)
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.ship_heading = port.exit_heading
        self.docked_port = port.name
        self.last_docked_port = port.name
        self.near_port = port
        self.player_hull = max(1, int(self.player_max_hull * 0.55))
        self.projectiles = [ball for ball in self.projectiles if ball.owner != "enemy"]
        self.add_journal(f"Your ship was dismasted and towed to {port.name}. Lost {penalty} gold in repairs.")
        self.toast_message(f"Your ship was nearly sunk. Repairs at {port.name} cost {penalty} gold.", 5.0)

    def update(self, dt):
        if getattr(self, "menu_mode", None) or getattr(self, "save_dialog_open", False):
            nearest = min((math.hypot(self.ship_x - port.x, self.ship_y - port.y) for port in self.ports), default=None)
            self.audio.update(dt, docked=bool(self.docked_port), near_port_distance=nearest,
                              speed=math.hypot(self.ship_vx, self.ship_vy),
                              wind_strength=self.wind_strength, important_encounter=False)
            return
        self.world_time += dt
        self.toast_time = max(0.0, self.toast_time - dt)
        self.mission_result_timer = max(0.0, self.mission_result_timer - dt)
        self.wind_angle = 24.0 + math.sin(self.world_time * 0.035) * 11.0
        self.wind_strength = 0.92 + math.sin(self.world_time * 0.06) * 0.08
        nearest_harbour = min((math.hypot(self.ship_x - port.x, self.ship_y - port.y) for port in self.ports), default=None)
        active_story = self.active_mission()
        nearby_threat = any(
            not pirate.dead and (pirate.objective_target or getattr(pirate, "player_attitude", "neutral") == "hostile")
            and math.hypot(pirate.x - self.ship_x, pirate.y - self.ship_y) < 1050.0
            for pirate in self.pirates
        ) or any(
            ship.hull > 0 and (getattr(ship, "hostile_to_player", False) or getattr(ship, "under_attack", False))
            and math.hypot(ship.x - self.ship_x, ship.y - self.ship_y) < 1050.0
            for ship in self.traffic_ships
        )
        important_encounter = bool(
            (self.conversation and getattr(getattr(self.conversation, "mission", None), "category", "") == "main")
            or (active_story and active_story.category == "main" and active_story.objective_type == "kills" and not self.mission_returning)
            or nearby_threat
        )
        self.audio.update(
            dt, docked=bool(self.docked_port), near_port_distance=nearest_harbour,
            speed=math.hypot(self.ship_vx, self.ship_vy), wind_strength=self.wind_strength,
            important_encounter=important_encounter,
        )

        # Ambient shipping and hostile sails keep moving even while the player
        # is moored, speaking to harbour officials, or browsing a shipyard.
        self.organise_npc_fleets()
        self.update_fleet_commanders(dt)
        self.refresh_npc_attitudes()
        self.assign_npc_battle_targets()
        self.update_pirates(dt)
        self.update_traffic_ships(dt)
        self.update_npc_battles(dt)
        self.update_port_defences(dt)
        self.resolve_ship_collisions(dt)
        self.update_projectiles(dt)
        self.update_cannon_smoke(dt)

        # Modal harbour/captain interfaces pause player input and fleet orders,
        # not the living sea outside the quay.
        if self.conversation or self.journal_open or getattr(self, "commander_ledger_open", False) or getattr(self, "diplomacy_open", False) or self.treasure_chart_open or self.shipyard_open or self.job_board_open or self.world_map_open or getattr(self, "diplomacy_open", False):
            self.cannon_held[-1] = False
            self.cannon_held[1] = False
            return
        self.update_player_cannons(dt)
        self.update_player_sailing(dt)
        self.update_fleet(dt)
        self.update_treasure_discovery()
