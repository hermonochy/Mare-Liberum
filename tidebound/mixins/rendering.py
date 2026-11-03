from ..common import *


class RenderingMixin:
    def toast_message(self, message, duration=3.0):
        self.toast = message
        self.toast_time = duration

    def draw_ocean(self):
        self.screen.fill((22, 86, 112))
        width, height = self.screen.get_size()
        visible_w = width / self.camera_zoom / 2 + 70
        visible_h = height / self.camera_zoom / 2 + 70
        tile = 118.0
        left = math.floor((self.camera_x - visible_w) / tile) * tile
        right = self.camera_x + visible_w
        top = math.floor((self.camera_y - visible_h) / tile) * tile
        bottom = self.camera_y + visible_h
        line_width = max(1, int(1.35 * self.camera_zoom))
        for world_x in range(int(left), int(right + tile), int(tile)):
            for world_y in range(int(top), int(bottom + tile), int(tile)):
                phase = math.sin(world_x * 0.013 + world_y * 0.007)
                drift = math.cos(world_x * 0.005 - world_y * 0.011)
                length = 24 + int((phase + 1.0) * 7)
                end_offset = int(drift * 5)
                sx, sy = self.world_to_screen(world_x + 17 + phase * 15, world_y + 23 + drift * 18)
                ex, ey = self.world_to_screen(world_x + 17 + phase * 15 + length, world_y + 23 + drift * 18 + end_offset)
                shade = int(108 + (phase + 1.0) * 8)
                color = (shade - 20, shade + 28, shade + 40)
                pygame.draw.line(self.screen, color, (sx, sy), (ex, ey), line_width)

    def draw_islands(self):
        visible_sites = [site for site in self.treasure_sites if site.revealed]
        for polygon in self.land + [site.polygon for site in visible_sites]:
            points = self.polygon_to_screen(polygon)
            pygame.draw.polygon(self.screen, (199, 178, 122), points)
            center_x = sum(point[0] for point in polygon) / len(polygon)
            center_y = sum(point[1] for point in polygon) / len(polygon)
            inner = [(center_x + (x - center_x) * 0.91, center_y + (y - center_y) * 0.91) for x, y in polygon]
            pygame.draw.polygon(self.screen, (54, 115, 73), self.polygon_to_screen(inner))
            inner_deep = [(center_x + (x - center_x) * 0.73, center_y + (y - center_y) * 0.73) for x, y in polygon]
            pygame.draw.polygon(self.screen, (47, 99, 67), self.polygon_to_screen(inner_deep))
            pygame.draw.lines(self.screen, (222, 202, 148), True, points, max(1, int(2 * self.camera_zoom)))
        visible_trees = self.tree_positions + [point for site in visible_sites for point in site.trees]
        for x, y in visible_trees:
            sx, sy = self.world_to_screen(x, y)
            radius = max(2, int(4 * self.camera_zoom))
            if -15 <= sx <= self.screen.get_width() + 15 and -15 <= sy <= self.screen.get_height() + 15:
                pygame.draw.circle(self.screen, (31, 77, 52), (sx + radius, sy + radius), radius + 2)
                pygame.draw.line(self.screen, (110, 83, 49), (sx, sy + radius), (sx + radius, sy - radius), max(1, int(2 * self.camera_zoom)))
                for angle in range(0, 360, 90):
                    end_x = sx + int(math.cos(math.radians(angle)) * radius * 2)
                    end_y = sy + int(math.sin(math.radians(angle)) * radius * 2)
                    pygame.draw.line(self.screen, (88, 142, 67), (sx + radius, sy), (end_x, end_y), max(1, int(2 * self.camera_zoom)))

    def draw_treasure_features(self):
        for site in self.treasure_sites:
            if not site.map_found:
                sx, sy = self.world_to_screen(site.bottle_x, site.bottle_y)
                if -40 <= sx <= self.screen.get_width() + 40 and -40 <= sy <= self.screen.get_height() + 40:
                    pygame.draw.ellipse(self.screen, (21, 49, 42), (sx - 11, sy - 5, 22, 11))
                    pygame.draw.ellipse(self.screen, (91, 160, 128), (sx - 8, sy - 8, 16, 12))
                    pygame.draw.rect(self.screen, (188, 164, 115), (sx - 3, sy - 12, 6, 6), border_radius=2)
                    pygame.draw.line(self.screen, (232, 218, 175), (sx - 4, sy - 2), (sx + 4, sy - 6), 2)
                    if self.camera_zoom > 0.72:
                        bottle_label = self.tiny_font.render("BOTTLE", True, (246, 231, 186))
                        bottle_rect = bottle_label.get_rect(center=(sx, sy - 25))
                        pygame.draw.rect(self.screen, (31, 45, 39), bottle_rect.inflate(8, 4), border_radius=3)
                        self.screen.blit(bottle_label, bottle_rect)
            if not site.revealed:
                continue
            label_pos = self.world_to_screen(sum(p[0] for p in site.polygon) / len(site.polygon), min(p[1] for p in site.polygon) - 22)
            label = self.small_font.render(site.island_name.upper(), True, (255, 236, 190))
            label_rect = label.get_rect(center=label_pos)
            pygame.draw.rect(self.screen, (28, 45, 42), label_rect.inflate(12, 6), border_radius=4)
            self.screen.blit(label, label_rect)
            chest_pos = self.world_to_screen(site.chest_x, site.chest_y)
            if site.dug:
                pygame.draw.rect(self.screen, (98, 52, 25), (chest_pos[0] - 11, chest_pos[1] - 6, 22, 13), border_radius=3)
                pygame.draw.rect(self.screen, (218, 167, 65), (chest_pos[0] - 11, chest_pos[1] - 6, 22, 5), border_radius=2)
                pygame.draw.circle(self.screen, (245, 213, 126), chest_pos, 3)
            else:
                if site.treasure_id == "gannet_cay":
                    pygame.draw.line(self.screen, (93, 57, 34), (chest_pos[0] - 18, chest_pos[1] + 5), (chest_pos[0] + 15, chest_pos[1] - 4), 5)
                    pygame.draw.line(self.screen, (132, 91, 51), (chest_pos[0] - 12, chest_pos[1] + 3), (chest_pos[0] + 7, chest_pos[1] - 2), 2)
                elif site.treasure_id == "widows_key":
                    pygame.draw.circle(self.screen, (220, 211, 183), (chest_pos[0] - 15, chest_pos[1]), 9)
                    pygame.draw.circle(self.screen, (220, 211, 183), (chest_pos[0] + 15, chest_pos[1]), 9)
                    pygame.draw.circle(self.screen, (160, 151, 129), (chest_pos[0] - 15, chest_pos[1]), 4)
                    pygame.draw.circle(self.screen, (160, 151, 129), (chest_pos[0] + 15, chest_pos[1]), 4)
                else:
                    pygame.draw.line(self.screen, (92, 57, 36), (chest_pos[0] - 23, chest_pos[1] - 7), (chest_pos[0] + 19, chest_pos[1] + 8), 6)
                    pygame.draw.line(self.screen, (177, 145, 98), (chest_pos[0] - 8, chest_pos[1] - 2), (chest_pos[0] - 3, chest_pos[1] + 1), 3)

    def draw_port(self, port):
        pier_start = self.world_to_screen(port.shore_x, port.shore_y)
        pier_end = self.world_to_screen(port.x, port.y)
        pygame.draw.line(self.screen, (76, 49, 33), pier_start, pier_end, max(5, int(14 * self.camera_zoom)))
        pygame.draw.line(self.screen, (155, 112, 70), pier_start, pier_end, max(2, int(8 * self.camera_zoom)))
        if self.camera_zoom > 0.7:
            dx = port.x - port.shore_x
            dy = port.y - port.shore_y
            length = max(1.0, math.hypot(dx, dy))
            px = -dy / length
            py = dx / length
            for amount in (0.18, 0.36, 0.54, 0.72, 0.9):
                cx = port.shore_x + dx * amount
                cy = port.shore_y + dy * amount
                a = self.world_to_screen(cx + px * 7, cy + py * 7)
                b = self.world_to_screen(cx - px * 7, cy - py * 7)
                pygame.draw.line(self.screen, (91, 62, 40), a, b, max(1, int(2 * self.camera_zoom)))
        sx, sy = self.world_to_screen(port.shore_x, port.shore_y)
        building_w = max(10, int(34 * self.camera_zoom))
        building_h = max(8, int(25 * self.camera_zoom))
        building = pygame.Rect(sx - building_w // 2, sy - building_h // 2, building_w, building_h)
        pygame.draw.rect(self.screen, (91, 53, 39), building.inflate(3, 3))
        pygame.draw.rect(self.screen, (191, 152, 99), building)
        roof = [(building.left - 3, building.top + 2), (building.centerx, building.top - building_h // 2), (building.right + 3, building.top + 2)]
        pygame.draw.polygon(self.screen, (105, 52, 43), roof)
        crane_x = sx + int(33 * self.camera_zoom)
        crane_y = sy + int(3 * self.camera_zoom)
        crane_height = max(7, int(25 * self.camera_zoom))
        pygame.draw.line(self.screen, (77, 48, 30), (crane_x, crane_y), (crane_x, crane_y - crane_height), max(2, int(3 * self.camera_zoom)))
        pygame.draw.line(self.screen, (77, 48, 30), (crane_x - int(13 * self.camera_zoom), crane_y - crane_height), (crane_x + int(16 * self.camera_zoom), crane_y - crane_height), max(2, int(3 * self.camera_zoom)))
        pygame.draw.line(self.screen, (77, 48, 30), (crane_x + int(12 * self.camera_zoom), crane_y - crane_height), (crane_x + int(12 * self.camera_zoom), crane_y + int(12 * self.camera_zoom)), max(1, int(2 * self.camera_zoom)))
        if self.camera_zoom > 0.68:
            yard_sign = self.tiny_font.render("YARD", True, (255, 225, 165))
            yard_rect = yard_sign.get_rect(center=(crane_x + int(23 * self.camera_zoom), crane_y + int(18 * self.camera_zoom)))
            pygame.draw.rect(self.screen, (57, 37, 27), yard_rect.inflate(8, 4), border_radius=2)
            self.screen.blit(yard_sign, yard_rect)
        flag_x = sx + int(23 * self.camera_zoom)
        flag_y = sy - int(23 * self.camera_zoom)
        pygame.draw.line(self.screen, (54, 39, 30), (flag_x, flag_y), (flag_x, flag_y - int(22 * self.camera_zoom)), max(1, int(2 * self.camera_zoom)))
        pygame.draw.polygon(self.screen, (35, 30, 28), [(flag_x, flag_y - int(22 * self.camera_zoom)), (flag_x + int(17 * self.camera_zoom), flag_y - int(17 * self.camera_zoom)), (flag_x, flag_y - int(12 * self.camera_zoom))])
        label_x, label_y = self.world_to_screen(port.x, port.y + 30)
        label = self.small_font.render(port.name, True, (255, 236, 190))
        label_box = label.get_rect(center=(label_x, label_y))
        pygame.draw.rect(self.screen, (28, 45, 42), label_box.inflate(12, 6), border_radius=4)
        self.screen.blit(label, label_box)

    def create_ship_surface(self, player=True, allied=False, rowing=False):
        surface = pygame.Surface((124, 86), pygame.SRCALPHA)
        if player:
            _, hull_color, trim_color, sail_color = SHIP_LIVERIES[self.player_livery]
            sail_shadow = tuple(max(0, channel - 45) for channel in sail_color)
        elif allied:
            hull_color = (42, 80, 69)
            trim_color = (179, 190, 135)
            sail_color = (191, 220, 202)
            sail_shadow = (118, 160, 143)
        else:
            hull_color = (69, 39, 34)
            trim_color = (165, 92, 65)
            sail_color = (155, 55, 48)
            sail_shadow = (100, 41, 38)
        pygame.draw.polygon(surface, (43, 30, 25), [(7, 43), (27, 22), (90, 22), (117, 43), (90, 65), (27, 65)])
        pygame.draw.polygon(surface, hull_color, [(10, 43), (29, 26), (88, 26), (111, 43), (88, 60), (29, 60)])
        pygame.draw.polygon(surface, trim_color, [(19, 43), (34, 31), (85, 31), (101, 43), (85, 55), (34, 55)], 2)
        pygame.draw.polygon(surface, (143, 100, 61), [(28, 36), (86, 36), (94, 43), (86, 50), (28, 50), (20, 43)])
        pygame.draw.line(surface, (39, 30, 25), (37, 43), (92, 43), 2)
        pygame.draw.line(surface, (48, 35, 26), (58, 43), (58, 15), 3)
        pygame.draw.line(surface, (48, 35, 26), (77, 43), (77, 20), 2)
        pygame.draw.polygon(surface, sail_color, [(59, 17), (82, 25), (59, 38)])
        pygame.draw.polygon(surface, sail_shadow, [(59, 17), (59, 38), (43, 31)])
        if player:
            pygame.draw.circle(surface, (48, 37, 29), (68, 27), 4)
            pygame.draw.circle(surface, (235, 224, 196), (67, 26), 1)
            pygame.draw.circle(surface, (235, 224, 196), (70, 26), 1)
            pygame.draw.line(surface, (48, 37, 29), (63, 33), (74, 38), 2)
            pygame.draw.line(surface, (48, 37, 29), (64, 38), (74, 32), 2)
        pygame.draw.polygon(surface, sail_color, [(78, 22), (96, 31), (78, 40)])
        pygame.draw.line(surface, (224, 210, 174), (58, 13), (58, 43), 2)
        pygame.draw.line(surface, (224, 210, 174), (77, 18), (77, 43), 1)
        for x in (34, 45, 69, 83):
            pygame.draw.circle(surface, (28, 25, 22), (x, 26), 2)
            pygame.draw.circle(surface, (28, 25, 22), (x, 60), 2)
        pygame.draw.line(surface, (38, 29, 24), (58, 43), (112, 43), 2)
        pygame.draw.line(surface, (38, 29, 24), (58, 43), (21, 43), 2)
        pygame.draw.polygon(surface, (28, 25, 24), [(96, 14), (119, 19), (98, 26)])
        pygame.draw.circle(surface, (235, 225, 195), (104, 20), 3)
        pygame.draw.circle(surface, (25, 23, 22), (103, 19), 1)
        pygame.draw.circle(surface, (25, 23, 22), (106, 21), 1)
        pygame.draw.line(surface, (241, 227, 190), (101, 23), (107, 23), 1)
        pygame.draw.line(surface, (241, 227, 190), (101, 25), (108, 17), 1)
        pygame.draw.line(surface, (241, 227, 190), (101, 17), (108, 25), 1)
        pygame.draw.line(surface, (233, 216, 176), (12, 43), (3, 43), 2)
        if rowing:
            stroke = math.sin(self.world_time * 8.0) * 3.5
            for oar_x in (34, 46, 58, 70, 82, 94):
                upper_tip = (int(oar_x + stroke), 7)
                lower_tip = (int(oar_x - stroke), 79)
                pygame.draw.line(surface, (92, 57, 31), (oar_x, 31), upper_tip, 3)
                pygame.draw.line(surface, (92, 57, 31), (oar_x, 55), lower_tip, 3)
                pygame.draw.ellipse(surface, (153, 111, 65), (upper_tip[0] - 4, upper_tip[1] - 3, 8, 5))
                pygame.draw.ellipse(surface, (153, 111, 65), (lower_tip[0] - 4, lower_tip[1] - 2, 8, 5))
                pygame.draw.circle(surface, (198, 148, 104), (oar_x, 34), 3)
                pygame.draw.circle(surface, (198, 148, 104), (oar_x, 52), 3)
                pygame.draw.line(surface, (62, 43, 32), (oar_x - 3, 36), (oar_x + 3, 40), 2)
                pygame.draw.line(surface, (62, 43, 32), (oar_x - 3, 50), (oar_x + 3, 46), 2)
        return surface

    def draw_ship(self, x, y, heading, player=True, hull=None, max_hull=None, allied=False, rowing=False):
        base = self.create_ship_surface(player, allied, rowing)
        scaled_w = max(28, int(base.get_width() * self.camera_zoom))
        scaled_h = max(22, int(base.get_height() * self.camera_zoom))
        if scaled_w != base.get_width() or scaled_h != base.get_height():
            base = pygame.transform.smoothscale(base, (scaled_w, scaled_h))
        rotated = pygame.transform.rotate(base, -heading)
        pos = self.world_to_screen(x, y)
        rect = rotated.get_rect(center=pos)
        self.screen.blit(rotated, rect)
        if not player and hull is not None and max_hull:
            bar_w = max(24, int(42 * self.camera_zoom))
            bar = pygame.Rect(pos[0] - bar_w // 2, pos[1] - int(38 * self.camera_zoom), bar_w, 5)
            pygame.draw.rect(self.screen, (40, 28, 27), bar)
            fill = pygame.Rect(bar.x, bar.y, int(bar.width * max(0, hull) / max_hull), bar.height)
            pygame.draw.rect(self.screen, (70, 171, 126) if allied else (171, 52, 40), fill)

    def draw_cannonballs(self):
        for ball in self.projectiles:
            pos = self.world_to_screen(ball.x, ball.y)
            radius = max(2, int(4.5 * self.camera_zoom))
            pygame.draw.circle(self.screen, (23, 22, 21), pos, radius)
            pygame.draw.circle(self.screen, (129, 113, 87), (pos[0] - 1, pos[1] - 1), max(1, radius // 2))
            trail = self.world_to_screen(ball.x - ball.vx * 0.025, ball.y - ball.vy * 0.025)
            pygame.draw.line(self.screen, (184, 177, 151), trail, pos, max(1, radius // 2))

    def draw_world(self):
        self.update_camera()
        self.draw_ocean()
        self.draw_islands()
        self.draw_treasure_features()
        self.draw_day_job_target()
        for port in self.ports:
            self.draw_port(port)
        self.draw_mission_waypoint()
        for escort in self.fleet:
            self.draw_ship(escort.x, escort.y, escort.heading, False, escort.hull, escort.max_hull, allied=True)
            label_pos = self.world_to_screen(escort.x, escort.y - 56)
            label = self.tiny_font.render(escort.name, True, (210, 237, 220))
            label_rect = label.get_rect(center=label_pos)
            pygame.draw.rect(self.screen, (25, 48, 42), label_rect.inflate(8, 4), border_radius=3)
            self.screen.blit(label, label_rect)
        for pirate in self.pirates:
            if not pirate.dead:
                self.draw_ship(pirate.x, pirate.y, pirate.heading, False, pirate.hull, pirate.max_hull)
                if pirate.objective_target:
                    target_pos = self.world_to_screen(pirate.x, pirate.y)
                    pygame.draw.circle(self.screen, (255, 185, 92), target_pos, max(17, int(27 * self.camera_zoom)), max(2, int(3 * self.camera_zoom)))
                if self.camera_zoom > 0.72:
                    label_pos = self.world_to_screen(pirate.x, pirate.y - 52)
                    label_color = (255, 191, 113) if pirate.objective_target else (255, 224, 185)
                    label = self.tiny_font.render(pirate.name, True, label_color)
                    label_rect = label.get_rect(center=label_pos)
                    pygame.draw.rect(self.screen, (37, 28, 24), label_rect.inflate(8, 4), border_radius=3)
                    self.screen.blit(label, label_rect)
        self.draw_ship(self.ship_x, self.ship_y, self.ship_heading, True, rowing=self.oars_deployed)
        self.draw_cannonballs()

    def draw_mission_waypoint(self):
        target = self.mission_navigation_target()
        if not target:
            return
        target_name, target_x, target_y, target_kind = target
        sx, sy = self.world_to_screen(target_x, target_y)
        pulse = 23 + int((math.sin(self.world_time * 3.0) + 1.0) * 5)
        color = (255, 201, 111) if target_kind == "battlefield" else (255, 230, 160)
        if -80 <= sx <= self.screen.get_width() + 80 and -80 <= sy <= self.screen.get_height() + 80:
            pygame.draw.circle(self.screen, color, (sx, sy), max(10, int(pulse * self.camera_zoom)), max(2, int(3 * self.camera_zoom)))
            pygame.draw.line(self.screen, color, (sx - 13, sy), (sx + 13, sy), max(2, int(3 * self.camera_zoom)))
            pygame.draw.line(self.screen, color, (sx, sy - 13), (sx, sy + 13), max(2, int(3 * self.camera_zoom)))
            caption = "BATTLE WATERS" if target_kind == "battlefield" else "MISSION PORT"
            label = self.tiny_font.render(f"{caption}: {target_name.upper()}", True, (255, 229, 176))
            label_rect = label.get_rect(center=(sx, sy - max(31, int(38 * self.camera_zoom))))
            pygame.draw.rect(self.screen, (39, 29, 21), label_rect.inflate(10, 5), border_radius=3)
            self.screen.blit(label, label_rect)

    def draw_hud(self):
        width, height = self.screen.get_size()
        panel = pygame.Rect(18, 16, 480, 196)
        pygame.draw.rect(self.screen, (38, 25, 19), panel.inflate(6, 6), border_radius=7)
        pygame.draw.rect(self.screen, (120, 77, 43), panel, border_radius=6)
        pygame.draw.rect(self.screen, (221, 185, 122), panel.inflate(-6, -6), 2, border_radius=5)
        title = self.title_font.render("TIDEBOUND", True, (247, 221, 170))
        self.screen.blit(title, (panel.x + 14, panel.y + 7))
        gold_text = self.small_font.render(f"Pieces of eight: {self.gold} g", True, (255, 236, 193))
        self.screen.blit(gold_text, (panel.x + 16, panel.y + 63))
        hull_text = self.small_font.render(f"Hull {int(100 * self.player_hull / max(1, self.player_max_hull))}%", True, (245, 224, 185))
        self.screen.blit(hull_text, (panel.x + 16, panel.y + 112))
        bar = pygame.Rect(panel.x + 69, panel.y + 119, 150, 13)
        pygame.draw.rect(self.screen, (37, 31, 25), bar)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * self.player_hull / max(1, self.player_max_hull)), bar.height)
        pygame.draw.rect(self.screen, (159, 55, 42), fill)
        pygame.draw.rect(self.screen, (232, 202, 155), bar, 1)
        speed = math.hypot(self.ship_vx, self.ship_vy)
        self.screen.blit(self.small_font.render(f"Way: {int(speed)} kn", True, (255, 236, 193)), (panel.x + 231, panel.y + 112))
        ship_line = self.tiny_font.render(f"Flagship: {self.player_ship_name}", True, (255, 236, 193))
        order_display = {"fight": "Fight", "hold_fire": "Hold fire", "gather": "Gather", "follow": "Follow"}.get(self.fleet_order, self.fleet_order.title())
        fleet_line = self.tiny_font.render(f"{self.current_ship}  |  Escorts: {len(self.fleet)}  |  Orders: {order_display}", True, (255, 236, 193))
        self.screen.blit(ship_line, (panel.x + 16, panel.y + 147))
        self.screen.blit(fleet_line, (panel.x + 16, panel.y + 171))
        right_x = width - 285
        info = pygame.Rect(right_x, 16, 267, 160)
        pygame.draw.rect(self.screen, (38, 25, 19), info.inflate(6, 6), border_radius=7)
        pygame.draw.rect(self.screen, (120, 77, 43), info, border_radius=6)
        pygame.draw.rect(self.screen, (221, 185, 122), info.inflate(-6, -6), 2, border_radius=5)
        wind_text = self.small_font.render(f"Wind: {int(self.wind_angle)} deg", True, (255, 236, 193))
        sails_text = self.small_font.render(f"Sails: {int(self.sail_setting * 100)}%", True, (255, 236, 193))
        zoom_text = self.small_font.render(f"Chart zoom: {int(self.camera_zoom * 100)}%", True, (255, 236, 193))
        oars_text = self.small_font.render(f"Oars: {'OUT' if self.oars_deployed else 'STOWED'}  (O)", True, (255, 236, 193))
        self.screen.blit(wind_text, (info.x + 14, info.y + 12))
        self.screen.blit(sails_text, (info.x + 14, info.y + 45))
        self.screen.blit(zoom_text, (info.x + 14, info.y + 78))
        self.screen.blit(oars_text, (info.x + 14, info.y + 109))
        arrow_center = (info.x + 226, info.y + 64)
        pygame.draw.circle(self.screen, (225, 200, 153), arrow_center, 20, 2)
        direction = math.radians(self.wind_angle)
        tip = (arrow_center[0] + int(math.cos(direction) * 15), arrow_center[1] + int(math.sin(direction) * 15))
        pygame.draw.line(self.screen, (245, 226, 182), arrow_center, tip, 3)
        pygame.draw.circle(self.screen, (245, 226, 182), tip, 3)
        self.draw_mini_map()
        if self.mission_result_timer > 0:
            result_width = min(680, width - 48)
            result_box = pygame.Rect(width // 2 - result_width // 2, 222, result_width, 88)
            pygame.draw.rect(self.screen, (37, 25, 18), result_box.inflate(8, 8), border_radius=7)
            pygame.draw.rect(self.screen, (221, 190, 123), result_box, border_radius=6)
            pygame.draw.rect(self.screen, (126, 83, 43), result_box.inflate(-6, -6), 2, border_radius=5)
            heading = self.font.render("VOYAGE COMPLETE", True, (255, 230, 173))
            detail = self.small_font.render(f"{self.mission_result_title}  •  Reward: {self.mission_result_reward} gold", True, (255, 239, 207))
            self.screen.blit(heading, heading.get_rect(midtop=(result_box.centerx, result_box.y + 8)))
            self.screen.blit(detail, detail.get_rect(midtop=(result_box.centerx, result_box.y + 49)))
        active = self.active_mission()
        day_job = self.active_day_job
        if active:
            objective = self.mission_guidance_text(active)
            quest_box = pygame.Rect(18, height - 190, min(760, width - 36), 84)
            pygame.draw.rect(self.screen, (38, 25, 19), quest_box.inflate(5, 5), border_radius=6)
            pygame.draw.rect(self.screen, (120, 77, 43), quest_box, border_radius=6)
            pygame.draw.rect(self.screen, (221, 185, 122), quest_box.inflate(-5, -5), 1, border_radius=5)
            self.screen.blit(self.small_font.render(active.name.upper(), True, (250, 222, 168)), (quest_box.x + 14, quest_box.y + 8))
            objective_surf = self.tiny_font.render(objective, True, (240, 239, 212))
            if objective_surf.get_width() > quest_box.width - 26:
                objective_lines = wrap_text(self.tiny_font, objective, quest_box.width - 26)
                for line_index, line in enumerate(objective_lines[:2]):
                    self.screen.blit(self.tiny_font.render(line, True, (240, 239, 212)), (quest_box.x + 14, quest_box.y + 42 + line_index * 22))
            else:
                self.screen.blit(objective_surf, (quest_box.x + 14, quest_box.y + 46))
        day_job_text = self.day_job_hud_text()
        if day_job_text:
            if active and width < 1320:
                day_box = pygame.Rect(18, height - 282, min(720, width - 36), 84)
            else:
                day_box = pygame.Rect(max(18, width - 530), height - 190, min(512, width - 36), 84)
            pygame.draw.rect(self.screen, (38, 31, 20), day_box.inflate(5, 5), border_radius=6)
            pygame.draw.rect(self.screen, (126, 96, 50), day_box, border_radius=6)
            pygame.draw.rect(self.screen, (229, 197, 125), day_box.inflate(-5, -5), 1, border_radius=5)
            self.screen.blit(self.small_font.render("DAY WORK  |  " + self.active_day_job.title.upper(), True, (250, 222, 168)), (day_box.x + 14, day_box.y + 8))
            self.screen.blit(self.small_font.render(day_job_text, True, (240, 239, 212)), (day_box.x + 14, day_box.y + 46))
        if self.near_port and not self.docked_port:
            prompt = self.small_font.render(f"E  Come alongside {self.near_port.name}", True, (255, 239, 198))
            box = prompt.get_rect(center=(width // 2, height - 35)).inflate(25, 13)
            pygame.draw.rect(self.screen, (36, 29, 21), box, border_radius=5)
            self.screen.blit(prompt, prompt.get_rect(center=box.center))
        elif self.docked_port:
            prompt = self.small_font.render(f"{self.docked_port}  |  E: cast off   Q: harbourmaster   B: shipyard", True, (255, 239, 198))
            box = prompt.get_rect(center=(width // 2, height - 35)).inflate(25, 13)
            pygame.draw.rect(self.screen, (36, 29, 21), box, border_radius=5)
            self.screen.blit(prompt, prompt.get_rect(center=box.center))
        if not self.docked_port:
            bottle = self.nearest_unfound_bottle(130.0)
            site = self.nearest_treasure_shore(230.0)
            prompt_text = None
            rescue_distance = self.day_job_rescue_distance()
            if rescue_distance <= 180:
                prompt_text = "R  Bring the stranded crew aboard"
            elif bottle:
                prompt_text = "R  Recover the bottle and its treasure chart"
            elif site and site.map_found and not site.dug:
                prompt_text = f"R  Search the beach of {site.island_name}"
            elif site and site.dug:
                prompt_text = f"Treasure claimed on {site.island_name}"
            elif site and not site.map_found:
                prompt_text = f"{site.island_name}: an uncharted beach — find a treasure map"
            if prompt_text:
                prompt = self.small_font.render(prompt_text, True, (255, 239, 198))
                box = prompt.get_rect(center=(width // 2, height - 78)).inflate(28, 14)
                pygame.draw.rect(self.screen, (36, 29, 21), box, border_radius=5)
                pygame.draw.rect(self.screen, (157, 116, 71), box, 2, border_radius=5)
                self.screen.blit(prompt, prompt.get_rect(center=box.center))

    def draw_mini_map(self):
        width = self.screen.get_width()
        rect = pygame.Rect(width - 230, 184, 210, 145)
        pygame.draw.rect(self.screen, (29, 39, 36), rect.inflate(6, 6), border_radius=5)
        pygame.draw.rect(self.screen, (154, 119, 76), rect, border_radius=4)
        inner = rect.inflate(-7, -7)
        sx = inner.width / WORLD_WIDTH
        sy = inner.height / WORLD_HEIGHT
        for polygon in self.land:
            points = [(inner.x + int(x * sx), inner.y + int(y * sy)) for x, y in polygon]
            pygame.draw.polygon(self.screen, (75, 123, 78), points)
            pygame.draw.lines(self.screen, (190, 171, 120), True, points, 1)
        for site in self.treasure_sites:
            if site.revealed:
                points = [(inner.x + int(x * sx), inner.y + int(y * sy)) for x, y in site.polygon]
                pygame.draw.polygon(self.screen, (73, 132, 81), points)
                pygame.draw.lines(self.screen, (208, 188, 135), True, points, 1)
        for port in self.ports:
            point = (inner.x + int(port.x * sx), inner.y + int(port.y * sy))
            pygame.draw.circle(self.screen, (243, 210, 139), point, 3)
        for pirate in self.pirates:
            if not pirate.dead:
                point = (inner.x + int(pirate.x * sx), inner.y + int(pirate.y * sy))
                color = (255, 177, 74) if pirate.objective_target else (184, 60, 49)
                radius = 4 if pirate.objective_target else 2
                pygame.draw.circle(self.screen, color, point, radius)
        navigation = self.mission_navigation_target()
        if navigation:
            target_name, target_x, target_y, target_kind = navigation
            target_point = (inner.x + int(target_x * sx), inner.y + int(target_y * sy))
            player_point = (inner.x + int(self.ship_x * sx), inner.y + int(self.ship_y * sy))
            pygame.draw.line(self.screen, (255, 214, 130), player_point, target_point, 2)
            pygame.draw.circle(self.screen, (255, 222, 135), target_point, 6)
            pygame.draw.circle(self.screen, (45, 37, 27), target_point, 6, 1)
        day_job = self.active_day_job
        if day_job and day_job.kind == "rescue" and not day_job.rescued and day_job.target_x is not None:
            rescue_point = (inner.x + int(day_job.target_x * sx), inner.y + int(day_job.target_y * sy))
            pygame.draw.circle(self.screen, (255, 219, 139), rescue_point, 4)
        point = (inner.x + int(self.ship_x * sx), inner.y + int(self.ship_y * sy))
        pygame.draw.circle(self.screen, (255, 250, 222), point, 3)
        title = self.tiny_font.render("CHART OF THE ISLES", True, (246, 222, 174))
        self.screen.blit(title, (rect.x + 8, rect.y + 5))

    def draw_help(self):
        width, height = self.screen.get_size()
        box = pygame.Rect(width - 470, height - 560, 450, 540)
        pygame.draw.rect(self.screen, (35, 26, 21), box, border_radius=6)
        pygame.draw.rect(self.screen, (146, 104, 64), box, 2, border_radius=6)
        self.screen.blit(self.small_font.render("CAPTAIN'S ORDERS", True, (248, 221, 172)), (box.x + 14, box.y + 10))
        lines = [
            "W / S   Trim or reef sails",
            "O       Ship / stow the oars",
            "A / D   Work the rudder",
            "Z       Port broadside",
            "X       Starboard broadside",
            "E       Dock / cast off",
            "Q       Speak at a port / browse day work",
            "R       Rescue / recover maps / dig for treasure",
            "B       Open the shipyard in port",
            "F       Fleet: fight nearby pirates",
            "H       Fleet: hold fire, keep formation",
            "G       Fleet: gather around your ship",
            "V       Fleet: follow in formation",
            "T       Open treasure charts",
            "Wheel   Zoom at mouse pointer",
            "Mouse drag   Pan the chart",
            "C       Centre on your ship",
            "J       Captain's log",
            "F1      Show / hide these orders",
        ]
        for index, line in enumerate(lines):
            rendered = self.tiny_font.render(line, True, (235, 222, 194))
            self.screen.blit(rendered, (box.x + 14, box.y + 48 + index * 25))

    def draw_toast(self):
        if self.toast_time <= 0:
            return
        width = self.screen.get_width()
        text = self.small_font.render(self.toast, True, (252, 235, 200))
        box = text.get_rect(center=(width // 2, 25)).inflate(30, 15)
        pygame.draw.rect(self.screen, (42, 27, 20), box, border_radius=6)
        pygame.draw.rect(self.screen, (157, 116, 71), box, 2, border_radius=6)
        self.screen.blit(text, text.get_rect(center=box.center))

    def draw_conversation(self):
        if not self.conversation or not self.conversation.current:
            return
        width, height = self.screen.get_size()
        box_height = min(390, height - 36)
        box = pygame.Rect(30, height - box_height - 18, width - 60, box_height)
        pygame.draw.rect(self.screen, (39, 25, 18), box.inflate(8, 8), border_radius=8)
        pygame.draw.rect(self.screen, (125, 79, 43), box, border_radius=7)
        parchment = box.inflate(-8, -8)
        pygame.draw.rect(self.screen, (224, 207, 163), parchment, border_radius=5)
        pygame.draw.rect(self.screen, (155, 118, 73), parchment, 2, border_radius=5)
        heading = self.title_font.render(self.dialogue_speaker.upper(), True, (83, 48, 31))
        self.screen.blit(heading, (box.x + 24, box.y + 12))
        pygame.draw.line(self.screen, (156, 119, 77), (box.x + 22, box.y + 61), (box.right - 22, box.y + 61), 2)
        current = self.conversation.current
        if isinstance(current, TextNode):
            lines = wrap_text(self.font, current.text, box.width - 64)
            line_step = 38
            max_lines = max(1, (box.height - 112) // line_step)
            for index, line in enumerate(lines[:max_lines]):
                rendered = self.font.render(line, True, (56, 43, 31))
                self.screen.blit(rendered, (box.x + 30, box.y + 78 + index * line_step))
            prompt = self.small_font.render("Enter / Space: continue", True, (104, 74, 48))
            self.screen.blit(prompt, (box.right - prompt.get_width() - 28, box.bottom - 38))
        elif isinstance(current, ChoiceNode):
            self.screen.blit(self.font.render("What do you say?", True, (56, 43, 31)), (box.x + 30, box.y + 72))
            start_y = box.y + 116
            row_height = 54 if len(current.options) >= 4 else 66
            for index, option in enumerate(current.options):
                selected = index == self.conversation.selected
                text = ("▶  " if selected else "   ") + option.text
                color = (93, 44, 26) if selected else (64, 51, 37)
                lines = wrap_text(self.small_font, text, box.width - 90)
                row_y = start_y + index * row_height
                if selected:
                    highlight = pygame.Rect(box.x + 22, row_y - 4, box.width - 44, row_height - 5)
                    pygame.draw.rect(self.screen, (210, 188, 143), highlight, border_radius=4)
                for line_index, line in enumerate(lines[:2]):
                    self.screen.blit(self.small_font.render(line, True, color), (box.x + 34, row_y + line_index * 25))
            prompt = self.small_font.render("Up / Down to choose   Enter to speak", True, (104, 74, 48))
            self.screen.blit(prompt, (box.right - prompt.get_width() - 28, box.bottom - 38))

    def draw_treasure_chart(self):
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((9, 17, 19, 205))
        self.screen.blit(overlay, (0, 0))
        box_width = min(1040, width - 48)
        box_height = min(720, height - 48)
        box = pygame.Rect(width // 2 - box_width // 2, height // 2 - box_height // 2, box_width, box_height)
        pygame.draw.rect(self.screen, (45, 27, 18), box.inflate(10, 10), border_radius=8)
        pygame.draw.rect(self.screen, (225, 207, 163), box, border_radius=5)
        pygame.draw.rect(self.screen, (144, 105, 66), box, 3, border_radius=5)
        title = self.big_font.render("BOTTLES, CHARTS & BURIED GOLD", True, (75, 44, 27))
        title_rect = title.get_rect(midtop=(box.centerx, box.y + 18))
        self.screen.blit(title, title_rect)
        y = box.y + 92
        found_sites = [site for site in self.treasure_sites if site.map_found]
        if not found_sites:
            message = "No treasure charts yet. Keep a sharp lookout while sailing: green-glass bottles bob on the open water. Sail close and press R to recover one."
            for index, line in enumerate(wrap_text(self.font, message, box.width - 90)):
                self.screen.blit(self.font.render(line, True, (73, 47, 31)), (box.x + 40, y + index * 39))
            y += 190
        else:
            for site in found_sites:
                if y > box.bottom - 150:
                    break
                card = pygame.Rect(box.x + 24, y, box.width - 48, 165)
                pygame.draw.rect(self.screen, (211, 192, 151), card, border_radius=5)
                pygame.draw.rect(self.screen, (159, 123, 80), card, 2, border_radius=5)
                name = self.font.render(site.map_title, True, (76, 43, 27))
                self.screen.blit(name, (card.x + 16, card.y + 10))
                status = "CHEST RECOVERED" if site.dug else ("ISLAND CHARTED" if site.revealed else "ISLAND STILL HIDDEN")
                status_surf = self.tiny_font.render(status, True, (111, 74, 43))
                self.screen.blit(status_surf, (card.right - status_surf.get_width() - 14, card.y + 16))
                clue_lines = wrap_text(self.tiny_font, f"{site.island_name}: {site.clue}", card.width - 36)
                for line_index, line in enumerate(clue_lines[:3]):
                    self.screen.blit(self.tiny_font.render(line, True, (67, 52, 37)), (card.x + 16, card.y + 48 + line_index * 22))
                riddle_lines = wrap_text(self.tiny_font, f"Beach riddle: {site.riddle}", card.width - 36)
                for line_index, line in enumerate(riddle_lines[:2]):
                    self.screen.blit(self.tiny_font.render(line, True, (92, 66, 43)), (card.x + 16, card.y + 113 + line_index * 22))
                y += 176
        if self.relics:
            relic_text = self.small_font.render("Keepsakes: " + ", ".join(self.relics), True, (82, 53, 32))
            self.screen.blit(relic_text, (box.x + 34, min(y + 4, box.bottom - 74)))
        footer = self.small_font.render("Sail near a drifting bottle and press R. Find its cay, approach the marked beach, then press R to answer the riddle. T / Esc: close", True, (104, 74, 48))
        footer_rect = footer.get_rect(midbottom=(box.centerx, box.bottom - 16))
        self.screen.blit(footer, footer_rect)

    def draw_journal(self):
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((9, 17, 19, 185))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(width // 2 - 390, height // 2 - 325, 780, 650)
        pygame.draw.rect(self.screen, (45, 27, 18), box.inflate(10, 10), border_radius=8)
        pygame.draw.rect(self.screen, (225, 207, 163), box, border_radius=5)
        pygame.draw.rect(self.screen, (144, 105, 66), box, 3, border_radius=5)
        title = self.big_font.render("THE CAPTAIN'S LOG", True, (75, 44, 27))
        self.screen.blit(title, (box.x + 28, box.y + 20))
        y = box.y + 82
        active = self.active_mission()
        day_job = self.active_day_job
        if active:
            objective = self.mission_guidance_text(active)
            self.screen.blit(self.font.render(f"Current voyage: {active.name}", True, (73, 47, 31)), (box.x + 30, y))
            objective_lines = wrap_text(self.small_font, objective, box.width - 60)
            for line_index, line in enumerate(objective_lines[:2]):
                self.screen.blit(self.small_font.render(line, True, (97, 66, 42)), (box.x + 30, y + 36 + line_index * 29))
            y += 88 if len(objective_lines) > 1 else 78
        else:
            self.screen.blit(self.font.render("No story voyage under contract.", True, (73, 47, 31)), (box.x + 30, y))
            y += 43
        if day_job:
            self.screen.blit(self.font.render(f"Day work: {day_job.title}", True, (73, 47, 31)), (box.x + 30, y))
            self.screen.blit(self.small_font.render(self.day_job_objective(), True, (97, 66, 42)), (box.x + 30, y + 36))
            y += 78
        pygame.draw.line(self.screen, (160, 125, 80), (box.x + 25, y), (box.right - 25, y), 1)
        y += 18
        for entry in self.journal[-10:]:
            lines = wrap_text(self.small_font, "- " + entry, box.width - 60)
            for line in lines:
                if y > box.bottom - 42:
                    break
                self.screen.blit(self.small_font.render(line, True, (70, 55, 39)), (box.x + 32, y))
                y += 31
            y += 9
        close = self.small_font.render("J / Esc: close the log", True, (104, 74, 48))
        self.screen.blit(close, (box.right - close.get_width() - 25, box.bottom - 38))

    def draw(self):
        self.draw_world()
        self.draw_hud()
        if self.show_help and not self.conversation and not self.journal_open:
            self.draw_help()
        self.draw_toast()
        if self.conversation:
            self.draw_conversation()
        if self.journal_open:
            self.draw_journal()
        if self.treasure_chart_open:
            self.draw_treasure_chart()
        if self.shipyard_open:
            self.draw_shipyard()
        pygame.display.flip()
