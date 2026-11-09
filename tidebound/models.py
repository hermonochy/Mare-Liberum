from dataclasses import dataclass, field


@dataclass
class Port:
    name: str
    x: float
    y: float
    shore_x: float
    shore_y: float
    exit_heading: float
    description: str
    region: str = "Old Caribbean"
    faction: str = "Independent"

@dataclass
class Reef:
    name: str
    polygon: list
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    bounds: tuple


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
    mission_id: str = ""
    objective_target: bool = False
    ship_type: str = "Sloop"
    npc_target_name: str = ""
    fleet_id: str = ""
    commander_name: str = ""
    formation_slot: int = 0
    fleet_morale: float = 1.0
    retreating: bool = False
    fleet_size: int = 1
    player_attitude: str = "hostile"
    player_incident_recorded: bool = False
    player_provoked: bool = False

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
class TrafficShip:
    name: str
    role: str
    ship_type: str
    x: float
    y: float
    heading: float
    destination: str
    hull: int = 5
    max_hull: int = 5
    vx: float = 0.0
    vy: float = 0.0
    wander: float = 0.0
    collision_bump_cooldown: float = 0.0
    combat_target_name: str = ""
    combat_cooldown: float = 0.0
    under_attack: bool = False
    fleet_id: str = ""
    commander_name: str = ""
    formation_slot: int = 0
    fleet_morale: float = 1.0
    retreating: bool = False
    fleet_size: int = 1
    hostile_to_player: bool = False
    faction: str = ""
    player_attitude: str = "neutral"
    player_provoked: bool = False
    player_incident_recorded: bool = False
    berth_port: str = ""
    berth_slot: int = -1
    port_dwell: float = 0.0

@dataclass
class Cannonball:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    owner: str
    source_commander: str = ""
    source_faction: str = ""
    source_fleet_id: str = ""

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


@dataclass
class DayJob:
    job_id: str
    kind: str
    title: str
    source: str
    destination: str
    reward: int
    speaker: str
    offer_text: str
    payload: str
    objective: str
    target_x: float = None
    target_y: float = None
    stage: str = "offered"
    rescued: bool = False


@dataclass
class ShipwreckSite:
    wreck_id: str
    name: str
    x: float
    y: float
    heading: float
    vessel_name: str
    age_description: str
    description: str
    hazard_description: str
    risk_level: int
    surface_gold: int
    deep_gold: int
    rare_discovery: str
    rare_chance: float
    discovered: bool = False
    surface_salvaged: bool = False
    deep_attempted: bool = False
    rare_found: bool = False

    @property
    def fully_salvaged(self):
        return self.surface_salvaged and self.deep_attempted
