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
        available = [
            mission for mission in self.missions
            if mission.category != "intro"
            and self.mission_state(mission) == "available"
            and mission.source == self.docked_port
            and self.requirements_met(mission)
        ]
        priority = {"main": 0, "side": 1}
        return sorted(available, key=lambda mission: (priority.get(mission.category, 2), mission.name))

    def available_intro_mission_at_port(self):
        if self.active_mission_id is not None or self.docked_port is None:
            return None
        return next((
            mission for mission in self.missions
            if mission.category == "intro"
            and mission.source == self.docked_port
            and self.mission_state(mission) == "available"
            and self.requirements_met(mission)
        ), None)

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
            if any(point_in_polygon((x, y), polygon) for polygon in polygons):
                continue
            if not self.reef_clear_at(x, y, 100.0):
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
                ship_type=self.rng.choice(["Cutter", "Schooner", "Brigantine", "Frigate"]),
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

    def mission_route_stops(self, mission):
        """Return the complete ordered list of ports for a multi-call voyage."""
        return [mission.source] + [stop.port for stop in getattr(mission, "waypoints", [])] + [mission.destination]

    def mission_route_distance(self, mission):
        source = self.ports_by_name.get(mission.source)
        destination = self.ports_by_name.get(mission.destination)
        if source is None or destination is None:
            return 0.0
        if mission.objective_type == "kills" and mission.battlefield_x is not None and mission.battlefield_y is not None:
            first_leg = math.hypot(mission.battlefield_x - source.x, mission.battlefield_y - source.y)
            second_leg = math.hypot(destination.x - mission.battlefield_x, destination.y - mission.battlefield_y)
            return first_leg + second_leg
        if getattr(mission, "waypoints", None):
            ports = [self.ports_by_name.get(name) for name in self.mission_route_stops(mission)]
            if any(port is None for port in ports):
                return 0.0
            return sum(math.hypot(b.x - a.x, b.y - a.y) for a, b in zip(ports, ports[1:]))
        return math.hypot(destination.x - source.x, destination.y - source.y)

    def mission_route_description(self, distance):
        if distance < 1500:
            return "a short island passage"
        if distance < 3000:
            return "a neighbouring-island crossing"
        if distance < 4500:
            return "a regional passage"
        if distance < 7000:
            return "a long inter-island voyage"
        if distance < 12000:
            return "an extended open-water voyage"
        return "a major ocean crossing"

    def mission_route_brief(self, mission):
        distance = self.mission_route_distance(mission)
        description = self.mission_route_description(distance)
        route = f"The full chart distance is about {distance:,.0f} chart units: {description}. Allow extra time to skirt reefs and shoals."
        if getattr(mission, "waypoints", None):
            stops = " → ".join(self.mission_route_stops(mission))
            calls = "; ".join(f"{stop.port}: {stop.objective}" for stop in mission.waypoints)
            return f"Route: {stops}. {route} Required calls: {calls}. Each call must be completed in order before the final destination will accept the voyage."
        if mission.objective_type == "kills" and mission.battlefield:
            return f"Route note: {route} The course runs via {mission.battlefield}, then on to {mission.destination}."
        return f"Route note: {route} Your destination is {mission.destination}."

    def mission_navigation_target(self, mission=None):
        mission = mission or self.active_mission()
        if mission is None:
            return None
        if mission.objective_type == "kills" and not self.mission_returning:
            if mission.battlefield_x is not None and mission.battlefield_y is not None:
                return mission.battlefield, mission.battlefield_x, mission.battlefield_y, "battlefield"
            return mission.battlefield or "Enemy waters", self.ship_x, self.ship_y, "battlefield"
        waypoints = getattr(mission, "waypoints", [])
        waypoint_index = max(0, int(getattr(self, "mission_waypoint_index", 0)))
        if waypoint_index < len(waypoints):
            stop = waypoints[waypoint_index]
            port = self.ports_by_name.get(stop.port)
            if port:
                return port.name, port.x, port.y, "waypoint"
        port = self.ports_by_name.get(mission.destination)
        if port:
            return port.name, port.x, port.y, "port"
        return None

    def navigation_target(self):
        story_target = self.mission_navigation_target()
        if story_target:
            return story_target
        candidates = []
        for job in getattr(self, "active_day_jobs", []):
            if job.stage == "rescue" and not job.rescued and job.target_x is not None and job.target_y is not None:
                x, y = job.target_x, job.target_y
                label = f"Rescue · {job.destination}"
                kind = "rescue"
            else:
                port = self.ports_by_name.get(job.destination)
                if port is None:
                    continue
                x, y = port.x, port.y
                label = job.destination
                kind = "day_job"
            candidates.append((math.hypot(x - self.ship_x, y - self.ship_y), label, x, y, kind))
        if not candidates:
            return None
        _, label, x, y, kind = min(candidates, key=lambda entry: entry[0])
        return label, x, y, kind

    def mission_guidance_text(self, mission=None):
        mission = mission or self.active_mission()
        if mission is None:
            return ""
        if mission.objective_type == "kills":
            if self.mission_returning:
                return f"RETURN TO {mission.destination.upper()}  •  berth there for your debrief"
            return f"SAIL TO {mission.battlefield.upper()}  •  SINK {self.mission_kills}/{mission.objective_count} TARGET SHIPS"
        waypoints = getattr(mission, "waypoints", [])
        waypoint_index = max(0, int(getattr(self, "mission_waypoint_index", 0)))
        if waypoint_index < len(waypoints):
            stop = waypoints[waypoint_index]
            return f"SAIL TO {stop.port.upper()}  •  {stop.objective.upper()}  •  PORT CALL {waypoint_index + 1}/{len(waypoints)}"
        if waypoints:
            return f"ALL PORT CALLS COMPLETE  •  SAIL TO {mission.destination.upper()} FOR FINAL DELIVERY"
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
        self.mission_waypoint_index = 0
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
                f"Voyage accepted: {mission.name}. {self.mission_route_brief(mission)}",
                6.0,
            )
        else:
            self.toast_message(f"Voyage accepted: {mission.name}. {self.mission_route_brief(mission)}", 5.0)

    def start_conversation(self, mission, event, on_end=None):
        nodes = mission.sections.get(event, []) if mission else []
        if not nodes:
            if on_end:
                on_end()
            return
        self.dialogue_speaker = mission.section_speakers.get(event, mission.speaker) if mission else "Harbourmaster"
        self.conversation = Conversation(self, mission, nodes, on_end)

    def story_lead_after(self, completed_mission):
        if completed_mission.category != "main":
            return ""
        for candidate in self.missions:
            if candidate.category != "main" or self.mission_state(candidate) != "available":
                continue
            if candidate.source == completed_mission.destination:
                continue
            required_titles = {item.removesuffix(": done").strip() for item in candidate.requires_done}
            if completed_mission.title not in required_titles:
                continue
            other_requirements_met = True
            for required_title in required_titles - {completed_mission.title}:
                required_mission = next((item for item in self.missions if item.title == required_title or item.name == required_title), None)
                if required_mission is None or self.mission_state(required_mission) != "done":
                    other_requirements_met = False
                    break
            if not other_requirements_met:
                continue
            if candidate.lead:
                return candidate.lead
            port = self.ports_by_name.get(candidate.source)
            detail = port.description if port else "a busy harbour on the trade routes"
            return (
                f"Before you go, {candidate.speaker} has been asking after you at {candidate.source}. "
                f"{detail} It is not urgent; there are other ports and other work between here and there."
            )
        return ""

    def start_completion_conversation(self, mission, on_end):
        nodes = list(mission.sections.get("complete", []))
        lead = self.story_lead_after(mission)
        if lead:
            nodes.append(TextNode(lead))
            self.add_journal(f"A new lead: {lead}")
        self.dialogue_speaker = mission.section_speakers.get("complete", mission.speaker)
        self.conversation = Conversation(self, mission, nodes, on_end)

    def start_custom_conversation(self, speaker, nodes):
        self.dialogue_speaker = speaker
        self.conversation = Conversation(self, None, nodes)

    def open_port_talk(self):
        available = self.available_missions_at_port()
        intro = self.available_intro_mission_at_port()
        options = []
        if intro:
            options.append(OptionNode(
                f"Special commission: {intro.name} — {intro.description}",
                [CommandNode("intro_mission")],
            ))
        for mission in available:
            route = " → ".join([mission.source] + [stop.port for stop in getattr(mission, "waypoints", [])] + [mission.destination])
            options.append(OptionNode(
                f"{mission.name} — {route} — {mission.reward} gold. {mission.description}",
                [CommandNode("mission_offer", mission.mission_id)],
            ))
        if options:
            options.append(OptionNode("No, thank you.", [CommandNode("close")]))
            nodes = [TextNode("The harbourmaster opens the special commissions ledger. These are personal contracts and unusual assignments, separate from the ordinary work posted on the job board."), ChoiceNode(options)]
        else:
            nodes = [TextNode("The harbourmaster checks the special commissions ledger. There are no special assignments available here at present. Ordinary cargo and local work can be found on the job board.")]
        self.start_custom_conversation("Harbourmaster", nodes)

    def open_intro_mission_offer(self):
        mission = self.available_intro_mission_at_port()
        if mission is None:
            self.start_custom_conversation("Harbour office", [TextNode("Captain Ward has already made his farewells. His advice is in your journal if you need a reminder.")])
            return
        self.start_conversation(mission, "offer")

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
                elif getattr(active, "waypoints", []):
                    target = self.mission_navigation_target(active)
                    next_port = target[0] if target else active.destination
                    message = f"The harbourmaster taps the marked route. \"Your next required call is {next_port}, captain. {self.mission_guidance_text(active)}. The remaining calls must be made in order before {active.destination}.\""
                else:
                    message = f"The harbourmaster taps your chart. \"Your business is not finished. Sail to {active.destination}, captain. Follow the gold route on your chart.\""
            else:
                message = "The harbourmaster turns a page in the ledger. \"No new work just now. Check the notice board another day, or listen for news in the taverns.\""
            self.start_custom_conversation("Harbourmaster", [TextNode(message)])
            return
        if len(available) == 1:
            self.start_conversation(available[0], "offer")
            return
        options = [
            OptionNode(
                f"[{('SIDE ADVENTURE' if mission.category == 'side' else 'MAIN STORY')}] {mission.name}  —  {' → '.join([mission.source] + [stop.port for stop in getattr(mission, 'waypoints', [])] + [mission.destination])}  —  {mission.reward} gold  —  {mission.description}",
                [CommandNode("mission_offer", mission.mission_id)],
            )
            for mission in available
        ]
        options.append(OptionNode("Not today. I will look around the harbour first.", [CommandNode("close")]))
        self.start_custom_conversation(
            "Harbourmaster",
            [
                TextNode("The harbourmaster opens the ledger. There are several matters being discussed around the islands; some are urgent, others can wait until you have a mind for them."),
                ChoiceNode(options),
            ],
        )

    def show_mission_offer_by_id(self, mission_id):
        mission = next((item for item in self.available_missions_at_port() if item.mission_id == mission_id), None)
        if mission is None:
            self.toast_message("That posting has already been taken or is no longer available.", 3.0)
            return
        self.start_conversation(mission, "offer")

    def open_curiosities(self):
        port = self.docked_port
        options = []
        if port == "Wreckers' Moon":
            options = [
                OptionNode("Buy a salvaged brass diving bell (unique keepsake, 320 gold).", [CommandNode("purchase_unique", "Salvager's Diving Bell|320|A small brass diving bell recovered from a wreck.")]),
                OptionNode("Hear the reef pilot's secret passage through the shoals.", [CommandNode("learn_secret", "Wreckers' Moon|The reef pilot marks a safe passage through the outer shoals in your journal.")]),
            ]
            speaker = "Marda Quill, salvage broker"
        elif port == "Bellweather Cay":
            options = [
                OptionNode("Buy an astronomer's tideglass (unique keepsake, 480 gold).", [CommandNode("purchase_unique", "Bellweather Tideglass|480|A finely etched instrument for reading the height and turn of the tide.")]),
                OptionNode("Ask the observatory keeper about the strange lights.", [CommandNode("learn_secret", "Bellweather Cay|The observatory records describe blue lights moving against the current near the Drowned Kingdom.")]),
            ]
            speaker = "Keeper Orlan"
        elif port == "San Aurelio":
            options = [
                OptionNode("Buy a sealed monastery folio (unique keepsake, 600 gold).", [CommandNode("purchase_unique", "Monastery Folio|600|A sealed folio containing fragments of an old sea chronicle.")]),
                OptionNode("Ask who has been buying old charts.", [CommandNode("learn_secret", "San Aurelio|A discreet buyer named Doctor Inez Salvatierra has been collecting charts of the western shoals.")]),
            ]
            speaker = "Brother Mateo"
        elif port == "Gallows Key":
            options = [
                OptionNode("Inspect the captain's too-good-to-be-true 'royal' compass.", [CommandNode("inspect_scam", "Royal Compass|260|The brass is plated and the needle is fixed; the seller hopes you will not notice.")]),
                OptionNode("Buy a genuine privateer's signal book (unique keepsake, 390 gold).", [CommandNode("purchase_unique", "Privateer's Signal Book|390|A coded signal book used by a long-dead privateer squadron.")]),
                OptionNode("Ask which captains have been meeting here.", [CommandNode("learn_secret", "Gallows Key|Three former fleet officers have been meeting at Gallows Key to discuss the blue lights and a lost expedition.")]),
            ]
            speaker = "Silas Rook, beachcomber"
        else:
            options = [
                OptionNode("Ask after a traveller called Doctor Inez Salvatierra.", [CommandNode("learn_secret", f"{port}|A travelling scholar named Doctor Inez Salvatierra has been asking about your voyages and the old western charts.")]),
                OptionNode("Ask for a rumour worth remembering.", [CommandNode("learn_secret", f"{port}|A quay-side rumour mentions lights at sea and a bell heard beneath the water on windless nights.")]),
            ]
            speaker = "A familiar face at the quay"
        options.append(OptionNode("Leave the matter for another time.", [CommandNode("close")]))
        intro = {
            "Wreckers' Moon": "Marda Quill has a table of salvaged curiosities. She insists every item has a story, though not every story is true.",
            "Bellweather Cay": "The observatory keeper offers a look at instruments and tide records. The charts on his wall are covered in careful annotations.",
            "San Aurelio": "A monk and a travelling scholar are speaking in low voices beside the monastery gate.",
            "Gallows Key": "A beachcomber has laid out several objects on a blanket. One compass looks suspiciously new for something supposedly recovered from a Spanish wreck.",
        }.get(port, "A sailor at the quay lowers their voice and offers a little local knowledge.")
        self.start_custom_conversation(speaker, [TextNode(intro), ChoiceNode(options)])

    def purchase_unique_offer(self, payload):
        parts = payload.split("|", 2)
        if len(parts) < 2:
            return
        item, price_text = parts[:2]
        description = parts[2] if len(parts) > 2 else "A rare object from the islands."
        price = max(0, int(price_text))
        if item in getattr(self, "unique_items", []):
            self.toast_message(f"You already own {item}.", 3.5)
            return
        if self.gold < price:
            self.toast_message(f"You need {price} gold to buy {item}; you have {self.gold}.", 4.0)
            return
        self.gold -= price
        self.unique_items = getattr(self, "unique_items", [])
        self.unique_items.append(item)
        self.relics.append(item)
        self.add_journal(f"Purchased {item} for {price} gold. {description}")
        self.toast_message(f"Purchased {item} for {price} gold.", 4.0)

    def inspect_scam_offer(self, payload):
        parts = payload.split("|", 2)
        item = parts[0] if parts else "the suspicious object"
        description = parts[2] if len(parts) > 2 else "The offer is not what it seems."
        if self.rng.random() < 0.82:
            self.add_journal(f"Exposed a harbour scam: {item}. {description}")
            self.toast_message(f"You spot the fraud before paying. The seller hurriedly packs up.", 4.5)
        else:
            loss = min(self.gold, 90)
            self.gold -= loss
            self.add_journal(f"A confidence trickster distracted you while you inspected {item}; {loss} gold went missing.")
            self.toast_message(f"The seller's accomplice lifts {loss} gold while you inspect the goods.", 4.5)

    def learn_local_secret(self, payload):
        parts = payload.split("|", 1)
        place, secret = parts if len(parts) == 2 else ("A harbour", payload)
        entry = f"Local knowledge from {place}: {secret}"
        self.add_journal(entry)
        self.toast_message("You have learned something worth keeping. Check your journal.", 4.0)

    def show_port_news(self):
        message = self.news_by_port.get(self.docked_port, "The harbour is full of rumours, though none worth repeating.")
        self.start_custom_conversation("A sailor at the quay", [TextNode(message)])

    def complete_mission(self, mission):
        self.reward_mission_diplomacy(mission)
        self.mission_states[mission.mission_id] = "done"
        self.gold += mission.reward
        self.add_journal(f"Completed {mission.name}. Received {mission.reward} gold.")
        self.mission_result_title = mission.name
        self.mission_result_reward = mission.reward
        self.mission_result_timer = 15.0
        self.toast_message(f"VOYAGE COMPLETE: {mission.name}  •  +{mission.reward} gold", 8.0)
        self.active_mission_id = None
        self.mission_kills = 0
        self.mission_waypoint_index = 0
        self.mission_returning = False
        self.mission_completion_started = False
        self.mission_fleet_spawned = False
        self.pirates = [
            pirate for pirate in self.pirates
            if pirate.mission_id != mission.mission_id or not pirate.objective_target
        ]

    def trigger_port_visit(self, port):
        mission = self.active_mission()
        if not mission:
            return

        waypoints = getattr(mission, "waypoints", [])
        waypoint_index = max(0, int(getattr(self, "mission_waypoint_index", 0)))
        if waypoints and mission.objective_type != "kills" and waypoint_index < len(waypoints):
            expected = waypoints[waypoint_index]
            if port.name != expected.port:
                if port.name == mission.destination:
                    self.toast_message(
                        f"You have reached {mission.destination}, but the passengers still need their call at {expected.port}. Return to the marked route first.",
                        5.5,
                    )
                return

            self.mission_waypoint_index = waypoint_index + 1
            entry = f"Voyage waypoint {self.mission_waypoint_index}/{len(waypoints)} completed at {port.name}: {expected.objective}."
            self.add_journal(entry)
            self.toast_message(f"PORT CALL COMPLETE · {port.name}  ({self.mission_waypoint_index}/{len(waypoints)})", 5.0)
            event = f"waypoint_{waypoint_index + 1}"
            if mission.sections.get(event):
                self.start_conversation(mission, event)
            return

        if mission.destination != port.name:
            return
        if mission.objective_type == "kills" and not self.mission_returning:
            return
        if self.mission_completion_started:
            return
        self.mission_completion_started = True

        def complete_after_visit():
            self.start_completion_conversation(mission, lambda: self.complete_mission(mission))

        self.start_conversation(mission, "visit", complete_after_visit)

    def register_pirate_sunk(self, pirate, by_player=False):
        if by_player:
            self.record_player_sunk_pirate(pirate)
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
        if self.port_attitude(port) == "HOSTILE":
            self.toast_message(f"The harbour guns of {port.name} refuse your entry. Press I near the harbour to seek safe conduct.", 5.0)
            return False

        slot = self.nearest_available_harbour_slot(port, self.ship_x, self.ship_y)
        if slot is None:
            self.toast_message(f"Every berth at {port.name} is occupied. Circle the harbour and try again shortly.", 4.5)
            return False

        self.player_berth_slot = slot
        self.last_docked_port_slot = slot
        self.docked_port = port.name
        self.last_docked_port = port.name
        if hasattr(self, "set_world_flag"):
            self.set_world_flag(f"visited_port:{port.name}", True)
            visit_key = f"port_visits:{port.name}"
            self.set_world_flag(visit_key, int(self.world_flags.get(visit_key, 0)) + 1)
        self.oars_deployed = False
        self.ship_heading = port.exit_heading
        self.ship_x, self.ship_y = self.harbour_berth_position(port, slot)
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        self.near_port = port
        self.toast_message(f"Made fast at {port.name}, berth {slot + 1}. Q: speak to the harbourmaster.", 4.0)
        self.trigger_port_visit(port)
        self.complete_day_job_at_port(port)
        try:
            self.save_game(AUTOSAVE_SLOT_NAME, notify=False)
            self.toast_message(f"Made fast at {port.name}, berth {slot + 1}. Autosaved.", 3.8)
        except (OSError, ValueError) as error:
            self.toast_message(f"Docked at {port.name}, but autosave failed: {error}", 5.0)
        if hasattr(self, "open_port_menu"):
            self.open_port_menu("overview")
        return True

    def undock(self):
        port = self.ports_by_name[self.docked_port]
        self.ship_heading = port.exit_heading
        if hasattr(self, "close_port_menu"):
            self.close_port_menu()
        self.docked_port = None
        self.toast_message("Cast off! Keep the wind in your sails and the rocks off your keel.", 3.0)
