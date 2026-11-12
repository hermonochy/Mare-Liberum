from ..common import *


class MissionEventsMixin:
    EVENT_STATUSES = {"waiting", "scheduled", "active", "cooldown", "completed", "disabled"}

    def initialise_mission_events(self):
        self.world_flags = {}
        self.mission_event_fleet_strength = {}
        self.mission_event_states = {
            event["id"]: {
                "status": "waiting",
                "trigger_count": 0,
                "remaining": None,
                "cooldown_remaining": 0.0,
                "active_fleets": [],
                "enabled": event["enabled"],
                "last_outcome": "",
                "conditions_met": False,
                "spawn_failed": False,
                "resolution_pending": False,
                "fleet_serial": 0,
                "random_rolls": {},
            }
            for event in self.mission_events
        }

    def restore_mission_event_state(self, saved_states=None, saved_flags=None):
        self.initialise_mission_events()
        if isinstance(saved_flags, dict):
            self.world_flags.update(saved_flags)
        if not isinstance(saved_states, dict):
            return
        for event_id, saved in saved_states.items():
            if event_id not in self.mission_event_states or not isinstance(saved, dict):
                continue
            current = self.mission_event_states[event_id]
            status = str(saved.get("status", current["status"]))
            current["status"] = status if status in self.EVENT_STATUSES else "waiting"
            current["trigger_count"] = max(0, int(saved.get("trigger_count", 0)))
            remaining = saved.get("remaining")
            current["remaining"] = None if remaining is None else max(0.0, float(remaining))
            current["cooldown_remaining"] = max(0.0, float(saved.get("cooldown_remaining", 0.0)))
            fleets = saved.get("active_fleets", [])
            current["active_fleets"] = [str(value) for value in fleets if value] if isinstance(fleets, list) else []
            current["enabled"] = bool(saved.get("enabled", current["enabled"]))
            current["last_outcome"] = str(saved.get("last_outcome", ""))
            current["conditions_met"] = bool(saved.get("conditions_met", False))
            current["spawn_failed"] = False
            current["resolution_pending"] = bool(saved.get("resolution_pending", False))
            current["fleet_serial"] = max(0, int(saved.get("fleet_serial", 0)))
            rolls = saved.get("random_rolls", {})
            current["random_rolls"] = dict(rolls) if isinstance(rolls, dict) else {}

    def set_world_flag(self, key, value=True):
        key = str(key).strip()
        if key:
            self.world_flags[key] = value

    @staticmethod
    def compare_event_value(current, expected, operator):
        try:
            if operator == "==":
                return current == expected
            if operator == "!=":
                return current != expected
            if operator == ">":
                return current > expected
            if operator == ">=":
                return current >= expected
            if operator == "<":
                return current < expected
            if operator == "<=":
                return current <= expected
            if operator == "in":
                return current in expected
            if operator == "not_in":
                return current not in expected
            if operator == "contains":
                return expected in current
        except (TypeError, ValueError):
            return False
        return False

    def current_player_region(self):
        if self.docked_port and self.docked_port in self.ports_by_name:
            return self.ports_by_name[self.docked_port].region
        nearest = min(
            self.ports,
            key=lambda port: math.hypot(port.x - self.ship_x, port.y - self.ship_y),
            default=None,
        )
        if nearest and math.hypot(nearest.x - self.ship_x, nearest.y - self.ship_y) <= 1500.0:
            return nearest.region
        return "Open Sea"

    def find_event_mission(self, target):
        target = str(target)
        return next((
            mission for mission in self.missions
            if mission.mission_id == target or mission.title == target or mission.name == target
        ), None)

    def mission_event_condition_value(self, condition):
        kind = condition["type"]
        if kind == "escort_count":
            return sum(1 for ship in self.fleet if ship.hull > 0 and not ship.sinking)
        if kind == "fleet_ship_count":
            escorts = sum(1 for ship in self.fleet if ship.hull > 0 and not ship.sinking)
            return escorts + int(self.player_hull > 0)
        if kind == "fleet_power":
            return self.player_fleet_power()
        if kind == "gold":
            return self.gold
        if kind == "world_time":
            return self.world_time
        if kind == "mission_state":
            target = condition.get("mission", condition.get("key", ""))
            mission = self.find_event_mission(target)
            return self.mission_state(mission) if mission else "missing"
        if kind == "faction_standing":
            return self.faction_standing(str(condition.get("faction", "")))
        if kind == "flag":
            return self.world_flags.get(str(condition.get("key", "")), condition.get("default"))
        if kind == "ship_class":
            return self.current_ship
        if kind == "ship_upgrade":
            return int(self.upgrades.get(str(condition.get("key", "")), 0))
        if kind == "hull_percent":
            return 100.0 * self.player_hull / max(1, self.player_max_hull)
        if kind == "completed_day_jobs":
            return self.completed_day_jobs
        if kind == "relic_count":
            return len(self.relics)
        if kind == "unique_item_count":
            return len(self.unique_items)
        if kind == "region":
            return self.current_player_region()
        if kind == "docked_port":
            return self.docked_port or ""
        if kind == "at_sea":
            return not bool(self.docked_port)
        if kind == "port_visited":
            port_name = str(condition.get("port", condition.get("key", "")))
            return bool(self.world_flags.get(f"visited_port:{port_name}", False))
        if kind == "port_visit_count":
            port_name = str(condition.get("port", condition.get("key", "")))
            return int(self.world_flags.get(f"port_visits:{port_name}", 0))
        if kind == "event_state":
            event_id = str(condition.get("event", condition.get("key", "")))
            return self.mission_event_states.get(event_id, {}).get("status", "missing")
        if kind == "cargo_quantity":
            good_id = str(condition.get("good", condition.get("key", "")))
            return self.cargo_quantity(good_id)
        if kind == "cargo_load":
            return self.cargo_load()
        if kind == "cargo_free_space":
            return self.cargo_free_space()
        return None

    def evaluate_mission_event_condition(self, condition, random_rolls=None, ignore_random=False):
        random_rolls = random_rolls if random_rolls is not None else {}
        if "all" in condition:
            if not all(self.evaluate_mission_event_condition(child, random_rolls, ignore_random) for child in condition["all"]):
                return False
        if "any" in condition:
            if not any(self.evaluate_mission_event_condition(child, random_rolls, ignore_random) for child in condition["any"]):
                return False
        if "not" in condition and self.evaluate_mission_event_condition(condition["not"], random_rolls, ignore_random):
            return False
        if "type" not in condition:
            return True
        kind = condition["type"]
        if kind == "constant":
            return bool(condition.get("value", False))
        if kind == "random":
            if ignore_random:
                return True
            roll_id = str(condition.get("roll_id", "random"))
            if roll_id not in random_rolls:
                random_rolls[roll_id] = self.rng.uniform(0.0, 100.0)
            current = random_rolls[roll_id]
        else:
            current = self.mission_event_condition_value(condition)
        expected = condition.get("value")
        operator = str(condition.get("op", condition.get("operator", "=="))).lower()
        return self.compare_event_value(current, expected, operator)

    @staticmethod
    def vessel_combat_power(max_hull, guns, health_ratio=1.0):
        hull_rating = math.sqrt(max(1.0, float(max_hull)) / 100.0)
        gun_rating = math.sqrt(max(1.0, float(guns)) / 3.0)
        condition = 0.25 + 0.75 * max(0.0, min(1.0, float(health_ratio)))
        return (hull_rating * 0.58 + gun_rating * 0.42) * condition

    def player_fleet_power(self):
        flagship_stats = SHIP_CLASSES.get(self.current_ship, SHIP_CLASSES["Sloop"])
        flagship_guns = flagship_stats["guns"] + max(0, self.upgrades.get("cannons", 0))
        total = self.vessel_combat_power(
            self.player_max_hull,
            flagship_guns,
            self.player_hull / max(1, self.player_max_hull),
        )
        for escort in self.fleet:
            if escort.hull <= 0 or escort.sinking:
                continue
            stats = SHIP_CLASSES.get(escort.ship_type, SHIP_CLASSES["Sloop"])
            upgrades = getattr(escort, "upgrades", {}) or {}
            guns = max(2, (stats["guns"] + max(0, upgrades.get("cannons", 0)) * 2) // 2)
            total += self.vessel_combat_power(
                escort.max_hull,
                guns,
                escort.hull / max(1, escort.max_hull),
            )
        return round(total, 3)

    def event_spawn_position(self, index, count, spawn_distance, occupied, land_polygons):
        base_angle = math.tau * index / max(1, count) + self.rng.uniform(-0.1, 0.1)
        ring = index // 10
        for attempt in range(220):
            angle = base_angle + attempt * 0.23
            radius = spawn_distance + ring * 260.0 + self.rng.uniform(-210.0, 210.0)
            x = self.ship_x + math.cos(angle) * radius
            y = self.ship_y + math.sin(angle) * radius
            if not (100.0 < x < WORLD_WIDTH - 100.0 and 100.0 < y < WORLD_HEIGHT - 100.0):
                continue
            if math.hypot(x - self.ship_x, y - self.ship_y) < 700.0:
                continue
            if not self.reef_clear_at(x, y, 105.0):
                continue
            if any(
                point_in_polygon((x, y), polygon)
                or nearest_polygon_edge(x, y, polygon)[1] < 70.0
                for polygon in land_polygons
            ):
                continue
            if any(math.hypot(x - port.x, y - port.y) < 320.0 for port in self.ports):
                continue
            if any(math.hypot(x - ship.x, y - ship.y) < 125.0 for ship in occupied):
                continue
            return x, y
        return None

    def event_ship_power(self, ship):
        return self.vessel_combat_power(ship.max_hull, ship.gun_count)

    def spawn_event_fleet(self, action, event_id, trigger_count, action_index, fleet_serial):
        ship_types = action.get("ship_types", ["Schooner", "Brigantine", "Frigate"])
        commander = str(action.get("commander", "")) or self.rng.choice(ADMIRAL_NAMES["pirate"])
        fleet_name = str(action.get("name", "Pirate Squadron"))
        minimum_ships = max(1, int(action.get("minimum_ships", action.get("min_ships", 6))))
        maximum_ships = max(minimum_ships, int(action.get("maximum_ships", action.get("max_ships", 48))))
        hard_maximum = max(maximum_ships, int(action.get("hard_maximum_ships", 128)))
        strength_ratio = max(0.1, float(action.get("strength_ratio", 1.0)))
        target_power = self.player_fleet_power() * strength_ratio

        def type_power(ship_type):
            stats = SHIP_CLASSES[ship_type]
            return self.vessel_combat_power(stats["hull"], stats["guns"])

        selected_types = [self.rng.choice(ship_types) for _ in range(minimum_ships)]
        selected_power = sum(type_power(ship_type) for ship_type in selected_types)
        strongest_type = max(ship_types, key=type_power)
        while selected_power < target_power and len(selected_types) < maximum_ships:
            selected_types.append(strongest_type)
            selected_power += type_power(strongest_type)
        while selected_power < target_power and len(selected_types) < hard_maximum:
            selected_types.append(strongest_type)
            selected_power += type_power(strongest_type)

        fleet_id = f"event-{event_id}-{trigger_count}-{action_index}-{fleet_serial}"
        spawn_distance = max(1000.0, float(action.get("spawn_distance", 2200.0)))
        occupied = [ship for ship in self.pirates if not ship.dead]
        occupied.extend(ship for ship in self.traffic_ships if ship.hull > 0)
        occupied.extend(ship for ship in self.fleet if ship.hull > 0)
        land_polygons = self.collision_land_polygons()
        spawned = []

        for index, ship_type in enumerate(selected_types):
            position = self.event_spawn_position(
                index,
                len(selected_types),
                spawn_distance,
                occupied,
                land_polygons,
            )
            if position is None:
                continue
            x, y = position
            stats = SHIP_CLASSES[ship_type]
            hull = max(1, int(stats["hull"]))
            gun_count = max(1, int(stats["guns"]))
            name_pool = action.get("ship_names", [])
            if index < len(name_pool):
                name = str(name_pool[index])
            else:
                name = f"{fleet_name} — {ship_type} {index + 1}"
            heading = math.degrees(math.atan2(self.ship_y - y, self.ship_x - x)) % 360.0
            pirate = PirateShip(
                name=name,
                x=x,
                y=y,
                heading=heading,
                hull=hull,
                max_hull=hull,
                side_choice=self.rng.choice([-1, 1]),
                wander=self.rng.random() * 6.0,
                objective_target=False,
                ship_type=ship_type,
                fleet_id=fleet_id,
                commander_name=commander,
                formation_slot=index,
                fleet_morale=1.0,
                retreating=False,
                fleet_size=len(selected_types),
                player_attitude="hostile",
                player_provoked=True,
                event_id=event_id,
                gun_count=gun_count,
                reload_seconds=max(1.2, float(stats["reload"])),
            )
            self.pirates.append(pirate)
            occupied.append(pirate)
            spawned.append(pirate)

        if len(spawned) < minimum_ships:
            self.pirates = [ship for ship in self.pirates if ship not in spawned]
            self.add_journal(
                f"The {fleet_name} was sighted, but the available water could not hold its minimum formation."
            )
            self.toast_message(
                f"A lookout reports sails in the distance, but the {fleet_name} cannot form up here.",
                5.0,
            )
            return None

        target_power = max(target_power, 0.001)
        actual_power = sum(self.event_ship_power(ship) for ship in spawned)
        if actual_power < target_power:
            scale = target_power / max(0.001, actual_power)
            stat_scale = scale * scale
            for pirate in spawned:
                pirate.max_hull = max(1, int(math.ceil(pirate.max_hull * stat_scale)))
                pirate.hull = pirate.max_hull
                pirate.gun_count = max(1, int(math.ceil(pirate.gun_count * stat_scale)))
                pirate.reload_seconds = max(1.2, pirate.reload_seconds / math.sqrt(scale))
            actual_power = sum(self.event_ship_power(ship) for ship in spawned)

        for pirate in spawned:
            pirate.fleet_size = len(spawned)
        self.commander_fleet_state(fleet_id, commander, "pirate", len(spawned))
        self.ensure_commander_record(commander, "pirate")
        self.mission_event_fleet_strength[fleet_id] = {
            "target_power": round(target_power, 3),
            "spawned_power": round(actual_power, 3),
            "strength_ratio": round(actual_power / max(0.001, self.player_fleet_power()), 3),
            "ship_count": len(spawned),
        }
        return fleet_id

    def format_mission_event_text(self, value, values=None):
        try:
            return str(value).format(**(values or {}))
        except (KeyError, ValueError, IndexError):
            return str(value)

    def modify_event_cargo(self, good_id, amount):
        good = TRADE_GOODS_BY_ID.get(str(good_id))
        if good is None:
            return 0
        amount = int(amount)
        current = self.cargo_quantity(good["id"])
        if amount > 0:
            capacity = int(self.cargo_free_space() // good["space"])
            changed = min(amount, capacity)
            if changed:
                self.cargo_hold[good["id"]] = current + changed
                self.cargo_average_cost.setdefault(good["id"], 0.0)
        else:
            changed = min(current, abs(amount))
            remaining = current - changed
            if remaining:
                self.cargo_hold[good["id"]] = remaining
            else:
                self.cargo_hold.pop(good["id"], None)
                self.cargo_average_cost.pop(good["id"], None)
            changed = -changed
        return changed

    def execute_event_mission_state(self, action):
        mission = self.find_event_mission(action.get("mission", ""))
        new_state = str(action.get("state", "available"))
        if mission is None or new_state not in {"available", "active", "done", "failed"}:
            return
        if new_state == "active":
            if self.active_mission_id not in {None, mission.mission_id}:
                return
            self.active_mission_id = mission.mission_id
            self.mission_kills = 0
            self.mission_waypoint_index = 0
            self.mission_returning = False
            self.mission_completion_started = False
            self.mission_fleet_spawned = False
            if mission.objective_type == "kills":
                self.spawn_mission_fleet(mission)
        elif self.active_mission_id == mission.mission_id:
            self.active_mission_id = None
        self.mission_states[mission.mission_id] = new_state

    def execute_mission_event_actions(self, actions, event, state):
        for action_index, action in enumerate(actions):
            kind = action["type"]
            if kind == "spawn_fleet":
                state["fleet_serial"] += 1
                fleet_id = self.spawn_event_fleet(
                    action,
                    event["id"],
                    state["trigger_count"],
                    action_index,
                    state["fleet_serial"],
                )
                if not fleet_id:
                    state["spawn_failed"] = True
                    continue
                state["active_fleets"].append(fleet_id)
                info = self.mission_event_fleet_strength.get(fleet_id, {})
                values = {
                    "fleet": action.get("name", event["name"]),
                    "commander": action.get("commander", "the enemy commander"),
                    "ships": info.get("ship_count", 0),
                    "power_ratio": info.get("strength_ratio", 0.0),
                }
                announcement = action.get("announcement")
                if announcement:
                    message = self.format_mission_event_text(announcement, values)
                    self.toast_message(message, float(action.get("announcement_seconds", 8.0)))
                journal_entry = action.get("journal_entry")
                if journal_entry:
                    self.add_journal(self.format_mission_event_text(journal_entry, values))
            elif kind == "toast":
                self.toast_message(action.get("text", event["name"]), float(action.get("seconds", 4.0)))
            elif kind == "journal":
                self.add_journal(action.get("text", event["name"]))
            elif kind == "give_gold":
                requested = int(action.get("amount", 0))
                old_gold = self.gold
                self.gold = max(0, self.gold + requested)
                change = self.gold - old_gold
                if change:
                    label = "Received" if change > 0 else "Paid"
                    self.toast_message(f"{label} {abs(change)} gold.", 3.5)
            elif kind == "set_gold":
                self.gold = max(0, int(action.get("amount", 0)))
            elif kind == "set_flag":
                self.set_world_flag(action.get("key", ""), action.get("value", True))
            elif kind == "add_flag":
                key = str(action.get("key", ""))
                current = self.world_flags.get(key, 0)
                amount = action.get("amount", 0)
                updated = float(current) + float(amount)
                self.set_world_flag(key, int(updated) if updated.is_integer() else updated)
            elif kind == "remove_flag":
                self.world_flags.pop(str(action.get("key", "")), None)
            elif kind == "adjust_relation":
                self.adjust_faction_relation(
                    str(action.get("faction", "Independent")),
                    int(action.get("amount", 0)),
                    str(action.get("reason", event["name"])),
                )
            elif kind == "set_mission_state":
                self.execute_event_mission_state(action)
            elif kind == "schedule_event":
                self.schedule_mission_event(
                    str(action.get("event", "")),
                    action.get("delay"),
                    force=bool(action.get("force", False)),
                )
            elif kind == "enable_event":
                target = str(action.get("event", ""))
                target_state = self.mission_event_states.get(target)
                if target_state is not None:
                    target_state["enabled"] = True
                    if target_state["status"] in {"disabled", "completed"}:
                        target_state.update({
                            "status": "waiting",
                            "trigger_count": 0,
                            "active_fleets": [],
                            "remaining": None,
                            "cooldown_remaining": 0.0,
                            "conditions_met": False,
                            "resolution_pending": False,
                        })
            elif kind == "disable_event":
                target = str(action.get("event", ""))
                target_state = self.mission_event_states.get(target)
                if target_state is not None:
                    target_state["enabled"] = False
                    if target_state["status"] != "active":
                        target_state["status"] = "disabled"
            elif kind == "add_cargo":
                changed = self.modify_event_cargo(action.get("good", ""), abs(int(action.get("amount", 0))))
                if changed:
                    good = TRADE_GOODS_BY_ID[action["good"]]
                    self.toast_message(f"Recovered {changed} units of {good['name']}.", 3.5)
            elif kind == "remove_cargo":
                changed = self.modify_event_cargo(action.get("good", ""), -abs(int(action.get("amount", 0))))
                if changed:
                    good = TRADE_GOODS_BY_ID[action["good"]]
                    self.toast_message(f"Lost {abs(changed)} units of {good['name']}.", 3.5)
            elif kind == "retreat_fleet":
                target = str(action.get("event", event["id"]))
                for pirate in self.pirates:
                    if getattr(pirate, "event_id", "") == target and not pirate.dead:
                        pirate.retreating = True
                        heading = math.degrees(math.atan2(pirate.y - self.ship_y, pirate.x - self.ship_x))
                        pirate.heading = heading % 360.0

    def schedule_mission_event(self, event_id, delay=None, force=False):
        event = next((item for item in self.mission_events if item["id"] == event_id), None)
        state = self.mission_event_states.get(event_id)
        if event is None or state is None or not state.get("enabled", True):
            return False
        if state["status"] == "active":
            return False
        if state["status"] in {"completed", "disabled"} and not force:
            return False
        if force:
            state["trigger_count"] = 0
            state["active_fleets"] = []
            state["cooldown_remaining"] = 0.0
            state["resolution_pending"] = False
            state["conditions_met"] = False
        if isinstance(delay, dict):
            minimum = max(0.0, float(delay.get("minimum", delay.get("min", 0.0))))
            maximum = max(minimum, float(delay.get("maximum", delay.get("max", minimum))))
            remaining = self.rng.uniform(minimum, maximum)
        elif delay is None:
            remaining = self.rng.uniform(event["delay"]["minimum"], event["delay"]["maximum"])
        else:
            remaining = max(0.0, float(delay))
        state["status"] = "scheduled"
        state["remaining"] = remaining
        state["conditions_met"] = True
        state["spawn_failed"] = False
        return True

    def finalize_mission_event(self, event, state):
        state["resolution_pending"] = False
        if state["status"] == "scheduled":
            return
        if not state.get("enabled", event["enabled"]):
            state["status"] = "disabled"
        elif event["repeatable"] and (not event["max_triggers"] or state["trigger_count"] < event["max_triggers"]):
            state["status"] = "cooldown" if state["cooldown_remaining"] > 0 else "waiting"
        else:
            state["status"] = "completed"

    def finish_mission_event(self, event, state, outcome):
        state["active_fleets"] = []
        state["remaining"] = None
        state["cooldown_remaining"] = event["cooldown_seconds"]
        state["last_outcome"] = outcome
        state["conditions_met"] = False
        state["random_rolls"] = {}
        if state["resolution_pending"]:
            self.finalize_mission_event(event, state)
            return
        actions = event["on_repelled"] if outcome == "repelled" else event["on_complete"]
        self.execute_mission_event_actions(actions, event, state)
        if state["active_fleets"]:
            state["resolution_pending"] = True
            state["status"] = "active"
            return
        self.finalize_mission_event(event, state)

    def update_mission_event_encounters(self, event, state):
        fleet_ids = set(state.get("active_fleets", []))
        if not fleet_ids:
            self.finish_mission_event(event, state, "destroyed")
            return
        vessels = [ship for ship in self.pirates if getattr(ship, "fleet_id", "") in fleet_ids]
        living = [ship for ship in vessels if not ship.dead and ship.hull > 0]
        if living and not all(ship.retreating for ship in living):
            return
        outcome = "repelled" if living else "destroyed"
        if outcome == "repelled":
            self.add_journal(f"The surviving ships of {event['name']} have withdrawn from the battle.")
            self.toast_message(f"The {event['name']} has been driven off.", 5.0)
        else:
            self.add_journal(f"The {event['name']} has been destroyed.")
            self.toast_message(f"The {event['name']} has been destroyed.", 5.0)
        self.finish_mission_event(event, state, outcome)

    def update_mission_events(self, dt):
        for event in self.mission_events:
            state = self.mission_event_states[event["id"]]
            if state["status"] == "active":
                self.update_mission_event_encounters(event, state)
                continue
            if not state.get("enabled", event["enabled"]) or state["status"] in {"disabled", "completed"}:
                continue
            if state["status"] == "cooldown":
                state["cooldown_remaining"] = max(0.0, state["cooldown_remaining"] - dt)
                if state["cooldown_remaining"] <= 0.0:
                    state["status"] = "waiting"
                    state["conditions_met"] = False
                continue
            if state["status"] == "scheduled":
                cancel_if = event.get("cancel_if")
                if cancel_if and self.evaluate_mission_event_condition(cancel_if):
                    state["status"] = "waiting"
                    state["remaining"] = None
                    state["conditions_met"] = False
                    state["random_rolls"] = {}
                    continue
                if event["pause_while_docked"] and self.docked_port:
                    continue
                state["remaining"] = max(0.0, float(state.get("remaining") or 0.0) - dt)
                if state["remaining"] > 0.0:
                    continue
                state["trigger_count"] += 1
                state["spawn_failed"] = False
                self.execute_mission_event_actions(event["actions"], event, state)
                if state["active_fleets"]:
                    state["status"] = "active"
                    state["remaining"] = None
                elif state["spawn_failed"]:
                    state["trigger_count"] = max(0, state["trigger_count"] - 1)
                    state["status"] = "scheduled"
                    state["remaining"] = 20.0
                else:
                    self.finish_mission_event(event, state, "destroyed")
                continue
            if state["status"] == "waiting":
                maximum = event["max_triggers"]
                if maximum and state["trigger_count"] >= maximum:
                    state["status"] = "completed"
                    continue
                eligible = self.evaluate_mission_event_condition(event["trigger"], ignore_random=True)
                if not eligible:
                    state["conditions_met"] = False
                    state["random_rolls"] = {}
                    continue
                if state["conditions_met"]:
                    continue
                state["conditions_met"] = True
                state["random_rolls"] = {}
                if self.evaluate_mission_event_condition(event["trigger"], state["random_rolls"]):
                    self.schedule_mission_event(event["id"])
