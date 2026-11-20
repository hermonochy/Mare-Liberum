from ..common import *


class CameraMixin:
    def screen_to_world(self, screen_x, screen_y):
        width, height = self.screen.get_size()
        world_x = self.camera_x + (screen_x - width / 2) / self.camera_zoom
        world_y = self.camera_y + (screen_y - height / 2) / self.camera_zoom
        return world_x, world_y

    def zoom(self, amount, anchor=None):
        width, height = self.screen.get_size()
        if anchor is None:
            anchor = (width / 2, height / 2)
        world_anchor = self.screen_to_world(anchor[0], anchor[1])
        old_zoom = self.camera_zoom
        self.camera_zoom = clamp(self.camera_zoom * amount, CAMERA_ZOOM_MIN, CAMERA_ZOOM_MAX)
        if abs(self.camera_zoom - old_zoom) < 0.000001:
            return
        self.camera_x = world_anchor[0] - (anchor[0] - width / 2) / self.camera_zoom
        self.camera_y = world_anchor[1] - (anchor[1] - height / 2) / self.camera_zoom
        self.camera_follow = False

    def recenter_camera(self):
        self.camera_follow = True
        self.camera_x = self.ship_x
        self.camera_y = self.ship_y
        self.toast_message("Chart centred on your ship. Click and drag to pan.", 3.0)

    def world_to_screen(self, x, y):
        width, height = self.screen.get_size()
        sx = (x - self.camera_x) * self.camera_zoom + width / 2
        sy = (y - self.camera_y) * self.camera_zoom + height / 2
        return int(sx), int(sy)

    def polygon_to_screen(self, polygon):
        return [self.world_to_screen(x, y) for x, y in polygon]


    @staticmethod
    def spread_world_map_points(points, minimum_spacing=16, reserved_points=()):
        placed = [(int(round(point[0])), int(round(point[1]))) for point in reserved_points]
        output = []
        for point_index, point in enumerate(points):
            candidate = (float(point[0]), float(point[1]))
            collision = lambda location: any(
                math.hypot(round(location[0]) - other[0], round(location[1]) - other[1]) < minimum_spacing
                for other in placed
            )
            if collision(candidate):
                found = None
                for ring in range(1, 5):
                    radius = minimum_spacing * (0.65 + ring * 0.35)
                    for step in range(24):
                        angle = (2 * math.pi * step / 24) + point_index * 0.173
                        trial = (
                            candidate[0] + math.cos(angle) * radius,
                            candidate[1] + math.sin(angle) * radius,
                        )
                        if not collision(trial):
                            found = trial
                            break
                    if found is not None:
                        break
                if found is not None:
                    candidate = found
            rounded_candidate = (int(round(candidate[0])), int(round(candidate[1])))
            placed.append(rounded_candidate)
            output.append(rounded_candidate)
        return output

    def world_map_point(self, world_x, world_y):
        chart = getattr(self, "world_map_chart_rect", None)
        if chart is None:
            return 0, 0
        sx = chart.width / WORLD_WIDTH
        sy = chart.height / WORLD_HEIGHT
        zoom = float(getattr(self, "world_map_zoom", 1.0))
        pan_x = float(getattr(self, "world_map_pan_x", 0.0))
        pan_y = float(getattr(self, "world_map_pan_y", 0.0))
        x = chart.centerx + (world_x * sx - chart.width / 2) * zoom + pan_x
        y = chart.centery + (world_y * sy - chart.height / 2) * zoom + pan_y
        return int(x), int(y)

    def zoom_world_map(self, amount, anchor=None):
        chart = getattr(self, "world_map_chart_rect", None)
        if chart is None:
            return
        if anchor is None:
            anchor = chart.center
        old_zoom = float(getattr(self, "world_map_zoom", 1.0))
        new_zoom = clamp(old_zoom * amount, 0.65, 5.0)
        if abs(new_zoom - old_zoom) < 0.000001:
            return
        sx = chart.width / WORLD_WIDTH
        sy = chart.height / WORLD_HEIGHT
        base_x = (anchor[0] - chart.centerx - self.world_map_pan_x) / old_zoom
        base_y = (anchor[1] - chart.centery - self.world_map_pan_y) / old_zoom
        self.world_map_zoom = new_zoom
        self.world_map_pan_x = anchor[0] - chart.centerx - base_x * new_zoom
        self.world_map_pan_y = anchor[1] - chart.centery - base_y * new_zoom

    def pan_world_map(self, delta_x, delta_y):
        chart = getattr(self, "world_map_chart_rect", None)
        if chart is None:
            return
        zoom = float(getattr(self, "world_map_zoom", 1.0))
        limit_x = chart.width * max(0.0, zoom - 1.0) / 2
        limit_y = chart.height * max(0.0, zoom - 1.0) / 2
        self.world_map_pan_x = clamp(float(getattr(self, "world_map_pan_x", 0.0)) + delta_x, -limit_x, limit_x)
        self.world_map_pan_y = clamp(float(getattr(self, "world_map_pan_y", 0.0)) + delta_y, -limit_y, limit_y)

    def reset_world_map_view(self):
        self.world_map_zoom = 1.0
        self.world_map_pan_x = 0.0
        self.world_map_pan_y = 0.0
        self.world_map_dragging = False
        self.toast_message("The atlas has been returned to its full-chart view.", 2.4)

    def world_map_port_colour(self, port):
        mode = getattr(self, "world_map_sort_mode", "faction")
        if mode == "hostility":
            colours = {
                "HOSTILE": (204, 69, 57),
                "NEUTRAL": (211, 171, 82),
                "FRIENDLY": (83, 166, 119),
            }
            return colours.get(self.port_attitude(port), (211, 171, 82))
        return FACTION_COLOURS.get(getattr(port, "faction", "Independent"), (255, 222, 152))

    def world_map_port_groups(self):
        if getattr(self, "world_map_sort_mode", "faction") == "hostility":
            group_order = ["HOSTILE", "NEUTRAL", "FRIENDLY"]
            return [
                (attitude.title(), [(index, port) for index, port in enumerate(self.ports, start=1)
                                    if self.port_attitude(port) == attitude])
                for attitude in group_order
            ]
        return [
            (faction, [(index, port) for index, port in enumerate(self.ports, start=1)
                       if getattr(port, "faction", "Independent") == faction])
            for faction in FACTION_COLOURS
        ]

    def handle_world_map_click(self, position):
        selector = getattr(self, "world_map_sort_selector_rect", None)
        if selector and selector.collidepoint(position):
            self.world_map_sort_menu_open = not self.world_map_sort_menu_open
            return
        for mode, rect in getattr(self, "world_map_sort_option_rects", {}).items():
            if rect.collidepoint(position):
                self.world_map_sort_mode = mode
                self.world_map_sort_menu_open = False
                return
        if getattr(self, "world_map_sort_menu_open", False):
            self.world_map_sort_menu_open = False
        chart = getattr(self, "world_map_chart_rect", None)
        if chart and chart.collidepoint(position):
            self.world_map_dragging = True
            self.world_map_drag_last = position

    def update_camera(self):
        if self.camera_follow:
            self.camera_x = self.ship_x
            self.camera_y = self.ship_y
