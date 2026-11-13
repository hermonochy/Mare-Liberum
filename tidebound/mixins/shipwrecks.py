from ..common import *


class ShipwreckMixin:
    # Wreck locations use the chart's design coordinate grid and are scaled at creation.
    # Every site is checked against land, reefs, ports and other wrecks.

    def create_shipwreck_sites(self):
        sites = []
        for row in SHIPWRECK_DATA:
            (wreck_id, name, x, y, heading, vessel_name, age_description, description,
             hazard_description, risk_level, surface_gold, deep_gold, rare_discovery, rare_chance) = row
            wx, wy = x * WORLD_SCALE, y * WORLD_SCALE
            if any(point_in_polygon((wx, wy), polygon) for polygon in self.land):
                raise ValueError(f"Shipwreck {name} was placed on land.")
            nearest_coast = min(nearest_polygon_edge(wx, wy, polygon)[1] for polygon in self.land)
            #if not (350.0 * WORLD_SCALE <= nearest_coast <= 200.0 * WORLD_SCALE):
            #    raise ValueError(f"Shipwreck {name} is not at a sensible distance from the coast.")
            if any(point_in_polygon((wx, wy), site.polygon)
                   or nearest_polygon_edge(wx, wy, site.polygon)[1] < 250.0 * WORLD_SCALE
                   for site in self.treasure_sites):
                raise ValueError(f"Shipwreck {name} is too close to a treasure cay.")
            if not self.reef_clear_at(wx, wy, 250.0 * WORLD_SCALE):
                raise ValueError(f"Shipwreck {name} overlaps a reef warning zone.")
            if any(math.hypot(wx - port.x, wy - port.y) < 450.0 * WORLD_SCALE for port in self.ports):
                raise ValueError(f"Shipwreck {name} is too close to a harbour entrance.")
            if any(math.hypot(wx - site.x, wy - site.y) < 350.0 * WORLD_SCALE for site in sites):
                raise ValueError(f"Shipwreck {name} is too close to another wreck.")
            sites.append(ShipwreckSite(
                wreck_id, name, wx, wy, heading, vessel_name, age_description, description,
                hazard_description, risk_level, surface_gold, deep_gold, rare_discovery, rare_chance,
            ))
        return sites

    def nearest_shipwreck(self, maximum_distance=190.0):
        candidates = [
            (math.hypot(self.ship_x - site.x, self.ship_y - site.y), site)
            for site in getattr(self, "shipwrecks", []) if site.discovered and not site.fully_salvaged
        ]
        if not candidates:
            return None
        distance, site = min(candidates, key=lambda item: item[0])
        return site if distance <= maximum_distance else None

    def update_shipwreck_discovery(self):
        if self.docked_port:
            return
        for site in getattr(self, "shipwrecks", []):
            if site.discovered:
                continue
            distance = math.hypot(self.ship_x - site.x, self.ship_y - site.y)
            if distance <= 1150.0:
                site.discovered = True
                self.add_journal(f"The crew spotted {site.name}, {site.age_description[0].lower() + site.age_description[1:]}.")
                self.toast_message(f"WRECK SIGHTED: {site.name}. Close carefully and press R to investigate.", 5.0)

    def interact_shipwreck(self):
        if self.docked_port or self.conversation or self.journal_open or self.treasure_chart_open:
            return False
        site = self.nearest_shipwreck(205.0)
        if site is None:
            return False
        if site.fully_salvaged:
            self.toast_message(f"The wreck of {site.name} has been thoroughly salvaged.", 3.0)
            return True
        nodes = [TextNode(
            f"You bring the ship alongside the broken hull of {site.name}. She was a {site.vessel_name}. Old charts describe her as {site.age_description[0].lower() + site.age_description[1:]}. {site.description} {site.hazard_description}"
        )]
        options = []
        if not site.surface_salvaged:
            options.append(OptionNode(
                f"Recover floating cargo and useful fittings (+{site.surface_gold} gold, low risk).",
                [CommandNode("wreck_surface", site.wreck_id)],
            ))
        if not site.deep_attempted:
            risk_label = "dangerous" if site.risk_level >= 3 else "risky" if site.risk_level == 2 else "cautious but uncertain"
            options.append(OptionNode(
                f"Send a salvage party into the flooded hull ({risk_label}; up to {site.deep_gold} gold and a rare find).",
                [CommandNode("wreck_deep", site.wreck_id)],
            ))
        options.append(OptionNode("Leave the wreck alone.", [CommandNode("close", "")]))
        nodes.append(ChoiceNode(options))
        self.start_custom_conversation(f"Salvage: {site.name}", nodes)
        return True

    def salvage_wreck_surface(self, wreck_id):
        site = next((item for item in self.shipwrecks if item.wreck_id == wreck_id), None)
        if site is None or site.surface_salvaged:
            return
        site.surface_salvaged = True
        self.gold += site.surface_gold
        self.add_journal(f"Salvaged floating cargo from {site.name}: {site.surface_gold} gold in recovered goods and fittings.")
        self.toast_message(f"Salvage recovered from {site.name}: +{site.surface_gold} gold.", 4.0)

    def salvage_wreck_deep(self, wreck_id):
        site = next((item for item in self.shipwrecks if item.wreck_id == wreck_id), None)
        if site is None or site.deep_attempted:
            return
        site.deep_attempted = True
        risk_chance = {1: 0.14, 2: 0.29, 3: 0.46}.get(site.risk_level, 0.25)
        damaged = self.rng.random() < risk_chance
        if damaged:
            damage = {1: 7, 2: 13, 3: 21}.get(site.risk_level, 10)
            self.player_hull = max(0, self.player_hull - damage)
            self.player_hit_flash = max(getattr(self, "player_hit_flash", 0.0), 0.22)
            self.gold += int(site.deep_gold * 0.55)
            self.audio.play("cannon_impact", volume=0.12)
            self.add_journal(f"The salvage attempt at {site.name} went wrong. A hazard damaged the flagship for {damage} hull points; the crew recovered only part of the cargo.")
            self.toast_message(f"DANGER AT {site.name.upper()}! Hull -{damage}; partial salvage recovered.", 4.5)
            if self.player_hull <= 0:
                self.player_sunk()
                return
        else:
            self.gold += site.deep_gold
            self.add_journal(f"A successful dive at {site.name} recovered valuable cargo worth {site.deep_gold} gold.")
            self.toast_message(f"Deep salvage from {site.name}: +{site.deep_gold} gold.", 4.0)

        rare_chance = site.rare_chance * (0.55 if damaged else 1.0)
        if self.rng.random() < rare_chance and site.rare_discovery not in self.unique_items:
            site.rare_found = True
            self.unique_items.append(site.rare_discovery)
            self.add_journal(f"RARE DISCOVERY: Recovered {site.rare_discovery} from {site.name}.")
            self.toast_message(f"RARE DISCOVERY! {site.rare_discovery}", 5.5)

