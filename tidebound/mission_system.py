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
        battlefield = ""
        battlefield_x = None
        battlefield_y = None
        enemy_names = []
        speaker = "Harbourmaster"
        category = "main"
        lead = ""
        waypoints = []
        event_expression = ""
        event_config = {
            "ship_types": [],
            "ship_names": [],
            "actions": [],
            "on_complete": [],
            "on_repelled": [],
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
            elif text.startswith("speaker "):
                parts = text.split(None, 2)
                if len(parts) == 3 and (parts[1] in {"offer", "accept", "visit", "complete", "fail"} or parts[1].startswith("waypoint_")):
                    section_speakers[parts[1]] = self.quoted(text)
                else:
                    speaker = self.quoted(text)
            elif text.startswith("objective "):
                parts = text.split()
                objective_type = parts[1].lower()
                objective_count = int(parts[2]) if len(parts) > 2 else 0
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
            elif text == "to offer":
                while self.index < len(self.lines) and self.lines[self.index][0] > 4:
                    condition_indent, condition = self.lines[self.index]
                    self.index += 1
                    if condition_indent >= 8 and condition.startswith("has "):
                        requirements.append(self.quoted(condition))
            elif text.startswith("on "):
                event = text[3:].strip()
                body = []
                while self.index < len(self.lines) and self.lines[self.index][0] > 4:
                    body.append(self.lines[self.index])
                    self.index += 1
                sections[event] = self.parse_nodes(body)
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
            category=category,
            lead=lead,
            waypoints=waypoints,
            event_expression=event_expression,
            event_config=event_config,
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
            elif text.startswith("`") and text.endswith("`"):
                nodes.append(TextNode(text[1:-1]))
            elif text in {"accept", "decline", "close", "launch"}:
                nodes.append(CommandNode(text))
            elif text.startswith("log "):
                nodes.append(CommandNode("log", self.quoted(text)))
            elif text.startswith(("purchase_unique ", "inspect_scam ", "learn_secret ")):
                command, _, payload = text.partition(" ")
                nodes.append(CommandNode(command, self.quoted(payload)))
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
    missions = []
    for path in sorted(Path(directory).glob("*.mission")):
        missions.append(MissionParser(path).parse())
    return missions
