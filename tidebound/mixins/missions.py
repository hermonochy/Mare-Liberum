from ..common import *


class MissionMixin:
    def add_journal(self, entry):
        if entry and entry not in self.journal:
            self.journal.append(entry)
            self.journal = self.journal[-24:]

    def active_mission(self):
        if self.active_mission_id is None:
            return None
        return next((mission for mission in self.missions if mission.mission_id == self.active_mission_id), None)

    def mission_state(self, mission):
        return self.mission_states.get(mission.mission_id, "available")

    def requirements_met(self, mission):
        for requirement in mission.requires_done:
            target = requirement.removesuffix(": done").strip()
            matching = next((item for item in self.missions if item.title == target or item.name == target), None)
            if matching is None or self.mission_state(matching) != "done":
                return False
        return True

    def available_missions_at_port(self):
        if self.active_mission_id is not None or self.docked_port is None:
            return []
        return [
            mission for mission in self.missions
            if self.mission_state(mission) == "available"
            and mission.source == self.docked_port
            and self.requirements_met(mission)
        ]

    def mission_spawn_position(self, mission, index, count):
        center_x = mission.battlefield_x
        center_y = mission.battlefield_y
        if center_x is None or center_y is None:
            angle = math.radians(self.ship_heading + 180.0)
            center_x = self.ship_x + math.cos(angle) * 720.0
            center_y = self.ship_y + math.sin(angle) * 720.0

        base_angle = math.tau * index / max(1, count)
        polygons = list(self.land) + [site.polygon for site in self.treasure_sites]
        for attempt in range(720):
            angle = base_angle + (attempt % 36) * math.tau / 36.0 + self.rng.uniform(-0.08, 0.08)
            radius = 125.0 + (attempt // 36) * 14.0
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            if not (55 <= x <= WORLD_WIDTH - 55 and 55 <= y <= WORLD_HEIGHT - 55):
                continue
            if any(point_in_polygon((x, y), polygon) for polygon in polygons):
                continue
            too_close_to_shore = False
            for polygon in polygons:
                _, distance = nearest_polygon_edge(x, y, polygon)
                if distance < 58:
                    too_close_to_shore = True
                    break
            if too_close_to_shore:
                continue
            if any(math.hypot(x - port.x, y - port.y) < 245 for port in self.ports):
                continue
            if any(not pirate.dead and math.hypot(x - pirate.x, y - pirate.y) < 76 for pirate in self.pirates):
                continue
            return x, y
        return None

    def spawn_mission_fleet(self, mission):
        existing = [
            pirate for pirate in self.pirates
            if not pirate.dead and pirate.mission_id == mission.mission_id and pirate.objective_target
        ]
        if len(existing) >= mission.objective_count:
            self.mission_fleet_spawned = True
            return
        names = list(mission.enemy_names)
        while len(names) < mission.objective_count:
            names.append(f"Vane's Raider {len(names) + 1}")
        names = names[:mission.objective_count]
        spawned = list(existing)
        for index in range(len(existing), len(names)):
            name = names[index]
            position = self.mission_spawn_position(mission, index, len(names))
            if position is None:
                continue
            x, y = position
            heading = math.degrees(math.atan2(self.ship_y - y, self.ship_x - x)) % 360.0
            hull = 7 if len(names) <= 3 else 8
            pirate = PirateShip(
                name,
                x,
                y,
                heading,
                hull=hull,
                max_hull=hull,
                side_choice=self.rng.choice([-1, 1]),
                wander=self.rng.random() * 6.0,
                mission_id=mission.mission_id,
                objective_target=True,
            )
            self.pirates.append(pirate)
            spawned.append(pirate)
        self.mission_fleet_spawned = len(spawned) == mission.objective_count
        if self.mission_fleet_spawned:
            self.toast_message(
                f"Enemy fleet sighted near {mission.battlefield}! {len(spawned)} named ships are on your chart.",
                6.0,
            )
            self.add_journal(f"Enemy fleet located near {mission.battlefield}: " + ", ".join(p.name for p in spawned) + ".")
        else:
            self.toast_message(
                f"Enemy fleet sighting near {mission.battlefield} is incomplete. Check the gold chart marker.",
                6.0,
            )
            self.add_journal(f"Warning: only {len(spawned)} of {mission.objective_count} mission ships were placed near {mission.battlefield}.")

    def mission_navigation_target(self, mission=None):
        mission = mission or self.active_mission()
        if mission is None:
            return None
        if mission.objective_type == "kills" and not self.mission_returning:
            if mission.battlefield_x is not None and mission.battlefield_y is not None:
                return mission.battlefield, mission.battlefield_x, mission.battlefield_y, "battlefield"
            return mission.battlefield or "Enemy waters", self.ship_x, self.ship_y, "battlefield"
        port = self.ports_by_name.get(mission.destination)
        if port:
            return port.name, port.x, port.y, "port"
        return None

    def mission_guidance_text(self, mission=None):
        mission = mission or self.active_mission()
        if mission is None:
            return ""
        if mission.objective_type == "kills":
            if self.mission_returning:
                return f"RETURN TO {mission.destination.upper()}  •  berth there for your debrief"
            return f"SAIL TO {mission.battlefield.upper()}  •  SINK {self.mission_kills}/{mission.objective_count} TARGET SHIPS"
        return f"SAIL TO {mission.destination.upper()}  •  follow the gold route on your chart"

    def accept_mission(self, mission):
        if mission is None:
            return
        if self.active_mission_id is not None:
            self.toast_message("You already have a voyage to finish.")
            return
        self.mission_states[mission.mission_id] = "active"
        self.active_mission_id = mission.mission_id
        self.mission_kills = 0
        self.mission_returning = False
        self.mission_completion_started = False
        self.mission_fleet_spawned = False
        self.mission_result_timer = 0.0
        self.add_journal(f"Accepted: {mission.name}. {mission.description}")
        for node in mission.sections.get("accept", []):
            if isinstance(node, CommandNode) and node.command == "log":
                self.add_journal(node.value)
        if mission.objective_type == "kills":
            self.spawn_mission_fleet(mission)
            self.toast_message(
                f"Voyage accepted: {mission.name}. Sail to {mission.battlefield}; the target fleet is marked on your chart.",
                6.0,
            )
        else:
            self.toast_message(f"Voyage accepted: {mission.name}. Sail to {mission.destination}; follow the gold route on your chart.", 5.0)

    def start_conversation(self, mission, event, on_end=None):
        nodes = mission.sections.get(event, []) if mission else []
        if not nodes:
            if on_end:
                on_end()
            return
        self.dialogue_speaker = mission.section_speakers.get(event, mission.speaker) if mission else "Harbourmaster"
        self.conversation = Conversation(self, mission, nodes, on_end)

    def start_custom_conversation(self, speaker, nodes):
        self.dialogue_speaker = speaker
        self.conversation = Conversation(self, None, nodes)

    def open_port_talk(self):
        greeting = self.port_greetings.get(self.docked_port, "A harbour official looks up as you enter.")
        nodes = [
            TextNode(greeting),
            ChoiceNode([
                self.make_option("Ask whether there is work for a captain.", "offers"),
                self.make_option("Look for ordinary day work on the notice board.", "day_jobs"),
                self.make_option("Ask for the latest harbour news.", "news"),
                self.make_option("Visit the shipwright and see the yard.", "shipyard"),
                self.make_option("Take my leave.", "close"),
            ]),
        ]
        self.start_custom_conversation("Harbour office", nodes)

    @staticmethod
    def make_option(text, command):
        return OptionNode(text, [CommandNode(command)])

    def open_mission_offer(self):
        available = self.available_missions_at_port()
        if not available:
            active = self.active_mission()
            if active:
                if active.objective_type == "kills":
                    if self.mission_returning:
                        message = (
                            f"The harbourmaster says, \"All {active.objective_count} target ships are down. "
                            f"Return to {active.destination} and make fast for your debrief, captain.\""
                        )
                    else:
                        message = (
                            f"The harbourmaster taps the chart. \"Your orders are to sail for {active.battlefield}. "
                            f"You have sunk {self.mission_kills} of {active.objective_count} named enemy ships. "
                            f"The gold marker shows the battle waters.\""
                        )
                else:
                    message = f"The harbourmaster taps your chart. \"Your business is not finished. Sail to {active.destination}, captain. Follow the gold route on your chart.\""
            else:
                message = "The harbourmaster turns a page in the ledger. \"No new work just now. Check the notice board another day, or listen for news in the taverns.\""
            self.start_custom_conversation("Harbourmaster", [TextNode(message)])
            return
        mission = available[0]
        self.start_conversation(mission, "offer")

    def show_port_news(self):
        message = self.news_by_port.get(self.docked_port, "The harbour is full of rumours, though none worth repeating.")
        self.start_custom_conversation("A sailor at the quay", [TextNode(message)])

    def complete_mission(self, mission):
        self.mission_states[mission.mission_id] = "done"
        self.gold += mission.reward
        self.add_journal(f"Completed {mission.name}. Received {mission.reward} gold.")
        self.mission_result_title = mission.name
        self.mission_result_reward = mission.reward
        self.mission_result_timer = 15.0
        self.toast_message(f"VOYAGE COMPLETE: {mission.name}  •  +{mission.reward} gold", 8.0)
        self.active_mission_id = None
        self.mission_kills = 0
        self.mission_returning = False
        self.mission_completion_started = False
        self.mission_fleet_spawned = False
        self.pirates = [
            pirate for pirate in self.pirates
            if pirate.mission_id != mission.mission_id or not pirate.objective_target
        ]

    def trigger_port_visit(self, port):
        mission = self.active_mission()
        if not mission or mission.destination != port.name:
            return
        if mission.objective_type == "kills" and not self.mission_returning:
            return
        if self.mission_completion_started:
            return
        self.mission_completion_started = True

        def complete_after_visit():
            self.start_conversation(mission, "complete", lambda: self.complete_mission(mission))

        self.start_conversation(mission, "visit", complete_after_visit)

    def register_pirate_sunk(self, pirate):
        self.gold += 65
        self.add_journal(f"Sank {pirate.name}. Salvaged 65 gold from the wreckage.")
        self.toast_message(f"{pirate.name} is going down! +65 gold", 3.6)
        mission = self.active_mission()
        if (
            mission
            and mission.objective_type == "kills"
            and pirate.objective_target
            and pirate.mission_id == mission.mission_id
            and not self.mission_returning
        ):
            self.mission_kills += 1
            self.toast_message(
                f"MISSION TARGET SUNK: {pirate.name}  •  {self.mission_kills}/{mission.objective_count}",
                4.0,
            )
            self.add_journal(f"Mission target destroyed: {pirate.name} ({self.mission_kills}/{mission.objective_count}).")
            if self.mission_kills >= mission.objective_count:
                self.mission_returning = True
                self.toast_message(
                    f"BATTLE OBJECTIVE COMPLETE! Return to {mission.destination} for your debrief and {mission.reward} gold reward.",
                    8.0,
                )
                self.add_journal(f"Battle objective complete. Return to {mission.destination} for the debrief and reward.")

    def dock(self, port):
        self.docked_port = port.name
        self.oars_deployed = False
        self.ship_heading = port.exit_heading
        self.ship_x = port.x
        self.ship_y = port.y
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.near_port = port
        self.toast_message(f"Made fast at {port.name}. Q: speak to the harbourmaster.", 4.0)
        self.trigger_port_visit(port)
        self.complete_day_job_at_port(port)

    def undock(self):
        port = self.ports_by_name[self.docked_port]
        self.ship_heading = port.exit_heading
        self.docked_port = None
        self.toast_message("Cast off! Keep the wind in your sails and the rocks off your keel.", 3.0)
