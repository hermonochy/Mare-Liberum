from .common import *
from .mixins import (
    TreasureMixin, MissionMixin, DayJobsMixin, ShipyardFleetMixin, ControlsMixin,
    VesselsMixin, CameraMixin, RenderingMixin,
)


class Game(
    TreasureMixin, MissionMixin, DayJobsMixin, ShipyardFleetMixin, ControlsMixin,
    VesselsMixin, CameraMixin, RenderingMixin,
):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tidebound: Caribbean Pirates")
        self.screen = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("georgia", 30)
        self.small_font = pygame.font.SysFont("georgia", 25)
        self.tiny_font = pygame.font.SysFont("georgia", 21)
        self.title_font = pygame.font.SysFont("georgia", 42, bold=True)
        self.big_font = pygame.font.SysFont("georgia", 52, bold=True)
        self.running = True
        self.rng = random.Random(41)
        self.world_time = 0.0
        self.camera_zoom = 1.0
        self.camera_x = 540.0
        self.camera_y = 825.0
        self.camera_follow = True
        self.camera_dragging = False
        self.camera_drag_last = (0, 0)
        self.toast = "Port Royal. Sail with W, or ship the oars with O when the wind turns against you."
        self.toast_time = 6.0
        self.show_help = True
        self.journal_open = False
        self.treasure_chart_open = False
        self.relics = []
        self.conversation = None
        self.dialogue_speaker = "Harbourmaster"
        self.docked_port = "Port Royal"
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
        self.upgrades = {"cannons": 0, "hull": 0, "rigging": 0, "rudder": 0}
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
        self.cannon_cooldowns = {-1: 0.0, 1: 0.0}
        self.projectiles = []
        self.journal = [
            "A battered sloop, a short purse, and a long stretch of blue water. Port Royal is your home for now.",
            "The harbourmaster may know who is hiring. Ask around before putting out to sea.",
        ]
        self.ports = [
            Port("Port Royal", 540, 825, 540, 682, 90.0, "A noisy free port of privateers, rum runners, fishwives, and crooked customs men."),
            Port("Tortuga", 1610, 605, 1600, 487, 90.0, "A lawless harbour tucked beneath green hills. Every tavern has a different version of the truth."),
            Port("Havana", 2245, 810, 2245, 938, -90.0, "A fortified Spanish harbour with high stone walls, merchant galleons, and watchful soldiers."),
        ]
        self.land = [
            [(145, 258), (290, 170), (520, 174), (735, 286), (820, 465), (744, 590), (570, 690), (355, 700), (186, 590), (105, 430)],
            [(1328, 260), (1458, 146), (1662, 105), (1853, 204), (1930, 362), (1812, 497), (1590, 520), (1400, 421), (1306, 340)],
            [(955, 1138), (1128, 1006), (1420, 922), (1740, 971), (2010, 900), (2290, 915), (2520, 1040), (2665, 1238), (2600, 1420), (2380, 1580), (2080, 1640), (1785, 1600), (1460, 1533), (1170, 1390), (1000, 1260)],
            [(2720, 438), (2846, 342), (2990, 420), (3060, 588), (2942, 760), (2770, 730), (2655, 585)],
            [(270, 1470), (416, 1364), (640, 1398), (810, 1538), (788, 1702), (605, 1812), (380, 1776), (244, 1638)],
            [(900, 535), (980, 485), (1058, 520), (1080, 612), (1014, 675), (930, 642)],
            [(2350, 1800), (2480, 1735), (2630, 1785), (2710, 1900), (2610, 2015), (2450, 1990), (2330, 1905)],
        ]
        self.tree_positions = self.make_tree_positions()
        self.treasure_sites = [
            TreasureSite(
                "gannet_cay",
                "Gannet Cay",
                [(760, 930), (782, 875), (833, 848), (900, 868), (940, 920), (918, 976), (862, 1008), (800, 990)],
                888, 958, 825, 770,
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
                [(968, 1812), (1028, 1765), (1102, 1782), (1160, 1840), (1165, 1912), (1100, 1974), (1025, 1970), (970, 1915)],
                1080, 1900, 1690, 1830,
                "The Broken Mast Chart",
                "Sail southwest from Havana, past the southern shadow of the great island. A tiny cay hides there, with a broken mast lying across its red-sand beach.",
                "A dead mast points no more to sea. When the sun sinks, its shadow touches the only red patch of sand. Where does the old captain sleep?",
                ["At the foot of the fallen mast", "Under the palm at the island's centre", "Beside the eastern tide pool"],
                0, 900, "The Black Pearl of Saint Elmo"
            ),
        ]
        for site in self.treasure_sites:
            site.trees = self.make_tree_positions_for_polygon(site.polygon, 7)
        self.ports_by_name = {port.name: port for port in self.ports}
        self.port_greetings = {
            "Port Royal": "The harbourmaster's office is a low, timber building wedged between a rum store and a sailmaker. A brass bell rings as you step inside. A clerk looks up from a ledger.",
            "Tortuga": "A tavern keeper wipes a pewter mug and watches you over its rim. Outside, men argue over dice while a schooner is careened on the beach.",
            "Havana": "A uniformed harbour officer waits beneath a portrait of the governor. Beyond the open shutters, bells ring over the crowded anchorage.",
        }
        self.news_by_port = {
            "Port Royal": "A fisherman says black-sailed vessels have been seen beyond the eastern reefs. The customs men claim it is none of their concern.",
            "Tortuga": "The taverns whisper of Captain Vane, a ruthless privateer who has taken to flying the black flag. His ships are gathering in the cays.",
            "Havana": "The merchants complain that no convoy dares leave harbour. The governor promises safety, but the harbour guns have been loaded for days.",
        }
        self.missions = load_missions(MISSION_DIR)
        self.mission_states = {mission.mission_id: "available" for mission in self.missions}
        self.active_mission_id = None
        self.mission_kills = 0
        self.mission_returning = False
        self.mission_completion_started = False
        self.mission_fleet_spawned = False
        self.mission_result_title = ""
        self.mission_result_reward = 0
        self.mission_result_timer = 0.0
        self.initialise_day_jobs()
        self.pirates = [
            PirateShip("The Drowned Crown", 2760, 1510, -130, side_choice=1, wander=4.1),
        ]
        self.reinforcement_number = 1
        self.reinforcement_timer = 45.0

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
        pygame.quit()
        sys.exit()
