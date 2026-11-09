from ..common import *


class ShipyardFleetMixin:
    def player_ship_stats(self):
        stats = dict(SHIP_CLASSES[self.current_ship])
        stats["hull"] += self.upgrades["hull"] * 25
        self.player_max_hull = stats["hull"]
        return stats

    def open_shipyard(self):
        if not self.docked_port:
            self.toast_message("The shipwright works in port. Come alongside first.", 3.0)
            return
        self.shipyard_open = True
        self.shipyard_tab = 0
        self.shipyard_selection = 0
        self.ship_rename_mode = False
        self.toast_message(f"The shipwright at {self.docked_port} is ready to do business.", 2.5)

    def shipyard_items(self):
        items = []
        if self.shipyard_tab == 0:
            for ship_name, stats in SHIP_CLASSES.items():
                if ship_name == self.current_ship:
                    continue
                items.append({
                    "label": f"Commission a {ship_name}  —  {stats['cost']} gold",
                    "detail": f"{stats['description']} Hull {stats['hull']}, {stats['guns']} guns, {stats.get('rowers', 12)} oarsmen, top way {int(stats['speed'])} kn.",
                    "action": "buy_flagship", "key": ship_name,
                })
        elif self.shipyard_tab == 1:
            upgrade_info = [
                ("cannons", "Long guns", "Add one cannon to each broadside and improve reload time."),
                ("hull", "Reinforced hull", "Add 25 points to your flagship's maximum hull strength."),
                ("rigging", "Fine-cut rigging", "Improve sail power and maximum speed."),
                ("rudder", "Balanced rudder", "Improve the ship's turning response."),
                ("cargo", "Expanded cargo hold", "Add 12 cargo units to your flagship's hold."),
            ]
            for key, title, detail in upgrade_info:
                level = self.upgrades[key]
                if level >= 3:
                    label = f"{title}  —  fully fitted"
                    action = "none"
                else:
                    cost = self.upgrade_cost(key)
                    label = f"Fit {title}  —  level {level + 1}  —  {cost} gold"
                    action = "upgrade"
                items.append({"label": label, "detail": f"{detail} Current level: {level}/3.", "action": action, "key": key})
        elif self.shipyard_tab == 2:
            for ship_name, cost in (("Sloop", 480), ("Cutter", 720), ("Schooner", 1080), ("Brigantine", 1650)):
                items.append({
                    "label": f"Hire {ship_name} escort  —  {cost} gold",
                    "detail": f"Add a {ship_name.lower()} to your personal fleet. Escorts sail with you and fire on hostile pirates.",
                    "action": "hire", "key": ship_name, "cost": cost,
                })
            order_info = [
                ("fight", "Fight (F)", "Hunt nearby pirate ships and attack with your broadsides."),
                ("hold_fire", "Hold fire (H)", "Keep station in formation, but never fire or pursue enemies."),
                ("gather", "Gather around flagship (G)", "Regroup in a close protective formation around your ship."),
                ("follow", "Follow in formation (V)", "Sail in a wider formation and defend the fleet when threatened."),
            ]
            for order, label, detail in order_info:
                active = "  [ACTIVE]" if self.fleet_order == order else ""
                items.append({
                    "label": f"Order fleet: {label}{active}",
                    "detail": detail,
                    "action": "set_order", "key": order,
                })
        elif self.shipyard_tab == 3:
            flagship_missing = max(0, self.player_max_hull - self.player_hull)
            flagship_cost = flagship_missing * 2
            items.append({
                "label": f"Repair flagship  —  {flagship_cost} gold",
                "detail": f"Restore your flagship to full hull. Current condition: {self.player_hull}/{self.player_max_hull}.",
                "action": "repair_flagship", "key": "",
            })
            fleet_missing = sum(max(0, escort.max_hull - escort.hull) for escort in self.fleet)
            fleet_cost = fleet_missing * 2
            items.append({
                "label": f"Repair all escorts  —  {fleet_cost} gold",
                "detail": f"Restore all surviving fleet ships. Combined missing hull: {fleet_missing}.",
                "action": "repair_fleet", "key": "",
            })
        else:
            items.append({
                "label": f"Rename flagship: {self.player_ship_name}",
                "detail": "Give your vessel a name worthy of the legend. Select this and type a new name.",
                "action": "rename", "key": "",
            })
            livery_name = SHIP_LIVERIES[self.player_livery][0]
            items.append({
                "label": f"Change paint and sails: {livery_name}",
                "detail": "Cycle through five hull, trim, and sail colour schemes.",
                "action": "livery", "key": "",
            })
        return items

    def upgrade_cost(self, key):
        bases = {"cannons": 430, "hull": 360, "rigging": 410, "rudder": 320, "cargo": 300}
        return bases[key] + self.upgrades[key] * 310

    def execute_shipyard_selection(self):
        items = self.shipyard_items()
        if not items:
            return
        item = items[self.shipyard_selection % len(items)]
        action = item["action"]
        key = item.get("key", "")
        if action == "buy_flagship":
            stats = SHIP_CLASSES[key]
            cost = stats["cost"]
            if self.gold < cost:
                self.toast_message(f"The {key} costs {cost} gold. You have {self.gold}.", 3.5)
                return
            if self.cargo_load() > self.cargo_capacity_for_ship(key, self.upgrades) + 0.001:
                self.toast_message(f"Your current cargo will not fit aboard a {key}. Sell some cargo or choose a larger ship first.", 4.0)
                return
            old_name = self.player_ship_name
            self.gold -= cost
            self.current_ship = key
            self.player_ship_name = f"The {key} {self.rng.choice(['Fortune', 'Revenge', 'Liberty', 'Tempest', 'Seahawk'])}"
            for side in (-1, 1):
                self.cannon_held[side] = False
                self.cannon_first_volley_fired[side] = False
                self.cannon_battery_timers[side] = []
                self.cannon_battery_rates[side] = []
            self.player_max_hull = stats["hull"] + self.upgrades["hull"] * 25
            self.player_hull = self.player_max_hull
            self.ship_vx = 0.0
            self.ship_vy = 0.0
            self.add_journal(f"Replaced {old_name} with a new {key}, christened {self.player_ship_name}.")
            self.toast_message(f"A new {key} is yours! Your old ship has been traded in.", 4.0)
        elif action == "upgrade":
            cost = self.upgrade_cost(key)
            if self.upgrades[key] >= 3:
                self.toast_message("That refit is already at its finest level.", 2.5)
            elif self.gold < cost:
                self.toast_message(f"The refit costs {cost} gold. You have {self.gold}.", 3.0)
            else:
                self.gold -= cost
                old_max = self.player_max_hull
                self.upgrades[key] += 1
                stats = self.player_ship_stats()
                if key == "hull":
                    self.player_hull += stats["hull"] - old_max
                self.add_journal(f"Installed level {self.upgrades[key]} {key} refit at {self.docked_port}.")
                self.toast_message(f"Refit complete: {key.title()} level {self.upgrades[key]}.", 3.0)
        elif action == "hire":
            cost = item["cost"]
            if self.gold < cost:
                self.toast_message(f"Hiring this escort costs {cost} gold. You have {self.gold}.", 3.0)
                return
            stats = SHIP_CLASSES[key]
            self.gold -= cost
            serial = self.fleet_serial
            self.fleet_serial += 1
            names = ["Jolly Raven", "Sea Witch", "Morning Star", "Copper Belle", "Dread Gull", "Merry Rogue"]
            name = f"{names[(serial - 1) % len(names)]} {serial}"
            new_fleet_count = len(self.fleet) + 1
            for index, existing in enumerate(self.fleet):
                existing_x, existing_y = self.fleet_formation_target(index, new_fleet_count, "follow")
                existing.x = existing_x
                existing.y = existing_y
                existing.vx = 0.0
                existing.vy = 0.0
            spawn_x, spawn_y = self.fleet_formation_target(new_fleet_count - 1, new_fleet_count, "follow")
            escort = FleetShip(name, key, spawn_x, spawn_y, self.ship_heading, stats["hull"], stats["hull"])
            escort.anchor_x = escort.x
            escort.anchor_y = escort.y
            self.fleet.append(escort)
            self.add_journal(f"Hired {name}, a {key}, into your personal fleet.")
            self.toast_message(f"{name}, your new {key} escort, joins the fleet.", 4.0)
        elif action == "set_order":
            self.set_fleet_order(key)
        elif action == "repair_flagship":
            missing = max(0, self.player_max_hull - self.player_hull)
            cost = missing * 2
            if missing == 0:
                self.toast_message("Your flagship is already shipshape.", 2.5)
            elif self.gold >= cost:
                self.gold -= cost
                self.player_hull = self.player_max_hull
                self.toast_message(f"Flagship repaired. {cost} gold paid.", 3.0)
            else:
                self.toast_message(f"Repairs cost {cost} gold. You have {self.gold}.", 3.0)
        elif action == "repair_fleet":
            missing = sum(max(0, escort.max_hull - escort.hull) for escort in self.fleet)
            cost = missing * 2
            if missing == 0:
                self.toast_message("Your escorts are already shipshape.", 2.5)
            elif self.gold >= cost:
                self.gold -= cost
                for escort in self.fleet:
                    escort.hull = escort.max_hull
                self.toast_message(f"Fleet repaired. {cost} gold paid.", 3.0)
            else:
                self.toast_message(f"Fleet repairs cost {cost} gold. You have {self.gold}.", 3.0)
        elif action == "rename":
            self.ship_name_input = self.player_ship_name
            self.ship_rename_mode = True
            pygame.key.start_text_input()
        elif action == "livery":
            self.player_livery = (self.player_livery + 1) % len(SHIP_LIVERIES)
            self.toast_message(f"New livery: {SHIP_LIVERIES[self.player_livery][0]}.", 2.5)
        self.shipyard_selection = min(self.shipyard_selection, max(0, len(self.shipyard_items()) - 1))

    def set_fleet_order(self, order):
        order_names = {
            "fight": "Fight: hunt and attack nearby pirates",
            "hold_fire": "Hold fire: maintain formation without shooting",
            "gather": "Gather: close formation around your flagship",
            "follow": "Follow: sail in formation and defend when threatened",
        }
        if order not in order_names:
            return
        self.fleet_order = order
        for escort in self.fleet:
            escort.anchor_x = escort.x
            escort.anchor_y = escort.y
        if self.fleet:
            self.toast_message(f"Fleet orders: {order_names[order]}.", 3.2)
        else:
            self.toast_message(f"Orders set: {order_names[order]}. They will apply when you hire escorts.", 3.2)

    def fleet_formation_target(self, index, count, order):
        heading = math.radians(self.ship_heading)
        forward = (math.cos(heading), math.sin(heading))
        side = (-forward[1], forward[0])
        if order == "gather":
            remaining = index
            ring = 1
            while remaining >= 6 * ring:
                remaining -= 6 * ring
                ring += 1
            capacity = 6 * ring
            angle = heading + (remaining / capacity) * math.tau
            radius = 140.0 + (ring - 1) * 125.0
            return self.ship_x + math.cos(angle) * radius, self.ship_y + math.sin(angle) * radius
        columns = 4
        row = index // columns
        row_start = row * columns
        row_count = min(columns, count - row_start)
        column = index - row_start
        lateral = (column - (row_count - 1) / 2.0) * 132.0
        trailing = 170.0 + row * 136.0
        direction = 1.0 if self.docked_port else -1.0
        target_x = self.ship_x + forward[0] * trailing * direction + side[0] * lateral
        target_y = self.ship_y + forward[1] * trailing * direction + side[1] * lateral
        return target_x, target_y

    def steer_escort_toward(self, escort, target_x, target_y, dt, turn_rate=54.0, thrust=58.0):
        dx = target_x - escort.x
        dy = target_y - escort.y
        distance = math.hypot(dx, dy)
        if distance > 34.0:
            desired = math.degrees(math.atan2(dy, dx))
            desired = self.reef_avoidance_heading(escort.x, escort.y, desired, lookahead=580.0, clearance=140.0)
            difference = angle_difference(desired, escort.heading)
            escort.heading = (escort.heading + clamp(difference, -turn_rate * dt, turn_rate * dt)) % 360.0
            angle = math.radians(escort.heading)
            acceleration = min(thrust, distance * 0.16)
            escort.vx += math.cos(angle) * acceleration * dt
            escort.vy += math.sin(angle) * acceleration * dt

    def aim_and_fire_fleet_broadside(self, escort, target, dt):
        bearing = math.degrees(math.atan2(target.y - escort.y, target.x - escort.x))
        heading_options = ((bearing - 90.0) % 360.0, (bearing + 90.0) % 360.0)
        desired_heading = min(heading_options, key=lambda value: abs(angle_difference(value, escort.heading)))
        difference = angle_difference(desired_heading, escort.heading)
        escort.heading = (escort.heading + clamp(difference, -66.0 * dt, 66.0 * dt)) % 360.0
        if abs(difference) < 24.0 and escort.cooldown <= 0:
            self.fire_fleet_broadside(escort, target)

    def update_fleet(self, dt):
        if self.docked_port or self.conversation or self.shipyard_open:
            return
        nearby_pirates = [pirate for pirate in self.pirates if not pirate.dead]
        fleet_count = len(self.fleet)
        land_polygons = self.collision_land_polygons()
        for index, escort in enumerate(self.fleet):
            if escort.hull <= 0:
                continue
            escort.cooldown = max(0.0, escort.cooldown - dt)
            target_pirate = None
            if nearby_pirates:
                target_pirate = min(nearby_pirates, key=lambda pirate: math.hypot(pirate.x - escort.x, pirate.y - escort.y))
            enemy_distance = math.hypot(target_pirate.x - escort.x, target_pirate.y - escort.y) if target_pirate else float("inf")

            if self.fleet_order == "fight" and target_pirate:
                dx = target_pirate.x - escort.x
                dy = target_pirate.y - escort.y
                distance = max(1.0, math.hypot(dx, dy))
                if distance > 335.0:
                    self.steer_escort_toward(escort, target_pirate.x, target_pirate.y, dt, 54.0, 62.0)
                if 145.0 < distance < 650.0:
                    self.aim_and_fire_fleet_broadside(escort, target_pirate, dt)
            else:
                formation_order = "gather" if self.fleet_order == "gather" else "follow"
                target_x, target_y = self.fleet_formation_target(index, fleet_count, formation_order)
                self.steer_escort_toward(escort, target_x, target_y, dt, 58.0, 64.0)
                if self.fleet_order == "follow" and target_pirate and 145.0 < enemy_distance < 560.0:
                    self.aim_and_fire_fleet_broadside(escort, target_pirate, dt)

            escort.heading = self.reef_avoidance_heading(
                escort.x, escort.y, escort.heading, lookahead=520.0, clearance=135.0
            )
            escort.vx *= math.exp(-0.19 * dt)
            escort.vy *= math.exp(-0.19 * dt)
            speed = math.hypot(escort.vx, escort.vy)
            max_speed = SHIP_CLASSES[escort.ship_type]["speed"] * 0.68
            if speed > max_speed:
                escort.vx *= max_speed / speed
                escort.vy *= max_speed / speed
            escort.x += escort.vx * dt
            escort.y += escort.vy * dt
            escort.x, escort.y, escort.vx, escort.vy, _ = resolve_land_collision(
                escort.x, escort.y, escort.vx, escort.vy, 29, land_polygons
            )
            self.apply_reef_damage(escort, dt, kind="npc", ship_radius=29.0)

    def fire_fleet_broadside(self, escort, target):
        bearing = math.degrees(math.atan2(target.y - escort.y, target.x - escort.x))
        options = []
        for side in (-1, 1):
            angle = (escort.heading + side * 90.0) % 360.0
            options.append((abs(angle_difference(bearing, angle)), side))
        alignment, side = min(options)
        if alignment > 30:
            return
        angle = math.radians(escort.heading)
        forward = (math.cos(angle), math.sin(angle))
        broadside_angle = angle + side * math.pi / 2
        broadside = (math.cos(broadside_angle), math.sin(broadside_angle))
        gun_count = max(2, SHIP_CLASSES[escort.ship_type]["guns"] // 2)
        for index in range(gun_count):
            offset = (index - (gun_count - 1) / 2) * 14
            x = escort.x + forward[0] * offset + broadside[0] * 17
            y = escort.y + forward[1] * offset + broadside[1] * 17
            vx = broadside[0] * 455 + escort.vx * 0.14
            vy = broadside[1] * 455 + escort.vy * 0.14
            self.projectiles.append(Cannonball(x, y, vx, vy, 1.4, "fleet"))
            self.spawn_cannon_smoke(x, y, broadside[0], broadside[1], amount=1)
        self.apply_cannon_recoil(escort, broadside[0], broadside[1], 8.0)
        distance_to_player = math.hypot(escort.x - self.ship_x, escort.y - self.ship_y)
        self.audio.play("cannon_fire", volume=max(0.04, 0.25 * (1.0 - distance_to_player / 2700.0)))
        escort.cooldown = SHIP_CLASSES[escort.ship_type]["reload"] + 0.25

    def draw_shipyard(self):
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((9, 15, 16, 205))
        self.screen.blit(overlay, (0, 0))
        box_width = min(1120, width - 42)
        box_height = min(700, height - 36)
        box = pygame.Rect(width // 2 - box_width // 2, height // 2 - box_height // 2, box_width, box_height)
        pygame.draw.rect(self.screen, (35, 22, 16), box.inflate(12, 12), border_radius=9)
        pygame.draw.rect(self.screen, (222, 203, 159), box, border_radius=7)
        pygame.draw.rect(self.screen, (142, 98, 60), box, 3, border_radius=7)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box.inflate(-8, -8))
        title = fit_text_surface(self.big_font, "THE SHIPWRIGHT'S YARD", (77, 43, 25), box.width - 50, 42)
        self.screen.blit(title, title.get_rect(midtop=(box.centerx, box.y + 13)))
        sub = fit_text_surface(self.small_font, f"{self.docked_port}  |  Pieces of eight: {self.gold} g  |  Flagship: {self.player_ship_name}", (87, 60, 38), box.width - 54, 25)
        self.screen.blit(sub, sub.get_rect(midtop=(box.centerx, box.y + 67)))
        tab_y = box.y + 111
        tab_width = (box.width - 42) // len(self.shipyard_tabs)
        for index, tab in enumerate(self.shipyard_tabs):
            tab_rect = pygame.Rect(box.x + 21 + index * tab_width, tab_y, tab_width - 5, 44)
            selected = index == self.shipyard_tab
            pygame.draw.rect(self.screen, (130, 78, 43) if selected else (193, 171, 130), tab_rect, border_radius=4)
            color = (255, 231, 184) if selected else (75, 51, 34)
            label = fit_text_surface(self.small_font, tab, color, tab_rect.width - 12, tab_rect.height - 8)
            self.screen.blit(label, label.get_rect(center=tab_rect.center))
        items = self.shipyard_items()
        start_y = tab_y + 56
        available_rows_height = max(1, box.bottom - start_y - 54)
        visible_rows = max(3, min(5, available_rows_height // 72))
        row_height = min(88, available_rows_height // visible_rows)
        if self.ship_rename_mode:
            prompt = fit_text_surface(self.title_font, "Name your flagship", (77, 43, 25), box.width - 84, 38)
            self.screen.blit(prompt, (box.x + 42, start_y + 18))
            input_box = pygame.Rect(box.x + 40, start_y + 82, box.width - 80, 58)
            pygame.draw.rect(self.screen, (246, 235, 210), input_box, border_radius=5)
            pygame.draw.rect(self.screen, (142, 98, 60), input_box, 2, border_radius=5)
            text = fit_text_surface(self.font, self.ship_name_input + "▏", (54, 43, 30), input_box.width - 30, input_box.height - 14)
            self.screen.blit(text, (input_box.x + 15, input_box.y + (input_box.height - text.get_height()) // 2))
            hint = fit_text_surface(self.small_font, "Type a name, then press Enter. Esc cancels.", (87, 60, 38), box.width - 84, 25)
            self.screen.blit(hint, (input_box.x, input_box.bottom + 16))
        elif not items:
            message = fit_text_surface(self.font, "Nothing needs doing on this page, captain.", (77, 54, 36), box.width - 84, 32)
            self.screen.blit(message, (box.x + 42, start_y + 30))
        else:
            visible_start = max(0, min(self.shipyard_selection - visible_rows + 1, len(items) - visible_rows))
            for visible_index, item in enumerate(items[visible_start:visible_start + visible_rows]):
                index = visible_start + visible_index
                row = pygame.Rect(box.x + 24, start_y + visible_index * row_height, box.width - 48, row_height - 7)
                selected = index == self.shipyard_selection
                pygame.draw.rect(self.screen, (196, 173, 132) if selected else (211, 195, 161), row, border_radius=5)
                if selected:
                    pygame.draw.rect(self.screen, (117, 69, 38), row, 3, border_radius=5)
                label = fit_text_surface(self.font, item["label"], (73, 43, 27), row.width - 30, 25)
                self.screen.blit(label, (row.x + 15, row.y + 6))
                for line_index, line in enumerate(wrap_text(self.small_font, item["detail"], row.width - 30)[:2]):
                    fitted_line = fit_text_surface(self.small_font, line, (94, 68, 43), row.width - 30, 17)
                    self.screen.blit(fitted_line, (row.x + 15, row.y + min(34, row.height - 39) + line_index * 18))
        footer = fit_text_surface(self.small_font, "Up / Down: choose   Enter: confirm   Left / Right: pages   B / Esc: leave the yard", (91, 62, 40), box.width - 48, 22)
        self.screen.blit(footer, footer.get_rect(midbottom=(box.centerx, box.bottom - 12)))
        self.screen.set_clip(previous_clip)
