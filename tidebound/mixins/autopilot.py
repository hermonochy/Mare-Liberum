import math
import time

from ..common import *


class AutopilotMixin:
    def world_map_port_at_screen(self, position):
        points = self.world_map_port_marker_positions()
        zoom = float(getattr(self, "world_map_zoom", 1.0))
        radius = max(13.0, min(21.0, 12.0 + zoom * 2.0))
        best = None
        best_distance = radius
        for port, marker in zip(self.ports, points):
            distance = math.hypot(position[0] - marker[0], position[1] - marker[1])
            if distance <= best_distance:
                best = port
                best_distance = distance
        return best

    def simulation_port_at_screen(self, position):
        best = None
        best_distance = float("inf")
        zoom = max(0.25, float(getattr(self, "camera_zoom", 1.0)))
        for port in self.ports:
            port_point = self.world_to_screen(port.x, port.y)
            label_point = self.world_to_screen(port.x, port.y + 42.0)
            shore_point = self.world_to_screen(port.shore_x + 22.0, port.shore_y - 25.0)
            port_distance = math.hypot(position[0] - port_point[0], position[1] - port_point[1])
            shore_distance = math.hypot(position[0] - shore_point[0], position[1] - shore_point[1])
            label_hit = abs(position[0] - label_point[0]) <= 92 and abs(position[1] - label_point[1]) <= 19
            candidate_distance = min(port_distance, shore_distance, 0.0 if label_hit else float("inf"))
            threshold = max(17.0, min(42.0, 16.0 + zoom * 12.0))
            if candidate_distance <= threshold and candidate_distance < best_distance:
                best = port
                best_distance = candidate_distance
        return best

    def clear_autopilot_click_if_dragged(self, position):
        previous = getattr(self, "autopilot_last_port_click", None)
        if not previous:
            return
        old_position = previous[2]
        if math.hypot(position[0] - old_position[0], position[1] - old_position[1]) > 9.0:
            self.autopilot_last_port_click = None

    def register_port_double_click(self, port, position, source):
        now = time.monotonic()
        previous = getattr(self, "autopilot_last_port_click", None)
        if previous:
            previous_name, previous_source, previous_position, previous_time = previous
            same_target = previous_name == port.name and previous_source == source
            close_enough = math.hypot(position[0] - previous_position[0], position[1] - previous_position[1]) <= 16.0
            timely = 0.0 <= now - previous_time <= 0.48
            if same_target and close_enough and timely:
                self.autopilot_last_port_click = None
                return True
        self.autopilot_last_port_click = (port.name, source, tuple(position), now)
        return False

    def start_port_autopilot(self, port):
        if port is None or getattr(self, "player_sinking_active", False) or getattr(self, "player_lost", False):
            return False
        if self.docked_port == port.name:
            self.toast_message(f"You are already berthed at {port.name}.", 2.8)
            return False
        if self.port_attitude(port) == "HOSTILE":
            self.toast_message(f"The harbour at {port.name} is hostile. The first mate will not attempt to enter.", 4.0)
            return False
        if self.nearest_available_harbour_slot(port, self.ship_x, self.ship_y) is None:
            self.toast_message(f"Every berth at {port.name} is occupied. Choose another harbour for now.", 3.8)
            return False
        if getattr(self, "autopilot_port_name", None):
            self.cancel_port_autopilot(show_message=False)
        if getattr(self, "port_menu_open", False) and hasattr(self, "close_port_menu"):
            self.close_port_menu()
        if self.docked_port:
            self.undock()
        self.world_map_open = False
        self.world_map_dragging = False
        self.world_map_sort_menu_open = False
        self.camera_dragging = False
        self.camera_follow = True
        self.autopilot_port_name = port.name
        self.autopilot_previous_oars = bool(self.oars_deployed)
        self.autopilot_repath_timer = 0.0
        self.autopilot_course_heading = self.ship_heading
        self.autopilot_harbour_stage = "approach"
        self.toast_message(f"First mate has the helm. Making for {port.name}. Press any arrow key to take command.", 5.0)
        return True

    def cancel_port_autopilot(self, show_message=True, restore_oars=True):
        destination = getattr(self, "autopilot_port_name", None)
        if not destination:
            return False
        previous_oars = getattr(self, "autopilot_previous_oars", None)
        self.autopilot_port_name = None
        self.autopilot_repath_timer = 0.0
        self.autopilot_harbour_stage = None
        if restore_oars and previous_oars is not None and not self.docked_port:
            stats = self.player_ship_stats()
            self.oars_deployed = bool(previous_oars and stats.get("rowers", 0) >= 8 and stats.get("oar_power", 0.0) > 0.0)
        self.autopilot_previous_oars = None
        if show_message:
            self.toast_message("You have taken the helm. The first mate stands down.", 3.2)
        return True

    def _autopilot_obstacles(self, destination):
        obstacles = []
        for polygon in getattr(self, "land", []):
            obstacles.append((polygon, (min(p[0] for p in polygon), min(p[1] for p in polygon),
                                        max(p[0] for p in polygon), max(p[1] for p in polygon)), "land"))
        for site in getattr(self, "treasure_sites", []):
            if getattr(site, "revealed", False):
                polygon = site.polygon
                obstacles.append((polygon, (min(p[0] for p in polygon), min(p[1] for p in polygon),
                                            max(p[0] for p in polygon), max(p[1] for p in polygon)), "land"))
        for reef in getattr(self, "reefs", []):
            obstacles.append((reef.polygon, reef.bounds, "reef"))
        for polygon in getattr(self, "harbour_wall_polygons", []):
            bounds = (min(point[0] for point in polygon), min(point[1] for point in polygon),
                      max(point[0] for point in polygon), max(point[1] for point in polygon))
            obstacles.append((polygon, bounds, "wall"))
        return obstacles

    def autopilot_harbour_approach_point(self, port):
        layout = getattr(self, "harbour_layouts", {}).get(port.name)
        if not layout:
            return float(port.x), float(port.y)
        axis_x, axis_y = layout["axis"]
        approach_distance = float(layout.get("end_distance", 360.0)) + 112.0
        return (float(port.shore_x) + axis_x * approach_distance,
                float(port.shore_y) + axis_y * approach_distance)

    def autopilot_navigation_heading(self, port, target_point=None):
        target_x, target_y = target_point if target_point is not None else (port.x, port.y)
        dx = float(target_x) - float(self.ship_x)
        dy = float(target_y) - float(self.ship_y)
        distance = max(1.0, math.hypot(dx, dy))
        desired = math.degrees(math.atan2(dy, dx)) % 360.0
        lookahead = min(900.0, max(140.0, distance - 62.0))
        clearance = max(42.0, SHIP_COLLISION_RADII.get(self.current_ship, PLAYER_RADIUS) + 48.0)
        obstacles = self._autopilot_obstacles(port)
        offsets = [0.0]
        for step in range(12, 181, 12):
            offsets.extend((-float(step), float(step)))
        sample_distances = [float(value) for value in range(70, int(lookahead) + 1, 75)]
        if not sample_distances or sample_distances[-1] < lookahead:
            sample_distances.append(lookahead)
        best_heading = desired
        best_score = float("inf")
        for offset in offsets:
            heading = (desired + offset) % 360.0
            angle = math.radians(heading)
            direction_x, direction_y = math.cos(angle), math.sin(angle)
            obstruction = 0.0
            for travelled in sample_distances:
                px = self.ship_x + direction_x * travelled
                py = self.ship_y + direction_y * travelled
                for polygon, bounds, kind in obstacles:
                    margin = clearance + (28.0 if kind == "reef" else 0.0)
                    if px < bounds[0] - margin or px > bounds[2] + margin or py < bounds[1] - margin or py > bounds[3] + margin:
                        continue
                    if point_in_polygon((px, py), polygon):
                        obstruction += 1500.0 + (lookahead - travelled) * 1.2
                        continue
                    _, edge_distance = nearest_polygon_edge(px, py, polygon)
                    if edge_distance < margin:
                        severity = (margin - edge_distance) / max(1.0, margin)
                        obstruction += severity * severity * (360.0 if kind == "reef" else 290.0)
            projected_x = self.ship_x + direction_x * lookahead
            projected_y = self.ship_y + direction_y * lookahead
            remaining = math.hypot(target_x - projected_x, target_y - projected_y)
            score = remaining + abs(offset) * 2.1 + obstruction
            if score < best_score:
                best_score = score
                best_heading = heading
        return best_heading

    def autopilot_control_inputs(self, dt):
        destination_name = getattr(self, "autopilot_port_name", None)
        if not destination_name:
            return None
        port = self.ports_by_name.get(destination_name)
        if port is None or self.docked_port or self.player_sinking_active or self.player_lost:
            self.cancel_port_autopilot(show_message=False)
            return None
        if self.port_attitude(port) == "HOSTILE":
            self.cancel_port_autopilot(show_message=False)
            self.toast_message(f"The harbour at {port.name} has turned hostile. The first mate abandons the approach.", 4.0)
            return None
        dx = port.x - self.ship_x
        dy = port.y - self.ship_y
        distance = math.hypot(dx, dy)
        speed = math.hypot(self.ship_vx, self.ship_vy)
        approach_point = self.autopilot_harbour_approach_point(port)
        approach_distance = math.hypot(approach_point[0] - self.ship_x, approach_point[1] - self.ship_y)
        if getattr(self, "autopilot_harbour_stage", "approach") == "approach" and approach_distance <= 105.0:
            self.autopilot_harbour_stage = "enter"
            self.autopilot_repath_timer = 0.0
            self.toast_message(f"Harbour entrance ahead. The first mate is bringing her in through the breakwaters at {port.name}.", 3.5)
        if distance <= 88.0 and speed <= 48.0:
            self.cancel_port_autopilot(show_message=False, restore_oars=False)
            if not self.dock(port):
                self.toast_message(f"Could not secure a berth at {port.name}. The helm is yours again.", 4.0)
            return {"docked": True}

        self.autopilot_repath_timer = max(0.0, self.autopilot_repath_timer - dt)
        if self.autopilot_repath_timer <= 0.0:
            route_target = approach_point if getattr(self, "autopilot_harbour_stage", "approach") == "approach" else (port.x, port.y)
            self.autopilot_course_heading = self.autopilot_navigation_heading(port, route_target)
            self.autopilot_repath_timer = 0.32
        course_error = angle_difference(self.autopilot_course_heading, self.ship_heading)
        stats = self.player_ship_stats()
        turn_rate = (7.0 + min(speed, 170.0) * 0.19) * stats["turn"] * (1.0 + self.upgrades["rudder"] * 0.12)
        rudder = clamp(course_error / max(8.0, turn_rate * 1.35), -1.0, 1.0)

        if distance > 760.0:
            sail_target = 1.0
        elif distance > 470.0:
            sail_target = 0.84
        elif distance > 260.0:
            sail_target = 0.62
        elif distance > 150.0:
            sail_target = 0.25
        else:
            sail_target = 0.07
        if abs(course_error) > 72.0:
            sail_target = min(sail_target, 0.34)
        elif abs(course_error) > 38.0:
            sail_target = min(sail_target, 0.58)
        target_speed = clamp(distance * 0.27, 18.0, min(138.0, stats["speed"] * 0.88))
        if speed > target_speed + 9.0:
            sail_target = min(sail_target, 0.04 if distance < 260.0 else 0.32)
        sail_rate = 0.88 if sail_target < self.sail_setting else 0.42
        self.sail_setting += clamp(sail_target - self.sail_setting, -sail_rate * dt, sail_rate * dt)

        angle_to_target = math.radians(self.autopilot_course_heading)
        wind_power = max(0.075, 0.5 + 0.5 * math.cos(angle_to_target - math.radians(self.wind_angle)))
        can_row = stats.get("rowers", 0) >= 8 and stats.get("oar_power", 0.0) > 0.0
        if distance > 220.0 and can_row and (wind_power < 0.30 or (speed < 16.0 and wind_power < 0.48)):
            self.oars_deployed = True
        else:
            self.oars_deployed = False
        extra_drag = 0.0
        if distance < 520.0 and speed > target_speed:
            extra_drag = 0.24 + 0.60 * (1.0 - clamp(distance / 520.0, 0.0, 1.0))
        return {"rudder": rudder, "target_speed": target_speed, "extra_drag": extra_drag}
