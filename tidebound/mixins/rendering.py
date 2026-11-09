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

    def draw_reefs(self):
        """Draw translucent red shoal zones above the water and below ships/UI."""
        if not getattr(self, "reefs", None):
            return
        overlay_size = self.screen.get_size()
        overlay = getattr(self, "_reef_overlay_surface", None)
        if overlay is None or overlay.get_size() != overlay_size:
            overlay = pygame.Surface(overlay_size, pygame.SRCALPHA)
            self._reef_overlay_surface = overlay
        overlay.fill((0, 0, 0, 0))
        for reef in self.reefs:
            points = self.polygon_to_screen(reef.polygon)
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            if max(xs) < -24 or min(xs) > self.screen.get_width() + 24 or max(ys) < -24 or min(ys) > self.screen.get_height() + 24:
                continue
            pygame.draw.polygon(overlay, (197, 43, 48, 66), points)
            pygame.draw.lines(overlay, (236, 86, 77, 175), True, points, max(1, int(2 * self.camera_zoom)))
            # A broken inner contour makes the hazard read as a shoal, not land.
            center_x = sum(x for x, _ in points) / len(points)
            center_y = sum(y for _, y in points) / len(points)
            inner = [(int(center_x + (x - center_x) * 0.76),
                      int(center_y + (y - center_y) * 0.76)) for x, y in points]
            pygame.draw.lines(overlay, (255, 137, 113, 100), True, inner, max(1, int(self.camera_zoom)))
        self.screen.blit(overlay, (0, 0))
        if self.camera_zoom >= 0.78:
            for reef in self.reefs:
                sx, sy = self.world_to_screen(reef.center_x, reef.center_y)
                if -80 <= sx <= self.screen.get_width() + 80 and -40 <= sy <= self.screen.get_height() + 40:
                    label = fit_text_surface(self.tiny_font, "REEF", (255, 220, 203), 76, 20)
                    label_rect = label.get_rect(center=(sx, sy))
                    pygame.draw.rect(self.screen, (105, 28, 31), label_rect.inflate(8, 4), border_radius=3)
                    self.screen.blit(label, label_rect)

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

    def draw_shipwrecks(self):
        """Draw discovered wreck silhouettes as debris embedded in the sea."""
        for site in getattr(self, "shipwrecks", []):
            if not site.discovered:
                continue
            sx, sy = self.world_to_screen(site.x, site.y)
            if sx < -90 or sx > self.screen.get_width() + 90 or sy < -70 or sy > self.screen.get_height() + 70:
                continue
            angle = math.radians(site.heading)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            hull_local = [(-25, -7), (-17, -13), (20, -10), (14, -2), (22, 7), (-14, 11), (-24, 3)]
            hull_points = []
            for lx, ly in hull_local:
                hull_points.append((int(sx + (lx * cos_a - ly * sin_a) * self.camera_zoom),
                                    int(sy + (lx * sin_a + ly * cos_a) * self.camera_zoom)))
            hull_color = (67, 48, 34) if not site.fully_salvaged else (89, 75, 60)
            pygame.draw.polygon(self.screen, hull_color, hull_points)
            pygame.draw.lines(self.screen, (153, 113, 68), True, hull_points, max(1, int(2 * self.camera_zoom)))
            mast_a = (sx + int(-9 * cos_a * self.camera_zoom), sy + int(-9 * sin_a * self.camera_zoom))
            mast_b = (sx + int(27 * cos_a * self.camera_zoom), sy + int(27 * sin_a * self.camera_zoom))
            pygame.draw.line(self.screen, (91, 65, 42), mast_a, mast_b, max(1, int(3 * self.camera_zoom)))
            for offset in (-15, 4, 17):
                px = sx + int((offset * cos_a - 13 * sin_a) * self.camera_zoom)
                py = sy + int((offset * sin_a + 13 * cos_a) * self.camera_zoom)
                pygame.draw.line(self.screen, (133, 99, 62), (px - 4, py - 3), (px + 5, py + 4), max(1, int(2 * self.camera_zoom)))
            if self.camera_zoom >= 0.64:
                label_text = "SALVAGED WRECK" if site.fully_salvaged else "SHIPWRECK"
                label = fit_text_surface(self.tiny_font, label_text, (248, 222, 174), 145, 21)
                label_rect = label.get_rect(center=(sx, sy - max(23, int(31 * self.camera_zoom))))
                pygame.draw.rect(self.screen, (43, 35, 27), label_rect.inflate(8, 4), border_radius=3)
                self.screen.blit(label, label_rect)

    def draw_port(self, port):
        pier_start = self.world_to_screen(port.shore_x, port.shore_y)
        pier_end = self.world_to_screen(port.x, port.y)
        pygame.draw.line(self.screen, (76, 49, 33), pier_start, pier_end, max(5, int(14 * self.camera_zoom)))
        pygame.draw.line(self.screen, (155, 112, 70), pier_start, pier_end, max(2, int(8 * self.camera_zoom)))
        # A broad outer quay with nine alongside berths. Each finger pier
        # has enough separation for a full-sized vessel and its rigging.
        axis_x, axis_y = port.x - port.shore_x, port.y - port.shore_y
        axis_len = max(1.0, math.hypot(axis_x, axis_y))
        axis_x, axis_y = axis_x / axis_len, axis_y / axis_len
        perp_x, perp_y = -axis_y, axis_x
        for berth_slot in range(PORT_BERTH_COUNT):
            offset = (berth_slot - PORT_BERTH_CENTER_SLOT) * PORT_BERTH_SPACING
            bx = port.x + perp_x * offset
            by = port.y + perp_y * offset
            berth_start = self.world_to_screen(bx - axis_x * 45.0, by - axis_y * 45.0)
            berth_end = self.world_to_screen(bx + axis_x * 100.0, by + axis_y * 100.0)
            pygame.draw.line(self.screen, (76, 49, 33), berth_start, berth_end, max(4, int(10 * self.camera_zoom)))
            pygame.draw.line(self.screen, (155, 112, 70), berth_start, berth_end, max(2, int(5 * self.camera_zoom)))
            cleat = self.world_to_screen(bx + axis_x * 100.0, by + axis_y * 100.0)
            pygame.draw.circle(self.screen, (213, 187, 139), cleat, max(2, int(3 * self.camera_zoom)))
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
        # Small stone coastal battery: the dark barrels represent the harbour's
        # automatic defensive guns which engage pirates in nearby waters.
        battery_y = sy + int(18 * self.camera_zoom)
        battery_x = sx - int(18 * self.camera_zoom)
        pygame.draw.rect(self.screen, (111, 100, 80),
                         (battery_x - max(4, int(8 * self.camera_zoom)), battery_y - max(3, int(5 * self.camera_zoom)),
                          max(9, int(17 * self.camera_zoom)), max(7, int(10 * self.camera_zoom))), border_radius=2)
        for barrel_offset in (-4, 4):
            start = (battery_x + int(barrel_offset * self.camera_zoom), battery_y)
            end = (start[0] + int(10 * self.camera_zoom), start[1] - int(7 * self.camera_zoom))
            pygame.draw.line(self.screen, (42, 39, 34), start, end, max(2, int(3 * self.camera_zoom)))
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
        faction_color = FACTION_COLOURS.get(getattr(port, "faction", "Independent"), (35, 30, 28))
        flag_points = [(flag_x, flag_y - int(22 * self.camera_zoom)),
                       (flag_x + int(17 * self.camera_zoom), flag_y - int(17 * self.camera_zoom)),
                       (flag_x, flag_y - int(12 * self.camera_zoom))]
        pygame.draw.polygon(self.screen, faction_color, flag_points)
        pygame.draw.lines(self.screen, (224, 203, 157), False, flag_points, max(1, int(self.camera_zoom)))
        label_x, label_y = self.world_to_screen(port.x, port.y + 30)
        label = fit_text_surface(self.small_font, port.name, (255, 236, 190), 170, 28)
        faction_dot = max(3, int(4 * self.camera_zoom))
        label_box = label.get_rect(center=(label_x, label_y))
        pygame.draw.rect(self.screen, (28, 45, 42), label_box.inflate(12, 6), border_radius=4)
        pygame.draw.circle(self.screen, faction_color, (label_box.left - 3, label_box.centery), faction_dot)
        self.screen.blit(label, label_box)

    def create_ship_surface(self, player=True, allied=False, rowing=False, ship_type="Sloop", faction=""):
        cache = getattr(self, "ship_surface_cache", None)
        if cache is None:
            cache = {}
            self.ship_surface_cache = cache
        rowing_phase = int(round(math.sin(self.world_time * 8.0) * 7)) if rowing else 0
        if not faction:
            faction = "player" if player else "allied" if allied else "pirate"
        cache_key = (player, allied, rowing, ship_type, faction, self.player_livery if player else None, rowing_phase)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        surface = pygame.Surface((132, 92), pygame.SRCALPHA)
        if player:
            _, hull_color, trim_color, sail_color = SHIP_LIVERIES[self.player_livery]
        elif allied:
            hull_color = (42, 80, 69)
            trim_color = (179, 190, 135)
            sail_color = (191, 220, 202)
        elif faction == "merchant":
            hull_color = (126, 83, 43)
            trim_color = (218, 180, 112)
            sail_color = (222, 211, 176)
        elif faction == "fishing":
            hull_color = (67, 91, 72)
            trim_color = (190, 172, 119)
            sail_color = (202, 191, 153)
        elif faction == "naval patrol":
            hull_color = (39, 60, 86)
            trim_color = (206, 194, 151)
            sail_color = (224, 224, 209)
        elif faction == "mail packet":
            hull_color = (107, 64, 54)
            trim_color = (218, 190, 143)
            sail_color = (220, 222, 200)
        elif faction == "whaler":
            hull_color = (73, 73, 61)
            trim_color = (180, 161, 123)
            sail_color = (170, 181, 169)
        else:
            hull_color = (69, 39, 34)
            trim_color = (165, 92, 65)
            sail_color = (155, 55, 48)
        sail_shadow = tuple(max(0, channel - 45) for channel in sail_color)

        profiles = {
            "Sloop": {
                "hull": [(12, 46), (29, 29), (94, 29), (118, 46), (94, 63), (29, 63)],
                "masts": [(61, 28)], "guns": 3, "rig": "gaff", "cabin": (28, 38, 18, 16),
            },
            "Cutter": {
                "hull": [(7, 46), (31, 35), (103, 35), (125, 46), (103, 57), (31, 57)],
                "masts": [(72, 26)], "guns": 2, "rig": "lateen", "cabin": (24, 39, 14, 14),
            },
            "Schooner": {
                "hull": [(6, 46), (25, 30), (105, 30), (125, 46), (105, 62), (25, 62)],
                "masts": [(43, 27), (83, 30)], "guns": 4, "rig": "foreaft", "cabin": (27, 37, 20, 18),
            },
            "Brigantine": {
                "hull": [(4, 46), (21, 22), (109, 22), (128, 46), (109, 70), (21, 70)],
                "masts": [(38, 21), (81, 24)], "guns": 5, "rig": "square", "cabin": (24, 36, 25, 20),
            },
            "Frigate": {
                "hull": [(2, 46), (17, 17), (113, 17), (130, 46), (113, 75), (17, 75)],
                "masts": [(29, 18), (60, 14), (92, 18)], "guns": 7, "rig": "three_mast", "cabin": (22, 33, 31, 25),
            },
        }
        profile = profiles.get(ship_type, profiles["Sloop"])
        hull = profile["hull"]
        shadow = [(x, y + 3) for x, y in hull]
        inset = []
        center_x = sum(x for x, _ in hull) / len(hull)
        center_y = sum(y for _, y in hull) / len(hull)
        for x, y in hull:
            inset.append((center_x + (x - center_x) * 0.84, center_y + (y - center_y) * 0.78))
        pygame.draw.polygon(surface, (34, 25, 21), shadow)
        pygame.draw.polygon(surface, (43, 30, 25), hull)
        pygame.draw.polygon(surface, hull_color, inset)
        pygame.draw.lines(surface, trim_color, True, inset, 3)
        pygame.draw.line(surface, (143, 100, 61), (24, 46), (112, 46), 3)

        cabin_x, cabin_y, cabin_w, cabin_h = profile["cabin"]
        pygame.draw.rect(surface, (73, 48, 34), (cabin_x, cabin_y, cabin_w, cabin_h), border_radius=3)
        pygame.draw.rect(surface, trim_color, (cabin_x + 2, cabin_y + 2, cabin_w - 4, cabin_h - 4), 1, border_radius=2)
        pygame.draw.line(surface, (221, 190, 135), (cabin_x + 3, cabin_y + 4), (cabin_x + cabin_w - 3, cabin_y + 4), 1)

        gun_count = profile["guns"]
        gun_spacing = 10 if gun_count >= 6 else 13
        gun_start = 66 - (gun_count - 1) * gun_spacing / 2
        for gun_index in range(gun_count):
            gun_x = int(gun_start + gun_index * gun_spacing)
            pygame.draw.circle(surface, (30, 25, 22), (gun_x, 29 if ship_type != "Cutter" else 36), 2)
            if ship_type in {"Brigantine", "Frigate"}:
                pygame.draw.circle(surface, (30, 25, 22), (gun_x, 63 if ship_type == "Brigantine" else 63), 2)

        for mast_index, (mast_x, mast_height) in enumerate(profile["masts"]):
            top_y = mast_height
            pygame.draw.line(surface, (53, 37, 26), (mast_x, 46), (mast_x, top_y), 3)
            pygame.draw.line(surface, (204, 182, 139), (mast_x - 1, top_y + 2), (mast_x - 1, 46), 1)
            if profile["rig"] == "lateen":
                sail_points = [(mast_x, top_y + 3), (mast_x + 21, 39), (mast_x - 3, 41)]
                pygame.draw.polygon(surface, sail_color, sail_points)
                pygame.draw.line(surface, sail_shadow, (mast_x, top_y + 3), (mast_x + 21, 39), 2)
                pygame.draw.line(surface, (224, 210, 174), (mast_x - 4, top_y + 1), (mast_x + 25, 41), 1)
            elif profile["rig"] in {"square", "three_mast"}:
                sail_w = 17 if ship_type == "Brigantine" else 15
                sail_h = 15 if ship_type == "Brigantine" else 14
                sail_rect = pygame.Rect(mast_x - sail_w // 2, top_y + 6, sail_w, sail_h)
                pygame.draw.polygon(surface, sail_shadow, [(sail_rect.left, sail_rect.top), (sail_rect.right, sail_rect.top + 3), (sail_rect.right, sail_rect.bottom), (sail_rect.left, sail_rect.bottom - 2)])
                pygame.draw.polygon(surface, sail_color, [(sail_rect.left + 2, sail_rect.top), (sail_rect.right - 2, sail_rect.top + 2), (sail_rect.right - 2, sail_rect.bottom - 2), (sail_rect.left + 2, sail_rect.bottom - 3)])
                pygame.draw.line(surface, (224, 210, 174), (mast_x - sail_w // 2 - 3, sail_rect.top), (mast_x + sail_w // 2 + 3, sail_rect.top + 2), 1)
                pygame.draw.line(surface, (224, 210, 174), (mast_x, top_y), (mast_x, sail_rect.bottom + 3), 1)
            else:
                sail_w = 19 if ship_type == "Schooner" else 24
                sail_h = 17 if ship_type == "Schooner" else 20
                sail_points = [(mast_x, top_y + 4), (mast_x + sail_w, top_y + sail_h), (mast_x, top_y + sail_h + 6)]
                pygame.draw.polygon(surface, sail_color, sail_points)
                pygame.draw.polygon(surface, sail_shadow, [(mast_x, top_y + 4), (mast_x, top_y + sail_h + 6), (mast_x - sail_w // 2, top_y + sail_h // 2)])
                pygame.draw.line(surface, (224, 210, 174), (mast_x, top_y), (mast_x + sail_w, top_y + sail_h), 1)
            if profile["rig"] == "foreaft" and mast_index == 0:
                pygame.draw.line(surface, (207, 188, 151), (mast_x, top_y + 2), (mast_x + 31, 43), 1)

        pygame.draw.line(surface, (71, 47, 29), (19, 46), (2, 46), 3)
        pygame.draw.line(surface, (71, 47, 29), (112, 46), (130, 46), 2)
        flag_y = max(8, min(mast_height for _, mast_height in profile["masts"]) - 5)
        flag_x = profile["masts"][0][0]
        pygame.draw.line(surface, (44, 32, 25), (flag_x, flag_y + 2), (flag_x, flag_y - 8), 1)
        flag_color = (24, 22, 20) if faction == "pirate" else (225, 218, 183) if allied else (53, 87, 126) if faction == "naval patrol" else (173, 139, 74) if faction == "merchant" else (100, 123, 91) if faction == "fishing" else (158, 62, 49) if faction == "mail packet" else (100, 100, 91)
        pygame.draw.polygon(surface, flag_color, [(flag_x, flag_y - 8), (flag_x + 13, flag_y - 5), (flag_x, flag_y - 2)])
        if player:
            pygame.draw.circle(surface, (48, 37, 29), (cabin_x + cabin_w // 2, cabin_y + 4), 4)
            pygame.draw.circle(surface, (235, 224, 196), (cabin_x + cabin_w // 2 - 1, cabin_y + 3), 1)
        if rowing:
            stroke = math.sin(self.world_time * 8.0) * 3.5
            oar_count = 5 if ship_type in {"Sloop", "Cutter"} else 7 if ship_type in {"Schooner", "Brigantine"} else 9
            for oar_index in range(oar_count):
                oar_x = int(24 + oar_index * (82 / max(1, oar_count - 1)))
                upper_tip = (int(oar_x + stroke), 7)
                lower_tip = (int(oar_x - stroke), 85)
                pygame.draw.line(surface, (92, 57, 31), (oar_x, 35), upper_tip, 2)
                pygame.draw.line(surface, (92, 57, 31), (oar_x, 57), lower_tip, 2)
                pygame.draw.ellipse(surface, (153, 111, 65), (upper_tip[0] - 4, upper_tip[1] - 3, 8, 5))
                pygame.draw.ellipse(surface, (153, 111, 65), (lower_tip[0] - 4, lower_tip[1] - 2, 8, 5))
        cache[cache_key] = surface
        if len(cache) > 96:
            cache.pop(next(iter(cache)))
        return surface

    def draw_ship(self, x, y, heading, player=True, hull=None, max_hull=None, allied=False, rowing=False, ship_type="Sloop", faction="", hit_flash=0.0, sinking_progress=0.0, damage_marks=None):
        """Render a vessel with progressive battle scars and a sinking animation."""
        progress = max(0.0, min(1.0, float(sinking_progress)))
        base = self.create_ship_surface(player, allied, rowing, ship_type, faction)
        sink_scale = 1.0 - 0.36 * progress
        scaled_w = max(22, int(base.get_width() * self.camera_zoom * sink_scale))
        scaled_h = max(18, int(base.get_height() * self.camera_zoom * sink_scale))
        if scaled_w != base.get_width() or scaled_h != base.get_height():
            base = pygame.transform.smoothscale(base, (scaled_w, scaled_h))
        render_heading = heading + math.sin(progress * math.pi) * 28.0
        rotated = pygame.transform.rotate(base, -render_heading)
        if progress > 0.0:
            rotated.set_alpha(max(0, int(255 * (1.0 - progress))))
        drift_x = math.cos(math.radians(heading)) * progress * 14.0
        drift_y = math.sin(math.radians(heading)) * progress * 14.0 + progress * 35.0
        pos = self.world_to_screen(x + drift_x, y + drift_y)
        rect = rotated.get_rect(center=pos)
        if progress > 0.02:
            ring = max(8, int((21.0 + progress * 18.0) * self.camera_zoom))
            pygame.draw.ellipse(self.screen, (177, 211, 207), (pos[0] - ring * 1.6, pos[1] - ring * 0.42,
                                                                  ring * 3.2, ring * 0.84), max(1, int(2 * self.camera_zoom)))
            pygame.draw.ellipse(self.screen, (220, 229, 211), (pos[0] - ring * 1.12, pos[1] - ring * 0.27,
                                                                  ring * 2.24, ring * 0.54), 1)
        self.screen.blit(rotated, rect)

        if progress < 0.72 and hull is not None and max_hull:
            ratio = max(0.0, min(1.0, float(hull) / max(1.0, float(max_hull))))
            self.draw_ship_damage_marks(x, y, heading, ratio, hit_flash, damage_marks)
        if not player and hull is not None and max_hull and progress <= 0.02:
            bar_w = max(24, int(42 * self.camera_zoom))
            bar = pygame.Rect(pos[0] - bar_w // 2, pos[1] - int(38 * self.camera_zoom), bar_w, 5)
            pygame.draw.rect(self.screen, (40, 28, 27), bar)
            fill = pygame.Rect(bar.x, bar.y, int(bar.width * max(0, hull) / max_hull), bar.height)
            pygame.draw.rect(self.screen, (70, 171, 126) if allied else (171, 52, 40), fill)

    def draw_ship_damage_marks(self, x, y, heading, hull_ratio, hit_flash=0.0, damage_marks=None):
        """Scorch holes and splinter cracks accumulate as a ship loses hull."""
        if hull_ratio >= 0.90 and hit_flash <= 0.0 and not damage_marks:
            return
        angle = math.radians(heading)
        positions = []
        if hull_ratio < 0.90:
            positions.append((-13.0, -5.0))
        if hull_ratio < 0.70:
            positions.extend([(7.0, 6.0), (20.0, -2.0)])
        if hull_ratio < 0.43:
            positions.extend([(-3.0, 9.0), (25.0, 5.0)])
        for index, (local_x, local_y) in enumerate(positions):
            world_x = x + math.cos(angle) * local_x - math.sin(angle) * local_y
            world_y = y + math.sin(angle) * local_x + math.cos(angle) * local_y
            point = self.world_to_screen(world_x, world_y)
            radius = max(2, int((3.2 + index * 0.30) * self.camera_zoom))
            pygame.draw.circle(self.screen, (35, 25, 21), point, radius + 1)
            pygame.draw.circle(self.screen, (105, 55, 35), point, max(1, radius - 1))
            if hull_ratio < 0.43 and index in (1, 3):
                endpoint = self.world_to_screen(world_x + math.cos(angle) * 8.0,
                                                world_y + math.sin(angle) * 8.0)
                pygame.draw.line(self.screen, (42, 29, 23), point, endpoint, max(1, int(1.5 * self.camera_zoom)))

        # Individual cannon impacts leave persistent scars at their actual
        # strike positions, rather than only changing a generic damage level.
        for mark in (damage_marks or [])[-18:]:
            local_x = float(mark.get("x", 0.0))
            local_y = float(mark.get("y", 0.0))
            world_x = x + math.cos(angle) * local_x - math.sin(angle) * local_y
            world_y = y + math.sin(angle) * local_x + math.cos(angle) * local_y
            point = self.world_to_screen(world_x, world_y)
            radius = max(2, int(float(mark.get("size", 3.0)) * self.camera_zoom))
            pygame.draw.circle(self.screen, (27, 22, 19), point, radius + 1)
            pygame.draw.circle(self.screen, (112, 62, 39), point, max(1, radius - 1))
            crack_angle = angle + float(mark.get("angle", 0.0))
            crack_length = float(mark.get("length", 10.0))
            end_world = (world_x + math.cos(crack_angle) * crack_length,
                         world_y + math.sin(crack_angle) * crack_length)
            end_point = self.world_to_screen(*end_world)
            pygame.draw.line(self.screen, (37, 25, 20), point, end_point,
                             max(1, int(1.6 * self.camera_zoom)))
            branch_world = (world_x + math.cos(crack_angle + 0.85) * crack_length * 0.52,
                            world_y + math.sin(crack_angle + 0.85) * crack_length * 0.52)
            pygame.draw.line(self.screen, (54, 34, 25), point, self.world_to_screen(*branch_world),
                             max(1, int(self.camera_zoom)))
        if hit_flash > 0.0:
            radius = max(10, int(30 * self.camera_zoom))
            pygame.draw.circle(self.screen, (244, 205, 126), self.world_to_screen(x, y), radius, max(1, int(2 * self.camera_zoom)))

    def draw_floating_debris(self):
        for piece in getattr(self, "floating_debris", []):
            sx, sy = self.world_to_screen(piece["x"], piece["y"])
            if sx < -60 or sy < -60 or sx > self.screen.get_width() + 60 or sy > self.screen.get_height() + 60:
                continue
            fade = min(1.0, max(0.0, piece.get("life", 0.0) / 10.0))
            angle = float(piece.get("angle", 0.0))
            dx, dy = math.cos(angle), math.sin(angle)
            px, py = -dy, dx
            length = max(3.0, float(piece.get("length", 15.0)) * self.camera_zoom)
            width = max(2.0, float(piece.get("width", 5.0)) * self.camera_zoom)
            points = [
                (int(sx - dx * length * 0.5 - px * width * 0.5), int(sy - dy * length * 0.5 - py * width * 0.5)),
                (int(sx + dx * length * 0.5 - px * width * 0.5), int(sy + dy * length * 0.5 - py * width * 0.5)),
                (int(sx + dx * length * 0.5 + px * width * 0.5), int(sy + dy * length * 0.5 + py * width * 0.5)),
                (int(sx - dx * length * 0.5 + px * width * 0.5), int(sy - dy * length * 0.5 + py * width * 0.5)),
            ]
            color = (159, 111, 67) if not piece.get("cloth") else (115, 91, 68)
            if fade < 0.25:
                color = tuple(int(channel * fade + 22 * (1.0 - fade)) for channel in color)
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.lines(self.screen, (77, 55, 39), True, points, 1)
            if not piece.get("cloth"):
                pygame.draw.line(self.screen, (198, 151, 96), points[0], points[2], 1)

    def draw_cannon_smoke(self):
        for puff in self.cannon_smoke:
            sx, sy = self.world_to_screen(puff["x"], puff["y"])
            life_ratio = max(0.0, min(1.0, puff["life"] / max(0.01, puff["max_life"])))
            radius = max(2, int(puff["radius"] * self.camera_zoom))
            if sx < -radius * 2 or sy < -radius * 2 or sx > self.screen.get_width() + radius * 2 or sy > self.screen.get_height() + radius * 2:
                continue
            alpha = int(150 * life_ratio)
            cloud = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(cloud, (190, 190, 181, alpha), (radius + 1, radius + 1), radius)
            self.screen.blit(cloud, (sx - radius - 1, sy - radius - 1))

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
        self.draw_reefs()
        self.draw_treasure_features()
        self.draw_shipwrecks()
        self.draw_day_job_target()
        for port in self.ports:
            self.draw_port(port)
        self.draw_mission_waypoint()
        for escort in self.fleet:
            if escort.hull > 0 or getattr(escort, "sinking", False):
                progress = min(1.0, escort.sink_elapsed / 5.0) if getattr(escort, "sinking", False) else 0.0
                self.draw_ship(escort.x, escort.y, escort.heading, False, escort.hull, escort.max_hull,
                               allied=True, ship_type=escort.ship_type, hit_flash=getattr(escort, "hit_flash", 0.0),
                               sinking_progress=progress, damage_marks=getattr(escort, "damage_marks", []))
                if progress < 0.85:
                    label_pos = self.world_to_screen(escort.x, escort.y - 56)
                    label = self.tiny_font.render(escort.name, True, (210, 237, 220))
                    label_rect = label.get_rect(center=label_pos)
                    pygame.draw.rect(self.screen, (25, 48, 42), label_rect.inflate(8, 4), border_radius=3)
                    self.screen.blit(label, label_rect)
        for traffic in self.traffic_ships:
            if traffic.hull > 0 or getattr(traffic, "sinking", False):
                progress = min(1.0, traffic.sink_elapsed / 5.0) if getattr(traffic, "sinking", False) else 0.0
                self.draw_ship(traffic.x, traffic.y, traffic.heading, False, traffic.hull, traffic.max_hull,
                               ship_type=traffic.ship_type, faction=traffic.role,
                               hit_flash=getattr(traffic, "hit_flash", 0.0), sinking_progress=progress,
                               damage_marks=getattr(traffic, "damage_marks", []))
                if self.camera_zoom > 0.82 and progress < 0.85:
                    label_pos = self.world_to_screen(traffic.x, traffic.y - 54)
                    label = self.tiny_font.render(f"{traffic.name} · {traffic.role.title()}", True, (234, 229, 196))
                    label_rect = label.get_rect(center=label_pos)
                    pygame.draw.rect(self.screen, (29, 47, 53), label_rect.inflate(8, 4), border_radius=3)
                    self.screen.blit(label, label_rect)
        for pirate in self.pirates:
            if not pirate.dead or getattr(pirate, "sinking", False):
                progress = min(1.0, pirate.sink_elapsed / 5.0) if getattr(pirate, "sinking", False) else 0.0
                self.draw_ship(pirate.x, pirate.y, pirate.heading, False, pirate.hull, pirate.max_hull,
                               ship_type=pirate.ship_type, hit_flash=getattr(pirate, "hit_flash", 0.0),
                               sinking_progress=progress, damage_marks=getattr(pirate, "damage_marks", []))
                if pirate.objective_target and progress < 0.85:
                    target_pos = self.world_to_screen(pirate.x, pirate.y)
                    pygame.draw.circle(self.screen, (255, 185, 92), target_pos, max(17, int(27 * self.camera_zoom)), max(2, int(3 * self.camera_zoom)))
                if self.camera_zoom > 0.72 and progress < 0.85:
                    label_pos = self.world_to_screen(pirate.x, pirate.y - 52)
                    label_color = (255, 191, 113) if pirate.objective_target else (255, 224, 185)
                    label = self.tiny_font.render(pirate.name, True, label_color)
                    label_rect = label.get_rect(center=label_pos)
                    pygame.draw.rect(self.screen, (37, 28, 24), label_rect.inflate(8, 4), border_radius=3)
                    self.screen.blit(label, label_rect)
        if self.player_sinking_active:
            self.draw_ship(self.ship_x, self.ship_y, self.ship_heading, True, self.player_hull, self.player_max_hull,
                           rowing=False, ship_type=self.current_ship,
                           sinking_progress=min(1.0, self.player_sink_elapsed / 5.4),
                           damage_marks=self.player_damage_marks)
        elif not self.player_lost:
            self.draw_ship(self.ship_x, self.ship_y, self.ship_heading, True, self.player_hull, self.player_max_hull,
                           rowing=self.oars_deployed, ship_type=self.current_ship, hit_flash=self.player_hit_flash,
                           damage_marks=self.player_damage_marks)
        self.draw_floating_debris()
        self.draw_cannon_smoke()
        self.draw_cannonballs()

    def draw_navigation_compass(self):
        target = self.navigation_target()
        if not target:
            return
        target_name, target_x, target_y, target_kind = target
        dx, dy = target_x - self.ship_x, target_y - self.ship_y
        distance = math.hypot(dx, dy)
        bearing = math.degrees(math.atan2(dy, dx)) % 360.0
        relative = math.radians(angle_difference(bearing, self.ship_heading))
        directions = ("E", "SE", "S", "SW", "W", "NW", "N", "NE")
        cardinal = directions[int((bearing + 22.5) // 45.0) % 8]
        width = self.screen.get_width()
        box = pygame.Rect(width // 2 - 150, 16, 300, 58)
        pygame.draw.rect(self.screen, (37, 27, 20), box.inflate(6, 6), border_radius=6)
        pygame.draw.rect(self.screen, (110, 76, 46), box, border_radius=6)
        pygame.draw.rect(self.screen, (220, 187, 126), box.inflate(-5, -5), 1, border_radius=5)
        arrow_cx, arrow_cy = box.x + 27, box.centery
        tip = (int(arrow_cx + math.sin(relative) * 16), int(arrow_cy - math.cos(relative) * 16))
        left = (int(arrow_cx + math.sin(relative + 2.45) * 11), int(arrow_cy - math.cos(relative + 2.45) * 11))
        right = (int(arrow_cx + math.sin(relative - 2.45) * 11), int(arrow_cy - math.cos(relative - 2.45) * 11))
        pygame.draw.polygon(self.screen, (246, 210, 139), [tip, left, right])
        title = fit_text_surface(self.tiny_font, f"COURSE TO {target_name.upper()}", (249, 224, 178), box.width - 54, 22)
        detail = fit_text_surface(self.tiny_font, f"{distance:,.0f} chart units  ·  {cardinal}", (235, 216, 184), box.width - 54, 20)
        self.screen.blit(title, (box.x + 48, box.y + 7))
        self.screen.blit(detail, (box.x + 48, box.y + 31))

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
            caption = "BATTLE WATERS" if target_kind == "battlefield" else "NEXT PORT CALL" if target_kind == "waypoint" else "MISSION PORT"
            label = fit_text_surface(self.tiny_font, f"{caption}: {target_name.upper()}", (255, 229, 176), 270, 25)
            label_rect = label.get_rect(center=(sx, sy - max(31, int(38 * self.camera_zoom))))
            pygame.draw.rect(self.screen, (39, 29, 21), label_rect.inflate(10, 5), border_radius=3)
            self.screen.blit(label, label_rect)

    def draw_hud(self):
        width, height = self.screen.get_size()
        panel = pygame.Rect(18, 16, 480, 222)
        pygame.draw.rect(self.screen, (38, 25, 19), panel.inflate(6, 6), border_radius=7)
        pygame.draw.rect(self.screen, (120, 77, 43), panel, border_radius=6)
        pygame.draw.rect(self.screen, (221, 185, 122), panel.inflate(-6, -6), 2, border_radius=5)
        title = fit_text_surface(self.title_font, "MARE LIBERUM", (247, 221, 170), panel.width - 28, 48)
        self.screen.blit(title, (panel.x + 14, panel.y + 7))
        gold_text = fit_text_surface(self.small_font, f"Pieces of eight: {self.gold} g", (255, 236, 193), panel.width - 32, 31)
        self.screen.blit(gold_text, (panel.x + 16, panel.y + 63))
        hull_text = fit_text_surface(self.small_font, f"Hull {int(100 * self.player_hull / max(1, self.player_max_hull))}%", (245, 224, 185), 205, 31)
        self.screen.blit(hull_text, (panel.x + 16, panel.y + 112))
        bar = pygame.Rect(panel.x + 69, panel.y + 119, 150, 13)
        pygame.draw.rect(self.screen, (37, 31, 25), bar)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * self.player_hull / max(1, self.player_max_hull)), bar.height)
        pygame.draw.rect(self.screen, (159, 55, 42), fill)
        pygame.draw.rect(self.screen, (232, 202, 155), bar, 1)
        speed = math.hypot(self.ship_vx, self.ship_vy)
        way_text = fit_text_surface(self.small_font, f"Way: {int(speed)} kn", (255, 236, 193), 220, 31)
        self.screen.blit(way_text, (panel.x + 231, panel.y + 112))
        ship_line = fit_text_surface(self.tiny_font, f"Flagship: {self.player_ship_name}", (255, 236, 193), panel.width - 32, 23)
        order_display = {"fight": "Fight", "hold_fire": "Hold fire", "gather": "Gather", "follow": "Follow"}.get(self.fleet_order, self.fleet_order.title())
        fleet_line = fit_text_surface(self.tiny_font, f"{self.current_ship}  |  Escorts: {len(self.fleet)}  |  Orders: {order_display}", (255, 236, 193), panel.width - 32, 23)
        self.screen.blit(ship_line, (panel.x + 16, panel.y + 147))
        self.screen.blit(fleet_line, (panel.x + 16, panel.y + 171))
        cargo_text = fit_text_surface(self.tiny_font, f"Cargo: {self.cargo_load():.1f} / {self.cargo_capacity():.0f} units", (255, 236, 193), panel.width - 32, 22)
        self.screen.blit(cargo_text, (panel.x + 16, panel.y + 194))
        right_x = width - 285
        info = pygame.Rect(right_x, 16, 267, 160)
        pygame.draw.rect(self.screen, (38, 25, 19), info.inflate(6, 6), border_radius=7)
        pygame.draw.rect(self.screen, (120, 77, 43), info, border_radius=6)
        pygame.draw.rect(self.screen, (221, 185, 122), info.inflate(-6, -6), 2, border_radius=5)
        wind_text = fit_text_surface(self.small_font, f"Wind: {int(self.wind_angle)} deg", (255, 236, 193), 175, 28)
        sails_text = fit_text_surface(self.small_font, f"Sails: {int(self.sail_setting * 100)}%", (255, 236, 193), 175, 28)
        zoom_text = fit_text_surface(self.small_font, f"Chart zoom: {int(self.camera_zoom * 100)}%", (255, 236, 193), 175, 28)
        oars_text = fit_text_surface(self.small_font, f"Oars: {'OUT' if self.oars_deployed else 'STOWED'}  (O)", (255, 236, 193), 175, 28)
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
        self.draw_navigation_compass()
        self.draw_mini_map()
        if self.mission_result_timer > 0:
            result_width = min(680, width - 48)
            result_box = pygame.Rect(width // 2 - result_width // 2, 222, result_width, 88)
            pygame.draw.rect(self.screen, (37, 25, 18), result_box.inflate(8, 8), border_radius=7)
            pygame.draw.rect(self.screen, (221, 190, 123), result_box, border_radius=6)
            pygame.draw.rect(self.screen, (126, 83, 43), result_box.inflate(-6, -6), 2, border_radius=5)
            heading = fit_text_surface(self.font, "VOYAGE COMPLETE", (255, 230, 173), result_box.width - 28, 32)
            detail = fit_text_surface(self.small_font, f"{self.mission_result_title}  •  Reward: {self.mission_result_reward} gold", (255, 239, 207), result_box.width - 32, 25)
            self.screen.blit(heading, heading.get_rect(midtop=(result_box.centerx, result_box.y + 7)))
            self.screen.blit(detail, detail.get_rect(midtop=(result_box.centerx, result_box.y + 49)))
        active = self.active_mission()
        if active:
            objective = self.mission_guidance_text(active)
            quest_box = pygame.Rect(18, height - 190, min(760, width - 36), 84)
            pygame.draw.rect(self.screen, (38, 25, 19), quest_box.inflate(5, 5), border_radius=6)
            pygame.draw.rect(self.screen, (120, 77, 43), quest_box, border_radius=6)
            pygame.draw.rect(self.screen, (221, 185, 122), quest_box.inflate(-5, -5), 1, border_radius=5)
            quest_title = fit_text_surface(self.small_font, active.name.upper(), (250, 222, 168), quest_box.width - 28, 24)
            self.screen.blit(quest_title, (quest_box.x + 14, quest_box.y + 7))
            objective_lines = wrap_text(self.tiny_font, objective, quest_box.width - 28)
            for line_index, line in enumerate(objective_lines[:2]):
                fitted_line = fit_text_surface(self.tiny_font, line, (240, 239, 212), quest_box.width - 28, 18)
                self.screen.blit(fitted_line, (quest_box.x + 14, quest_box.y + 39 + line_index * 20))
        day_job_lines = self.day_job_hud_texts()
        if day_job_lines:
            row_count = min(3, len(day_job_lines))
            day_box_height = 48 + row_count * 25
            if active and width < 1320:
                day_box = pygame.Rect(18, height - 202 - day_box_height, min(720, width - 36), day_box_height)
            else:
                day_box = pygame.Rect(max(18, width - 570), height - 190 - day_box_height + 84, min(552, width - 36), day_box_height)
            pygame.draw.rect(self.screen, (38, 31, 20), day_box.inflate(5, 5), border_radius=6)
            pygame.draw.rect(self.screen, (126, 96, 50), day_box, border_radius=6)
            pygame.draw.rect(self.screen, (229, 197, 125), day_box.inflate(-5, -5), 1, border_radius=5)
            day_title = fit_text_surface(self.small_font, f"DAY WORK  |  {len(self.active_day_jobs)} ACTIVE", (250, 222, 168), day_box.width - 28, 24)
            self.screen.blit(day_title, (day_box.x + 14, day_box.y + 7))
            for line_index, line in enumerate(day_job_lines[:3]):
                fitted_line = fit_text_surface(self.tiny_font, line, (240, 239, 212), day_box.width - 28, 20)
                self.screen.blit(fitted_line, (day_box.x + 14, day_box.y + 35 + line_index * 24))
        if self.near_port and not self.docked_port:
            faction_name = getattr(self.near_port, "faction", "Independent")
            prompt = fit_text_surface(self.small_font, f"E  Take nearest open berth at {self.near_port.name} · {faction_name}", (255, 239, 198), width - 54, 34)
            box = prompt.get_rect(center=(width // 2, height - 35)).inflate(25, 13)
            pygame.draw.rect(self.screen, (36, 29, 21), box, border_radius=5)
            self.screen.blit(prompt, prompt.get_rect(center=box.center))
        elif self.docked_port:
            port_record = self.ports_by_name.get(self.docked_port)
            faction_name = getattr(port_record, "faction", "Independent")
            standing = self.faction_attitude(faction_name)
            prompt_text = f"{self.docked_port} · {faction_name} ({standing})  |  E: cast off   Q: harbourmaster   B: shipyard   Y: market   I: diplomacy"
            prompt = fit_text_surface(self.small_font, prompt_text, (255, 239, 198), width - 54, 34)
            box = prompt.get_rect(center=(width // 2, height - 35)).inflate(25, 13)
            pygame.draw.rect(self.screen, (36, 29, 21), box, border_radius=5)
            self.screen.blit(prompt, prompt.get_rect(center=box.center))
        if not self.docked_port:
            bottle = self.nearest_unfound_bottle(130.0)
            site = self.nearest_treasure_shore(230.0)
            wreck = self.nearest_shipwreck(230.0)
            prompt_text = None
            rescue_distance = self.day_job_rescue_distance()
            if rescue_distance <= 180:
                prompt_text = "R  Bring the stranded crew aboard"
            elif wreck and not wreck.fully_salvaged:
                prompt_text = f"R  Investigate the wreck of {wreck.name}"
            elif wreck and wreck.fully_salvaged:
                prompt_text = f"The wreck of {wreck.name} has been salvaged"
            elif bottle:
                prompt_text = "R  Recover the bottle and its treasure chart"
            elif site and site.map_found and not site.dug:
                prompt_text = f"R  Search the beach of {site.island_name}"
            elif site and site.dug:
                prompt_text = f"Treasure claimed on {site.island_name}"
            elif site and not site.map_found:
                prompt_text = f"{site.island_name}: an uncharted beach — find a treasure map"
            if prompt_text:
                prompt = fit_text_surface(self.small_font, prompt_text, (255, 239, 198), width - 58, 30)
                box = prompt.get_rect(center=(width // 2, height - 78)).inflate(28, 14)
                box.clamp_ip(self.screen.get_rect())
                pygame.draw.rect(self.screen, (36, 29, 21), box, border_radius=5)
                pygame.draw.rect(self.screen, (157, 116, 71), box, 2, border_radius=5)
                self.screen.blit(prompt, prompt.get_rect(center=box.center))

    def draw_mini_map(self):
        width = self.screen.get_width()
        rect = pygame.Rect(width - 230, 184, 210, 145)
        pygame.draw.rect(self.screen, (29, 39, 36), rect.inflate(6, 6), border_radius=5)
        pygame.draw.rect(self.screen, (154, 119, 76), rect, border_radius=4)
        inner = rect.inflate(-7, -7)
        view_width = 5200.0
        view_height = 3400.0
        left = self.ship_x - view_width / 2
        top = self.ship_y - view_height / 2
        sx = inner.width / view_width
        sy = inner.height / view_height
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(inner)
        for polygon in self.land:
            points = [(inner.x + int((x - left) * sx), inner.y + int((y - top) * sy)) for x, y in polygon]
            pygame.draw.polygon(self.screen, (75, 123, 78), points)
            pygame.draw.lines(self.screen, (190, 171, 120), True, points, 1)
        for site in self.treasure_sites:
            if site.revealed:
                points = [(inner.x + int((x - left) * sx), inner.y + int((y - top) * sy)) for x, y in site.polygon]
                pygame.draw.polygon(self.screen, (73, 132, 81), points)
                pygame.draw.lines(self.screen, (208, 188, 135), True, points, 1)
        for port in self.ports:
            px = inner.x + int((port.x - left) * sx)
            py = inner.y + int((port.y - top) * sy)
            if inner.collidepoint(px, py):
                pygame.draw.circle(self.screen, FACTION_COLOURS.get(getattr(port, "faction", "Independent"), (243, 210, 139)), (px, py), 3)
        for wreck in getattr(self, "shipwrecks", []):
            if wreck.discovered:
                wx = inner.x + int((wreck.x - left) * sx)
                wy = inner.y + int((wreck.y - top) * sy)
                if inner.collidepoint(wx, wy):
                    pygame.draw.line(self.screen, (237, 207, 150), (wx - 3, wy - 3), (wx + 3, wy + 3), 2)
                    pygame.draw.line(self.screen, (237, 207, 150), (wx - 3, wy + 3), (wx + 3, wy - 3), 2)
        for pirate in self.pirates:
            if not pirate.dead:
                px = inner.x + int((pirate.x - left) * sx)
                py = inner.y + int((pirate.y - top) * sy)
                if inner.collidepoint(px, py):
                    color = (255, 177, 74) if pirate.objective_target else (184, 60, 49)
                    radius = 4 if pirate.objective_target else 2
                    pygame.draw.circle(self.screen, color, (px, py), radius)
        for traffic in self.traffic_ships:
            if traffic.hull > 0:
                px = inner.x + int((traffic.x - left) * sx)
                py = inner.y + int((traffic.y - top) * sy)
                if inner.collidepoint(px, py):
                    color = (105, 222, 200) if traffic.role == "merchant" else (220, 216, 170) if traffic.role in {"fishing", "whaler"} else (140, 177, 231)
                    pygame.draw.circle(self.screen, color, (px, py), 2)
        navigation = self.mission_navigation_target()
        if navigation:
            target_name, target_x, target_y, target_kind = navigation
            target_px = inner.x + int((target_x - left) * sx)
            target_py = inner.y + int((target_y - top) * sy)
            player_px = inner.centerx
            player_py = inner.centery
            dx = target_px - player_px
            dy = target_py - player_py
            outside = not inner.collidepoint(target_px, target_py)
            if outside:
                scale = min((inner.width * 0.46) / max(1.0, abs(dx)), (inner.height * 0.42) / max(1.0, abs(dy)))
                target_px = int(player_px + dx * scale)
                target_py = int(player_py + dy * scale)
            pygame.draw.line(self.screen, (255, 214, 130), (player_px, player_py), (target_px, target_py), 2)
            pygame.draw.circle(self.screen, (255, 222, 135), (target_px, target_py), 5 if outside else 6)
            if outside:
                bearing = math.atan2(dy, dx)
                tip = (target_px + int(math.cos(bearing) * 7), target_py + int(math.sin(bearing) * 7))
                left_wing = (target_px + int(math.cos(bearing + 2.5) * 7), target_py + int(math.sin(bearing + 2.5) * 7))
                right_wing = (target_px + int(math.cos(bearing - 2.5) * 7), target_py + int(math.sin(bearing - 2.5) * 7))
                pygame.draw.polygon(self.screen, (255, 222, 135), [tip, left_wing, right_wing])
        for job_index, day_job in enumerate(self.active_day_jobs[:8]):
            destination = self.ports_by_name.get(day_job.destination)
            if destination:
                job_px = inner.x + int((destination.x - left) * sx)
                job_py = inner.y + int((destination.y - top) * sy)
                player_px, player_py = inner.centerx, inner.centery
                dx, dy = job_px - player_px, job_py - player_py
                outside = not inner.collidepoint(job_px, job_py)
                if outside:
                    scale = min((inner.width * 0.46) / max(1.0, abs(dx)), (inner.height * 0.42) / max(1.0, abs(dy)))
                    job_px = int(player_px + dx * scale)
                    job_py = int(player_py + dy * scale)
                pygame.draw.line(self.screen, (222, 188, 121), (player_px, player_py), (job_px, job_py), 1)
                pygame.draw.circle(self.screen, (255, 218, 146), (job_px, job_py), 3 if outside else 4, 1)
                if outside:
                    bearing = math.atan2(dy, dx)
                    tip = (job_px + int(math.cos(bearing) * 5), job_py + int(math.sin(bearing) * 5))
                    left_wing = (job_px + int(math.cos(bearing + 2.5) * 5), job_py + int(math.sin(bearing + 2.5) * 5))
                    right_wing = (job_px + int(math.cos(bearing - 2.5) * 5), job_py + int(math.sin(bearing - 2.5) * 5))
                    pygame.draw.polygon(self.screen, (255, 218, 146), [tip, left_wing, right_wing])
            if day_job.kind == "rescue" and not day_job.rescued and day_job.target_x is not None:
                rescue_px = inner.x + int((day_job.target_x - left) * sx)
                rescue_py = inner.y + int((day_job.target_y - top) * sy)
                if inner.collidepoint(rescue_px, rescue_py):
                    pygame.draw.circle(self.screen, (255, 151, 101), (rescue_px, rescue_py), 4)
        pygame.draw.circle(self.screen, (255, 250, 222), inner.center, 4)
        self.screen.set_clip(previous_clip)
        title = fit_text_surface(self.tiny_font, "LOCAL WATERS  •  M: FULL CHART", (246, 222, 174), rect.width - 16, 18)
        self.screen.blit(title, (rect.x + 8, rect.y + 5))

    def draw_world_map(self):
        width, height = self.screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((8, 16, 19, 210))
        self.screen.blit(shade, (0, 0))
        box = pygame.Rect(34, 28, width - 68, height - 56)
        pygame.draw.rect(self.screen, (42, 31, 22), box.inflate(12, 12), border_radius=8)
        pygame.draw.rect(self.screen, (222, 190, 135), box, border_radius=6)
        pygame.draw.rect(self.screen, (116, 79, 48), box.inflate(-8, -8), 2, border_radius=5)
        title = fit_text_surface(self.big_font, "THE CARIBBEAN & OUTER SEAS", (248, 224, 180), box.width - 60, 54)
        self.screen.blit(title, title.get_rect(midtop=(box.centerx, box.y + 10)))

        content_top = box.y + 76
        footer_y = box.bottom - 42
        available_height = footer_y - content_top
        legend_width = min(326, int(box.width * 0.29))
        gap = 18
        chart_width = box.width - 40 - legend_width - gap
        chart_height = int(chart_width * WORLD_HEIGHT / WORLD_WIDTH)
        if chart_height > available_height:
            chart_height = available_height
            chart_width = int(chart_height * WORLD_WIDTH / WORLD_HEIGHT)
        chart = pygame.Rect(box.x + 20, content_top + (available_height - chart_height) // 2, chart_width, chart_height)
        legend = pygame.Rect(chart.right + gap, content_top, box.right - chart.right - gap - 18, available_height)

        pygame.draw.rect(self.screen, (23, 84, 105), chart, border_radius=4)
        pygame.draw.rect(self.screen, (177, 146, 99), chart, 2, border_radius=4)
        sx = chart.width / WORLD_WIDTH
        sy = chart.height / WORLD_HEIGHT
        for polygon in self.land:
            points = [(chart.x + int(x * sx), chart.y + int(y * sy)) for x, y in polygon]
            pygame.draw.polygon(self.screen, (83, 132, 82), points)
            pygame.draw.lines(self.screen, (204, 184, 137), True, points, 1)
        for site in self.treasure_sites:
            if site.revealed:
                points = [(chart.x + int(x * sx), chart.y + int(y * sy)) for x, y in site.polygon]
                pygame.draw.polygon(self.screen, (102, 143, 85), points)
        reef_overlay = pygame.Surface((chart.width, chart.height), pygame.SRCALPHA)
        for reef in getattr(self, "reefs", []):
            points = [(int(x * sx), int(y * sy)) for x, y in reef.polygon]
            pygame.draw.polygon(reef_overlay, (225, 55, 55, 92), points)
            pygame.draw.lines(reef_overlay, (255, 133, 117, 195), True, points, 1)
        self.screen.blit(reef_overlay, chart.topleft)

        regions = [
            ("OLD CARIBBEAN", "Old Caribbean", (1450 * WORLD_SCALE, 1850 * WORLD_SCALE)),
            ("WINDWARD REACH", "Windward Reach", None),
            ("LEEWARD EXPANSE", "Leeward Expanse", None),
            ("SPANISH MAIN", "Spanish Main", None),
            ("OUTER ANTILLES", "Outer Antilles", None),
            ("THE FAR SHOALS", "The Far Shoals", None),
        ]
        for label_text, region_name, fallback in regions:
            regional_ports = [port for port in self.ports if port.region == region_name]
            if regional_ports and region_name != "Old Caribbean":
                world_x = sum(port.x for port in regional_ports) / len(regional_ports)
                world_y = sum(port.y for port in regional_ports) / len(regional_ports)
            else:
                world_x, world_y = fallback
            label_offsets = {
                "Old Caribbean": (0, 0),
                "Windward Reach": (0, -360),
                "Leeward Expanse": (250, 150),
                "Spanish Main": (0, -300),
                "Outer Antilles": (180, 170),
            }
            offset_x, offset_y = label_offsets.get(region_name, (0, 0))
            pos = (chart.x + int((world_x + offset_x) * sx), chart.y + int((world_y + offset_y) * sy))
            label = fit_text_surface(self.map_heading_font, label_text, (239, 224, 179), 180, 26)
            self.screen.blit(label, label.get_rect(center=pos))

        for index, port in enumerate(self.ports, start=1):
            px = chart.x + int(port.x * sx)
            py = chart.y + int(port.y * sy)
            faction_colour = FACTION_COLOURS.get(getattr(port, "faction", "Independent"), (255, 222, 152))
            pygame.draw.circle(self.screen, faction_colour, (px, py), 4)
            number = fit_text_surface(self.map_font, f"{index:02d}", (255, 245, 215), 24, 20)
            self.screen.blit(number, (px + 4, py - 9))
        for wreck in getattr(self, "shipwrecks", []):
            if wreck.discovered:
                wx = chart.x + int(wreck.x * sx)
                wy = chart.y + int(wreck.y * sy)
                if chart.collidepoint(wx, wy):
                    pygame.draw.line(self.screen, (247, 219, 165), (wx - 4, wy - 4), (wx + 4, wy + 4), 2)
                    pygame.draw.line(self.screen, (247, 219, 165), (wx - 4, wy + 4), (wx + 4, wy - 4), 2)

        ship_point = (chart.x + int(self.ship_x * sx), chart.y + int(self.ship_y * sy))
        if chart.collidepoint(ship_point):
            pygame.draw.circle(self.screen, (255, 255, 229), ship_point, 6)
            pygame.draw.circle(self.screen, (32, 31, 25), ship_point, 6, 1)
        navigation = self.mission_navigation_target()
        if navigation:
            target_name, target_x, target_y, target_kind = navigation
            target = (chart.x + int(target_x * sx), chart.y + int(target_y * sy))
            if chart.collidepoint(ship_point) and chart.collidepoint(target):
                pygame.draw.line(self.screen, (255, 211, 126), ship_point, target, 2)
                pygame.draw.circle(self.screen, (255, 210, 115), target, 6, 2)

        pygame.draw.rect(self.screen, (37, 49, 43), legend, border_radius=4)
        pygame.draw.rect(self.screen, (154, 119, 76), legend, 1, border_radius=4)
        legend_title = fit_text_surface(self.map_heading_font, "HARBOURS • FACTIONS • REGIONS", (248, 224, 180), legend.width - 24, 23)
        self.screen.blit(legend_title, (legend.x + 12, legend.y + 7))
        region_order = ["Old Caribbean", "Windward Reach", "Leeward Expanse", "Spanish Main", "Outer Antilles", "The Far Shoals"]
        grouped = [(region_name, [(index, port) for index, port in enumerate(self.ports, start=1) if port.region == region_name])
                   for region_name in region_order]
        grouped = [(name, ports) for name, ports in grouped if ports]
        # Divide the list into two compact columns so every harbour remains visible
        # at the largest text setting without drawing beyond the parchment panel.
        columns = [[], []]
        heights = [0, 0]
        for region_name, ports_in_region in grouped:
            target_col = 0 if heights[0] <= heights[1] else 1
            columns[target_col].append((region_name, ports_in_region))
            heights[target_col] += 1 + len(ports_in_region)
        active = self.active_mission()
        navigation_target = self.mission_navigation_target(active) if active else None
        target_port = navigation_target[0] if navigation_target and navigation_target[3] in {"port", "waypoint"} else None
        col_gap = 8
        col_width = (legend.width - 30 - col_gap) // 2
        content_top_y = legend.y + 36
        content_height = legend.height - 48
        for col_index, sections in enumerate(columns):
            x = legend.x + 12 + col_index * (col_width + col_gap)
            total_rows = sum(1 + len(items) for _, items in sections)
            row_step = min(18, max(12, content_height // max(1, total_rows)))
            y = content_top_y
            for region_name, ports_in_region in sections:
                heading_surf = fit_text_surface(self.map_heading_font, region_name.upper(), (238, 205, 145), col_width, row_step)
                self.screen.blit(heading_surf, (x, y))
                y += row_step
                for index, port in ports_in_region:
                    label = f"{index:02d}  {port.name}"
                    if port.name == target_port:
                        label = "› " + label
                    pygame.draw.circle(self.screen, FACTION_COLOURS.get(getattr(port, "faction", "Independent"), (246, 236, 210)),
                                       (x + 4, y + max(3, row_step // 2)), max(2, min(4, row_step // 3)))
                    entry = fit_text_surface(self.map_font, label, (246, 236, 210), col_width - 12, row_step)
                    self.screen.blit(entry, (x + 12, y))
                    y += row_step

        player_status = "YOUR SHIP: ON CHART" if chart.collidepoint(ship_point) else "YOUR SHIP: BEYOND THE CHART"
        status = fit_text_surface(self.map_font, player_status, (255, 227, 172), chart.width - 16, 20)
        self.screen.blit(status, (chart.x + 8, chart.bottom + 8))
        footer_text = f"M / Esc: close  •  {len(self.ports)} ports  •  Red patches = reefs  •  Gold crosses = discovered shipwrecks  •  Faction colours mark harbours"
        footer = fit_text_surface(self.map_font, footer_text, (248, 226, 188), box.width - 40, 22)
        self.screen.blit(footer, footer.get_rect(midbottom=(box.centerx, box.bottom - 12)))

    def draw_help(self):
        width, height = self.screen.get_size()
        box_width = min(560, max(300, width - 32))
        box_height = min(370, max(250, height - 32))
        box = pygame.Rect(width - box_width - 16, height - box_height - 16, box_width, box_height)
        pygame.draw.rect(self.screen, (35, 26, 21), box, border_radius=7)
        pygame.draw.rect(self.screen, (146, 104, 64), box, 2, border_radius=7)
        heading = fit_text_surface(self.small_font, "CAPTAIN'S ORDERS", (248, 221, 172), box.width - 28, 27)
        self.screen.blit(heading, heading.get_rect(center=(box.centerx, box.y + 18)))
        pygame.draw.line(self.screen, (130, 95, 61), (box.x + 14, box.y + 39), (box.right - 14, box.y + 39), 1)
        lines = [
            "W / S  Set / reef sails", "A / D  Steer", "O  Deploy / stow oars",
            "Hold Z / X  Port / starboard guns", "E  Dock / cast off", "Q  Harbour office / jobs",
            "R  Interact / salvage / treasure", "B  Shipyard (in port)",
            "F / H / G / V  Escort orders", "M  Full sea chart", "C  Centre camera",
            "Wheel / drag  Zoom / pan", "J  Captain's journal", "T  Treasure charts",
            "N  Commanders' ledger", "I  Faction diplomacy", "F5  Save voyage", "Y  Trade market (in port)",
            "Esc / F9  Pause menu", "F1  Hide these orders",
            "Red water  Reef hazard", "Gold marker  Story objective", "Gold cross  Discovered wreck",
        ]
        split = (len(lines) + 1) // 2
        columns = (lines[:split], lines[split:])
        gap = 14
        col_width = (box.width - 36 - gap) // 2
        row_height = max(18, min(25, (box.height - 60) // split))
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box)
        for col_index, column in enumerate(columns):
            x = box.x + 14 + col_index * (col_width + gap)
            for row_index, line in enumerate(column):
                rendered = fit_text_surface(self.tiny_font, line, (235, 222, 194), col_width, row_height - 1)
                self.screen.blit(rendered, (x, box.y + 49 + row_index * row_height))
        self.screen.set_clip(previous_clip)

    def draw_toast(self):
        if self.toast_time <= 0:
            return
        width = self.screen.get_width()
        text = fit_text_surface(self.small_font, self.toast, (252, 235, 200), width - 52, 38)
        box = text.get_rect(center=(width // 2, 25)).inflate(24, 12)
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
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box)
        heading = fit_text_surface(self.title_font, self.dialogue_speaker.upper(), (83, 48, 31), box.width - 48, 44)
        self.screen.blit(heading, (box.x + 24, box.y + 12))
        pygame.draw.line(self.screen, (156, 119, 77), (box.x + 22, box.y + 61), (box.right - 22, box.y + 61), 2)
        current = self.conversation.current
        if isinstance(current, TextNode):
            line_step = max(22, self.font.get_linesize() + 4)
            lines = wrap_text(self.font, current.text, box.width - 64)
            content_height = max(40, box.height - 142)
            max_lines = max(1, content_height // line_step)
            for index, line in enumerate(lines[:max_lines]):
                rendered = fit_text_surface(self.font, line, (56, 43, 31), box.width - 64, line_step - 2)
                self.screen.blit(rendered, (box.x + 30, box.y + 78 + index * line_step))
            prompt = fit_text_surface(self.small_font, "Enter / Space: continue", (104, 74, 48), box.width - 60, 26)
            self.screen.blit(prompt, prompt.get_rect(bottomright=(box.right - 28, box.bottom - 15)))
        elif isinstance(current, ChoiceNode):
            choice_prompt = fit_text_surface(self.font, "What do you say?", (56, 43, 31), box.width - 64, 33)
            self.screen.blit(choice_prompt, (box.x + 30, box.y + 72))
            start_y = box.y + 116
            available_height = max(120, box.bottom - 46 - start_y)
            row_height = min(66, max(36, available_height // max(1, len(current.options))))
            option_font = self.small_font if row_height >= 52 else self.tiny_font
            line_step = max(18, option_font.get_linesize() + 2)
            max_lines = max(1, min(2, (row_height - 8) // line_step))
            for index, option in enumerate(current.options):
                selected = index == self.conversation.selected
                text = ("▶  " if selected else "   ") + option.text
                color = (93, 44, 26) if selected else (64, 51, 37)
                lines = wrap_text(option_font, text, box.width - 90)
                row_y = start_y + index * row_height
                if selected:
                    highlight = pygame.Rect(box.x + 22, row_y - 4, box.width - 44, row_height - 5)
                    pygame.draw.rect(self.screen, (210, 188, 143), highlight, border_radius=4)
                for line_index, line in enumerate(lines[:max_lines]):
                    rendered_option = fit_text_surface(option_font, line, color, box.width - 90, line_step - 2)
                    self.screen.blit(rendered_option, (box.x + 34, row_y + line_index * line_step))
            prompt = fit_text_surface(self.small_font, "Up / Down to choose   Enter to speak", (104, 74, 48), box.width - 60, 26)
            self.screen.blit(prompt, prompt.get_rect(bottomright=(box.right - 28, box.bottom - 15)))
        self.screen.set_clip(previous_clip)

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
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box)
        title = fit_text_surface(self.big_font, "BOTTLES, CHARTS & BURIED GOLD", (75, 44, 27), box.width - 60, 52)
        title_rect = title.get_rect(midtop=(box.centerx, box.y + 18))
        self.screen.blit(title, title_rect)
        y = box.y + 92
        found_sites = [site for site in self.treasure_sites if site.map_found]
        if not found_sites:
            message = "No treasure charts yet. Keep a sharp lookout while sailing: green-glass bottles bob on the open water. Sail close and press R to recover one."
            for index, line in enumerate(wrap_text(self.font, message, box.width - 90)):
                line_surface = fit_text_surface(self.font, line, (73, 47, 31), box.width - 90, max(22, self.font.get_linesize() + 2))
                self.screen.blit(line_surface, (box.x + 40, y + index * max(22, self.font.get_linesize() + 3)))
            y += 190
        else:
            for site in found_sites:
                if y > box.bottom - 150:
                    break
                card = pygame.Rect(box.x + 24, y, box.width - 48, 165)
                pygame.draw.rect(self.screen, (211, 192, 151), card, border_radius=5)
                pygame.draw.rect(self.screen, (159, 123, 80), card, 2, border_radius=5)
                name = fit_text_surface(self.font, site.map_title, (76, 43, 27), card.width - 220, 32)
                self.screen.blit(name, (card.x + 16, card.y + 10))
                status = "CHEST RECOVERED" if site.dug else ("ISLAND CHARTED" if site.revealed else "ISLAND STILL HIDDEN")
                status_surf = fit_text_surface(self.tiny_font, status, (111, 74, 43), 190, 24)
                self.screen.blit(status_surf, (card.right - status_surf.get_width() - 14, card.y + 16))
                clue_lines = wrap_text(self.tiny_font, f"{site.island_name}: {site.clue}", card.width - 36)
                small_step = max(20, self.tiny_font.get_linesize() + 1)
                for line_index, line in enumerate(clue_lines[:2]):
                    line_surface = fit_text_surface(self.tiny_font, line, (67, 52, 37), card.width - 36, small_step - 2)
                    self.screen.blit(line_surface, (card.x + 16, card.y + 48 + line_index * small_step))
                riddle_lines = wrap_text(self.tiny_font, f"Beach riddle: {site.riddle}", card.width - 36)
                for line_index, line in enumerate(riddle_lines[:2]):
                    line_surface = fit_text_surface(self.tiny_font, line, (92, 66, 43), card.width - 36, small_step - 2)
                    self.screen.blit(line_surface, (card.x + 16, card.y + 92 + line_index * small_step))
                y += 176
        if self.relics:
            relic_text = fit_text_surface(self.small_font, "Keepsakes: " + ", ".join(self.relics), (82, 53, 32), box.width - 68, 30)
            self.screen.blit(relic_text, (box.x + 34, min(y + 4, box.bottom - 74)))
        footer = fit_text_surface(self.small_font, "Sail near a drifting bottle and press R. Find its cay, approach the marked beach, then press R to answer the riddle. T / Esc: close", (104, 74, 48), box.width - 54, 30)
        footer_rect = footer.get_rect(midbottom=(box.centerx, box.bottom - 16))
        self.screen.blit(footer, footer_rect)
        self.screen.set_clip(previous_clip)

    def draw_journal(self):
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((9, 17, 19, 185))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(width // 2 - 390, height // 2 - 325, 780, 650)
        pygame.draw.rect(self.screen, (45, 27, 18), box.inflate(10, 10), border_radius=8)
        pygame.draw.rect(self.screen, (225, 207, 163), box, border_radius=5)
        pygame.draw.rect(self.screen, (144, 105, 66), box, 3, border_radius=5)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box)
        title = fit_text_surface(self.big_font, "THE CAPTAIN'S LOG", (75, 44, 27), box.width - 56, 54)
        self.screen.blit(title, (box.x + 28, box.y + 20))
        y = box.y + 82
        active = self.active_mission()
        day_jobs = self.active_day_jobs
        if active:
            objective = self.mission_guidance_text(active)
            voyage_line = fit_text_surface(self.font, f"Current voyage: {active.name}", (73, 47, 31), box.width - 60, 34)
            self.screen.blit(voyage_line, (box.x + 30, y))
            objective_lines = wrap_text(self.small_font, objective, box.width - 60)
            objective_step = max(22, self.small_font.get_linesize() + 2)
            for line_index, line in enumerate(objective_lines[:2]):
                line_surface = fit_text_surface(self.small_font, line, (97, 66, 42), box.width - 60, objective_step - 2)
                self.screen.blit(line_surface, (box.x + 30, y + 36 + line_index * objective_step))
            y += 88 if len(objective_lines) > 1 else 78
        else:
            empty_voyage = fit_text_surface(self.font, "No story voyage under contract.", (73, 47, 31), box.width - 60, 34)
            self.screen.blit(empty_voyage, (box.x + 30, y))
            y += 43
        if day_jobs:
            day_heading = fit_text_surface(self.font, f"Active day work: {len(day_jobs)} job(s)", (73, 47, 31), box.width - 60, 34)
            self.screen.blit(day_heading, (box.x + 30, y))
            y += 38
            for job in day_jobs[:4]:
                lines = wrap_text(self.small_font, f"• {job.title}: {self.day_job_objective(job)}", box.width - 66)
                line_step = max(22, self.small_font.get_linesize() + 2)
                for line in lines[:2]:
                    line_surface = fit_text_surface(self.small_font, line, (97, 66, 42), box.width - 76, line_step - 2)
                    self.screen.blit(line_surface, (box.x + 38, y))
                    y += line_step
                y += 3
            y += 8
        pygame.draw.line(self.screen, (160, 125, 80), (box.x + 25, y), (box.right - 25, y), 1)
        y += 18
        for entry in self.journal[-10:]:
            lines = wrap_text(self.small_font, "- " + entry, box.width - 60)
            for line in lines:
                if y > box.bottom - 42:
                    break
                line_step = max(22, self.small_font.get_linesize() + 2)
                line_surface = fit_text_surface(self.small_font, line, (70, 55, 39), box.width - 64, line_step - 2)
                self.screen.blit(line_surface, (box.x + 32, y))
                y += line_step
            y += 9
        close = fit_text_surface(self.small_font, "J / Esc: close the log", (104, 74, 48), box.width - 50, 27)
        self.screen.blit(close, close.get_rect(bottomright=(box.right - 25, box.bottom - 13)))
        self.screen.set_clip(previous_clip)

    def draw_commander_ledger(self):
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((9, 17, 19, 195))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(max(24, width // 2 - 470), max(24, height // 2 - 330), min(940, width - 48), min(660, height - 48))
        pygame.draw.rect(self.screen, (45, 27, 18), box.inflate(10, 10), border_radius=8)
        pygame.draw.rect(self.screen, (225, 207, 163), box, border_radius=5)
        pygame.draw.rect(self.screen, (144, 105, 66), box, 3, border_radius=5)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box)
        title = fit_text_surface(self.title_font, "THE ADMIRALS' & CAPTAINS' LEDGER", (75, 44, 27), box.width - 48, 42)
        self.screen.blit(title, (box.x + 24, box.y + 16))
        subtitle = fit_text_surface(self.small_font, "Reputation measures standing; notoriety measures how widely a name is feared or known.", (97, 66, 42), box.width - 52, 29)
        self.screen.blit(subtitle, (box.x + 26, box.y + 76))
        records = sorted(getattr(self, "commander_records", {}).values(),
                         key=lambda record: (int(record.get("notoriety", 0)) + int(record.get("reputation", 50)),
                                             int(record.get("victories", 0))), reverse=True)
        if not records:
            message = fit_text_surface(self.font, "No commanders have yet made a name for themselves.", (73, 47, 31), box.width - 60, 34)
            self.screen.blit(message, (box.x + 30, box.y + 150))
        else:
            visible = 7
            max_scroll = max(0, len(records) - visible)
            self.commander_ledger_scroll = max(0, min(int(getattr(self, "commander_ledger_scroll", 0)), max_scroll))
            for index, record in enumerate(records[self.commander_ledger_scroll:self.commander_ledger_scroll + visible]):
                y = box.y + 116 + index * 69
                row = pygame.Rect(box.x + 22, y, box.width - 44, 63)
                pygame.draw.rect(self.screen, (213, 195, 157) if index % 2 == 0 else (222, 205, 169), row, border_radius=4)
                name = record.get("commander", "Unknown Commander")
                faction = self.commander_faction_label(record.get("faction", "Unknown"))
                rank = self.commander_rank(record)
                label = fit_text_surface(self.font, f"{name}  —  {rank}", (68, 43, 27), row.width - 24, 26)
                self.screen.blit(label, (row.x + 12, row.y + 5))
                personal = int(getattr(self, "commander_relations", {}).get(name, 0))
                stats = (f"{faction}  |  Reputation {int(record.get('reputation', 50))}/100"
                         f"  |  Notoriety {int(record.get('notoriety', 0))}"
                         f"  |  Your standing with them {personal:+d} ({self.relation_label(personal).lower()})")
                detail = fit_text_surface(self.map_font, stats, (92, 66, 43), row.width - 26, 21)
                self.screen.blit(detail, (row.x + 13, row.y + 31))
                history = (f"Victories {int(record.get('victories', 0))}  |  Ships sunk/lost "
                           f"{int(record.get('ships_sunk', 0))}/{int(record.get('ships_lost', 0))}"
                           f"  |  Retreats {int(record.get('retreats', 0))}")
                history_surf = fit_text_surface(self.map_font, history, (92, 66, 43), row.width - 26, 15)
                self.screen.blit(history_surf, (row.x + 13, row.y + 47))
        footer_text = f"Showing {min(7, len(records))} of {len(records)} commanders   •   Up/Down: scroll   •   N / Esc: close"
        footer = fit_text_surface(self.small_font, footer_text, (104, 74, 48), box.width - 40, 26)
        self.screen.blit(footer, footer.get_rect(midbottom=(box.centerx, box.bottom - 13)))
        self.screen.set_clip(previous_clip)

    def draw_diplomacy_ledger(self):
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((7, 15, 17, 205))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(max(22, width // 2 - 440), max(22, height // 2 - 300), min(880, width - 44), min(600, height - 44))
        pygame.draw.rect(self.screen, (43, 27, 19), box.inflate(10, 10), border_radius=8)
        pygame.draw.rect(self.screen, (226, 208, 166), box, border_radius=6)
        pygame.draw.rect(self.screen, (145, 104, 66), box, 3, border_radius=6)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(box)
        title = fit_text_surface(self.big_font, "THE LEDGER OF FLAGS & TREATIES", (76, 46, 29), box.width - 48, 48)
        self.screen.blit(title, (box.x + 24, box.y + 18))
        subtitle = fit_text_surface(self.small_font, "Factions remember your deeds. Their ports and captains respond to your standing.", (96, 68, 44), box.width - 52, 27)
        self.screen.blit(subtitle, (box.x + 26, box.y + 76))
        factions = list(FACTION_NAMES)
        row_top = box.y + 116
        for index, faction in enumerate(factions):
            row = pygame.Rect(box.x + 22, row_top + index * 51, box.width - 44, 45)
            selected = index == self.diplomacy_selection
            pygame.draw.rect(self.screen, (192, 173, 137) if selected else (216, 199, 162), row, border_radius=4)
            if selected:
                pygame.draw.rect(self.screen, (104, 62, 34), row, 3, border_radius=4)
            colour = FACTION_COLOURS.get(faction, (89, 89, 89))
            pygame.draw.rect(self.screen, colour, pygame.Rect(row.x + 10, row.y + 9, 8, 27), border_radius=2)
            score = self.faction_standing(faction)
            state = self.relation_label(score)
            left = fit_text_surface(self.font, faction, (67, 44, 29), 270, 30)
            self.screen.blit(left, (row.x + 28, row.y + 7))
            right = fit_text_surface(self.small_font, f"{state}   ·   Standing {score:+d}", (72, 54, 37), 250, 28)
            self.screen.blit(right, right.get_rect(midright=(row.right - 14, row.centery)))
            port_count = sum(1 for port in self.ports if port.faction == faction)
            ports = fit_text_surface(self.tiny_font, f"{port_count} harbour(s)", (105, 78, 51), 110, 22)
            self.screen.blit(ports, ports.get_rect(midright=(row.right - 280, row.centery)))
        selected_faction = factions[self.diplomacy_selection]
        selected_score = self.faction_standing(selected_faction)
        detail = fit_text_surface(self.small_font,
            f"{selected_faction}: {self.relation_label(selected_score)}. Friendly ≥ +30; hostile ≤ -30.",
            (81, 57, 37), box.width - 50, 25)
        self.screen.blit(detail, (box.x + 26, box.bottom - 143))
        econ = self.faction_economy_summary(selected_faction)
        economy_line = (f"Treasury {econ['treasury']:,}g  ·  Balance {econ['trade_balance']:+,}g  ·  "
                        f"Prosperity {econ['prosperity']:.0f}/100  ·  Shortages {econ['shortage_pressure']:.0f}%")
        economy_surface = fit_text_surface(self.tiny_font, economy_line, (89, 83, 51), box.width - 50, 22)
        self.screen.blit(economy_surface, (box.x + 26, box.bottom - 113))
        hint = fit_text_surface(self.tiny_font, self.diplomatic_action_hint(), (101, 73, 46), box.width - 50, 23)
        self.screen.blit(hint, (box.x + 26, box.bottom - 82))
        footer = fit_text_surface(self.small_font, "Up/Down: select faction   ·   P: request safe conduct   ·   G: give harbour gift   ·   I / Esc: close",
                                  (104, 74, 48), box.width - 42, 25)
        self.screen.blit(footer, footer.get_rect(midbottom=(box.centerx, box.bottom - 13)))
        self.screen.set_clip(previous_clip)

    def draw_job_board(self):
        if not self.job_board_open or not self.docked_port:
            return
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((8, 16, 18, 205))
        self.screen.blit(overlay, (0, 0))
        panel, rows, accept_rect, close_rect = self.job_board_layout()
        pygame.draw.rect(self.screen, (42, 26, 18), panel.inflate(12, 12), border_radius=10)
        pygame.draw.rect(self.screen, (226, 210, 170), panel, border_radius=7)
        pygame.draw.rect(self.screen, (143, 98, 57), panel, 3, border_radius=7)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(panel)
        title = fit_text_surface(self.big_font, "HARBOUR JOB BOARD", (76, 45, 28), panel.width - 56, 48)
        self.screen.blit(title, (panel.x + 28, panel.y + 17))
        subtitle_text = f"{self.docked_port}  •  Pick one or several; accepted jobs remain active together."
        subtitle = fit_text_surface(self.small_font, subtitle_text, (103, 74, 47), panel.width - 60, 28)
        self.screen.blit(subtitle, (panel.x + 30, panel.y + 76))
        offers = self.day_job_offers.get(self.docked_port, [])
        for index, row in enumerate(rows[:len(offers)]):
            job = offers[index]
            selected = job.job_id in self.job_board_selected_ids
            background = (198, 180, 143) if selected else (218, 201, 165)
            pygame.draw.rect(self.screen, background, row, border_radius=5)
            if index == self.job_board_selected_index:
                pygame.draw.rect(self.screen, (116, 68, 34), row, 4, border_radius=5)
            else:
                pygame.draw.rect(self.screen, (143, 103, 66), row, 2, border_radius=5)
            checkbox = pygame.Rect(row.x + 13, row.y + 16, 27, 27)
            pygame.draw.rect(self.screen, (246, 236, 210), checkbox, border_radius=3)
            pygame.draw.rect(self.screen, (91, 64, 42), checkbox, 2, border_radius=3)
            if selected:
                pygame.draw.line(self.screen, (47, 112, 70), (checkbox.x + 5, checkbox.y + 14), (checkbox.x + 11, checkbox.y + 21), 4)
                pygame.draw.line(self.screen, (47, 112, 70), (checkbox.x + 11, checkbox.y + 21), (checkbox.x + 23, checkbox.y + 5), 4)
            kind_labels = {"cargo": "CARGO", "letter": "LETTER", "passenger": "PASSAGE", "rescue": "RESCUE"}
            job_title = fit_text_surface(self.small_font, f"{job.title}  ·  {kind_labels.get(job.kind, 'WORK')}", (68, 43, 28), max(80, row.width - 240), 29)
            self.screen.blit(job_title, (row.x + 54, row.y + 3))
            reward = fit_text_surface(self.small_font, f"{job.reward} gold", (76, 105, 64), 150, 27)
            self.screen.blit(reward, reward.get_rect(topright=(row.right - 16, row.y + 3)))
            detail = fit_text_surface(self.tiny_font, f"To {job.destination}", (99, 69, 43), 190, 24)
            self.screen.blit(detail, (row.x + 55, row.y + 36))
            summary = job.payload if job.kind != "rescue" else "Recover the crew from a drifting longboat."
            summary_lines = wrap_text(self.tiny_font, summary, row.width - 380)
            for line_index, line in enumerate(summary_lines[:1]):
                summary_surface = fit_text_surface(self.tiny_font, line, (105, 81, 54), max(80, row.width - 390), 24)
                self.screen.blit(summary_surface, (row.x + 260, row.y + 36))
        if not offers:
            empty = fit_text_surface(self.font, "No work is posted at this harbour just now.", (76, 48, 30), panel.width - 60, 34)
            self.screen.blit(empty, empty.get_rect(center=(panel.centerx, panel.centery)))
        active_count = len(self.active_day_jobs)
        active_text = fit_text_surface(self.small_font, f"Already aboard: {active_count} active job(s).  Selected: {len(self.job_board_selected_ids)}", (96, 68, 43), panel.width - 60, 28)
        self.screen.blit(active_text, (panel.x + 30, panel.bottom - 113))
        pygame.draw.rect(self.screen, (115, 78, 47), close_rect, border_radius=5)
        pygame.draw.rect(self.screen, (226, 206, 165), close_rect, 2, border_radius=5)
        close_text = fit_text_surface(self.small_font, "Leave board", (255, 239, 211), close_rect.width - 12, close_rect.height - 8)
        self.screen.blit(close_text, close_text.get_rect(center=close_rect.center))
        pygame.draw.rect(self.screen, (55, 103, 68), accept_rect, border_radius=5)
        pygame.draw.rect(self.screen, (226, 206, 165), accept_rect, 2, border_radius=5)
        accept_text = fit_text_surface(self.small_font, f"Accept selected ({len(self.job_board_selected_ids)})", (255, 243, 215), accept_rect.width - 12, accept_rect.height - 8)
        self.screen.blit(accept_text, accept_text.get_rect(center=accept_rect.center))
        footer = fit_text_surface(self.tiny_font, "Up / Down move  •  Space select  •  Enter accept  •  Click rows to select  •  Esc close", (103, 74, 47), panel.width - 40, 24)
        self.screen.blit(footer, footer.get_rect(midbottom=(panel.centerx, panel.bottom - 12)))
        self.screen.set_clip(previous_clip)

    def draw(self):
        self.draw_world()
        self.draw_hud()
        if self.menu_mode == "main":
            self.draw_main_menu()
            pygame.display.flip()
            return
        if self.menu_mode == "pause":
            self.draw_pause_menu()
            pygame.display.flip()
            return
        if self.menu_mode == "load":
            self.draw_load_menu()
            pygame.display.flip()
            return
        if self.menu_mode == "settings":
            self.draw_settings_menu()
            pygame.display.flip()
            return
        if self.menu_mode == "guide":
            self.draw_guide_menu()
            pygame.display.flip()
            return
        if self.menu_mode == "game_over":
            self.draw_menu_panel(
                "YOUR SHIP IS LOST",
                "The flagship has sunk. This voyage is over; choose a saved captain's log to sail again.",
                ["Load Last Save", "Choose a Save", "Return to Main Menu", "Quit"],
                selected=self.menu_selection,
                footer="Your last save has not been changed. Enter: select",
            )
            pygame.display.flip()
            return
        if self.save_dialog_open:
            self.draw_save_dialog()
            pygame.display.flip()
            return
        if self.show_help and not self.conversation and not self.journal_open:
            self.draw_help()
        self.draw_toast()
        if self.conversation:
            self.draw_conversation()
        if self.journal_open:
            self.draw_journal()
        if getattr(self, "commander_ledger_open", False):
            self.draw_commander_ledger()
        if getattr(self, "diplomacy_open", False):
            self.draw_diplomacy_ledger()
        if self.treasure_chart_open:
            self.draw_treasure_chart()
        if self.shipyard_open:
            self.draw_shipyard()
        if self.world_map_open:
            self.draw_world_map()
        if self.job_board_open:
            self.draw_job_board()
        if getattr(self, "market_open", False):
            self.draw_trade_market()
        pygame.display.flip()
