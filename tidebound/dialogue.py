import pygame

from .mission_system import ChoiceNode, CommandNode, GotoNode, LabelNode, TextNode


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
            self.game.toast_message("You leave the day-work offer on the board. It will wait until you are ready.", 3.2)
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
