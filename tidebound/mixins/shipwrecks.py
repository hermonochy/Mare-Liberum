from ..common import *


class ShipwreckMixin:
    # Coordinates are authored on the original chart and scaled to the V26+ world.
    # Every site was checked against all land, reef polygons, ports and the other wrecks.
    SHIPWRECK_DATA = [
        ("black_gull", "The Black Gull", 3604.8, 1631.9, 18, "merchant brig", "A merchant brig lost in a winter squall",
         "Her foremast is gone and a broken cargo boom lies across the deck. Several sealed crates still float in the lee of the hull.",
         "A split cargo of lamp oil has soaked the lower deck; a careless spark could ignite it.", 2, 95, 225, "The Black Gull's silver trade seal", 0.25),
        ("widows_promise", "The Widow's Promise", 1158.8, 5834.1, 214, "coastal schooner", "A coastal schooner abandoned decades ago",
         "The schooner's stern is almost intact. Crockery, copper pots and a captain's sea chest are visible beneath the waterline.",
         "The hull is weakened and shifts whenever the swell catches it.", 2, 70, 175, "A miniature ivory ship carved by the captain", 0.18),
        ("saint_elmos_prize", "Saint Elmo's Prize", 846.9, 9963.3, 306, "Spanish treasure barque", "A Spanish barque that vanished with a colonial payroll",
         "A gilded figurehead still clings to the bow. Rumour says the paymaster hid his strongbox below the officers' cabin.",
         "A powder locker lies beneath the stern. The smallest disturbance may set off a violent blast.", 3, 180, 360, "A gold-and-enamel astrolabe", 0.36),
        ("cormorant", "The Cormorant", 10297.7, 4801.5, 128, "merchant galleon", "A deep-draught galleon lost on a calm night",
         "The galleon's cargo decks remain largely sealed. Barrels and trade chests can be seen through a torn hatch.",
         "The wreck sits in a strong cross-current that can drag a small boat against jagged timbers.", 2, 125, 285, "A merchant prince's engraved pocket watch", 0.24),
        ("hms_tyrant", "HMS Tyrant", 12704.9, 5796.5, 42, "Royal Navy frigate", "A Royal Navy frigate lost during an undeclared engagement",
         "The ship's brass fittings and a sealed officer's dispatch case may still be recoverable.",
         "A shattered gun deck is littered with unstable cannon and splintered beams.", 3, 145, 310, "An Admiralty cipher wheel", 0.30),
        ("red_wake", "The Red Wake", 17288.8, 5086.0, 252, "pirate brig", "A feared pirate brig whose crew vanished overnight",
         "The blackened hull carries old boarding marks. A few lockers appear untouched, despite the wreck's reputation.",
         "The surrounding water is thick with broken spars and dangerous undertow.", 2, 115, 260, "The captain's black-ivory pistol crest", 0.27),
        ("la_belladonna", "La Belladonna", 9943.2, 6387.7, 76, "French merchantman", "A French merchantman carrying rare dyes and fine instruments",
         "The stern cabin has collapsed, but the hold contains sealed dye jars and navigational equipment.",
         "The wreck is infested with sharp coral growth and a dense tangle of rigging.", 1, 100, 205, "A rosewood octant with silver inlay", 0.22),
        ("old_hope", "The Old Hope", 586.5, 5500.1, 330, "fishing ketch", "A fishing ketch caught in a sudden squall",
         "This small vessel was no warship, but its crew were known to carry a private savings box for the winter.",
         "The water is shallow and the broken hull is close to the rocks; approach slowly.", 1, 45, 95, "A sailor's carved bone playing set", 0.12),
        ("santa_isidora", "Santa Isidora", 8286.4, 3074.5, 166, "Spanish treasure galleon", "A heavily laden galleon lost during a storm",
         "A line of silver ingots is visible through a rent in the hull. The captain's cabin is buried beneath the collapsed quarterdeck.",
         "The wreck's powder room is partly flooded but not completely safe.", 3, 210, 420, "A silver crown medallion from the lost expedition", 0.38),
        ("mercy_of_lune", "Mercy of Lune", 1024.5, 10404.9, 112, "hospital ship", "A small hospital ship wrecked while carrying supplies between islands",
         "Medical chests and trade goods are still lashed below deck. A sealed surgeon's journal may have survived.",
         "A foul current runs through the wreck, and loose timbers can trap a diver.", 2, 80, 190, "The surgeon's annotated field journal", 0.23),
        ("iron_duke", "The Iron Duke", 4274.6, 3063.6, 290, "armed merchant brig", "An armed merchant brig that fought off raiders before sinking",
         "Some of the gun deck remains intact. The cargo includes shot, tools and a locked pay chest.",
         "A loaded swivel gun is still wedged in the upper deck and may shift without warning.", 2, 135, 275, "A brass maker's plate from a famous shipyard", 0.21),
        ("serpent_dor", "Le Serpent d'Or", 8944.3, 2431.0, 12, "French privateer", "A French privateer whose last prize was never recorded",
         "Her prize room may contain captured jewellery and papers identifying a secret buyer.",
         "The wreck lies in a fast current and its flooded passageways are difficult to navigate.", 2, 150, 295, "A signet ring bearing the mark of a hidden trading house", 0.28),
        ("morning_star", "The Morning Star", 15955.4, 596.2, 196, "mail packet", "A mail packet lost while carrying dispatches between governors",
         "The letter lockers are sealed. The dispatches may be worth more to a scholar than to a fence.",
         "The bow is pinned beneath a heavy spar; removing it could bring the deck down.", 1, 65, 145, "A coded packet addressed to the first cartographer", 0.20),
        ("black_mermaid", "The Black Mermaid", 4009.3, 5394.9, 48, "pirate schooner", "A pirate schooner sunk after a mutiny",
         "The crew's scattered belongings remain aboard. One locked chest bears the initials of a notorious captain.",
         "The wreck is surrounded by tangled chain and jagged boarding hooks.", 2, 105, 250, "A captain's journal naming a forgotten anchorage", 0.31),
        ("san_jorge", "San Jorge", 13535.5, 5126.8, 226, "Spanish naval transport", "A naval transport lost while carrying fortification supplies",
         "The hold contains tools, iron fittings and a sealed dispatch box from the colonial command.",
         "An old magazine has been breached; a sudden impact could scatter burning debris.", 3, 130, 285, "A royal engineer's survey of an uncharted channel", 0.33),
        ("blue_lantern", "The Blue Lantern", 9254.5, 563.4, 84, "merchant schooner", "A merchant schooner whose lantern was seen long after the ship disappeared",
         "The wreck's cabin is remarkably well preserved. Its cargo was modest, but the navigation table may be valuable.",
         "The hull is lodged at an awkward angle and the upper deck can collapse.", 1, 85, 180, "A rare blue-glass tide compass", 0.26),
        ("la_reina", "La Reina de Sal", 14426.1, 292.7, 310, "Spanish treasure ship", "A treasure ship said to have carried the governor's private collection",
         "A heavy iron coffer is visible near the stern. The wreck has resisted generations of salvagers.",
         "The coffer is trapped beneath the gun deck beside a volatile powder store.", 3, 220, 460, "A pearl-inlaid royal seal", 0.40),
        ("northwind", "The Northwind", 11941.8, 10598.2, 154, "whaling brig", "A whaling brig that never returned from the outer waters",
         "Barrels of whale oil and a carpenter's chest remain aboard. The captain kept detailed weather notes.",
         "The wreck is deep and the current pulls strongly beneath the broken keel.", 2, 100, 220, "A whaler's storm journal with unusual current readings", 0.24),
    ]

    def create_shipwreck_sites(self):
        sites = []
        for row in self.SHIPWRECK_DATA:
            (wreck_id, name, x, y, heading, vessel_name, age_description, description,
             hazard_description, risk_level, surface_gold, deep_gold, rare_discovery, rare_chance) = row
            wx, wy = x * WORLD_SCALE, y * WORLD_SCALE
            if any(point_in_polygon((wx, wy), polygon) for polygon in self.land):
                raise ValueError(f"Shipwreck {name} was placed on land.")
            nearest_coast = min(nearest_polygon_edge(wx, wy, polygon)[1] for polygon in self.land)
            if not (350.0 * WORLD_SCALE <= nearest_coast <= 1200.0 * WORLD_SCALE):
                raise ValueError(f"Shipwreck {name} is not at a sensible distance from the coast.")
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

