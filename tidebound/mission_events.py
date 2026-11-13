import ast
import math
import re
from pathlib import Path

from .config import SHIP_CLASSES, TRADE_GOODS_BY_ID
from .mission_system import MissionParser


CONDITION_TYPES = {
    "escort_count",
    "fleet_ship_count",
    "fleet_power",
    "gold",
    "world_time",
    "mission_state",
    "faction_standing",
    "flag",
    "ship_class",
    "ship_upgrade",
    "hull_percent",
    "completed_day_jobs",
    "relic_count",
    "unique_item_count",
    "region",
    "docked_port",
    "at_sea",
    "port_visited",
    "port_visit_count",
    "event_state",
    "cargo_quantity",
    "cargo_load",
    "cargo_free_space",
    "random",
    "constant",
}

ACTION_TYPES = {
    "spawn_fleet",
    "toast",
    "journal",
    "give_gold",
    "set_gold",
    "set_flag",
    "add_flag",
    "remove_flag",
    "adjust_relation",
    "set_mission_state",
    "schedule_event",
    "enable_event",
    "disable_event",
    "add_cargo",
    "remove_cargo",
    "retreat_fleet",
}

COMPARISON_OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "in", "not_in", "contains"}
SHIP_TYPES = set(SHIP_CLASSES)


def validate_condition(condition, source):
    if not isinstance(condition, dict):
        raise ValueError(f"Invalid condition in {source}")
    has_expression = False
    for group in ("all", "any"):
        if group not in condition:
            continue
        has_expression = True
        children = condition[group]
        if not isinstance(children, list):
            raise ValueError(f"Condition '{group}' must be a list in {source}")
        for child in children:
            validate_condition(child, source)
    if "not" in condition:
        has_expression = True
        validate_condition(condition["not"], source)
    if "type" in condition:
        has_expression = True
        kind = str(condition.get("type", "")).strip()
        if kind not in CONDITION_TYPES:
            raise ValueError(f"Unknown condition type '{kind}' in {source}")
        operator = str(condition.get("op", condition.get("operator", "=="))).lower()
        if operator not in COMPARISON_OPERATORS:
            raise ValueError(f"Unknown condition operator '{operator}' in {source}")
        if kind in {"cargo_quantity", "cargo_load", "cargo_free_space"}:
            good_id = str(condition.get("good", condition.get("key", "")))
            if kind == "cargo_quantity" and good_id not in TRADE_GOODS_BY_ID:
                raise ValueError(f"Unknown cargo good '{good_id}' in {source}")
        if kind == "random" and not math.isfinite(float(condition.get("value", 0))):
            raise ValueError(f"Random event threshold must be finite in {source}")
    if not has_expression:
        raise ValueError(f"A condition requires a type or logical group in {source}")


def validate_actions(actions, source):
    if not isinstance(actions, list):
        raise ValueError(f"Actions must be a list in {source}")
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError(f"Invalid action in {source}")
        kind = str(action.get("type", "")).strip()
        if kind not in ACTION_TYPES:
            raise ValueError(f"Unknown action type '{kind}' in {source}")
        if kind == "spawn_fleet":
            ship_types = action.setdefault("ship_types", ["Schooner", "Brigantine", "Brig", "Corvette", "Frigate", "Ship of the Line"])
            if not isinstance(ship_types, list) or not ship_types:
                raise ValueError(f"spawn_fleet requires a non-empty ship_types list in {source}")
            action["ship_types"] = [str(value) for value in ship_types]
            unknown_types = set(action["ship_types"]) - SHIP_TYPES
            if unknown_types:
                raise ValueError(f"spawn_fleet contains unknown ship types {sorted(unknown_types)} in {source}")
            if "ship_names" in action and not isinstance(action["ship_names"], list):
                raise ValueError(f"spawn_fleet ship_names must be a list in {source}")
            numeric_fields = (
                "minimum_ships", "min_ships", "maximum_ships", "max_ships",
                "hard_maximum_ships", "strength_ratio", "spawn_distance",
                "announcement_seconds",
            )
            for field in numeric_fields:
                if field in action and not math.isfinite(float(action[field])):
                    raise ValueError(f"spawn_fleet field '{field}' must be finite in {source}")
        if kind in {"add_cargo", "remove_cargo"}:
            good_id = str(action.get("good", ""))
            if good_id not in TRADE_GOODS_BY_ID:
                raise ValueError(f"Unknown cargo good '{good_id}' in {source}")
        if kind in {"give_gold", "set_gold", "add_flag", "add_cargo", "remove_cargo"}:
            if not math.isfinite(float(action.get("amount", 0))):
                raise ValueError(f"Action '{kind}' requires a finite amount in {source}")
        if kind in {"schedule_event", "enable_event", "disable_event"} and not action.get("event"):
            raise ValueError(f"Action '{kind}' requires an event id in {source}")


def validate_event_references(condition, event_ids, source):
    if not isinstance(condition, dict):
        return
    if condition.get("type") == "event_state":
        target = str(condition.get("event", condition.get("key", "")))
        if target not in event_ids:
            raise ValueError(f"Condition references unknown event '{target}' in {source}")
    for group in ("all", "any"):
        for child in condition.get(group, []):
            validate_event_references(child, event_ids, source)
    if "not" in condition:
        validate_event_references(condition["not"], event_ids, source)


EVENT_VARIABLES = {
    "escorts": "escort_count",
    "fleet": "fleet_ship_count",
    "fleet_power": "fleet_power",
    "gold": "gold",
    "ship_class": "ship_class",
    "time": "world_time",
    "world_time": "world_time",
    "hull": "hull_percent",
    "hull_percent": "hull_percent",
    "jobs": "completed_day_jobs",
    "completed_day_jobs": "completed_day_jobs",
    "relics": "relic_count",
    "relic_count": "relic_count",
    "unique_items": "unique_item_count",
    "unique_item_count": "unique_item_count",
    "region": "region",
    "docked_port": "docked_port",
    "at_sea": "at_sea",
    "cargo": "cargo_load",
    "cargo_load": "cargo_load",
    "cargo_free_space": "cargo_free_space",
    "random": "random",
}

EVENT_FUNCTIONS = {
    "standing": ("faction_standing", "faction"),
    "flag": ("flag", "key"),
    "visited": ("port_visited", "port"),
    "visits": ("port_visit_count", "port"),
    "mission": ("mission_state", "mission"),
    "upgrade": ("ship_upgrade", "key"),
    "cargo": ("cargo_quantity", "good"),
    "event": ("event_state", "event"),
}


class EventExpressionParser:
    token_pattern = re.compile(r'\s*(>=|<=|==|!=|>|<|\(|\)|\band\b|\bor\b|\bnot\b|"(?:\\.|[^"\\])*"|\'[^\']*\'|-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*)', re.IGNORECASE)

    def __init__(self, expression):
        self.expression = expression
        self.tokens = []
        position = 0
        for match in self.token_pattern.finditer(expression):
            if expression[position:match.start()].strip():
                raise ValueError(f"Invalid event expression near '{expression[position:match.start()].strip()}'")
            self.tokens.append(match.group(1))
            position = match.end()
        if expression[position:].strip():
            raise ValueError(f"Invalid event expression near '{expression[position:].strip()}'")
        self.index = 0
        self.random_index = 0

    def peek(self):
        return self.tokens[self.index].lower() if self.index < len(self.tokens) else None

    def take(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def parse(self):
        if not self.tokens:
            raise ValueError("Event expression cannot be empty")
        result = self.parse_or()
        if self.index != len(self.tokens):
            raise ValueError(f"Unexpected token '{self.tokens[self.index]}' in event expression")
        return result

    def parse_or(self):
        children = [self.parse_and()]
        while self.peek() == "or":
            self.take()
            children.append(self.parse_and())
        return children[0] if len(children) == 1 else {"any": children}

    def parse_and(self):
        children = [self.parse_not()]
        while self.peek() == "and":
            self.take()
            children.append(self.parse_not())
        return children[0] if len(children) == 1 else {"all": children}

    def parse_not(self):
        if self.peek() == "not":
            self.take()
            return {"not": self.parse_not()}
        if self.peek() == "(":
            self.take()
            value = self.parse_or()
            if self.peek() != ")":
                raise ValueError("Unclosed parenthesis in event expression")
            self.take()
            return value
        return self.parse_comparison()

    @staticmethod
    def parse_operand(token):
        if token.startswith(('"', "'")):
            return "literal", ast.literal_eval(token)
        lower = token.lower()
        if lower == "true":
            return "literal", True
        if lower == "false":
            return "literal", False
        try:
            number = float(token)
            return "literal", int(number) if number.is_integer() else number
        except ValueError:
            return "symbol", token

    def parse_reference(self):
        token = self.take()
        kind, value = self.parse_operand(token)
        if kind != "symbol" or self.peek() != "(":
            return kind, value
        function = value.lower()
        if function not in EVENT_FUNCTIONS:
            raise ValueError(f"Unknown event function '{value}'")
        self.take()
        if self.index >= len(self.tokens):
            raise ValueError(f"Event function '{value}' requires an argument")
        argument_kind, argument = self.parse_operand(self.take())
        if argument_kind == "symbol" and argument.lower() in EVENT_VARIABLES:
            raise ValueError(f"Event function '{value}' requires a literal argument")
        if self.peek() != ")":
            raise ValueError(f"Event function '{value}' accepts one argument")
        self.take()
        event_type, argument_name = EVENT_FUNCTIONS[function]
        return "reference", (event_type, argument_name, argument)

    def parse_comparison(self):
        left_kind, left_value = self.parse_reference()
        operator = self.peek()
        if operator in {">", ">=", "<", "<=", "==", "!="}:
            self.take()
            if self.index >= len(self.tokens):
                raise ValueError("An event comparison requires a value")
            right_kind, right_value = self.parse_operand(self.take())
            if left_kind == "reference":
                event_type, argument_name, argument = left_value
                condition = {"type": event_type, argument_name: argument, "op": operator, "value": right_value}
            elif left_kind == "symbol" and left_value.lower() in EVENT_VARIABLES:
                if right_kind == "symbol" and right_value.lower() in EVENT_VARIABLES:
                    raise ValueError("Comparisons between two event values are not supported")
                condition = {"type": EVENT_VARIABLES[left_value.lower()], "op": operator, "value": right_value}
            else:
                raise ValueError(f"Unknown event value '{left_value}'")
            if condition["type"] == "random":
                condition["roll_id"] = f"random_{self.random_index}"
                self.random_index += 1
            return condition
        if left_kind == "reference":
            event_type, argument_name, argument = left_value
            return {"type": event_type, argument_name: argument, "op": "==", "value": True}
        if left_kind == "symbol" and left_value.lower() in EVENT_VARIABLES:
            condition = {"type": EVENT_VARIABLES[left_value.lower()], "op": "==", "value": True}
            if condition["type"] == "random":
                condition["roll_id"] = f"random_{self.random_index}"
                self.random_index += 1
            return condition
        return {"type": "constant", "value": bool(left_value)}


def parse_event_expression(expression):
    return EventExpressionParser(expression).parse()


def load_mission_events(directory):
    events = []
    for path in sorted(Path(directory).glob("*.mission")):
        mission = MissionParser(path).parse()
        if not mission.event_expression:
            continue
        data = mission.event_config
        trigger = parse_event_expression(mission.event_expression)
        validate_condition(trigger, path.name)
        cancel_expression = data.get("cancel_if_expression")
        cancel_if = parse_event_expression(cancel_expression) if cancel_expression else None
        if cancel_if is not None:
            validate_condition(cancel_if, path.name)
        spawn_config = data.get("spawn_fleet")
        actions = list(data.get("actions", []))
        if spawn_config:
            fleet_action = dict(spawn_config)
            fleet_action["type"] = "spawn_fleet"
            fleet_action["ship_types"] = data.get("ship_types") or ["Schooner", "Brigantine", "Brig", "Corvette", "Frigate", "Ship of the Line"]
            fleet_action["ship_names"] = data.get("ship_names", [])
            for key in ("announcement", "announcement_seconds", "journal_entry"):
                if key in data:
                    fleet_action[key] = data[key]
            actions.append(fleet_action)
        validate_actions(actions, path.name)
        on_complete = list(data.get("on_complete", []))
        on_repelled = list(data.get("on_repelled", []))
        complete_flag = str(data.get("complete_flag", "")).strip()
        if complete_flag:
            on_complete.append({"type": "set_flag", "key": complete_flag, "value": True})
            on_repelled.append({"type": "set_flag", "key": complete_flag, "value": True})
        if mission.reward:
            on_complete.append({"type": "give_gold", "amount": mission.reward})
        if data.get("complete_text"):
            on_complete.append({"type": "journal", "text": data["complete_text"]})
        if data.get("repelled_text"):
            on_repelled.append({"type": "journal", "text": data["repelled_text"]})
        validate_actions(on_complete, path.name)
        validate_actions(on_repelled, path.name)
        delay = data.get("delay", {"minimum": 0.0, "maximum": 0.0})
        minimum = max(0.0, float(delay.get("minimum", 0.0)))
        maximum = max(minimum, float(delay.get("maximum", minimum)))
        if not math.isfinite(minimum) or not math.isfinite(maximum):
            raise ValueError(f"Event delay must be finite in {path.name}")
        repeatable = bool(data.get("repeatable", False))
        event = {
            "id": mission.mission_id,
            "name": mission.name or mission.title,
            "trigger": trigger,
            "delay": {"minimum": minimum, "maximum": maximum},
            "repeatable": repeatable,
            "cooldown_seconds": max(0.0, float(data.get("cooldown_seconds", 0.0))),
            "max_triggers": max(0, int(data.get("max_triggers", 0 if repeatable else 1))),
            "pause_while_docked": bool(data.get("pause_while_docked", True)),
            "enabled": True,
            "actions": actions,
            "on_complete": on_complete,
            "on_repelled": on_repelled,
            "cancel_if": cancel_if,
        }
        events.append(event)
    event_ids = {event["id"] for event in events}
    for event in events:
        validate_actions(event["actions"], event["id"])
        validate_actions(event["on_complete"], event["id"])
        validate_actions(event["on_repelled"], event["id"])
        validate_event_references(event["trigger"], event_ids, event["id"])
        if event["cancel_if"] is not None:
            validate_event_references(event["cancel_if"], event_ids, event["id"])
        for action in event["actions"] + event["on_complete"] + event["on_repelled"]:
            if action["type"] in {"schedule_event", "enable_event", "disable_event", "retreat_fleet"}:
                target = str(action.get("event", event["id"]))
                if target not in event_ids:
                    raise ValueError(f"Action references unknown event '{target}' in {event['id']}")
    return events
