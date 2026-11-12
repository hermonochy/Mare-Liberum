from .common import *
from .audio import AudioEngine
from .mixins import (
    TreasureMixin, MissionMixin, MissionEventsMixin, DayJobsMixin, ShipyardFleetMixin, ControlsMixin,
    VesselsMixin, CameraMixin, RenderingMixin, TrafficMixin, SaveLoadMixin, DiplomacyMixin, ReefsMixin, ShipwreckMixin, TradeMixin, PortMenuMixin,
)


class Game(
    TreasureMixin, MissionMixin, MissionEventsMixin, DayJobsMixin, ShipyardFleetMixin, ControlsMixin,
    VesselsMixin, CameraMixin, RenderingMixin, TrafficMixin, SaveLoadMixin, DiplomacyMixin, ReefsMixin, ShipwreckMixin, TradeMixin, PortMenuMixin,
):
    def __init__(self):
        pygame.init()
        self.audio = AudioEngine(PROJECT_ROOT / "assets" / "audio")
        pygame.display.set_caption("Mare Liberum")
        self.screen = pygame.display.set_mode(GAME_WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.load_user_settings()
        self.apply_text_scale()
        self.apply_audio_settings()
        self.running = True
        self.rng = random.Random(STARTING_RANDOM_SEED)
        self.world_time = 0.0
        self.camera_zoom = STARTING_CAMERA_ZOOM
        self.camera_x = STARTING_SHIP_POSITION[0]
        self.camera_y = STARTING_SHIP_POSITION[1]
        self.camera_follow = True
        self.world_map_open = False
        self.camera_dragging = False
        self.camera_drag_last = (0, 0)
        self.toast = "Port Royal. Sail with W, or ship the oars with O when the wind turns against you."
        self.toast_time = 6.0
        self.show_help = True
        self.journal_open = False
        self.treasure_chart_open = False
        self.relics = []
        self.unique_items = []
        self.conversation = None
        self.dialogue_speaker = "Harbourmaster"
        self.docked_port = STARTING_PORT_NAME
        # The player uses an ordinary quay slot like every other vessel; no
        # harbour slot is permanently reserved for the flagship.
        self.player_berth_slot = PORT_BERTH_CENTER_SLOT
        self.last_docked_port_slot = PORT_BERTH_CENTER_SLOT
        self.near_port = None
        self.ship_x, self.ship_y = STARTING_SHIP_POSITION
        self.ship_heading = STARTING_SHIP_HEADING
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.sail_setting = STARTING_SAIL_SETTING
        self.oars_deployed = False
        self.wind_angle = STARTING_WIND[0]
        self.wind_strength = STARTING_WIND[1]
        self.current_ship = STARTING_SHIP_CLASS
        self.player_ship_name = STARTING_SHIP_NAME
        self.player_livery = STARTING_SHIP_LIVERY
        self.ship_surface_cache = {}
        self.upgrades = dict(STARTING_SHIP_UPGRADES)
        self.player_max_hull = PLAYER_HULL
        self.player_hull = PLAYER_HULL
        self.player_hit_flash = 0.0
        self.player_damage_marks = []
        self.player_sinking_active = False
        self.player_sink_elapsed = 0.0
        self.player_lost = False
        self.floating_debris = []
        self.fleet = []
        self.fleet_serial = 1
        self.fleet_order = STARTING_FLEET_ORDER
        self.shipyard_open = False
        self.shipyard_tab = 0
        self.shipyard_selection = 0
        self.ship_rename_mode = False
        self.ship_name_input = ""
        self.shipyard_tabs = list(SHIPYARD_TABS)
        self.gold = STARTING_GOLD
        self.cannon_held = {-1: False, 1: False}
        self.cannon_first_volley_fired = {-1: False, 1: False}
        self.cannon_battery_timers = {-1: [], 1: []}
        self.cannon_battery_rates = {-1: [], 1: []}
        self.projectiles = []
        self.cannon_smoke = []
        self.journal = list(STARTING_JOURNAL)
        self.land = [list(map(tuple, polygon)) for polygon in BASE_LAND_POLYGONS]
        self.ports = [Port(*data) for data in STARTING_PORT_DATA]
        self.add_regional_islands_and_ports()
        self.treasure_sites = [TreasureSite(*data) for data in STARTING_TREASURE_DATA]
        self.add_scattered_cays()
        self.add_faction_ports()
        self.add_reefs()
        self.expand_world_layout(WORLD_SCALE)
        self.shipwrecks = self.create_shipwreck_sites()
        self.tree_positions = self.make_tree_positions()
        for site in self.treasure_sites:
            site.trees = self.make_tree_positions_for_polygon(site.polygon, 7)
        self.ports_by_name = {port.name: port for port in self.ports}
        self.port_greetings = dict(PORT_GREETING_TEXT)
        for port in self.ports:
            self.port_greetings.setdefault(port.name, f"The harbour office at {port.name} smells of tar, salt, and damp ledgers. A clerk looks up as you enter.")
            self.port_greetings[port.name] += f" The harbour flies the colours of the {port.faction}."
        self.news_by_port = dict(PORT_NEWS_TEXT)
        for port in self.ports:
            self.news_by_port.setdefault(port.name, f"Word from {port.region}: merchant captains report strange sails, missing cargoes, and unfamiliar agents asking after old charts.")
        self.missions = load_missions(MISSION_DIR)
        self.mission_events = load_mission_events(MISSION_DIR)
        for mission in self.missions:
            if mission.battlefield_x is not None:
                mission.battlefield_x *= WORLD_SCALE
            if mission.battlefield_y is not None:
                mission.battlefield_y *= WORLD_SCALE
        self.mission_states = {mission.mission_id: "available" for mission in self.missions}
        self.active_mission_id = None
        self.mission_kills = 0
        self.mission_waypoint_index = 0
        self.mission_returning = False
        self.mission_completion_started = False
        self.mission_fleet_spawned = False
        self.mission_result_title = ""
        self.mission_result_reward = 0
        self.mission_result_timer = 0.0
        self.initialise_mission_events()
        self.initialise_day_jobs()
        self.pirates = [PirateShip(*args, **kwargs) for args, kwargs in INITIAL_PIRATE_DATA]
        self.reinforcement_number = 1
        self.reinforcement_timer = self.pirate_reinforcement_interval()
        self.pirate_collision_notice_timer = 0.0
        self.ship_collision_notice_timer = 0.0
        self.port_defence_cooldowns = {port.name: self.rng.uniform(0.0, 0.8) for port in self.ports}
        self.port_defence_notice_timer = 0.0
        self.npc_battle_notice_timer = 0.0
        self.commander_records = {}
        self.commander_fleets = {}
        self.commander_ledger_open = False
        self.commander_ledger_scroll = 0
        self.initialise_diplomacy()
        self.traffic_ships = []
        self.traffic_spawn_timer = INITIAL_TRAFFIC_SPAWN_INTERVAL
        self.traffic_serial = 1
        self.initialise_traffic_ships(INITIAL_TRAFFIC_COUNT)
        self.last_docked_port = self.docked_port or "Port Royal"
        self.menu_mode = "main"
        self.menu_selection = 0
        self.menu_scroll = 0
        self.load_return_mode = "main"
        self.save_dialog_open = False
        self.save_dialog_return_to_pause = False
        self.save_name_input = ""
        self.initialise_trade_economy()
        self.initialise_port_menu()

    def expand_world_layout(self, factor):
        """Enlarge the whole chart coherently: islands, reefs, berths and passages."""
        factor = float(factor)
        self.land = [[(x * factor, y * factor) for x, y in polygon] for polygon in self.land]
        for port in self.ports:
            port.x *= factor
            port.y *= factor
            port.shore_x *= factor
            port.shore_y *= factor
        for reef in getattr(self, "reefs", []):
            reef.polygon = [(x * factor, y * factor) for x, y in reef.polygon]
            reef.center_x *= factor
            reef.center_y *= factor
            reef.radius_x *= factor
            reef.radius_y *= factor
            reef.bounds = (min(x for x, _ in reef.polygon), min(y for _, y in reef.polygon),
                           max(x for x, _ in reef.polygon), max(y for _, y in reef.polygon))
        for site in self.treasure_sites:
            site.polygon = [(x * factor, y * factor) for x, y in site.polygon]
            site.chest_x *= factor
            site.chest_y *= factor
            site.bottle_x *= factor
            site.bottle_y *= factor
        self.ship_x *= factor
        self.ship_y *= factor
        self.camera_x *= factor
        self.camera_y *= factor
        if self.ports:
            self.ship_x, self.ship_y = self.harbour_berth_position(self.ports[0], self.player_berth_slot)
            self.camera_x, self.camera_y = self.ship_x, self.ship_y

    def make_regional_island_polygon(self, cx, cy, index):
        """Build a substantial standalone island for a single-port harbour."""
        shape_rng = random.Random(7319 + index * 977)
        vertex_count = shape_rng.randint(11, 17)
        rotation = shape_rng.uniform(0.0, math.tau)
        # Standalone islands deliberately span several size classes. The
        # former near-uniform 200–300 unit cays made the four multi-port
        # landmasses dominate the chart too strongly.
        size_classes = (
            (360.0, 480.0, 245.0, 340.0),
            (520.0, 690.0, 330.0, 470.0),
            (720.0, 940.0, 440.0, 620.0),
            (430.0, 570.0, 285.0, 395.0),
            (820.0, 1050.0, 520.0, 720.0),
            (315.0, 410.0, 215.0, 295.0),
            (600.0, 780.0, 380.0, 535.0),
        )
        size_class = size_classes[index % len(size_classes)]
        rx = shape_rng.uniform(size_class[0], size_class[1])
        ry = shape_rng.uniform(size_class[2], size_class[3])
        points = []
        for point_index in range(vertex_count):
            angle = rotation + math.tau * point_index / vertex_count
            broad_coast = 1.0 + 0.17 * math.sin(angle * 2.0 + shape_rng.uniform(-0.35, 0.35))
            small_bays = 1.0 + shape_rng.uniform(-0.15, 0.15)
            spur = 0.07 * math.sin(angle * 5.0 + index * 0.7)
            variation = max(0.68, broad_coast * small_bays + spur)
            points.append((cx + math.cos(angle) * rx * variation, cy + math.sin(angle) * ry * variation))
        return points

    def make_megaisland_polygon(self, cx, cy, rx, ry, index):
        """Generate a broad, irregular island capable of supporting many ports."""
        shape_rng = random.Random(84191 + index * 1877)
        vertex_count = shape_rng.randint(22, 30)
        rotation = shape_rng.uniform(-0.12, 0.12)
        points = []
        for point_index in range(vertex_count):
            angle = rotation + math.tau * point_index / vertex_count
            broad_coast = 1.0 + 0.10 * math.sin(angle * 2.0 + index * 0.7)
            bays = 1.0 + shape_rng.uniform(-0.09, 0.09)
            long_inlets = 0.06 * math.sin(angle * 5.0 + index)
            factor = max(0.78, broad_coast * bays + long_inlets)
            points.append((cx + math.cos(angle) * rx * factor,
                           cy + math.sin(angle) * ry * factor))
        return points

    @staticmethod
    def port_coast_point(polygon, cx, cy, bearing_degrees):
        angle = math.radians(bearing_degrees)
        dx, dy = math.cos(angle), math.sin(angle)
        shore_x, shore_y = max(
            polygon,
            key=lambda point: (point[0] - cx) * dx + (point[1] - cy) * dy,
        )
        return shore_x, shore_y, dx, dy

    def add_regional_islands_and_ports(self):
        """Create a varied archipelago: giant, medium and substantial single-port islands."""
        regional_rows = {row[0]: row for row in REGIONAL_PORT_DATA}
        faction_rows = {row[0]: row for row in FACTION_PORT_DATA}
        grouped_names = set()

        for index, group in enumerate(MULTI_PORT_ISLAND_GROUPS):
            cx, cy = group["center"]
            rx, ry = group["radius"]
            polygon = self.make_megaisland_polygon(cx, cy, rx, ry, index)
            self.land.append(polygon)
            for port_name, bearing in group["ports"]:
                if port_name in regional_rows:
                    _, _, _, region, description = regional_rows[port_name]
                    faction = REGIONAL_PORT_FACTIONS.get(port_name, "Independent")
                elif port_name in faction_rows:
                    _, _, _, region, description, faction = faction_rows[port_name]
                else:
                    continue
                shore_x, shore_y, dx, dy = self.port_coast_point(polygon, cx, cy, bearing)
                # Long breakwater and outer harbour approach, scaled with the chart.
                harbour_length = 190.0
                berth_x = shore_x + dx * harbour_length
                berth_y = shore_y + dy * harbour_length
                self.ports.append(Port(
                    port_name, berth_x, berth_y, shore_x, shore_y,
                    float(bearing) % 360.0, description, region, faction,
                ))
                grouped_names.add(port_name)

        for index, (name, cx, cy, region, description) in enumerate(REGIONAL_PORT_DATA):
            if name in grouped_names:
                continue
            polygon = self.make_regional_island_polygon(cx, cy, index)
            self.land.append(polygon)
            westmost = min(polygon, key=lambda point: point[0])
            shore_x = westmost[0] + 6.0
            shore_y = westmost[1]
            berth_x = westmost[0] - 190.0
            faction = REGIONAL_PORT_FACTIONS.get(name, "Independent")
            self.ports.append(
                Port(name, berth_x, shore_y, shore_x, shore_y, 180.0, description, region, faction)
            )

    def make_scattered_cay_polygon(self, cx, cy, index):
        shape_rng = random.Random(42137 + index * 613)
        vertex_count = shape_rng.randint(7, 11)
        rotation = shape_rng.uniform(0.0, math.tau)
        rx = shape_rng.uniform(62.0, 118.0)
        ry = shape_rng.uniform(48.0, 91.0)
        points = []
        for point_index in range(vertex_count):
            angle = rotation + math.tau * point_index / vertex_count
            variation = shape_rng.uniform(0.76, 1.22)
            variation += 0.08 * math.sin(angle * 3.0 + index)
            points.append((cx + math.cos(angle) * rx * variation, cy + math.sin(angle) * ry * variation))
        return points

    def add_faction_ports(self):
        """Place extra faction strongholds on isolated islands without crowding existing harbours."""
        for index, (name, anchor_x, anchor_y, region, description, faction) in enumerate(FACTION_PORT_DATA):
            if name == "Puerto Escondido":
                continue  # already placed as a second Spanish harbour on the Outer Antilles island
            placement_rng = random.Random(9900 + index * 137)
            accepted = None
            for attempt in range(900):
                cx = anchor_x + placement_rng.uniform(-650.0, 650.0)
                cy = anchor_y + placement_rng.uniform(-500.0, 500.0)
                base_width = WORLD_WIDTH / WORLD_SCALE
                base_height = WORLD_HEIGHT / WORLD_SCALE
                if not (350.0 < cx < base_width - 350.0 and 350.0 < cy < base_height - 350.0):
                    continue
                polygon = self.make_regional_island_polygon(cx, cy, 100 + index)
                if any(point_in_polygon((cx, cy), existing) or nearest_polygon_edge(cx, cy, existing)[1] < 520.0 for existing in self.land):
                    continue
                if any(math.hypot(cx - port.x, cy - port.y) < 900.0 for port in self.ports):
                    continue
                if any(point_in_polygon((cx, cy), site.polygon) or nearest_polygon_edge(cx, cy, site.polygon)[1] < 420.0 for site in self.treasure_sites):
                    continue
                accepted = polygon
                break
            if accepted is None:
                continue
            self.land.append(accepted)
            westmost = min(accepted, key=lambda point: point[0])
            shore_x, shore_y = westmost[0] + 6.0, westmost[1]
            berth_x = westmost[0] - 180.0
            self.ports.append(Port(name, berth_x, shore_y, shore_x, shore_y, 180.0, description, region, faction))

    def add_scattered_cays(self):
        cay_rng = random.Random(86420)
        placed = 0
        for anchor_index, (anchor_x, anchor_y) in enumerate(SCATTERED_CAY_ANCHORS):
            accepted = None
            for attempt in range(80):
                cx = anchor_x + cay_rng.uniform(-340.0, 340.0)
                cy = anchor_y + cay_rng.uniform(-300.0, 300.0)
                polygon = self.make_scattered_cay_polygon(cx, cy, anchor_index)
                if any(point_in_polygon((cx, cy), existing) for existing in self.land):
                    continue
                clear_of_land = True
                for existing in self.land:
                    _, edge_distance = nearest_polygon_edge(cx, cy, existing)
                    if edge_distance < 360.0:
                        clear_of_land = False
                        break
                if not clear_of_land:
                    continue
                if any(math.hypot(cx - port.x, cy - port.y) < 720.0 for port in self.ports):
                    continue
                if any(point_in_polygon((cx, cy), site.polygon) or nearest_polygon_edge(cx, cy, site.polygon)[1] < 340.0 for site in self.treasure_sites):
                    continue
                accepted = polygon
                break
            if accepted is not None:
                self.land.append(accepted)
                placed += 1
        self.scattered_cay_count = placed

    def make_tree_positions(self):
        positions = []
        for polygon in self.land:
            min_x = min(point[0] for point in polygon)
            max_x = max(point[0] for point in polygon)
            min_y = min(point[1] for point in polygon)
            max_y = max(point[1] for point in polygon)
            made = 0
            attempts = 0
            while made < 14 and attempts < 180:
                attempts += 1
                point = (self.rng.uniform(min_x, max_x), self.rng.uniform(min_y, max_y))
                if point_in_polygon(point, polygon):
                    positions.append(point)
                    made += 1
        return positions

    def make_tree_positions_for_polygon(self, polygon, count):
        positions = []
        min_x = min(point[0] for point in polygon)
        max_x = max(point[0] for point in polygon)
        min_y = min(point[1] for point in polygon)
        max_y = max(point[1] for point in polygon)
        attempts = 0
        while len(positions) < count and attempts < count * 40:
            attempts += 1
            point = (self.rng.uniform(min_x, max_x), self.rng.uniform(min_y, max_y))
            if point_in_polygon(point, polygon):
                positions.append(point)
        return positions

    def collision_land_polygons(self):
        return self.land + [site.polygon for site in self.treasure_sites if site.revealed]

    def run(self):
        while self.running:
            dt = min(self.clock.tick(GAME_TARGET_FPS) / 1000.0, GAME_FRAME_TIME_LIMIT)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        self.audio.close()
        pygame.quit()
        sys.exit()
