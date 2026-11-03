import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from mission_system import (
    ChoiceNode,
    CommandNode,
    GotoNode,
    LabelNode,
    TextNode,
    OptionNode,
    load_missions,
)


ROOT = Path(__file__).resolve().parent
MISSION_DIR = ROOT / "missions"
WORLD_WIDTH = 3200
WORLD_HEIGHT = 2200
PLAYER_RADIUS = 36
MAX_PLAYER_SPEED = 205.0
PLAYER_HULL = 100
SHIP_CLASSES = {
    "Sloop": {"cost": 0, "hull": 100, "speed": 205.0, "turn": 1.0, "guns": 3, "reload": 1.45, "oar_power": 34.0, "rowers": 12, "description": "A nimble little vessel. A sound first command."},
    "Cutter": {"cost": 650, "hull": 92, "speed": 238.0, "turn": 1.2, "guns": 2, "reload": 1.22, "oar_power": 32.0, "rowers": 12, "description": "Quick through the water and handy for chasing prizes."},
    "Schooner": {"cost": 1250, "hull": 138, "speed": 218.0, "turn": 1.05, "guns": 4, "reload": 1.48, "oar_power": 39.0, "rowers": 16, "description": "A balanced trader-raider with a stronger broadside."},
    "Brigantine": {"cost": 2200, "hull": 188, "speed": 194.0, "turn": 0.9, "guns": 5, "reload": 1.7, "oar_power": 46.0, "rowers": 20, "description": "A sturdy two-masted fighter with plenty of room for guns."},
    "Frigate": {"cost": 3600, "hull": 250, "speed": 176.0, "turn": 0.76, "guns": 7, "reload": 1.95, "oar_power": 54.0, "rowers": 24, "description": "A costly gun platform built to dominate a fleet action."},
}
SHIP_LIVERIES = [
    ("Weathered Pirate", (98, 47, 31), (205, 155, 89), (227, 215, 177)),
    ("Royal Blue", (38, 66, 91), (190, 163, 104), (222, 225, 211)),
    ("Emerald Corsair", (39, 83, 59), (197, 157, 81), (227, 219, 180)),
    ("Blood Red", (104, 35, 34), (204, 155, 90), (231, 210, 184)),
    ("Ivory & Gold", (130, 105, 69), (221, 190, 116), (246, 235, 207)),
]


def clamp(value, low, high):
    return max(low, min(high, value))


def angle_difference(target, current):
    return (target - current + 180.0) % 360.0 - 180.0


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        if (y1 > y) != (y2 > y):
            crossing = (x2 - x1) * (y - y1) / ((y2 - y1) or 0.000001) + x1
            if x < crossing:
                inside = not inside
    return inside


def closest_point_on_segment(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ax, ay
    amount = clamp(((px - ax) * dx + (py - ay) * dy) / length_sq, 0.0, 1.0)
    return ax + amount * dx, ay + amount * dy


def nearest_polygon_edge(x, y, polygon):
    best_point = None
    best_distance = float("inf")
    for index in range(len(polygon)):
        ax, ay = polygon[index]
        bx, by = polygon[(index + 1) % len(polygon)]
        point = closest_point_on_segment(x, y, ax, ay, bx, by)
        distance = math.hypot(x - point[0], y - point[1])
        if distance < best_distance:
            best_point = point
            best_distance = distance
    return best_point, best_distance


def resolve_land_collision(x, y, vx, vy, radius, polygons):
    collided = False
    for polygon in polygons:
        inside = point_in_polygon((x, y), polygon)
        nearest, distance = nearest_polygon_edge(x, y, polygon)
        if not inside and distance >= radius:
            continue
        collided = True
        nx = nearest[0] - x if inside else x - nearest[0]
        ny = nearest[1] - y if inside else y - nearest[1]
        length = math.hypot(nx, ny)
        if length < 0.001:
            nx, ny, length = 0.0, -1.0, 1.0
        nx /= length
        ny /= length
        x = nearest[0] + nx * (radius + 2.0)
        y = nearest[1] + ny * (radius + 2.0)
        normal_speed = vx * nx + vy * ny
        if normal_speed < 0:
            vx -= 1.48 * normal_speed * nx
            vy -= 1.48 * normal_speed * ny
        vx *= 0.84
        vy *= 0.84
    return x, y, vx, vy, collided


def wrap_text(font, value, width):
    words = value.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if font.size(candidate)[0] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def calculate_propulsion(heading_degrees, wind_degrees, sail_setting, wind_strength, rigging_level, oars_deployed, oar_power, time_seconds):
    heading = math.radians(heading_degrees)
    wind_power = max(0.075, 0.5 + 0.5 * math.cos(heading - math.radians(wind_degrees)))
    sail_thrust = 51.0 * sail_setting * wind_power * wind_strength * (1.0 + rigging_level * 0.10)
    oar_thrust = 0.0
    if oars_deployed:
        stroke_power = 0.90 + 0.10 * (0.5 + 0.5 * math.sin(time_seconds * 8.0))
        oar_thrust = oar_power * 0.30 * stroke_power
    return sail_thrust + oar_thrust, wind_power, sail_thrust, oar_thrust


@dataclass
class Port:
    name: str
    x: float
    y: float
    shore_x: float
    shore_y: float
    exit_heading: float
    description: str


@dataclass
class PirateShip:
    name: str
    x: float
    y: float
    heading: float
    hull: int = 6
    max_hull: int = 6
    vx: float = 0.0
    vy: float = 0.0
    cooldown: float = 1.0
    side_choice: int = 1
    dead: bool = False
    wander: float = 0.0


@dataclass
class FleetShip:
    name: str
    ship_type: str
    x: float
    y: float
    heading: float
    hull: int
    max_hull: int
    vx: float = 0.0
    vy: float = 0.0
    cooldown: float = 1.0
    anchor_x: float = 0.0
    anchor_y: float = 0.0


@dataclass
class Cannonball:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    owner: str


@dataclass
class TreasureSite:
    treasure_id: str
    island_name: str
    polygon: list
    chest_x: float
    chest_y: float
    bottle_x: float
    bottle_y: float
    map_title: str
    clue: str
    riddle: str
    answers: list
    correct_answer: int
    reward: int
    relic: str
    map_found: bool = False
    revealed: bool = False
    dug: bool = False
    trees: list = field(default_factory=list)


class Conversation:
    def __init__(self, game, mission, nodes, on_end=None):
        self.game = game
        self.mission = mission
        self.nodes = []
        self.labels = {}
        self.index = 0
        self.current = None
        self.selected = 0
        self.on_end = on_end
        self.ended = False
        self.flatten(nodes)
        self.advance()

    def flatten(self, nodes):
        for node in nodes:
            if isinstance(node, LabelNode):
                self.labels[node.name] = len(self.nodes)
                self.flatten(node.children)
            else:
                self.nodes.append(node)

    def finish(self):
        if self.ended:
            return
        self.ended = True
        self.current = None
        callback = self.on_end
        self.game.conversation = None
        if callback:
            callback()

    def jump(self, label):
        if label not in self.labels:
            self.finish()
            return
        self.index = self.labels[label]
        self.advance()

    def run_command(self, node):
        if node.command == "accept":
            self.game.accept_mission(self.mission)
            self.finish()
            return True
        if node.command in {"close", "launch", "decline"}:
            if node.command == "decline":
                self.game.toast_message("The offer remains open. Fair winds, captain.", 3.2)
            self.finish()
            return True
        if node.command == "log":
            self.game.add_journal(node.value)
            return False
        if node.command == "offers":
            self.finish()
            self.game.open_mission_offer()
            return True
        if node.command == "news":
            self.finish()
            self.game.show_port_news()
            return True
        if node.command == "shipyard":
            self.finish()
            self.game.open_shipyard()
            return True
        if node.command == "treasure_solve":
            self.game.complete_treasure(node.value)
            self.finish()
            return True
        if node.command == "treasure_wrong":
            self.game.fail_treasure_guess(node.value)
            self.finish()
            return True
        return False

    def advance(self):
        while self.index < len(self.nodes):
            node = self.nodes[self.index]
            self.index += 1
            if isinstance(node, TextNode):
                self.current = node
                self.selected = 0
                return
            if isinstance(node, ChoiceNode):
                self.current = node
                self.selected = 0
                return
            if isinstance(node, GotoNode):
                self.jump(node.label)
                return
            if isinstance(node, CommandNode) and self.run_command(node):
                return
        self.finish()

    def choose(self):
        if not isinstance(self.current, ChoiceNode) or not self.current.options:
            return
        option = self.current.options[self.selected]
        actions = []
        for action in option.actions:
            if isinstance(action, GotoNode):
                self.jump(action.label)
                return
            if isinstance(action, CommandNode):
                if self.run_command(action):
                    return
            elif isinstance(action, LabelNode):
                actions.extend(action.children)
            else:
                actions.append(action)
        self.nodes[self.index:self.index] = actions
        self.advance()

    def handle_key(self, key):
        if isinstance(self.current, ChoiceNode):
            if key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.current.options)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.current.options)
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.choose()
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.advance()


class Game:
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
        self.mission_completion_started = False
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

    def nearest_unfound_bottle(self, maximum_distance=115.0):
        candidates = [
            (math.hypot(self.ship_x - site.bottle_x, self.ship_y - site.bottle_y), site)
            for site in self.treasure_sites if not site.map_found
        ]
        if not candidates:
            return None
        distance, site = min(candidates, key=lambda item: item[0])
        return site if distance <= maximum_distance else None

    def nearest_treasure_shore(self, maximum_distance=210.0):
        candidates = [
            (math.hypot(self.ship_x - site.chest_x, self.ship_y - site.chest_y), site)
            for site in self.treasure_sites if site.revealed
        ]
        if not candidates:
            return None
        distance, site = min(candidates, key=lambda item: item[0])
        return site if distance <= maximum_distance else None

    def update_treasure_discovery(self):
        for site in self.treasure_sites:
            if site.revealed:
                continue
            distance = math.hypot(self.ship_x - (sum(p[0] for p in site.polygon) / len(site.polygon)), self.ship_y - (sum(p[1] for p in site.polygon) / len(site.polygon)))
            reveal_distance = 610.0 if site.map_found else 235.0
            if distance <= reveal_distance:
                site.revealed = True
                if site.map_found:
                    self.toast_message(f"The chart is true! {site.island_name} lies ahead. Search its beach for the mark.", 5.0)
                else:
                    self.toast_message(f"Land ho! An uncharted island has appeared: {site.island_name}.", 4.5)
                    self.add_journal(f"Discovered {site.island_name}, an uncharted cay hidden among the reefs.")

    def interact_treasure(self):
        if self.docked_port or self.conversation or self.journal_open or self.treasure_chart_open:
            return
        bottle = self.nearest_unfound_bottle()
        if bottle:
            bottle.map_found = True
            self.add_journal(f"Recovered a bottle containing {bottle.map_title}. {bottle.clue}")
            self.toast_message(f"Treasure chart recovered: {bottle.map_title}. Press T to study it.", 5.0)
            self.update_treasure_discovery()
            return
        site = self.nearest_treasure_shore()
        if site:
            if site.dug:
                self.toast_message(f"The chest on {site.island_name} has already been claimed.", 3.0)
            elif not site.map_found:
                self.toast_message("The beach is full of old footprints, but you need a chart to find the buried chest.", 4.0)
            else:
                self.start_treasure_riddle(site)
            return
        self.toast_message("Nothing to search here. Keep watch for green-glass bottles drifting on the tide.", 3.5)

    def start_treasure_riddle(self, site):
        options = []
        for index, answer in enumerate(site.answers):
            command = "treasure_solve" if index == site.correct_answer else "treasure_wrong"
            options.append(OptionNode(answer, [CommandNode(command, site.treasure_id)]))
        nodes = [
            TextNode(f"You follow the chart's marks along the beach of {site.island_name}. Beneath the sand you find a weathered chest, its lock carved with a final riddle."),
            TextNode(site.riddle),
            ChoiceNode(options),
        ]
        self.start_custom_conversation("The old pirate's riddle", nodes)

    def complete_treasure(self, treasure_id):
        site = next((item for item in self.treasure_sites if item.treasure_id == treasure_id), None)
        if site is None or site.dug:
            return
        site.dug = True
        self.gold += site.reward
        self.relics.append(site.relic)
        self.add_journal(f"Unearthed the treasure of {site.island_name}: {site.reward} gold and {site.relic}.")
        self.toast_message(f"TREASURE FOUND! +{site.reward} gold — {site.relic}", 6.0)

    def fail_treasure_guess(self, treasure_id):
        site = next((item for item in self.treasure_sites if item.treasure_id == treasure_id), None)
        if site:
            self.toast_message("The lock clicks shut. That answer was not right. Study the chart and try again.", 4.5)

    def toast_message(self, message, duration=3.0):
        self.toast = message
        self.toast_time = duration

    def add_journal(self, entry):
        if entry and entry not in self.journal:
            self.journal.append(entry)
            self.journal = self.journal[-16:]

    def active_mission(self):
        if self.active_mission_id is None:
            return None
        return next((mission for mission in self.missions if mission.mission_id == self.active_mission_id), None)

    def mission_state(self, mission):
        return self.mission_states.get(mission.mission_id, "available")

    def requirements_met(self, mission):
        for requirement in mission.requires_done:
            target = requirement.removesuffix(": done").strip()
            matching = next((item for item in self.missions if item.title == target or item.name == target), None)
            if matching is None or self.mission_state(matching) != "done":
                return False
        return True

    def available_missions_at_port(self):
        if self.active_mission_id is not None or self.docked_port is None:
            return []
        return [
            mission for mission in self.missions
            if self.mission_state(mission) == "available"
            and mission.source == self.docked_port
            and self.requirements_met(mission)
        ]

    def accept_mission(self, mission):
        if mission is None:
            return
        if self.active_mission_id is not None:
            self.toast_message("You already have a voyage to finish.")
            return
        self.mission_states[mission.mission_id] = "active"
        self.active_mission_id = mission.mission_id
        self.mission_kills = 0
        self.mission_completion_started = False
        self.add_journal(f"Accepted: {mission.name}. {mission.description}")
        for node in mission.sections.get("accept", []):
            if isinstance(node, CommandNode) and node.command == "log":
                self.add_journal(node.value)
        if mission.objective_type == "kills":
            self.toast_message(f"Voyage accepted: {mission.name}. Sink {mission.objective_count} pirate ships.", 4.5)
        else:
            self.toast_message(f"Voyage accepted: {mission.name}. Make for {mission.destination}.", 4.5)

    def start_conversation(self, mission, event, on_end=None):
        nodes = mission.sections.get(event, []) if mission else []
        if not nodes:
            if on_end:
                on_end()
            return
        self.dialogue_speaker = mission.section_speakers.get(event, mission.speaker) if mission else "Harbourmaster"
        self.conversation = Conversation(self, mission, nodes, on_end)

    def start_custom_conversation(self, speaker, nodes):
        self.dialogue_speaker = speaker
        self.conversation = Conversation(self, None, nodes)

    def open_port_talk(self):
        greeting = self.port_greetings.get(self.docked_port, "A harbour official looks up as you enter.")
        nodes = [
            TextNode(greeting),
            ChoiceNode([
                self.make_option("Ask whether there is work for a captain.", "offers"),
                self.make_option("Ask for the latest harbour news.", "news"),
                self.make_option("Visit the shipwright and see the yard.", "shipyard"),
                self.make_option("Take my leave.", "close"),
            ]),
        ]
        self.start_custom_conversation("Harbour office", nodes)

    @staticmethod
    def make_option(text, command):
        from mission_system import OptionNode
        return OptionNode(text, [CommandNode(command)])

    def open_mission_offer(self):
        available = self.available_missions_at_port()
        if not available:
            active = self.active_mission()
            if active:
                if active.objective_type == "kills":
                    message = f"The harbourmaster nods toward the open sea. \"You have your orders, captain. {self.mission_kills} of {active.objective_count} pirate ships sent down. Finish the work before you ask me for another voyage.\""
                else:
                    message = f"The harbourmaster taps your chart. \"Your business is not finished. Make for {active.destination}, captain. We will speak again when you return.\""
            else:
                message = "The harbourmaster turns a page in the ledger. \"No new work just now. Check the notice board another day, or listen for news in the taverns.\""
            self.start_custom_conversation("Harbourmaster", [TextNode(message)])
            return
        mission = available[0]
        self.start_conversation(mission, "offer")

    def show_port_news(self):
        message = self.news_by_port.get(self.docked_port, "The harbour is full of rumours, though none worth repeating.")
        self.start_custom_conversation("A sailor at the quay", [TextNode(message)])

    def complete_mission(self, mission):
        self.mission_states[mission.mission_id] = "done"
        self.gold += mission.reward
        self.add_journal(f"Completed {mission.name}. Received {mission.reward} gold.")
        self.toast_message(f"Voyage complete: {mission.name}   +{mission.reward} gold", 5.0)
        self.active_mission_id = None
        self.mission_kills = 0
        self.mission_completion_started = False

    def trigger_port_visit(self, port):
        mission = self.active_mission()
        if not mission or mission.objective_type == "kills" or mission.destination != port.name:
            return
        if self.mission_completion_started:
            return
        self.mission_completion_started = True

        def complete_after_visit():
            self.start_conversation(mission, "complete", lambda: self.complete_mission(mission))

        self.start_conversation(mission, "visit", complete_after_visit)

    def register_pirate_sunk(self, pirate):
        self.gold += 65
        self.add_journal(f"Sank {pirate.name}. Salvaged 65 gold from the wreckage.")
        self.toast_message(f"{pirate.name} is going down! +65 gold", 3.6)
        mission = self.active_mission()
        if mission and mission.objective_type == "kills" and not self.mission_completion_started:
            self.mission_kills += 1
            self.toast_message(f"Pirate ship sunk. Objective: {self.mission_kills}/{mission.objective_count}.", 3.0)
            if self.mission_kills >= mission.objective_count:
                self.mission_completion_started = True
                self.start_conversation(mission, "complete", lambda: self.complete_mission(mission))

    def dock(self, port):
        self.docked_port = port.name
        self.oars_deployed = False
        self.ship_heading = port.exit_heading
        self.ship_x = port.x
        self.ship_y = port.y
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.near_port = port
        self.toast_message(f"Made fast at {port.name}. Q: speak to the harbourmaster.", 4.0)
        self.trigger_port_visit(port)

    def undock(self):
        port = self.ports_by_name[self.docked_port]
        self.ship_heading = port.exit_heading
        self.docked_port = None
        self.toast_message("Cast off! Keep the wind in your sails and the rocks off your keel.", 3.0)

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
        self.camera_zoom = clamp(self.camera_zoom * amount, 0.55, 2.4)
        if abs(self.camera_zoom - old_zoom) < 0.000001:
            return
        self.camera_x = world_anchor[0] - (anchor[0] - width / 2) / self.camera_zoom
        self.camera_y = world_anchor[1] - (anchor[1] - height / 2) / self.camera_zoom
        self.camera_follow = False


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
        bases = {"cannons": 430, "hull": 360, "rigging": 410, "rudder": 320}
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
            old_name = self.player_ship_name
            self.gold -= cost
            self.current_ship = key
            self.player_ship_name = f"The {key} {self.rng.choice(['Fortune', 'Revenge', 'Liberty', 'Tempest', 'Seahawk'])}"
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
            escort = FleetShip(name, key, self.ship_x - 95, self.ship_y + (serial % 2 * 110 - 55), self.ship_heading, stats["hull"], stats["hull"])
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
            radius = 105.0 + (ring - 1) * 82.0
            return self.ship_x + math.cos(angle) * radius, self.ship_y + math.sin(angle) * radius
        columns = 4
        row = index // columns
        row_start = row * columns
        row_count = min(columns, count - row_start)
        column = index - row_start
        lateral = (column - (row_count - 1) / 2.0) * 112.0
        trailing = 145.0 + row * 118.0
        target_x = self.ship_x - forward[0] * trailing + side[0] * lateral
        target_y = self.ship_y - forward[1] * trailing + side[1] * lateral
        return target_x, target_y

    def steer_escort_toward(self, escort, target_x, target_y, dt, turn_rate=54.0, thrust=58.0):
        dx = target_x - escort.x
        dy = target_y - escort.y
        distance = math.hypot(dx, dy)
        if distance > 34.0:
            desired = math.degrees(math.atan2(dy, dx))
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
        title = self.big_font.render("THE SHIPWRIGHT'S YARD", True, (77, 43, 25))
        self.screen.blit(title, title.get_rect(midtop=(box.centerx, box.y + 15)))
        sub = self.small_font.render(f"{self.docked_port}  |  Pieces of eight: {self.gold} g  |  Flagship: {self.player_ship_name}", True, (87, 60, 38))
        self.screen.blit(sub, sub.get_rect(midtop=(box.centerx, box.y + 76)))
        tab_y = box.y + 126
        tab_width = (box.width - 42) // len(self.shipyard_tabs)
        for index, tab in enumerate(self.shipyard_tabs):
            tab_rect = pygame.Rect(box.x + 21 + index * tab_width, tab_y, tab_width - 5, 48)
            selected = index == self.shipyard_tab
            pygame.draw.rect(self.screen, (130, 78, 43) if selected else (193, 171, 130), tab_rect, border_radius=4)
            color = (255, 231, 184) if selected else (75, 51, 34)
            label = self.small_font.render(tab, True, color)
            self.screen.blit(label, label.get_rect(center=tab_rect.center))
        items = self.shipyard_items()
        start_y = tab_y + 64
        row_height = 88
        if self.ship_rename_mode:
            prompt = self.title_font.render("Name your flagship", True, (77, 43, 25))
            self.screen.blit(prompt, (box.x + 42, start_y + 30))
            input_box = pygame.Rect(box.x + 40, start_y + 100, box.width - 80, 66)
            pygame.draw.rect(self.screen, (246, 235, 210), input_box, border_radius=5)
            pygame.draw.rect(self.screen, (142, 98, 60), input_box, 2, border_radius=5)
            text = self.font.render(self.ship_name_input + "▏", True, (54, 43, 30))
            self.screen.blit(text, (input_box.x + 16, input_box.y + 12))
            hint = self.small_font.render("Type a name, then press Enter. Esc cancels.", True, (87, 60, 38))
            self.screen.blit(hint, (input_box.x, input_box.bottom + 24))
        elif not items:
            message = self.font.render("Nothing needs doing on this page, captain.", True, (77, 54, 36))
            self.screen.blit(message, (box.x + 42, start_y + 36))
        else:
            visible_start = max(0, min(self.shipyard_selection - 4, len(items) - 5))
            for visible_index, item in enumerate(items[visible_start:visible_start + 5]):
                index = visible_start + visible_index
                row = pygame.Rect(box.x + 24, start_y + visible_index * row_height, box.width - 48, row_height - 7)
                selected = index == self.shipyard_selection
                pygame.draw.rect(self.screen, (196, 173, 132) if selected else (211, 195, 161), row, border_radius=5)
                if selected:
                    pygame.draw.rect(self.screen, (117, 69, 38), row, 3, border_radius=5)
                label = self.font.render(item["label"], True, (73, 43, 27))
                self.screen.blit(label, (row.x + 15, row.y + 8))
                for line_index, line in enumerate(wrap_text(self.small_font, item["detail"], row.width - 30)[:2]):
                    self.screen.blit(self.small_font.render(line, True, (94, 68, 43)), (row.x + 15, row.y + 43 + line_index * 25))
        footer = self.small_font.render("Up / Down: choose   Enter: confirm   Left / Right: pages   B / Esc: leave the yard", True, (91, 62, 40))
        self.screen.blit(footer, footer.get_rect(midbottom=(box.centerx, box.bottom - 17)))

    def recenter_camera(self):
        self.camera_follow = True
        self.camera_x = self.ship_x
        self.camera_y = self.ship_y
        self.toast_message("Chart centred on your ship. Click and drag to pan.", 3.0)

    def handle_keydown(self, event):
        key = event.key
        if self.shipyard_open:
            if self.ship_rename_mode:
                if key == pygame.K_ESCAPE:
                    self.ship_rename_mode = False
                    pygame.key.stop_text_input()
                elif key == pygame.K_BACKSPACE:
                    self.ship_name_input = self.ship_name_input[:-1]
                elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    clean_name = self.ship_name_input.strip()[:24]
                    if clean_name:
                        self.player_ship_name = clean_name
                        self.add_journal(f"Renamed your flagship to {clean_name}.")
                        self.toast_message(f"Your ship shall be known as {clean_name}.", 3.0)
                    self.ship_rename_mode = False
                    pygame.key.stop_text_input()
                return
            if key in (pygame.K_ESCAPE, pygame.K_b):
                self.shipyard_open = False
                return
            if key in (pygame.K_LEFT, pygame.K_a, pygame.K_TAB):
                self.shipyard_tab = (self.shipyard_tab - 1) % len(self.shipyard_tabs)
                self.shipyard_selection = 0
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.shipyard_tab = (self.shipyard_tab + 1) % len(self.shipyard_tabs)
                self.shipyard_selection = 0
            elif key in (pygame.K_UP, pygame.K_w):
                items = self.shipyard_items()
                if items:
                    self.shipyard_selection = (self.shipyard_selection - 1) % len(items)
            elif key in (pygame.K_DOWN, pygame.K_s):
                items = self.shipyard_items()
                if items:
                    self.shipyard_selection = (self.shipyard_selection + 1) % len(items)
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.execute_shipyard_selection()
            return
        if self.conversation:
            if key == pygame.K_ESCAPE:
                self.conversation.finish()
            else:
                self.conversation.handle_key(key)
            return
        if self.journal_open:
            if key in (pygame.K_ESCAPE, pygame.K_j):
                self.journal_open = False
            return
        if self.treasure_chart_open:
            if key in (pygame.K_ESCAPE, pygame.K_t):
                self.treasure_chart_open = False
            return
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_F1:
            self.show_help = not self.show_help
        elif key == pygame.K_j:
            self.journal_open = True
        elif key == pygame.K_t:
            self.treasure_chart_open = True
        elif key == pygame.K_r:
            self.interact_treasure()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.zoom(1.12)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.zoom(1 / 1.12)
        elif key == pygame.K_c:
            self.recenter_camera()
        elif key == pygame.K_o:
            if self.docked_port:
                self.toast_message("The oarsmen are ashore while the ship is moored.", 2.8)
            else:
                self.oars_deployed = not self.oars_deployed
                if self.oars_deployed:
                    rowers = self.player_ship_stats().get("rowers", 8)
                    self.toast_message(f"OARS OUT! {rowers} oarsmen take their benches. Pull against the wind!", 3.6)
                else:
                    self.toast_message("Oars shipped. Let the canvas carry you.", 2.8)
        elif key == pygame.K_q and self.docked_port:
            self.open_port_talk()
        elif key == pygame.K_b:
            if self.docked_port:
                self.open_shipyard()
            else:
                self.toast_message("The shipyard is in port, captain. Make fast alongside first.", 3.0)
        elif key == pygame.K_e:
            if self.docked_port:
                self.undock()
            elif self.near_port:
                speed = math.hypot(self.ship_vx, self.ship_vy)
                if speed > 62:
                    self.toast_message("Too much way on! Reef the sails and come alongside slowly.", 3.0)
                else:
                    self.dock(self.near_port)
            else:
                self.toast_message("No pier nearby. Find a harbour and come in slowly.", 2.5)
        elif key == pygame.K_z:
            self.fire_broadside(-1)
        elif key == pygame.K_x:
            self.fire_broadside(1)
        elif key == pygame.K_f:
            self.set_fleet_order("fight")
        elif key == pygame.K_h:
            self.set_fleet_order("hold_fire")
        elif key == pygame.K_g:
            self.set_fleet_order("gather")
        elif key == pygame.K_v:
            self.set_fleet_order("follow")

    def handle_event(self, event):
        if event.type == pygame.TEXTINPUT and self.shipyard_open and self.ship_rename_mode:
            allowed = "".join(character for character in event.text if character.isprintable())
            self.ship_name_input = (self.ship_name_input + allowed)[:24]
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3):
            if not self.conversation and not self.journal_open and not self.treasure_chart_open and not self.shipyard_open:
                self.camera_dragging = True
                self.camera_drag_last = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 2, 3):
            self.camera_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.camera_dragging:
            if not self.conversation and not self.journal_open and not self.treasure_chart_open and not self.shipyard_open:
                dx = event.pos[0] - self.camera_drag_last[0]
                dy = event.pos[1] - self.camera_drag_last[1]
                self.camera_x -= dx / self.camera_zoom
                self.camera_y -= dy / self.camera_zoom
                self.camera_follow = False
                self.camera_drag_last = event.pos
        elif event.type == pygame.MOUSEWHEEL and not self.conversation and not self.journal_open and not self.treasure_chart_open and not self.shipyard_open:
            anchor = getattr(event, "mouse_pos", None)
            if anchor is None and hasattr(event, "mouse_x") and hasattr(event, "mouse_y"):
                anchor = (event.mouse_x, event.mouse_y)
            if anchor is None:
                anchor = pygame.mouse.get_pos()
            self.zoom(1.12 ** event.y, anchor)
        elif event.type == pygame.QUIT:
            self.running = False

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
        reinforcement_delay = 22.0 if active_mission and active_mission.objective_type == "kills" else 45.0
        if active_count < 2:
            self.reinforcement_timer -= dt
            if self.reinforcement_timer <= 0:
                self.spawn_pirate_reinforcement()
                self.reinforcement_timer = reinforcement_delay
        else:
            self.reinforcement_timer = reinforcement_delay
        for pirate in self.pirates:
            if pirate.dead:
                continue
            pirate.cooldown = max(0.0, pirate.cooldown - dt)
            distance = math.hypot(self.ship_x - pirate.x, self.ship_y - pirate.y)
            dx = self.ship_x - pirate.x
            dy = self.ship_y - pirate.y
            bearing = math.degrees(math.atan2(dy, dx))
            if distance < 1100:
                if distance > 430:
                    desired = bearing
                else:
                    side_a = bearing - 90
                    side_b = bearing + 90
                    current_a = abs(angle_difference(side_a, pirate.heading))
                    current_b = abs(angle_difference(side_b, pirate.heading))
                    desired = side_a if current_a <= current_b else side_b
            else:
                pirate.wander += dt * 0.22
                desired = pirate.heading + math.sin(pirate.wander) * 17.0
            difference = angle_difference(desired, pirate.heading)
            pirate.heading = (pirate.heading + clamp(difference, -43.0 * dt, 43.0 * dt)) % 360.0
            angle = math.radians(pirate.heading)
            pirate.vx += math.cos(angle) * (36.0 if distance < 1100 else 18.0) * dt
            pirate.vy += math.sin(angle) * (36.0 if distance < 1100 else 18.0) * dt
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

    def world_to_screen(self, x, y):
        width, height = self.screen.get_size()
        sx = (x - self.camera_x) * self.camera_zoom + width / 2
        sy = (y - self.camera_y) * self.camera_zoom + height / 2
        return int(sx), int(sy)

    def polygon_to_screen(self, polygon):
        return [self.world_to_screen(x, y) for x, y in polygon]

    def update_camera(self):
        if self.camera_follow:
            self.camera_x = self.ship_x
            self.camera_y = self.ship_y

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
        for port in self.ports:
            self.draw_port(port)
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
                if self.camera_zoom > 0.72:
                    label_pos = self.world_to_screen(pirate.x, pirate.y - 52)
                    label = self.tiny_font.render(pirate.name, True, (255, 224, 185))
                    label_rect = label.get_rect(center=label_pos)
                    pygame.draw.rect(self.screen, (37, 28, 24), label_rect.inflate(8, 4), border_radius=3)
                    self.screen.blit(label, label_rect)
        self.draw_ship(self.ship_x, self.ship_y, self.ship_heading, True, rowing=self.oars_deployed)
        self.draw_cannonballs()

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
        active = self.active_mission()
        if active:
            objective = f"SINK {self.mission_kills}/{active.objective_count} SHIPS" if active.objective_type == "kills" else f"SAIL FOR {active.destination.upper()}"
            quest_box = pygame.Rect(18, height - 190, min(720, width - 36), 84)
            pygame.draw.rect(self.screen, (38, 25, 19), quest_box.inflate(5, 5), border_radius=6)
            pygame.draw.rect(self.screen, (120, 77, 43), quest_box, border_radius=6)
            pygame.draw.rect(self.screen, (221, 185, 122), quest_box.inflate(-5, -5), 1, border_radius=5)
            self.screen.blit(self.small_font.render(active.name.upper(), True, (250, 222, 168)), (quest_box.x + 14, quest_box.y + 8))
            self.screen.blit(self.small_font.render(objective, True, (240, 239, 212)), (quest_box.x + 14, quest_box.y + 46))
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
            if bottle:
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
                pygame.draw.circle(self.screen, (184, 60, 49), point, 2)
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
            "Q       Speak at a port",
            "R       Recover maps / dig for treasure",
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
        if active:
            objective = f"Ships sunk: {self.mission_kills}/{active.objective_count}" if active.objective_type == "kills" else f"Destination: {active.destination}"
            self.screen.blit(self.font.render(f"Current voyage: {active.name}", True, (73, 47, 31)), (box.x + 30, y))
            self.screen.blit(self.small_font.render(objective, True, (97, 66, 42)), (box.x + 30, y + 36))
            y += 78
        else:
            self.screen.blit(self.font.render("No voyage under contract.", True, (73, 47, 31)), (box.x + 30, y))
            y += 43
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

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.04)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
