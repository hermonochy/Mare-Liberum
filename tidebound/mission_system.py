import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TextNode:
    text: str


@dataclass
class GotoNode:
    label: str


@dataclass
class BranchNode:
    label: str
    expression: str


@dataclass
class CommandNode:
    command: str
    value: str = ""


@dataclass
class LabelNode:
    name: str
    children: list = field(default_factory=list)


@dataclass
class OptionNode:
    text: str
    actions: list = field(default_factory=list)


@dataclass
class ChoiceNode:
    options: list = field(default_factory=list)


@dataclass
class MissionWaypoint:
    port: str
    objective: str


@dataclass
class Mission:
    mission_id: str
    title: str
    name: str
    description: str
    source: str
    destination: str
    reward: int
    requires_done: list
    objective_type: str
    objective_count: int
    battlefield: str
    battlefield_x: float
    battlefield_y: float
    enemy_names: list
    speaker: str
    section_speakers: dict
    sections: dict
    path: Path
    category: str = "main"
    lead: str = ""
    waypoints: list = field(default_factory=list)
    event_expression: str = ""
    event_config: dict = field(default_factory=dict)
    offer_expression: str = ""
    fail_expression: str = ""
    start_expression: str = ""
    complete_expression: str = ""
    show_expression: str = ""
    display_expression: str = ""
    accept_expression: str = ""
    offer_at: str = "port"
    ambient: bool = False
    repeatable: bool = False
    cooldown_seconds: float = 0.0
    max_triggers: int = 0
    deadline_seconds: float = 0.0
    priority: int = 0
    mission_kind: str = "voyage"
    directives: dict = field(default_factory=dict)
    objective_target: str = ""


class MissionParser:
    def __init__(self, path):
        self.path = Path(path)
        self.lines = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                indent = len(raw) - len(raw.lstrip(" "))
                self.lines.append((indent, raw.strip()))
        self.index = 0
        self.node_lines = []
        self.node_index = 0

    @staticmethod
    def quoted(text):
        match = re.search(r'"(.*)"', text)
        if match:
            return match.group(1)
        return text.split(None, 1)[-1] if " " in text else ""

    def parse(self):
        if not self.lines or not self.lines[0][1].startswith("mission "):
            raise ValueError(f"Missing mission declaration in {self.path.name}")
        title = self.quoted(self.lines[0][1])
        mission_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        name = title
        description = ""
        source = ""
        destination = ""
        reward = 0
        requirements = []
        objective_type = "port"
        objective_count = 0
        objective_target = ""
        battlefield = ""
        battlefield_x = None
        battlefield_y = None
        enemy_names = []
        speaker = "Harbourmaster"
        category = "main"
        lead = ""
        waypoints = []
        event_expression = ""
        offer_expression = ""
        fail_expression = ""
        start_expression = ""
        complete_expression = ""
        show_expression = ""
        display_expression = ""
        accept_expression = ""
        offer_at = "port"
        ambient = False
        repeatable = False
        cooldown_seconds = 0.0
        max_triggers = 0
        deadline_seconds = 0.0
        priority = 0
        mission_kind = "voyage"
        directives = {}
        event_config = {
            "ship_types": [],
            "ship_names": [],
            "actions": [],
            "on_complete": [],
            "on_repelled": [],
            "faction": "pirate",
            "attitude": "hostile",
        }
        section_speakers = {}
        sections = {}
        self.index = 1
        while self.index < len(self.lines):
            indent, text = self.lines[self.index]
            if indent != 4:
                self.index += 1
                continue
            self.index += 1
            if text.startswith("event "):
                event_expression = text[len("event "):].strip()
                if not event_expression:
                    raise ValueError(f"Event requires a trigger expression in {self.path.name}")
            elif text.startswith("event_delay "):
                values = text.split()[1:]
                if len(values) != 2:
                    raise ValueError(f"event_delay requires minimum and maximum in {self.path.name}")
                event_config["delay"] = {"minimum": float(values[0]), "maximum": float(values[1])}
            elif text.startswith("event_cancel_if "):
                event_config["cancel_if_expression"] = text[len("event_cancel_if "):].strip()
            elif text.startswith("event_action "):
                event_config["actions"].append(self.parse_event_action(text[len("event_action "):]))
            elif text.startswith("event_on_complete "):
                event_config["on_complete"].append(self.parse_event_action(text[len("event_on_complete "):]))
            elif text.startswith("event_on_repelled "):
                event_config["on_repelled"].append(self.parse_event_action(text[len("event_on_repelled "):]))
            elif text.startswith("event_pause_while_docked "):
                event_config["pause_while_docked"] = text.split(None, 1)[1].lower() in {"true", "yes", "1"}
            elif text.startswith("event_repeatable "):
                event_config["repeatable"] = text.split(None, 1)[1].lower() in {"true", "yes", "1"}
            elif text.startswith("event_max_triggers "):
                event_config["max_triggers"] = int(text.split(None, 1)[1])
            elif text.startswith("event_cooldown "):
                event_config["cooldown_seconds"] = float(text.split(None, 1)[1])
            elif text.startswith("event_spawn_fleet "):
                quoted = re.findall(r'"([^"\n]*)"', text)
                trailing = text.rsplit('"', 1)[-1].split()
                if len(quoted) < 2 or len(trailing) < 5:
                    raise ValueError(f"event_spawn_fleet requires name, commander, min, max, hard max, strength ratio and spawn distance in {self.path.name}")
                event_config["spawn_fleet"] = {
                    "name": quoted[0],
                    "commander": quoted[1],
                    "minimum_ships": int(trailing[0]),
                    "maximum_ships": int(trailing[1]),
                    "hard_maximum_ships": int(trailing[2]),
                    "strength_ratio": float(trailing[3]),
                    "spawn_distance": float(trailing[4]),
                }
            elif text.startswith("event_faction "):
                event_config["faction"] = self.quoted(text)
            elif text.startswith("event_attitude "):
                event_config["attitude"] = self.quoted(text).lower()
            elif text.startswith("event_ship_types "):
                event_config["ship_types"] = re.findall(r'"([^"\n]*)"', text)
            elif text.startswith("event_ship_name "):
                event_config["ship_names"].append(self.quoted(text))
            elif text.startswith("event_announcement "):
                event_config["announcement"] = self.quoted(text)
                trailing = text.rsplit('"', 1)[-1].split()
                if trailing:
                    event_config["announcement_seconds"] = float(trailing[0])
            elif text.startswith("event_journal_entry "):
                event_config["journal_entry"] = self.quoted(text)
            elif text.startswith("event_complete_flag "):
                event_config["complete_flag"] = self.quoted(text)
            elif text.startswith("event_complete_text "):
                event_config["complete_text"] = self.quoted(text)
            elif text.startswith("event_repelled_text "):
                event_config["repelled_text"] = self.quoted(text)
            elif text.startswith("offer_expression "):
                offer_expression = self.quoted(text)
            elif text.startswith("offer_at "):
                offer_at = self.quoted(text).lower()
            elif text.startswith("ambient "):
                ambient = text.split(None, 1)[1].lower() in {"true", "yes", "1"}
            elif text == "repeat":
                repeatable = True
            elif text.startswith(("repeatable ", "repeat ")):
                repeatable = text.split(None, 1)[1].lower() in {"true", "yes", "1"}
            elif text.startswith("cooldown "):
                cooldown_seconds = max(0.0, float(text.split(None, 1)[1]))
            elif text.startswith("max_triggers "):
                max_triggers = max(0, int(text.split(None, 1)[1]))
            elif text.startswith("deadline "):
                deadline_seconds = max(0.0, float(text.split(None, 1)[1]))
            elif text.startswith("priority "):
                priority = int(text.split(None, 1)[1])
            elif text.startswith("kind "):
                mission_kind = self.quoted(text).lower()
            elif text.startswith("name "):
                name = self.quoted(text)
            elif text.startswith("description "):
                description = self.quoted(text)
            elif text.startswith("source "):
                source = self.quoted(text)
            elif text.startswith("destination "):
                destination = self.quoted(text)
            elif text.startswith("reward "):
                reward = int(text.split(None, 1)[1])
            elif text.startswith("category "):
                category = self.quoted(text).lower()
            elif text.startswith("lead "):
                lead = self.quoted(text)
            elif text.startswith("waypoint "):
                values = re.findall(r'"([^"\n]*)"', text)
                if len(values) < 2:
                    raise ValueError(f"Waypoint must contain a port and objective in {self.path.name}: {text}")
                waypoints.append(MissionWaypoint(values[0], values[1]))
            elif text.startswith("stopover "):
                waypoints.append(MissionWaypoint(self.quoted(text), "Make the required stopover"))
            elif text == "landing":
                directives["landing_required"] = True
            elif text in {"minor", "invisible", "non-blocking", "job"}:
                directives[text.replace("-", "_")] = True
            elif text.startswith("passengers "):
                directives["passengers"] = max(0, int(text.split(None, 1)[1]))
            elif text.startswith("speaker "):
                parts = text.split(None, 2)
                if len(parts) == 3 and (parts[1] in {"offer", "accept", "visit", "complete", "fail"} or parts[1].startswith("waypoint_")):
                    section_speakers[parts[1]] = self.quoted(text)
                else:
                    speaker = self.quoted(text)
            elif text.startswith("objective "):
                parts = shlex.split(text)
                objective_type = parts[1].lower() if len(parts) > 1 else "port"
                if len(parts) > 2:
                    try:
                        objective_count = int(parts[2])
                    except ValueError:
                        objective_target = parts[2]
            elif text.startswith("battlefield "):
                quoted_values = re.findall(r'"([^"]*)"', text)
                battlefield = quoted_values[0] if quoted_values else ""
                coordinate_text = text.rsplit('"', 1)[-1].strip()
                coordinates = coordinate_text.split()
                if len(coordinates) >= 2:
                    battlefield_x = float(coordinates[0])
                    battlefield_y = float(coordinates[1])
            elif text.startswith("enemy "):
                enemy_names.append(self.quoted(text))
            elif text in {"to offer", "to fail", "to start", "to complete", "to show", "to display", "to accept"}:
                condition_lines = []
                while self.index < len(self.lines) and self.lines[self.index][0] > 4:
                    condition_lines.append(self.lines[self.index])
                    self.index += 1
                from .mission_expression import legacy_condition_to_expression
                converted = legacy_condition_to_expression(condition_lines)
                target = {"to offer": "offer_expression", "to fail": "fail_expression", "to start": "start_expression", "to complete": "complete_expression", "to show": "show_expression", "to display": "display_expression", "to accept": "accept_expression"}[text]
                existing = {
                    "offer_expression": offer_expression,
                    "fail_expression": fail_expression,
                    "start_expression": start_expression,
                    "complete_expression": complete_expression,
                    "show_expression": show_expression,
                    "display_expression": display_expression,
                    "accept_expression": accept_expression,
                }[target]
                locals_value = f"({existing}) and ({converted})" if existing and converted else existing or converted
                if target == "offer_expression":
                    offer_expression = locals_value
                    if not any(condition.strip().lower() == "or" for _, condition in condition_lines):
                        for _, condition in condition_lines:
                            if condition.startswith("has ") and self.quoted(condition).lower().endswith(": done"):
                                requirements.append(self.quoted(condition))
                elif target == "fail_expression":
                    fail_expression = locals_value
                elif target == "start_expression":
                    start_expression = locals_value
                elif target == "show_expression":
                    show_expression = locals_value
                elif target == "display_expression":
                    display_expression = locals_value
                elif target == "accept_expression":
                    accept_expression = locals_value
                else:
                    complete_expression = locals_value
            elif text.startswith("on "):
                event = text[3:].strip()
                body = []
                while self.index < len(self.lines) and self.lines[self.index][0] > 4:
                    body.append(self.lines[self.index])
                    self.index += 1
                sections[event] = self.parse_nodes(body)
        from .mission_expression import MissionExpression
        for condition_expression in (offer_expression, fail_expression, start_expression, complete_expression, show_expression, display_expression, accept_expression):
            if condition_expression:
                try:
                    MissionExpression(condition_expression)
                except ValueError as error:
                    raise ValueError(f"Invalid mission condition in {self.path.name}: {error}") from error
        return Mission(
            mission_id=mission_id,
            title=title,
            name=name,
            description=description,
            source=source,
            destination=destination,
            reward=reward,
            requires_done=requirements,
            objective_type=objective_type,
            objective_count=objective_count,
            battlefield=battlefield,
            battlefield_x=battlefield_x,
            battlefield_y=battlefield_y,
            enemy_names=enemy_names,
            speaker=speaker,
            section_speakers=section_speakers,
            sections=sections,
            path=self.path,
            category="event" if event_expression else category,
            lead=lead,
            waypoints=waypoints,
            event_expression=event_expression,
            event_config=event_config,
            offer_expression=offer_expression,
            fail_expression=fail_expression,
            start_expression=start_expression,
            complete_expression=complete_expression,
            show_expression=show_expression,
            display_expression=display_expression,
            accept_expression=accept_expression,
            offer_at=offer_at,
            ambient=ambient or category == "ambient" or mission_kind == "ambient",
            repeatable=repeatable,
            cooldown_seconds=cooldown_seconds,
            max_triggers=max_triggers,
            deadline_seconds=deadline_seconds,
            priority=priority,
            mission_kind=mission_kind,
            directives=directives,
            objective_target=objective_target,
        )

    @staticmethod
    def parse_event_action(text):
        parts = shlex.split(text)
        if not parts:
            raise ValueError("Event action cannot be empty")
        kind = parts[0].lower()
        args = parts[1:]

        def amount(index):
            try:
                value = float(args[index])
            except (IndexError, ValueError):
                raise ValueError(f"Event action '{kind}' requires a numeric amount")
            return int(value) if value.is_integer() else value

        def required(index):
            if index >= len(args):
                raise ValueError(f"Event action '{kind}' is missing an argument")
            return args[index]

        if kind == "spawn_fleet":
            if len(args) < 7:
                raise ValueError("Event action 'spawn_fleet' requires name, commander, minimum, maximum, hard maximum, strength ratio and spawn distance")
            action = {
                "type": kind,
                "name": required(0),
                "commander": required(1),
                "minimum_ships": int(args[2]),
                "maximum_ships": int(args[3]),
                "hard_maximum_ships": int(args[4]),
                "strength_ratio": float(args[5]),
                "spawn_distance": float(args[6]),
                "ship_types": [str(value) for value in args[7:] if value],
            }
            if len(action["ship_types"]) == 0:
                action["ship_types"] = ["Schooner", "Brigantine", "Brig"]
            return action
        if kind in {"toast", "journal"}:
            action = {"type": kind, "text": required(0)}
            if kind == "toast" and len(args) > 1:
                action["seconds"] = float(args[1])
            return action
        if kind in {"give_gold", "set_gold"}:
            return {"type": kind, "amount": amount(0)}
        if kind == "set_flag":
            value = required(1) if len(args) > 1 else "true"
            lowered = value.lower()
            if lowered in {"true", "false"}:
                parsed = lowered == "true"
            else:
                try:
                    parsed_number = float(value)
                    parsed = int(parsed_number) if parsed_number.is_integer() else parsed_number
                except ValueError:
                    parsed = value
            return {"type": kind, "key": required(0), "value": parsed}
        if kind == "add_flag":
            return {"type": kind, "key": required(0), "amount": amount(1)}
        if kind == "remove_flag":
            return {"type": kind, "key": required(0)}
        if kind == "adjust_relation":
            action = {"type": kind, "faction": required(0), "amount": amount(1)}
            if len(args) > 2:
                action["reason"] = " ".join(args[2:])
            return action
        if kind == "set_mission_state":
            return {"type": kind, "mission": required(0), "state": required(1)}
        if kind == "schedule_event":
            action = {"type": kind, "event": required(0)}
            if len(args) == 2:
                action["delay"] = {"minimum": float(args[1]), "maximum": float(args[1])}
            elif len(args) >= 3:
                action["delay"] = {"minimum": float(args[1]), "maximum": float(args[2])}
            if len(args) >= 4:
                action["force"] = args[3].lower() in {"true", "yes", "1"}
            return action
        if kind in {"enable_event", "disable_event", "retreat_fleet"}:
            return {"type": kind, "event": required(0)}
        if kind in {"add_cargo", "remove_cargo"}:
            return {"type": kind, "good": required(0), "amount": amount(1)}
        if kind == "reveal_island":
            return {"type": kind, "name": required(0)}
        if kind == "reveal_wreck":
            return {"type": kind, "name": required(0)}
        if kind == "spawn_island":
            return {
                "type": kind,
                "name": required(0),
                "offset_x": float(args[1]) if len(args) > 1 else 1800.0,
                "offset_y": float(args[2]) if len(args) > 2 else 900.0,
                "radius": float(args[3]) if len(args) > 3 else 360.0,
            }
        if kind == "set_port_faction":
            return {"type": kind, "port": required(0), "faction": required(1)}
        if kind == "set_wind":
            if len(args) < 2:
                raise ValueError("Event action 'set_wind' requires angle and strength")
            return {
                "type": kind,
                "angle": float(args[0]),
                "strength": float(args[1]),
                "duration": float(args[2]) if len(args) > 2 else 240.0,
            }
        if kind == "set_sea_state":
            return {"type": kind, "state": required(0), "duration": float(args[1]) if len(args) > 1 else 240.0}
        raise ValueError(f"Unknown event action '{kind}'")

    def parse_nodes(self, lines):
        self.node_lines = lines
        self.node_index = 0
        if not lines:
            return []
        base_indent = min(indent for indent, _ in lines)
        return self.parse_sequence(base_indent)

    def parse_sequence(self, base_indent):
        nodes = []
        while self.node_index < len(self.node_lines):
            indent, text = self.node_lines[self.node_index]
            if indent < base_indent:
                break
            if indent > base_indent:
                self.node_index += 1
                continue
            self.node_index += 1
            if text == "conversation":
                nodes.extend(self.parse_sequence(indent + 4))
            elif text == "choice":
                nodes.append(self.parse_choice(indent))
            elif text.startswith("label "):
                label_name = text.split(None, 1)[1].strip()
                nodes.append(LabelNode(label_name, self.parse_sequence(indent + 4)))
            elif text.startswith("goto "):
                nodes.append(GotoNode(text.split(None, 1)[1].strip()))
            elif text.startswith("branch "):
                label = text.split(None, 1)[1].strip()
                condition_lines = []
                while self.node_index < len(self.node_lines) and self.node_lines[self.node_index][0] > indent:
                    condition_lines.append(self.node_lines[self.node_index])
                    self.node_index += 1
                from .mission_expression import MissionExpression, legacy_condition_to_expression
                expression = legacy_condition_to_expression(condition_lines)
                if not expression:
                    raise ValueError(f"Branch '{label}' requires a condition")
                MissionExpression(expression)
                nodes.append(BranchNode(label, expression))
            elif text == "action":
                nodes.extend(self.parse_sequence(indent + 4))
            elif text.startswith("`") and text.endswith("`"):
                nodes.append(TextNode(text[1:-1]))
            elif text in {
                "accept", "decline", "defer", "close", "launch", "depart", "flee",
                "offers", "intro_mission", "day_jobs", "accept_day_job", "decline_day_job",
                "news", "shipyard", "curiosities",
            }:
                nodes.append(CommandNode(text))
            elif text.startswith("mission_offer "):
                nodes.append(CommandNode("mission_offer", self.quoted(text)))
            elif text.startswith("log "):
                nodes.append(CommandNode("log", self.quoted(text)))
            elif text.startswith(("purchase_unique ", "inspect_scam ", "learn_secret ")):
                command, _, payload = text.partition(" ")
                nodes.append(CommandNode(command, self.quoted(payload)))
            elif text.startswith("set "):
                payload = text.partition(" ")[2].strip()
                values = shlex.split(payload)
                if len(values) == 2 and values[1] in {"++", "--"}:
                    nodes.append(CommandNode("increment_flag", f"{values[0]} {1 if values[1] == '++' else -1}"))
                else:
                    nodes.append(CommandNode("set_flag", payload))
            elif text.startswith("clear "):
                nodes.append(CommandNode("clear_flag", text.partition(" ")[2].strip()))
            elif text.startswith(("set_flag ", "clear_flag ", "give_gold ", "adjust_relation ", "schedule_event ", "reveal_island ", "reveal_wreck ", "set_wind ", "set_sea_state ")):
                command, _, payload = text.partition(" ")
                nodes.append(CommandNode(command, payload.strip()))
        return nodes

    def parse_choice(self, choice_indent):
        options = []
        option_indent = choice_indent + 4
        while self.node_index < len(self.node_lines):
            indent, text = self.node_lines[self.node_index]
            if indent <= choice_indent:
                break
            if indent != option_indent:
                self.node_index += 1
                continue
            if not (text.startswith("`") and text.endswith("`")):
                self.node_index += 1
                continue
            self.node_index += 1
            actions = self.parse_sequence(option_indent + 4)
            options.append(OptionNode(text[1:-1], actions))
        return ChoiceNode(options)


def load_missions(directory):
    missions = [MissionParser(path).parse() for path in sorted(Path(directory).glob("*.mission"))]
    used_ids = set()
    for mission in missions:
        base_id = mission.mission_id
        if base_id in used_ids:
            prefix = mission.path.stem.split("_", 1)[0]
            suffix = prefix if prefix.isdigit() else mission.path.stem
            candidate = f"{base_id}_{suffix}"
            serial = 2
            while candidate in used_ids:
                candidate = f"{base_id}_{suffix}_{serial}"
                serial += 1
            mission.mission_id = candidate
        used_ids.add(mission.mission_id)
    return missions
