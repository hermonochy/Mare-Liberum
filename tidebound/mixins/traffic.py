from ..common import *


class TrafficMixin:


    def initialise_traffic_ships(self, count=6):
        self.traffic_ships = []
        for _ in range(count):
            self.spawn_traffic_ship()

    def choose_traffic_destination(self, exclude=None):
        choices = [port for port in self.ports if port.name != exclude]
        if not choices:
            return None
        weights = [0.65 + float(getattr(self, "faction_economies", {}).get(port.faction, {}).get("prosperity", 50.0)) / 100.0 for port in choices]
        return self.rng.choices(choices, weights=weights, k=1)[0]

    @staticmethod
    def harbour_berth_position(port, slot):
        axis_x, axis_y = port.x - port.shore_x, port.y - port.shore_y
        length = max(1.0, math.hypot(axis_x, axis_y))
        axis_x, axis_y = axis_x / length, axis_y / length
        perp_x, perp_y = -axis_y, axis_x
        offset = (int(slot) - PORT_BERTH_CENTER_SLOT) * PORT_BERTH_SPACING
        return port.x + axis_x * 26.0 + perp_x * offset, port.y + axis_y * 26.0 + perp_y * offset

    def occupied_harbour_slots(self, port):
        """Return quay slots occupied by the player and berthed NPC vessels."""
        used = set()
        if self.docked_port == port.name:
            player_slot = int(getattr(self, "player_berth_slot", PORT_BERTH_CENTER_SLOT))
            if player_slot in range(PORT_BERTH_COUNT):
                used.add(player_slot)
        for ship in getattr(self, "traffic_ships", []):
            slot = int(getattr(ship, "berth_slot", -1))
            if (ship.hull > 0 and getattr(ship, "port_dwell", 0.0) > 0.0
                    and getattr(ship, "berth_port", "") == port.name
                    and slot in range(PORT_BERTH_COUNT)):
                used.add(slot)
        return used

    def nearest_available_harbour_slot(self, port, x, y, occupied=None):
        """Find the free berth closest to an approaching ship's current position."""
        used = self.occupied_harbour_slots(port) if occupied is None else set(occupied)
        available = [slot for slot in range(PORT_BERTH_COUNT) if slot not in used]
        if not available:
            return None
        return min(
            available,
            key=lambda slot: math.hypot(
                self.harbour_berth_position(port, slot)[0] - x,
                self.harbour_berth_position(port, slot)[1] - y,
            ),
        )


    def spawn_traffic_ship(self):
        if len(self.traffic_ships) >= 18:
            return False
        roles = list(TRAFFIC_ROLES)
        weights = self.trade_traffic_role_weights() if hasattr(self, "trade_traffic_role_weights") else [42, 23, 14, 15, 6]
        role = self.rng.choices(roles, weights=weights, k=1)[0]
        profile = TRAFFIC_ROLES[role]
        destination = self.choose_traffic_destination()
        if destination is None:
            return False
        position = None
        for _ in range(1400):
            x = self.rng.uniform(260.0, WORLD_WIDTH - 260.0)
            y = self.rng.uniform(260.0, WORLD_HEIGHT - 260.0)
            if math.hypot(x - self.ship_x, y - self.ship_y) < 620.0:
                continue
            if any(point_in_polygon((x, y), polygon) for polygon in self.collision_land_polygons()):
                continue
            if not self.reef_clear_at(x, y, 105.0):
                continue
            if any(nearest_polygon_edge(x, y, polygon)[1] < 86.0 for polygon in self.land):
                continue
            if any(math.hypot(x - port.x, y - port.y) < 190.0 for port in self.ports):
                continue
            if any(math.hypot(x - ship.x, y - ship.y) < 150.0 for ship in self.traffic_ships):
                continue
            if any(ship.hull > 0 and math.hypot(x - ship.x, y - ship.y) < 145.0 for ship in self.fleet):
                continue
            if any(not pirate.dead and math.hypot(x - pirate.x, y - pirate.y) < 150.0 for pirate in self.pirates):
                continue
            position = (x, y)
            break
        if position is None:
            return False
        x, y = position
        heading = math.degrees(math.atan2(destination.y - y, destination.x - x)) % 360.0
        name = self.rng.choice(profile["names"])
        faction_weights = {
            "naval patrol": [("British Crown", 48), ("Spanish Crown", 32), ("French Crown", 20)],
            "merchant": [("Merchant League", 58), ("Independent", 20), ("British Crown", 8), ("Spanish Crown", 8), ("French Crown", 6)],
            "fishing": [("Independent", 85), ("Merchant League", 15)],
            "mail packet": [("British Crown", 30), ("Spanish Crown", 20), ("French Crown", 20), ("Merchant League", 20), ("Independent", 10)],
            "whaler": [("Merchant League", 50), ("Independent", 50)],
        }
        faction_choices = faction_weights.get(role, [("Independent", 1)])
        ship_faction = self.rng.choices([item[0] for item in faction_choices],
                                        weights=[item[1] for item in faction_choices], k=1)[0]
        attitude = self.relation_label(self.faction_standing(ship_faction))
        self.traffic_ships.append(
            TrafficShip(
                name=f"{name} {self.traffic_serial}",
                role=role,
                ship_type=self.rng.choice(profile["types"]),
                x=x,
                y=y,
                heading=heading,
                destination=destination.name,
                hull=profile["hull"],
                max_hull=profile["hull"],
                wander=self.rng.random() * math.tau,
                faction=ship_faction,
                player_attitude=attitude.lower(),
                hostile_to_player=(attitude == "HOSTILE"),
            )
        )
        self.traffic_serial += 1
        return True


    def organise_npc_fleets(self):
        """Occasionally bind nearby ships into named, persistent NPC squadrons."""
        # A few ships sail alone; others form small named squadrons.
        for role in ("merchant", "naval patrol"):
            unassigned = [s for s in self.traffic_ships if s.hull > 0 and s.role == role and not s.fleet_id]
            while len(unassigned) >= 2:
                leader = unassigned.pop(0)
                same_flag = [ship for ship in unassigned if getattr(ship, "faction", "") == getattr(leader, "faction", "")]
                if self.rng.random() > (0.68 if role == "naval patrol" else 0.48):
                    continue
                nearby = sorted(same_flag, key=lambda s: math.hypot(s.x-leader.x, s.y-leader.y))
                if not nearby or math.hypot(nearby[0].x-leader.x, nearby[0].y-leader.y) > 980:
                    continue
                wing = [nearby[0]]
                unassigned.remove(nearby[0])
                if self.rng.random() < 0.38:
                    remaining_same_flag = [ship for ship in unassigned if getattr(ship, "faction", "") == getattr(leader, "faction", "")]
                    if remaining_same_flag:
                        extra = min(remaining_same_flag, key=lambda s: math.hypot(s.x-leader.x, s.y-leader.y))
                        if math.hypot(extra.x-leader.x, extra.y-leader.y) < 1250:
                            wing.append(extra); unassigned.remove(extra)
                fid = f"{role.replace(' ','-')}-{leader.name.replace(' ','-')}"
                commander = self.rng.choice(ADMIRAL_NAMES[role])
                members = [leader] + wing
                self.commander_fleet_state(fid, commander, role, len(members))
                self.ensure_commander_record(commander, role)
                for slot, member in enumerate(members):
                    member.fleet_id, member.commander_name = fid, commander
                    member.formation_slot = slot
                    member.fleet_size = len(members)
                    member.fleet_morale = 1.0
        # Pirate bands form around a nearby uncommitted captain.
        free = [p for p in self.pirates if not p.dead and not p.objective_target and not p.fleet_id]
        while len(free) >= 2:
            leader = free.pop(0)
            if self.rng.random() > 0.62:
                continue
            wing = min(free, key=lambda p: math.hypot(p.x-leader.x, p.y-leader.y), default=None)
            if wing is None or math.hypot(wing.x-leader.x, wing.y-leader.y) > 900:
                continue
            free.remove(wing)
            members = [leader, wing]
            if free and self.rng.random() < 0.35:
                extra = min(free, key=lambda p: math.hypot(p.x-leader.x, p.y-leader.y))
                if math.hypot(extra.x-leader.x, extra.y-leader.y) < 1150:
                    members.append(extra); free.remove(extra)
            fid = f"pirate-{leader.name.replace(' ','-')}"
            commander = self.rng.choice(ADMIRAL_NAMES["pirate"])
            self.commander_fleet_state(fid, commander, "pirate", len(members))
            self.ensure_commander_record(commander, "pirate")
            for slot, member in enumerate(members):
                member.fleet_id, member.commander_name = fid, commander
                member.formation_slot, member.fleet_morale = slot, 1.0
                member.fleet_size = len(members)


    def ensure_commander_record(self, commander_name, faction):
        if not commander_name:
            return None
        records = getattr(self, "commander_records", None)
        if records is None:
            self.commander_records = {}
            records = self.commander_records
        record = records.setdefault(commander_name, {
            "commander": commander_name,
            "faction": faction,
            "reputation": 50,
            "notoriety": 0,
            "victories": 0,
            "defeats": 0,
            "ships_sunk": 0,
            "ships_lost": 0,
            "retreats": 0,
            "last_event": "Recently entered Caribbean waters",
        })
        # Keep a commander's allegiance stable if a similarly named captain is
        # ever encountered in another context.
        record.setdefault("faction", faction)
        for key, default in (("reputation", 50), ("notoriety", 0), ("victories", 0),
                             ("defeats", 0), ("ships_sunk", 0), ("ships_lost", 0),
                             ("retreats", 0), ("last_event", "No recent reports")):
            record.setdefault(key, default)
        return record

    def commander_rank(self, record):
        faction = record.get("faction", "")
        reputation = int(record.get("reputation", 50))
        notoriety = int(record.get("notoriety", 0))
        if faction == "pirate":
            if notoriety >= 90: return "Terror of the Caribbean"
            if notoriety >= 65: return "Dread Captain"
            if notoriety >= 40: return "Infamous Raider"
            if notoriety >= 20: return "Wanted Captain"
            return "Rising Pirate"
        if faction == "naval patrol":
            if reputation >= 90: return "Legendary Admiral"
            if reputation >= 72: return "Decorated Commander"
            if reputation >= 55: return "Respected Officer"
            if reputation >= 40: return "Promising Officer"
            if reputation >= 25: return "Under Scrutiny"
            return "Disgraced Commander"
        if reputation >= 85: return "Master of the Trade Routes"
        if reputation >= 68: return "Trusted Convoy Master"
        if reputation >= 52: return "Respected Merchant"
        if reputation >= 35: return "Risky Speculator"
        return "Shunned Merchant"

    def adjust_commander_record(self, commander_name, faction, *, reputation=0, notoriety=0,
                                event=None, counter=None):
        record = self.ensure_commander_record(commander_name, faction)
        if record is None:
            return None
        record["reputation"] = max(0, min(100, int(record.get("reputation", 50)) + int(reputation)))
        record["notoriety"] = max(0, min(1000, int(record.get("notoriety", 0)) + int(notoriety)))
        if counter:
            record[counter] = int(record.get(counter, 0)) + 1
        if event:
            record["last_event"] = event
        return record

    def commander_fleet_state(self, fleet_id, commander_name="", faction="", fleet_size=1):
        if not fleet_id:
            return None
        states = getattr(self, "commander_fleets", None)
        if states is None:
            self.commander_fleets = {}
            states = self.commander_fleets
        state = states.setdefault(fleet_id, {
            "commander": commander_name,
            "faction": faction,
            "size": max(1, int(fleet_size)),
            "losses": 0,
            "retreat_recorded": False,
            "defeat_recorded": False,
        })
        state["size"] = max(int(state.get("size", 1)), int(fleet_size), 1)
        if commander_name:
            state["commander"] = commander_name
        if faction:
            state["faction"] = faction
        return state

    def record_commander_retreat(self, members):
        if not members:
            return
        leader = min(members, key=lambda member: getattr(member, "formation_slot", 0))
        commander = getattr(leader, "commander_name", "")
        if not commander:
            return
        faction = "pirate" if isinstance(leader, PirateShip) else leader.role
        fleet_id = getattr(leader, "fleet_id", "")
        state = self.commander_fleet_state(fleet_id, commander, faction, getattr(leader, "fleet_size", len(members)))
        if state and state.get("retreat_recorded"):
            return
        if state:
            state["retreat_recorded"] = True
        rep_change = -4 if faction == "naval patrol" else (-2 if faction == "pirate" else -3)
        notoriety_change = 2 if faction == "pirate" else 1
        record = self.adjust_commander_record(
            commander, faction, reputation=rep_change, notoriety=notoriety_change,
            event="Ordered a withdrawal after taking heavy losses", counter="retreats")
        if record:
            self.add_journal(f"{commander} ordered a retreat. Reports now describe them as {self.commander_rank(record).lower()}.")

    def record_commander_ship_loss(self, victim, cause="an independent sea battle", attacker=None):
        victim_commander = getattr(victim, "commander_name", "")
        victim_faction = "pirate" if isinstance(victim, PirateShip) else getattr(victim, "role", "merchant")
        if victim_commander:
            record = self.adjust_commander_record(
                victim_commander, victim_faction, reputation=-5, notoriety=2,
                event=f"Lost {victim.name} to {cause}", counter="ships_lost")
            fleet_id = getattr(victim, "fleet_id", "")
            state = self.commander_fleet_state(fleet_id, victim_commander, victim_faction,
                                               getattr(victim, "fleet_size", 1))
            if state and not state.get("defeat_recorded"):
                state["losses"] = int(state.get("losses", 0)) + 1
                if state["losses"] >= int(state.get("size", 1)):
                    state["defeat_recorded"] = True
                    record["defeats"] = int(record.get("defeats", 0)) + 1
                    record["reputation"] = max(0, int(record.get("reputation", 50)) - 10)
                    record["notoriety"] = min(1000, int(record.get("notoriety", 0)) + 4)
                    record["last_event"] = "Commanded a fleet that was destroyed"
                    self.add_journal(f"The fleet of {victim_commander} has been destroyed; their standing suffers across the Caribbean.")
        if attacker:
            attacker_name = getattr(attacker, "source_commander", "")
            attacker_faction = getattr(attacker, "source_faction", "")
            if attacker_name:
                reward = 6 if attacker_faction == "naval patrol" else (4 if attacker_faction == "merchant" else 5)
                fear = 7 if attacker_faction == "pirate" else (2 if attacker_faction == "naval patrol" else 1)
                record = self.adjust_commander_record(
                    attacker_name, attacker_faction, reputation=reward, notoriety=fear,
                    event=f"Sank {victim.name}", counter="ships_sunk")
                record["victories"] = int(record.get("victories", 0)) + 1
                self.add_journal(f"{attacker_name} wins renown after {victim.name} is sunk in an independent battle.")

    def commander_faction_label(self, faction):
        return {"naval patrol": "Royal Navy", "merchant": "Merchant Fleet", "pirate": "Pirate Brotherhood"}.get(faction, faction.title())

    def fleet_members(self, ship):
        if not getattr(ship, "fleet_id", ""):
            return [ship]
        members = [s for s in self.traffic_ships + self.pirates
                   if getattr(s, "fleet_id", "") == ship.fleet_id and
                   (getattr(s, "hull", 0) > 0 if hasattr(s, "hull") else not s.dead)]
        return members or [ship]

    def fleet_formation_point(self, ship):
        members = self.fleet_members(ship)
        leader = min(members, key=lambda m: getattr(m, "formation_slot", 0))
        if ship is leader:
            return None
        angle = math.radians(leader.heading)
        slot = getattr(ship, "formation_slot", 1)
        row = (slot + 1) // 2
        side = -1 if slot % 2 else 1
        return (leader.x - math.cos(angle) * (105.0 * row) - math.sin(angle) * side * 82.0,
                leader.y - math.sin(angle) * (105.0 * row) + math.cos(angle) * side * 82.0)

    def update_fleet_commanders(self, dt):
        # Commanders weigh the squadron's remaining strength and order a withdrawal
        # when losses make the engagement untenable.
        seen = set()
        for ship in self.traffic_ships + self.pirates:
            fid = getattr(ship, "fleet_id", "")
            if not fid or fid in seen:
                continue
            seen.add(fid)
            members = self.fleet_members(ship)
            living = [m for m in members if (m.hull > 0 if hasattr(m, "hull") else not m.dead)]
            if not living:
                continue
            leader = min(living, key=lambda m: getattr(m, "formation_slot", 0))
            faction = "pirate" if isinstance(leader, PirateShip) else leader.role
            state = self.commander_fleet_state(fid, leader.commander_name, faction, getattr(leader, "fleet_size", len(members)))
            fleet_size = max(1, int(state.get("size", len(members))) if state else len(members))
            strength = sum(max(0, m.hull) / max(1, m.max_hull) for m in living) / fleet_size
            should_retreat = strength < 0.43 or (len(living) / fleet_size <= 0.5)
            if should_retreat and not any(getattr(m, "retreating", False) for m in members):
                self.record_commander_retreat(members)
            for member in members:
                member.fleet_morale = strength
                if should_retreat:
                    member.retreating = True
                elif strength > 0.78:
                    member.retreating = False
                    if state:
                        state["retreat_recorded"] = False
            if any(getattr(m, "retreating", False) for m in members):
                # Retreat as a squadron toward the leader's next port, or away
                # from its pursuer when a pirate band has no port itinerary.
                leader = min(living, key=lambda m: getattr(m, "formation_slot", 0))
                if hasattr(leader, "destination") and leader.destination in self.ports_by_name:
                    dest = self.ports_by_name[leader.destination]
                    away = math.degrees(math.atan2(dest.y-leader.y, dest.x-leader.x))
                else:
                    threats = [v for v in self.traffic_ships if v.hull > 0]
                    threats += [p for p in self.pirates if not p.dead and p.fleet_id != fid]
                    target_name = getattr(leader, "npc_target_name", "")
                    named_target = next((v for v in threats if getattr(v, "name", "") == target_name), None)
                    threat = named_target or (min(threats, key=lambda v: math.hypot(v.x-leader.x, v.y-leader.y)) if threats else None)
                    if threat is not None:
                        away = math.degrees(math.atan2(leader.y-threat.y, leader.x-threat.x))
                    else:
                        away = leader.heading
                for member in living:
                    member.heading = (member.heading + clamp(angle_difference(away, member.heading), -30*dt, 30*dt)) % 360

    def assign_npc_battle_targets(self):
        """Give autonomous ships sensible opponents without involving the player."""
        living_pirates = [pirate for pirate in self.pirates if not pirate.dead]
        battle_vessels = [
            ship for ship in self.traffic_ships
            if ship.hull > 0 and ship.role in {"merchant", "naval patrol"}
        ]

        # Pirates seek merchant prizes and naval patrols. Story-mission enemies
        # keep their scripted objective and are not diverted into ambient fights.
        for pirate in living_pirates:
            pirate.npc_target_name = ""
            if pirate.objective_target or pirate.retreating:
                continue
            candidates = []
            for ship in battle_vessels:
                distance = math.hypot(ship.x - pirate.x, ship.y - pirate.y)
                limit = 1450.0 if ship.role == "naval patrol" else 1120.0
                if distance <= limit:
                    # Patrols are the more dangerous opponent; merchants are the
                    # easier prize. A modest navy preference produces convoy escorts.
                    score = distance * (0.78 if ship.role == "naval patrol" else 1.0)
                    candidates.append((score, distance, ship))
            if candidates:
                _, _, target = min(candidates, key=lambda item: item[0])
                if pirate.fleet_id:
                    squad_targets = [p.npc_target_name for p in living_pirates
                                     if p.fleet_id == pirate.fleet_id and p.npc_target_name]
                    if squad_targets:
                        shared = next((v for v in battle_vessels if v.name == squad_targets[0]), None)
                        if shared is not None:
                            target = shared
                pirate.npc_target_name = target.name

        # Naval patrols actively hunt pirates. Armed merchantmen join a fight
        # when a pirate comes close enough to threaten the vessel or convoy.
        for ship in self.traffic_ships:
            ship.combat_target_name = ""
            ship.under_attack = False
            if ship.hostile_to_player and ship.hull > 0 and not ship.retreating:
                ship.combat_target_name = "__player__"
                ship.under_attack = True
                continue
            if ship.hull <= 0 or ship.retreating or ship.role not in {"merchant", "naval patrol"}:
                continue
            candidates = []
            for pirate in living_pirates:
                if pirate.objective_target:
                    continue
                distance = math.hypot(pirate.x - ship.x, pirate.y - ship.y)
                limit = 1650.0 if ship.role == "naval patrol" else 760.0
                if distance <= limit:
                    candidates.append((distance, pirate))
            if candidates:
                distance, target = min(candidates, key=lambda item: item[0])
                ship.combat_target_name = target.name
                ship.under_attack = distance <= 500.0

    def _combat_target_for_traffic(self, ship):
        if ship.combat_target_name == "__player__":
            return self
        if not ship.combat_target_name:
            return None
        return next((pirate for pirate in self.pirates
                     if not pirate.dead and pirate.name == ship.combat_target_name), None)

    def _battle_target_position(self, target):
        if target is self:
            return self.ship_x, self.ship_y
        return target.x, target.y

    def provoke_traffic_ship(self, ship, source="Your guns"):
        """A friendly vessel struck by player-owned guns turns hostile with its squadron."""
        was_hostile = bool(ship.hostile_to_player)
        self.record_player_attack_on_npc(ship, source)
        if not was_hostile:
            self.add_journal(f"{source} struck {ship.name}. {ship.name} and any surviving ships in its fleet now regard your vessel as hostile.")
            self.toast_message(f"{ship.name} turns hostile and brings its guns to bear!", 3.2)

    def _combat_target_for_pirate(self, pirate):
        if not pirate.npc_target_name:
            return None
        return next((ship for ship in self.traffic_ships
                     if ship.hull > 0 and ship.name == pirate.npc_target_name), None)

    @staticmethod
    def _broadside_course(bearing, current_heading, distance):
        """Approach, then circle at cannon range with a broadside facing the target."""
        if distance > 690.0:
            return bearing
        if distance < 265.0:
            return (bearing + 180.0) % 360.0
        choices = ((bearing - 90.0) % 360.0, (bearing + 90.0) % 360.0)
        return min(choices, key=lambda course: abs(angle_difference(course, current_heading)))

    def fire_npc_broadside(self, attacker, target, owner, shot_count=3, speed=415.0):
        target_x, target_y = self._battle_target_position(target)
        dx = target_x - attacker.x
        dy = target_y - attacker.y
        distance = math.hypot(dx, dy)
        if distance < 145.0 or distance > 720.0:
            return False
        bearing = math.degrees(math.atan2(dy, dx))
        port_alignment = abs(angle_difference((attacker.heading - 90.0) % 360.0, bearing))
        starboard_alignment = abs(angle_difference((attacker.heading + 90.0) % 360.0, bearing))
        if min(port_alignment, starboard_alignment) > 31.0:
            return False

        angle = math.radians(bearing)
        side = -1.0 if port_alignment <= starboard_alignment else 1.0
        broadside = angle + side * math.pi / 2.0
        forward = math.radians(attacker.heading)
        for index in range(shot_count):
            offset = (index - (shot_count - 1) / 2.0) * 12.0
            spread = (index - (shot_count - 1) / 2.0) * 0.018
            aim = angle + spread
            muzzle_x = attacker.x + math.cos(forward) * offset + math.cos(broadside) * 18.0
            muzzle_y = attacker.y + math.sin(forward) * offset + math.sin(broadside) * 18.0
            self.projectiles.append(Cannonball(
                muzzle_x, muzzle_y,
                math.cos(aim) * speed + attacker.vx * 0.12,
                math.sin(aim) * speed + attacker.vy * 0.12,
                1.7,
                owner,
                getattr(attacker, "commander_name", ""),
                "pirate" if isinstance(attacker, PirateShip) else getattr(attacker, "role", ""),
                getattr(attacker, "fleet_id", ""),
            ))
            self.spawn_cannon_smoke(muzzle_x, muzzle_y, math.cos(broadside), math.sin(broadside), amount=1)
        self.apply_cannon_recoil(attacker, math.cos(broadside), math.sin(broadside), 8.5)
        distance_to_player = math.hypot(attacker.x - self.ship_x, attacker.y - self.ship_y)
        self.audio.play("cannon_fire", volume=max(0.03, 0.24 * (1.0 - distance_to_player / 3200.0)))
        return True

    def update_npc_battles(self, dt):
        """Resolve independent merchant/pirate/naval engagements in the living sea."""
        battle_notice_timer = max(0.0, getattr(self, "npc_battle_notice_timer", 0.0) - dt)
        self.npc_battle_notice_timer = battle_notice_timer

        for pirate in self.pirates:
            if pirate.dead or pirate.objective_target:
                continue
            target = self._combat_target_for_pirate(pirate)
            if target is None:
                continue
            distance = math.hypot(target.x - pirate.x, target.y - pirate.y)
            bearing = math.degrees(math.atan2(target.y - pirate.y, target.x - pirate.x))
            desired = (bearing + 180.0) % 360.0 if pirate.retreating else self._broadside_course(bearing, pirate.heading, distance)
            pirate.heading = (pirate.heading + clamp(angle_difference(desired, pirate.heading), -40.0 * dt, 40.0 * dt)) % 360.0
            pirate.cooldown = max(0.0, pirate.cooldown - dt)
            if pirate.cooldown <= 0.0 and self.fire_npc_broadside(pirate, target, "npc_pirate", shot_count=3, speed=390.0):
                pirate.cooldown = 2.8 + self.rng.uniform(0.0, 1.0)
                if math.hypot(pirate.x - self.ship_x, pirate.y - self.ship_y) < 1350.0 and self.npc_battle_notice_timer <= 0.0:
                    self.toast_message(f"Beyond the waves, {pirate.name} trades broadsides with {target.name}.", 2.6)
                    self.npc_battle_notice_timer = 7.0

        for ship in self.traffic_ships:
            if ship.hull <= 0 or ship.retreating:
                continue
            if ship.role not in {"merchant", "naval patrol"} and not ship.hostile_to_player:
                continue
            target = self._combat_target_for_traffic(ship)
            if target is None:
                continue
            target_x, target_y = self._battle_target_position(target)
            distance = math.hypot(target_x - ship.x, target_y - ship.y)
            bearing = math.degrees(math.atan2(target_y - ship.y, target_x - ship.x))
            desired = (bearing + 180.0) % 360.0 if ship.retreating else self._broadside_course(bearing, ship.heading, distance)
            ship.heading = (ship.heading + clamp(angle_difference(desired, ship.heading), -38.0 * dt, 38.0 * dt)) % 360.0
            ship.combat_cooldown = max(0.0, ship.combat_cooldown - dt)
            shot_limit = 760.0 if ship.role == "naval patrol" else 650.0
            if distance <= shot_limit and ship.combat_cooldown <= 0.0:
                shots = 4 if ship.role == "naval patrol" else (3 if ship.hostile_to_player else 2)
                speed = 435.0 if ship.role == "naval patrol" else 375.0
                owner = "npc_traffic_hostile" if target is self else ("npc_navy" if ship.role == "naval patrol" else "npc_merchant")
                if self.fire_npc_broadside(ship, target, owner, shot_count=shots, speed=speed):
                    ship.combat_cooldown = (2.25 if ship.role == "naval patrol" else 3.0) + self.rng.uniform(0.0, 0.85)
                    if math.hypot(ship.x - self.ship_x, ship.y - self.ship_y) < 1350.0 and self.npc_battle_notice_timer <= 0.0:
                        target_name = "your ship" if target is self else target.name
                        self.toast_message(f"{ship.name} opens fire on {target_name}.", 2.6)
                        self.npc_battle_notice_timer = 7.0

    def update_traffic_ships(self, dt):
        self.traffic_spawn_timer -= dt
        if self.traffic_spawn_timer <= 0.0:
            self.spawn_traffic_ship()
            self.traffic_spawn_timer = self.rng.uniform(22.0, 36.0)

        land_polygons = self.collision_land_polygons()
        occupied_berths = {}
        for port in self.ports:
            slots = self.occupied_harbour_slots(port)
            if slots:
                occupied_berths[port.name] = slots

        for ship in list(self.traffic_ships):
            if ship.hull <= 0:
                continue
            destination = self.ports_by_name.get(ship.destination)
            if destination is None:
                destination = self.choose_traffic_destination()
                if destination is None:
                    continue
                ship.destination = destination.name

            combat_target = None if ship.retreating else self._combat_target_for_traffic(ship)
            # Merchantmen and patrols can spend a little time alongside. This
            # creates a visible multi-ship anchorage rather than passing through
            # every port without stopping. Combat immediately breaks the berth.
            if getattr(ship, "port_dwell", 0.0) > 0.0 and getattr(ship, "berth_port", "") and combat_target is None and not ship.retreating:
                berth = self.ports_by_name.get(ship.berth_port)
                if berth is not None:
                    ship.port_dwell = max(0.0, ship.port_dwell - dt)
                    ship.x, ship.y = self.harbour_berth_position(berth, ship.berth_slot)
                    ship.vx = ship.vy = 0.0
                    ship.heading = berth.exit_heading
                    if ship.port_dwell > 0.0:
                        continue
                ship.berth_port = ""
                ship.berth_slot = -1
                destination = self.choose_traffic_destination(ship.destination)
                if destination is not None:
                    ship.destination = destination.name
            elif getattr(ship, "berth_port", "") and (combat_target is not None or ship.retreating):
                occupied_berths.get(ship.berth_port, set()).discard(getattr(ship, "berth_slot", -1))
                ship.berth_port = ""
                ship.berth_slot = -1
                ship.port_dwell = 0.0

            dx = destination.x - ship.x
            dy = destination.y - ship.y
            distance = math.hypot(dx, dy)
            if combat_target is None and not ship.retreating and distance < 205.0:
                used = occupied_berths.setdefault(destination.name, set())
                available = [slot for slot in range(PORT_BERTH_COUNT) if slot not in used]
                if available:
                    slot = min(available, key=lambda value: abs(value - PORT_BERTH_CENTER_SLOT) + self.rng.random() * 0.2)
                    used.add(slot)
                    ship.berth_port = destination.name
                    ship.berth_slot = slot
                    ship.port_dwell = self.rng.uniform(17.0, 36.0)
                    ship.x, ship.y = self.harbour_berth_position(destination, slot)
                    ship.vx = ship.vy = 0.0
                    ship.heading = destination.exit_heading
                    continue
                # All berths are occupied: choose another harbour rather than
                # crowding vessels into the same water.
                destination = self.choose_traffic_destination(ship.destination)
                if destination is not None:
                    ship.destination = destination.name
                    dx = destination.x - ship.x
                    dy = destination.y - ship.y
                    distance = max(1.0, math.hypot(dx, dy))

            if ship.retreating:
                desired = ship.heading
            elif combat_target is not None:
                battle_target_x, battle_target_y = self._battle_target_position(combat_target)
                battle_dx = battle_target_x - ship.x
                battle_dy = battle_target_y - ship.y
                battle_distance = math.hypot(battle_dx, battle_dy)
                battle_bearing = math.degrees(math.atan2(battle_dy, battle_dx))
                desired = self._broadside_course(battle_bearing, ship.heading, battle_distance)
            else:
                if distance < 165.0:
                    destination = self.choose_traffic_destination(ship.destination)
                    if destination is not None:
                        ship.destination = destination.name
                        dx = destination.x - ship.x
                        dy = destination.y - ship.y
                        distance = max(1.0, math.hypot(dx, dy))
                desired = math.degrees(math.atan2(dy, dx))
                point = self.fleet_formation_point(ship)
                if point and not ship.retreating:
                    desired = math.degrees(math.atan2(point[1]-ship.y, point[0]-ship.x))
            desired = self.reef_avoidance_heading(ship.x, ship.y, desired, lookahead=720.0, clearance=145.0)
            difference = angle_difference(desired, ship.heading)
            turn_rate = 25.0 if ship.role == "whaler" else (38.0 if combat_target is not None else 34.0)
            ship.heading = (ship.heading + clamp(difference, -turn_rate * dt, turn_rate * dt)) % 360.0
            heading = math.radians(ship.heading)
            profile = TRAFFIC_ROLES[ship.role]
            ship.vx += math.cos(heading) * profile["speed"] * 0.62 * dt
            ship.vy += math.sin(heading) * profile["speed"] * 0.62 * dt
            drag = math.exp(-0.10 * dt)
            ship.vx *= drag
            ship.vy *= drag
            speed = math.hypot(ship.vx, ship.vy)
            maximum = profile["speed"]
            if speed > maximum:
                ship.vx *= maximum / speed
                ship.vy *= maximum / speed
            ship.x += ship.vx * dt
            ship.y += ship.vy * dt
            old_heading = ship.heading
            ship.x, ship.y, ship.vx, ship.vy, collided = resolve_land_collision(
                ship.x, ship.y, ship.vx, ship.vy, SHIP_COLLISION_RADII.get(ship.ship_type, 32.0), land_polygons
            )
            if collided:
                ship.heading = (old_heading + self.rng.choice([-1, 1]) * self.rng.uniform(48.0, 82.0)) % 360.0
                ship.vx *= 0.42
                ship.vy *= 0.42
            self.apply_reef_damage(ship, dt, kind="npc", ship_radius=SHIP_COLLISION_RADII.get(ship.ship_type, 32.0))

    def _ship_collision_bodies(self):
        bodies = []
        bodies.append({
            "entity": self,
            "x_key": "ship_x", "y_key": "ship_y", "vx_key": "ship_vx", "vy_key": "ship_vy",
            "radius": SHIP_COLLISION_RADII.get(self.current_ship, 34.0) + 3.0,
            "mass": max(1.0, self.player_max_hull / 95.0), "player": True,
            "static": bool(self.docked_port),
        })
        for ship in self.fleet:
            if ship.hull > 0:
                bodies.append({
                    "entity": ship, "x_key": "x", "y_key": "y", "vx_key": "vx", "vy_key": "vy",
                    "radius": SHIP_COLLISION_RADII.get(ship.ship_type, 32.0),
                    "mass": max(0.9, ship.max_hull / 100.0), "player": False, "static": False,
                })
        for ship in self.pirates:
            if not ship.dead:
                bodies.append({
                    "entity": ship, "x_key": "x", "y_key": "y", "vx_key": "vx", "vy_key": "vy",
                    "radius": SHIP_COLLISION_RADII.get(ship.ship_type, 32.0),
                    "mass": max(0.9, ship.max_hull / 6.5), "player": False, "static": False,
                })
        for ship in self.traffic_ships:
            if ship.hull > 0:
                bodies.append({
                    "entity": ship, "x_key": "x", "y_key": "y", "vx_key": "vx", "vy_key": "vy",
                    "radius": SHIP_COLLISION_RADII.get(ship.ship_type, 32.0),
                    "mass": max(0.9, ship.max_hull / 6.5), "player": False, "static": bool(getattr(ship, "port_dwell", 0.0) > 0.0),
                })
        return bodies

    @staticmethod
    def _body_value(body, key):
        return getattr(body["entity"], body[key])

    @staticmethod
    def _set_body_value(body, key, value):
        setattr(body["entity"], body[key], value)

    def resolve_ship_collisions(self, dt=0.04):
        bodies = self._ship_collision_bodies()
        if len(bodies) < 2:
            return
        cell_size = 144.0
        player_bumped = False
        for _ in range(5):
            buckets = {}
            for index, body in enumerate(bodies):
                x = self._body_value(body, "x_key")
                y = self._body_value(body, "y_key")
                cell = (math.floor(x / cell_size), math.floor(y / cell_size))
                buckets.setdefault(cell, []).append(index)
            checked = set()
            for cell, indexes in buckets.items():
                for offset_x in (-1, 0, 1):
                    for offset_y in (-1, 0, 1):
                        neighbour = (cell[0] + offset_x, cell[1] + offset_y)
                        for index_a in indexes:
                            for index_b in buckets.get(neighbour, ()):
                                if index_a >= index_b:
                                    continue
                                pair = (index_a, index_b)
                                if pair in checked:
                                    continue
                                checked.add(pair)
                                a, b = bodies[index_a], bodies[index_b]
                                ax = self._body_value(a, "x_key")
                                ay = self._body_value(a, "y_key")
                                bx = self._body_value(b, "x_key")
                                by = self._body_value(b, "y_key")
                                dx, dy = bx - ax, by - ay
                                distance = math.hypot(dx, dy)
                                minimum = a["radius"] + b["radius"]
                                if distance >= minimum:
                                    continue
                                if distance < 0.001:
                                    angle = (index_a * 2.399963229728653 + index_b) % math.tau
                                    nx, ny, distance = math.cos(angle), math.sin(angle), 0.001
                                else:
                                    nx, ny = dx / distance, dy / distance
                                overlap = minimum - distance + 0.8
                                inverse_a = 0.0 if a["static"] else 1.0 / max(0.25, a["mass"])
                                inverse_b = 0.0 if b["static"] else 1.0 / max(0.25, b["mass"])
                                inverse_total = inverse_a + inverse_b
                                if inverse_total <= 0.0:
                                    continue
                                move_a = overlap * inverse_a / inverse_total
                                move_b = overlap * inverse_b / inverse_total
                                self._set_body_value(a, "x_key", ax - nx * move_a)
                                self._set_body_value(a, "y_key", ay - ny * move_a)
                                self._set_body_value(b, "x_key", bx + nx * move_b)
                                self._set_body_value(b, "y_key", by + ny * move_b)
                                avx = self._body_value(a, "vx_key")
                                avy = self._body_value(a, "vy_key")
                                bvx = self._body_value(b, "vx_key")
                                bvy = self._body_value(b, "vy_key")
                                relative_normal = (bvx - avx) * nx + (bvy - avy) * ny
                                if relative_normal < 0.0:
                                    restitution = 0.58
                                    impulse = -(1.0 + restitution) * relative_normal / inverse_total
                                    avx -= impulse * inverse_a * nx
                                    avy -= impulse * inverse_a * ny
                                    bvx += impulse * inverse_b * nx
                                    bvy += impulse * inverse_b * ny
                                    self._set_body_value(a, "vx_key", avx)
                                    self._set_body_value(a, "vy_key", avy)
                                    self._set_body_value(b, "vx_key", bvx)
                                    self._set_body_value(b, "vy_key", bvy)
                                if a["player"] or b["player"]:
                                    player_bumped = True
        if player_bumped and self.ship_collision_notice_timer <= 0.0:
            self.toast_message("Ships collide! The hulls glance apart and both vessels are knocked off course.", 2.4)
            self.ship_collision_notice_timer = 2.5
        self.ship_collision_notice_timer = max(0.0, self.ship_collision_notice_timer - dt)
