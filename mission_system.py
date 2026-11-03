import re
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
    speaker: str
    section_speakers: dict
    sections: dict
    path: Path


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
        speaker = "Harbourmaster"
        section_speakers = {}
        sections = {}
        self.index = 1
        while self.index < len(self.lines):
            indent, text = self.lines[self.index]
            if indent != 4:
                self.index += 1
                continue
            self.index += 1
            if text.startswith("name "):
                name = self.quoted(text)
            elif text.startswith("description "):
                description = self.quoted(text)
            elif text.startswith("source "):
                source = self.quoted(text)
            elif text.startswith("destination "):
                destination = self.quoted(text)
            elif text.startswith("reward "):
                reward = int(text.split(None, 1)[1])
            elif text.startswith("speaker "):
                parts = text.split(None, 2)
                if len(parts) == 3 and parts[1] in {"offer", "accept", "visit", "complete", "fail"}:
                    section_speakers[parts[1]] = self.quoted(text)
                else:
                    speaker = self.quoted(text)
            elif text.startswith("objective "):
                parts = text.split()
                objective_type = parts[1].lower()
                objective_count = int(parts[2]) if len(parts) > 2 else 0
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
            speaker=speaker,
            section_speakers=section_speakers,
            sections=sections,
            path=self.path,
        )

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
