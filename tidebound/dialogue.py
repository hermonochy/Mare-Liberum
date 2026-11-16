import pygame
import shlex

from .mission_system import BranchNode, ChoiceNode, CommandNode, GotoNode, LabelNode, TextNode


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
            mission = self.mission
            accepted = False
            if mission is not None and not getattr(mission, "ambient", False):
                accepted = self.game.accept_mission(mission, start_accept_dialogue=False)
            self.finish()
            if accepted and mission.sections.get("accept"):
                self.game.start_conversation(mission, "accept")
            return True
        if node.command in {"close", "launch", "decline", "defer", "depart", "flee"}:
            mission = self.mission
            if node.command == "decline":
                self.game.toast_message("The offer remains open. Fair winds, captain.", 3.2)
            if node.command == "defer" and mission is not None:
                self.game.set_world_flag(f"mission_deferred:{mission.mission_id}", True)
            self.finish()
            if mission is not None and node.command in {"decline", "defer"} and mission.sections.get(node.command):
                self.game.start_conversation(mission, node.command)
            return True
        if node.command == "abort_mission":
            mission = self.game.abort_active_mission(start_abort_dialogue=False)
            self.finish()
            if mission is not None and mission.sections.get("abort"):
                self.game.start_conversation(mission, "abort")
            return True
        if node.command == "log":
            self.game.add_journal(node.value)
            return False
        if node.command in {"set_flag", "set"}:
            parts = shlex.split(node.value)
            if parts:
                raw = parts[1].lower() if len(parts) > 1 else "true"
                parsed = True if raw == "true" else False if raw == "false" else raw
                try:
                    numeric = float(raw)
                    parsed = int(numeric) if numeric.is_integer() else numeric
                except ValueError:
                    pass
                self.game.set_world_flag(parts[0], parsed)
            return False
        if node.command in {"clear_flag", "clear"}:
            parts = shlex.split(node.value)
            if parts:
                self.game.world_flags.pop(parts[0], None)
            return False
        if node.command == "increment_flag":
            parts = shlex.split(node.value)
            if len(parts) >= 2:
                key = parts[0]
                try:
                    amount = int(parts[1])
                except ValueError:
                    amount = 1
                current = self.game.world_flags.get(key, 0)
                try:
                    current = int(current)
                except (TypeError, ValueError):
                    current = 0
                self.game.set_world_flag(key, current + amount)
            return False
        if node.command == "give_gold":
            amount = int(float(node.value.strip() or 0))
            self.game.gold = max(0, self.game.gold + amount)
            return False
        if node.command == "adjust_relation":
            parts = shlex.split(node.value)
            if len(parts) >= 2:
                self.game.adjust_faction_relation(parts[0], int(float(parts[1])), "A conversation changed your standing.")
            return False
        if node.command == "schedule_event":
            parts = shlex.split(node.value)
            if parts:
                delay = float(parts[1]) if len(parts) > 1 else None
                self.game.schedule_mission_event(parts[0], delay)
            return False
        if node.command == "reveal_island":
            parts = shlex.split(node.value)
            if parts:
                self.game.reveal_event_island(parts[0])
            return False
        if node.command == "reveal_wreck":
            parts = shlex.split(node.value)
            target = parts[0] if parts else ""
            wreck = next((item for item in self.game.shipwrecks if item.wreck_id == target or item.name == target), None)
            if wreck:
                wreck.discovered = True
            return False
        if node.command == "set_wind":
            parts = node.value.split()
            if len(parts) >= 2:
                self.game.mission_wind_override = {
                    "angle": float(parts[0]) % 360.0,
                    "strength": max(0.0, min(1.0, float(parts[1]))),
                    "remaining": float(parts[2]) if len(parts) > 2 else 240.0,
                }
            return False
        if node.command == "set_sea_state":
            parts = shlex.split(node.value)
            state_name = parts[0] if parts else ""
            strengths = {"calm": 0.16, "swell": 0.38, "rough": 0.68, "storm": 0.92}
            if state_name in strengths:
                self.game.mission_wind_override = {
                    "angle": self.game.wind_angle,
                    "strength": strengths[state_name],
                    "remaining": float(parts[1]) if len(parts) > 1 else 240.0,
                }
                self.game.set_world_flag("sea_state", state_name)
            return False
        if node.command == "offers":
            self.finish()
            self.game.open_mission_offer()
            return True
        if node.command == "mission_offer":
            self.finish()
            self.game.show_mission_offer_by_id(node.value)
            return True
        if node.command == "intro_mission":
            self.finish()
            self.game.open_intro_mission_offer()
            return True
        if node.command == "day_jobs":
            self.finish()
            self.game.open_day_job_board()
            return True
        if node.command == "accept_day_job":
            self.game.accept_day_job()
            self.finish()
            return True
        if node.command == "decline_day_job":
            self.game.toast_message("You leave the day-work offer on the board.", 3.2)
            self.finish()
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
        if node.command == "wreck_surface":
            self.game.salvage_wreck_surface(node.value)
            self.finish()
            return True
        if node.command == "wreck_deep":
            self.game.salvage_wreck_deep(node.value)
            self.finish()
            return True
        if node.command == "curiosities":
            self.finish()
            self.game.open_curiosities()
            return True
        if node.command == "purchase_unique":
            self.game.purchase_unique_offer(node.value)
            self.finish()
            return True
        if node.command == "inspect_scam":
            self.game.inspect_scam_offer(node.value)
            self.finish()
            return True
        if node.command == "learn_secret":
            self.game.learn_local_secret(node.value)
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
            if isinstance(node, BranchNode):
                try:
                    if node.expression and self.game.evaluate_mission_script_expression(node.expression):
                        self.jump(node.label)
                        return
                except (ValueError, TypeError) as error:
                    self.game.add_journal(f"A conversation condition could not be evaluated: {error}")
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
