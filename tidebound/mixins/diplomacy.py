from ..common import *


class DiplomacyMixin:
    """Player standing with Caribbean powers, individual commanders and harbours."""


    def initialise_diplomacy(self):
        # Small starting biases give the captain a past without locking any doors.
        self.faction_relations = {
            "British Crown": 5,
            "Spanish Crown": 0,
            "French Crown": 0,
            "Merchant League": 8,
            "Pirate Brotherhood": -5,
            "Independent": 12,
        }
        self.port_standings = {}
        self.commander_relations = {}
        self.diplomacy_open = False
        self.diplomacy_selection = 0
        self.diplomacy_scroll = 0
        self.refresh_port_standings()

    @staticmethod
    def clamp_relation(value):
        return max(-100, min(100, int(value)))

    @staticmethod
    def relation_label(value):
        value = int(value)
        if value <= -30:
            return "HOSTILE"
        if value >= 30:
            return "FRIENDLY"
        return "NEUTRAL"

    def faction_standing(self, faction):
        return int(getattr(self, "faction_relations", {}).get(faction, 0))

    def faction_attitude(self, faction):
        return self.relation_label(self.faction_standing(faction))

    def port_attitude(self, port):
        return getattr(self, "port_standings", {}).get(port.name, self.faction_attitude(port.faction))

    def refresh_port_standings(self):
        relations = getattr(self, "faction_relations", {})
        self.port_standings = {
            port.name: self.relation_label(relations.get(port.faction, 0))
            for port in getattr(self, "ports", [])
        }

    def faction_for_npc(self, npc):
        if isinstance(npc, PirateShip):
            return "Pirate Brotherhood"
        faction = getattr(npc, "faction", "")
        if faction in FACTION_NAMES:
            return faction
        role = getattr(npc, "role", "")
        return {
            "naval patrol": "British Crown",
            "merchant": "Merchant League",
            "fishing": "Independent",
            "mail packet": "Independent",
            "whaler": "Merchant League",
        }.get(role, "Independent")

    def npc_relation_score(self, npc):
        faction_score = self.faction_standing(self.faction_for_npc(npc))
        commander = getattr(npc, "commander_name", "")
        personal_score = int(getattr(self, "commander_relations", {}).get(commander, 0)) if commander else 0
        score = min(faction_score, personal_score)
        if getattr(npc, "player_provoked", False):
            score = min(score, -30)
        return score

    def npc_relation_label(self, npc):
        return self.relation_label(self.npc_relation_score(npc))

    def refresh_npc_attitudes(self):
        """Recalculate fleet attitudes after diplomacy changes or a save is loaded."""
        for ship in getattr(self, "traffic_ships", []):
            if not getattr(ship, "faction", ""):
                ship.faction = self.faction_for_npc(ship)
            attitude = self.npc_relation_label(ship)
            ship.player_attitude = attitude.lower()
            ship.hostile_to_player = bool(getattr(ship, "player_provoked", False) or attitude == "HOSTILE")
            if ship.hostile_to_player and ship.hull > 0 and not ship.retreating:
                ship.combat_target_name = "__player__"
            elif ship.combat_target_name == "__player__":
                ship.combat_target_name = ""
        for pirate in getattr(self, "pirates", []):
            pirate.player_attitude = self.npc_relation_label(pirate).lower()

    def adjust_faction_relation(self, faction, amount, reason, announce=True):
        if faction not in FACTION_NAMES or not amount:
            return self.faction_standing(faction)
        old = self.faction_standing(faction)
        new = self.clamp_relation(old + amount)
        if new == old:
            return new
        self.faction_relations[faction] = new
        self.refresh_port_standings()
        self.refresh_npc_attitudes()
        direction = "improves" if new > old else "suffers"
        if hasattr(self, "add_journal"):
            self.add_journal(f"Your standing with the {faction} {direction} ({new:+d}). {reason}")
        if announce and hasattr(self, "toast_message"):
            self.toast_message(f"{faction}: {self.relation_label(new)} ({new:+d})", 3.4)
        return new

    def adjust_commander_relation(self, commander, amount, reason=""):
        if not commander or not amount:
            return int(getattr(self, "commander_relations", {}).get(commander, 0))
        relations = getattr(self, "commander_relations", None)
        if relations is None:
            self.commander_relations = {}
            relations = self.commander_relations
        old = int(relations.get(commander, 0))
        new = self.clamp_relation(old + amount)
        relations[commander] = new
        if reason and new != old and hasattr(self, "add_journal"):
            self.add_journal(f"{commander}'s personal opinion of you shifts ({new:+d}): {reason}")
        self.refresh_npc_attitudes()
        return new

    def record_player_attack_on_npc(self, ship, source="your guns"):
        """One incident per ship hit prevents cannon volleys from applying endless penalties."""
        if not getattr(ship, "player_incident_recorded", False):
            faction = self.faction_for_npc(ship)
            self.adjust_faction_relation(faction, -18, f"Your forces fired upon {ship.name}.")
            commander = getattr(ship, "commander_name", "")
            if commander:
                self.adjust_commander_relation(commander, -18, f"{source} struck a ship under their command.")
            ship.player_incident_recorded = True
        group = [ship]
        fleet_id = getattr(ship, "fleet_id", "")
        if fleet_id:
            group = [member for member in getattr(self, "traffic_ships", [])
                     if member.fleet_id == fleet_id and member.hull > 0]
        for member in group:
            member.player_provoked = True
            member.hostile_to_player = True
            member.player_attitude = "hostile"
            member.combat_target_name = "__player__"
            member.under_attack = True
        self.refresh_port_standings()

    def record_player_attack_on_pirate(self, pirate, source="your guns"):
        if getattr(pirate, "player_incident_recorded", False):
            return
        self.adjust_faction_relation("Pirate Brotherhood", -10,
            f"Your forces fired on {pirate.name}.")
        commander = getattr(pirate, "commander_name", "")
        if commander:
            self.adjust_commander_relation(commander, -15,
                f"{source} struck a vessel in their pirate band.")
        pirate.player_incident_recorded = True
        pirate.player_provoked = True
        pirate.player_attitude = "hostile"
        self.add_journal(f"Your attack on {pirate.name} has been reported among the Pirate Brotherhood.")

    def record_player_sunk_npc(self, ship):
        faction = self.faction_for_npc(ship)
        self.adjust_faction_relation(faction, -22, f"You sank {ship.name}.")
        commander = getattr(ship, "commander_name", "")
        if commander:
            self.adjust_commander_relation(commander, -12, f"You sank one of their vessels.")

    def record_player_sunk_pirate(self, pirate):
        self.adjust_faction_relation("Pirate Brotherhood", -6, f"You destroyed the pirate vessel {pirate.name}.")
        for faction, gain in (
            ("British Crown", 2), ("Spanish Crown", 2), ("French Crown", 2),
            ("Merchant League", 3), ("Independent", 1),
        ):
            self.adjust_faction_relation(faction, gain, f"Your actions helped reduce pirate attacks.", announce=False)
        commander = getattr(pirate, "commander_name", "")
        if commander:
            self.adjust_commander_relation(commander, -10, "You sank a ship in their pirate band.")
        for npc in getattr(self, "traffic_ships", []):
            if npc.hull > 0 and npc.commander_name and math.hypot(npc.x - pirate.x, npc.y - pirate.y) <= 1500:
                if self.faction_for_npc(npc) in {"British Crown", "Spanish Crown", "French Crown", "Merchant League", "Independent"}:
                    self.adjust_commander_relation(npc.commander_name, 2, "You helped clear nearby pirate sails.")
        self.refresh_port_standings()

    def reward_mission_diplomacy(self, mission):
        seen = set()
        for port_name, gain in ((mission.source, 3), (mission.destination, 2)):
            port = self.ports_by_name.get(port_name)
            if port and port.faction not in seen:
                seen.add(port.faction)
                self.adjust_faction_relation(port.faction, gain,
                    f"You fulfilled an undertaking connected with {port_name}.", announce=False)
        if seen:
            self.toast_message("Your conduct has been noted by the local powers.", 3.0)

    def reward_day_job_diplomacy(self, port):
        self.adjust_faction_relation(port.faction, 2,
            f"You completed work for people at {port.name}.", announce=False)

    def nearest_port_for_parley(self, radius=520.0, faction=None):
        candidates = [(math.hypot(port.x - self.ship_x, port.y - self.ship_y), port)
                      for port in self.ports
                      if self.port_attitude(port) == "HOSTILE" and (faction is None or port.faction == faction)]
        candidates = [(distance, port) for distance, port in candidates if distance <= radius]
        return min(candidates, key=lambda item: item[0])[1] if candidates else None

    def request_safe_conduct(self, faction=None):
        port = self.nearest_port_for_parley(faction=faction)
        if port is None:
            self.toast_message("No hostile harbour is close enough to receive your parley.", 3.2)
            return False
        faction = port.faction
        standing = self.faction_standing(faction)
        if standing > -30:
            self.toast_message(f"The {faction} are not hostile enough to require safe conduct.", 3.2)
            return False
        required_gain = -20 - standing
        cost = 100 + required_gain * 2
        if self.gold < cost:
            self.toast_message(f"The harbour demands {cost} gold in reparations; you have only {self.gold}.", 4.0)
            return False
        self.gold -= cost
        self.adjust_faction_relation(faction, required_gain, "You paid reparations and requested safe conduct.")
        # A costly parley can cool personal grudges among the commanders whose
        # pennants belong to this faction; it does not erase a captain's history.
        for npc in getattr(self, "traffic_ships", []) + getattr(self, "pirates", []):
            if self.faction_for_npc(npc) == faction and getattr(npc, "commander_name", ""):
                current = int(self.commander_relations.get(npc.commander_name, 0))
                if current < -20:
                    self.commander_relations[npc.commander_name] = -20
        self.refresh_npc_attitudes()
        self.add_journal(f"Paid {cost} gold for safe conduct at {port.name}. The harbour is neutral to you again.")
        self.toast_message(f"Safe conduct granted at {port.name}. The harbour will receive you as neutral.", 4.8)
        return True

    def offer_diplomatic_gift(self, faction=None):
        if not self.docked_port:
            self.toast_message("Diplomatic gifts must be presented from a harbour office.", 3.0)
            return False
        port = self.ports_by_name.get(self.docked_port)
        faction = faction or (port.faction if port else None)
        if not port or port.faction != faction:
            self.toast_message("You must be berthed at a port belonging to that faction.", 3.0)
            return False
        cost = 150
        if self.gold < cost:
            self.toast_message("You cannot afford a diplomatic gift of 150 gold.", 3.0)
            return False
        old_label = self.faction_attitude(faction)
        self.gold -= cost
        self.adjust_faction_relation(faction, 8, "You presented a generous gift to the harbour authorities.")
        self.add_journal(f"Presented a 150-gold diplomatic gift at {port.name} ({old_label.lower()} relations before the gift).")
        return True

    def open_diplomacy_ledger(self):
        if self.docked_port and hasattr(self, "open_port_menu"):
            self.open_port_menu("diplomacy")
            return
        self.cannon_held[-1] = False
        self.cannon_held[1] = False
        self.diplomacy_open = True
        self.diplomacy_selection = max(0, min(self.diplomacy_selection, len(FACTION_NAMES) - 1))
        self.diplomacy_scroll = 0

    def handle_diplomacy_key(self, key):
        if key in (pygame.K_i, pygame.K_ESCAPE):
            self.diplomacy_open = False
        elif key in (pygame.K_UP, pygame.K_w):
            self.diplomacy_selection = (self.diplomacy_selection - 1) % len(FACTION_NAMES)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.diplomacy_selection = (self.diplomacy_selection + 1) % len(FACTION_NAMES)
        elif key == pygame.K_p:
            self.request_safe_conduct(FACTION_NAMES[self.diplomacy_selection])
        elif key == pygame.K_g:
            self.offer_diplomatic_gift(FACTION_NAMES[self.diplomacy_selection])

    def diplomatic_action_hint(self):
        port = self.nearest_port_for_parley()
        if port and self.faction_attitude(port.faction) == "HOSTILE":
            return f"P: pay {100 + (-20 - self.faction_standing(port.faction)) * 2} gold for safe conduct at {port.name}"
        if self.docked_port:
            port = self.ports_by_name.get(self.docked_port)
            if port:
                return f"G: present a 150-gold gift to the {port.faction} at {port.name}"
        return "Visit a faction harbour to present a gift, or approach a hostile port to request safe conduct"
