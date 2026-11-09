from .common import *
from .audio import AudioEngine
from .mixins import (
    TreasureMixin, MissionMixin, DayJobsMixin, ShipyardFleetMixin, ControlsMixin,
    VesselsMixin, CameraMixin, RenderingMixin, TrafficMixin, SaveLoadMixin, DiplomacyMixin, ReefsMixin, ShipwreckMixin, TradeMixin,
)


class Game(
    TreasureMixin, MissionMixin, DayJobsMixin, ShipyardFleetMixin, ControlsMixin,
    VesselsMixin, CameraMixin, RenderingMixin, TrafficMixin, SaveLoadMixin, DiplomacyMixin, ReefsMixin, ShipwreckMixin, TradeMixin,
):
    def __init__(self):
        pygame.init()
        self.audio = AudioEngine(PROJECT_ROOT / "assets" / "audio")
        pygame.display.set_caption("Mare Liberum")
        self.screen = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.load_user_settings()
        self.apply_text_scale()
        self.apply_audio_settings()
        self.running = True
        self.rng = random.Random(41)
        self.world_time = 0.0
        self.camera_zoom = 1.0
        self.camera_x = 540.0
        self.camera_y = 825.0
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
        self.docked_port = "Port Royal"
        # The player uses an ordinary quay slot like every other vessel; no
        # harbour slot is permanently reserved for the flagship.
        self.player_berth_slot = PORT_BERTH_CENTER_SLOT
        self.last_docked_port_slot = PORT_BERTH_CENTER_SLOT
        self.near_port = None
        self.ship_x = 540.0
        self.ship_y = 825.0
        self.ship_heading = 90.0
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.sail_setting = 0.72
        self.oars_deployed = False
        self.wind_angle = 24.0
        self.wind_strength = 1.0
        self.current_ship = "Sloop"
        self.player_ship_name = "The Wayward Gull"
        self.player_livery = 0
        self.ship_surface_cache = {}
        self.upgrades = {"cannons": 0, "hull": 0, "rigging": 0, "rudder": 0, "cargo": 0}
        self.player_max_hull = PLAYER_HULL
        self.player_hull = PLAYER_HULL
        self.fleet = []
        self.fleet_serial = 1
        self.fleet_order = "follow"
        self.shipyard_open = False
        self.shipyard_tab = 0
        self.shipyard_selection = 0
        self.ship_rename_mode = False
        self.ship_name_input = ""
        self.shipyard_tabs = ["Flagship", "Refits", "Fleet", "Repairs", "Name & Colours"]
        self.gold = 175
        self.cannon_held = {-1: False, 1: False}
        self.cannon_first_volley_fired = {-1: False, 1: False}
        self.cannon_battery_timers = {-1: [], 1: []}
        self.cannon_battery_rates = {-1: [], 1: []}
        self.projectiles = []
        self.cannon_smoke = []
        self.journal = [
            "A battered sloop, a short purse, and a long stretch of blue water. Port Royal is your home for now.",
            "The harbourmaster may know who is hiring. Ask around before putting out to sea.",
        ]
        self.land = [[(145, 258),
  (290, 170),
  (520, 174),
  (735, 286),
  (820, 465),
  (744, 590),
  (570, 690),
  (355, 700),
  (186, 590),
  (105, 430)],
 [(1328, 260),
  (1458, 146),
  (1662, 105),
  (1853, 204),
  (1930, 362),
  (1812, 497),
  (1590, 520),
  (1400, 421),
  (1306, 340)],
 [(1850, 1170),
  (1910, 1040),
  (2040, 960),
  (2180, 925),
  (2350, 950),
  (2490, 1030),
  (2585, 1160),
  (2550, 1300),
  (2420, 1415),
  (2240, 1460),
  (2050, 1410),
  (1900, 1300)],
 [(2720, 438), (2846, 342), (2990, 420), (3060, 588), (2942, 760), (2770, 730), (2655, 585)],
 [(520, 3600), (666, 3485), (890, 3520), (1060, 3660), (1038, 3822), (855, 3930), (630, 3890), (494, 3755)],
 [(1710, 3170),
  (1790, 3110),
  (1900, 3140),
  (1970, 3230),
  (1930, 3345),
  (1820, 3410),
  (1725, 3350),
  (1670, 3255)],
 [(3250, 3500), (3380, 3415), (3540, 3460), (3640, 3600), (3570, 3760), (3410, 3810), (3270, 3710)]]
        self.ports = [
            Port("Port Royal", 540, 825, 540, 682, 90.0, "A noisy free port of privateers, rum runners, fishwives, and crooked customs men.", "Old Caribbean", "Independent"),
            Port("Tortuga", 1610, 605, 1600, 487, 90.0, "A lawless harbour tucked beneath green hills. Every tavern has a different version of the truth.", "Old Caribbean", "Pirate Brotherhood"),
            Port("Havana", 2245, 810, 2245, 938, -90.0, "A fortified Spanish harbour with high stone walls, merchant galleons, and watchful soldiers.", "Old Caribbean", "Spanish Crown"),
        ]
        self.add_regional_islands_and_ports()
        self.treasure_sites = [
            TreasureSite(
                "gannet_cay",
                "Gannet Cay",
                [(915, 1450), (955, 1385), (1025, 1370), (1090, 1400), (1120, 1465), (1090, 1530), (1020, 1550), (950, 1520)],
                1035, 1495, 875, 1350,
                "The Crooked Palm Chart",
                "Sail east from Port Royal until a low green cay rises beyond the reef. Its crooked palm leans toward the sunrise. The chart marks the pale beach beneath it.",
                "Three roots drink from one stone. From the crooked palm, take seven paces toward the rising sun. Which place hides the chest?",
                ["The pale sand beside the split log", "The pool beneath the northern cliff", "The reef where the gulls circle"],
                0, 420, "A silver sextant"
            ),
            TreasureSite(
                "widows_key",
                "Widow's Key",
                [(2824, 950), (2870, 900), (2940, 908), (3004, 956), (3022, 1027), (2974, 1094), (2900, 1112), (2842, 1068)],
                2930, 1045, 2500, 840,
                "The Widow's Last Key",
                "Run east of the great green island, where the open sea meets a small key watched by two pale rocks. At sunset the western beach turns the colour of old gold.",
                "The widow keeps her fortune where two white sentries face the western tide. Do not dig beneath the taller one; seek the sand between them. What marks the right place?",
                ["The black rock at the island's point", "The sand between the twin white stones", "The mangrove pool behind the beach"],
                1, 650, "A ruby-encrusted ring"
            ),
            TreasureSite(
                "dead_mans_cay",
                "Dead Man's Cay",
                [(1660, 2350), (1715, 2285), (1790, 2290), (1855, 2350), (1850, 2425), (1785, 2490), (1705, 2480), (1650, 2410)],
                1750, 2390, 1960, 2180,
                "The Broken Mast Chart",
                "Sail southwest from Havana, past the southern shadow of the great island. A tiny cay hides there, with a broken mast lying across its red-sand beach.",
                "A dead mast points no more to sea. When the sun sinks, its shadow touches the only red patch of sand. Where does the old captain sleep?",
                ["At the foot of the fallen mast", "Under the palm at the island's centre", "Beside the eastern tide pool"],
                0, 900, "The Black Pearl of Saint Elmo"
            ),
        ]
        self.add_scattered_cays()
        self.add_faction_ports()
        self.add_reefs()
        self.expand_world_layout(WORLD_SCALE)
        self.shipwrecks = self.create_shipwreck_sites()
        self.tree_positions = self.make_tree_positions()
        for site in self.treasure_sites:
            site.trees = self.make_tree_positions_for_polygon(site.polygon, 7)
        self.ports_by_name = {port.name: port for port in self.ports}
        self.port_greetings = {
            "Port Royal": "The harbourmaster's office is a low, timber building wedged between a rum store and a sailmaker. A brass bell rings as you step inside. A clerk looks up from a ledger; by the window, an old captain with a silver beard folds his charts and watches the sea.",
            "Tortuga": "A tavern keeper wipes a pewter mug and watches you over its rim. Outside, men argue over dice while a schooner is careened on the beach.",
            "Havana": "A uniformed harbour officer waits beneath a portrait of the governor. Beyond the open shutters, bells ring over the crowded anchorage.",
        }
        for port in self.ports:
            self.port_greetings.setdefault(port.name, f"The harbour office at {port.name} smells of tar, salt, and damp ledgers. A clerk looks up as you enter.")
            self.port_greetings[port.name] += f" The harbour flies the colours of the {port.faction}."
        self.news_by_port = {
            "Port Royal": "A fisherman says black-sailed vessels have been seen beyond the eastern reefs. The customs men claim it is none of their concern.",
            "Tortuga": "The taverns whisper of Captain Vane, a ruthless privateer who has taken to flying the black flag. His ships are gathering in the cays.",
            "Havana": "The merchants complain that no convoy dares leave harbour. The governor promises safety, but the harbour guns have been loaded for days.",
        }
        for port in self.ports:
            self.news_by_port.setdefault(port.name, f"Word from {port.region}: merchant captains report strange sails, missing cargoes, and unfamiliar agents asking after old charts.")
        self.missions = load_missions(MISSION_DIR)
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
        self.initialise_day_jobs()
        self.pirates = [
            PirateShip("The Drowned Crown", 2760 * WORLD_SCALE, 1510 * WORLD_SCALE, -130, side_choice=1, wander=4.1),
        ]
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
        self.traffic_spawn_timer = 20.0
        self.traffic_serial = 1
        self.initialise_traffic_ships(7)
        self.last_docked_port = self.docked_port or "Port Royal"
        self.menu_mode = "main"
        self.menu_selection = 0
        self.menu_scroll = 0
        self.load_return_mode = "main"
        self.save_dialog_open = False
        self.save_dialog_return_to_pause = False
        self.save_name_input = ""
        self.initialise_trade_economy()

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
            dt = min(self.clock.tick(60) / 1000.0, 0.04)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        self.audio.close()
        pygame.quit()
        sys.exit()
