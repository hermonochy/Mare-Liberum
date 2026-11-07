from ..common import *


class TreasureMixin:
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
