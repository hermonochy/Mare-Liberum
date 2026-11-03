from ..common import *


class DayJobsMixin:
    def initialise_day_jobs(self):
        self.day_job_offers = {}
        self.active_day_job = None
        self.day_job_serial = 1
        self.completed_day_jobs = 0

    def make_day_job(self, source_name):
        destinations = [port for port in self.ports if port.name != source_name]
        destination = self.rng.choice(destinations)
        source = self.ports_by_name[source_name]
        distance = math.hypot(destination.x - source.x, destination.y - source.y)
        kind = self.rng.choices(
            ["cargo", "letter", "passenger", "rescue"],
            weights=[34, 24, 24, 18],
            k=1,
        )[0]
        serial = self.day_job_serial
        self.day_job_serial += 1

        if kind == "cargo":
            goods = self.rng.choice(["coffee sacks", "sugar barrels", "indigo crates", "lime casks", "sailcloth bales", "salted fish"])
            amount = self.rng.randint(4, 9)
            reward = 38 + round(distance * 0.034) + self.rng.randint(0, 5)
            title = f"A Few Honest Barrels"
            speaker = self.rng.choice(["A merchant's factor", "The quay master", "A warehouse keeper"])
            offer_text = (
                f"A merchant's factor beckons you over. \"Nothing grand, captain. We have {amount} lots of {goods} "
                f"that need carrying to {destination.name}. The regular coaster is laid up for want of a mast, "
                f"and these goods are wanted before the next market day. No privateers, no secrets — just freight.\""
            )
            payload = f"{amount} lots of {goods}"
        elif kind == "letter":
            sender = self.rng.choice(["the parish clerk", "a ship's surgeon", "the harbour pilot", "a retired boatswain", "a merchant's widow"])
            recipient = self.rng.choice(["the customs clerk", "the apothecary", "the parish priest", "the harbour master", "the schoolmistress"])
            reward = 25 + round(distance * 0.023) + self.rng.randint(0, 4)
            title = "A Sealed Letter"
            speaker = "A local clerk"
            offer_text = (
                f"A local clerk holds out a small packet sealed with red wax. \"Would you carry this to {destination.name} "
                f"and put it into the hands of {recipient}? It is a letter from {sender}. Nothing dangerous, "
                f"I assure you, and certainly not for curious eyes. It should reach them before the week's end.\""
            )
            payload = f"a sealed letter for {recipient}"
        elif kind == "passenger":
            passenger = self.rng.choice(["a schoolmaster", "a cooper's apprentice", "a retired sailor", "a travelling midwife", "a quiet bookseller", "a young fiddler"])
            reward = 43 + round(distance * 0.029) + self.rng.randint(0, 5)
            title = "Passage for a Passenger"
            speaker = "A tavern keeper"
            offer_text = (
                f"The tavern keeper introduces you to {passenger} who needs passage to {destination.name}. "
                f"\"They have paid their fare and travel with one sea chest. A calm voyage is all they ask. "
                f"No need to hurry, and no need to go looking for trouble.\""
            )
            payload = passenger
        else:
            reward = 48 + round(distance * 0.028) + self.rng.randint(0, 5)
            title = "A Boat Adrift"
            speaker = "A fishing master"
            rescue_x, rescue_y = self.find_day_job_rescue_position(source_name, destination.name)
            offer_text = (
                f"A fishing master describes a small longboat seen drifting between {source_name} and {destination.name}. "
                f"\"There were people aboard, waving cloth for a signal. They may be sailors from a coaster that lost its way. "
                f"Find them, bring them aboard, and see them safely to {destination.name}. There is no call to fight anyone — "
                f"they simply need a hand.\""
            )
            payload = "a stranded crew"

        rescue_x = locals().get("rescue_x")
        rescue_y = locals().get("rescue_y")
        if kind == "rescue":
            objective = f"Find the drifting longboat, rescue the crew with R, then deliver them to {destination.name}."
        else:
            objective = f"Carry {payload} from {source_name} to {destination.name}."

        job = DayJob(
            job_id=f"day_job_{serial}",
            kind=kind,
            title=title,
            source=source_name,
            destination=destination.name,
            reward=int(reward),
            speaker=speaker,
            offer_text=offer_text,
            payload=payload,
            objective=objective,
            target_x=rescue_x,
            target_y=rescue_y,
        )
        return job

    def find_day_job_rescue_position(self, source_name, destination_name):
        source = self.ports_by_name[source_name]
        destination = self.ports_by_name[destination_name]
        dx = destination.x - source.x
        dy = destination.y - source.y
        length = max(1.0, math.hypot(dx, dy))
        perpendicular = (-dy / length, dx / length)
        candidates = []
        polygons = self.land + [site.polygon for site in self.treasure_sites]
        for fraction in (0.34, 0.46, 0.58, 0.68):
            base_x = source.x + dx * fraction
            base_y = source.y + dy * fraction
            for offset in (0, 130, -130, 250, -250, 370, -370):
                x = base_x + perpendicular[0] * offset
                y = base_y + perpendicular[1] * offset
                if any(point_in_polygon((x, y), polygon) for polygon in polygons):
                    continue
                if math.hypot(x - source.x, y - source.y) < 250:
                    continue
                if math.hypot(x - destination.x, y - destination.y) < 250:
                    continue
                candidates.append((x, y))
        if candidates:
            return self.rng.choice(candidates)
        return (source.x + dx * 0.5, source.y + dy * 0.5)

    def open_day_job_board(self):
        if not self.docked_port:
            self.toast_message("The day-work board hangs beside the harbour office. Come ashore first.", 3.0)
            return
        if self.active_day_job:
            job = self.active_day_job
            message = f"The clerk checks the ledger. \"You already have a small job aboard, captain: {job.title}. {self.day_job_objective()} Finish that run before taking another.\""
            self.start_custom_conversation("Harbour clerk", [TextNode(message)])
            return
        offer = self.day_job_offers.get(self.docked_port)
        if offer is None:
            offer = self.make_day_job(self.docked_port)
            self.day_job_offers[self.docked_port] = offer
        destination_text = f"The destination is {offer.destination}. The agreed pay is {offer.reward} pieces of eight."
        nodes = [
            TextNode(offer.offer_text),
            TextNode(destination_text + " The work is ordinary harbour business: no bounty, no battle, and no grand promises."),
            ChoiceNode([
                OptionNode("Accept the work.", [CommandNode("accept_day_job")]),
                OptionNode("Decline for now. Leave the offer on the board.", [CommandNode("decline_day_job")]),
            ]),
        ]
        self.start_custom_conversation(offer.speaker, nodes)

    def accept_day_job(self):
        if self.active_day_job:
            self.toast_message("Finish your current day job before taking another.", 3.0)
            return
        if not self.docked_port:
            self.toast_message("You must be in port to accept harbour work.", 2.5)
            return
        job = self.day_job_offers.get(self.docked_port)
        if job is None:
            self.toast_message("That offer has been taken off the board.", 2.5)
            return
        self.active_day_job = job
        job.stage = "rescue" if job.kind == "rescue" else "deliver"
        self.day_job_offers.pop(self.docked_port, None)
        self.add_journal(f"Accepted day work: {job.title}. {job.objective}")
        self.toast_message(f"Day work accepted: {job.title}. Destination: {job.destination}.", 4.0)

    def day_job_objective(self):
        job = self.active_day_job
        if not job:
            return "No day work accepted."
        if job.kind == "rescue" and not job.rescued:
            return "Find the drifting longboat and press R when close enough."
        return f"Deliver {job.payload} to {job.destination}."

    def day_job_rescue_distance(self):
        job = self.active_day_job
        if not job or job.kind != "rescue" or job.rescued or job.target_x is None:
            return float("inf")
        return math.hypot(self.ship_x - job.target_x, self.ship_y - job.target_y)

    def try_interact_day_job(self):
        job = self.active_day_job
        if not job or job.kind != "rescue" or job.rescued:
            return False
        distance = self.day_job_rescue_distance()
        if distance > 135:
            return False
        job.rescued = True
        job.stage = "deliver"
        self.add_journal(f"Recovered {job.payload}. Take them safely to {job.destination}.")
        self.toast_message(f"The stranded crew are aboard. Make for {job.destination}.", 4.2)
        return True

    def draw_day_job_target(self):
        job = self.active_day_job
        if not job or job.kind != "rescue" or job.rescued or job.target_x is None:
            return
        center = self.world_to_screen(job.target_x, job.target_y)
        pygame.draw.circle(self.screen, (244, 211, 142), center, max(12, int(18 * self.camera_zoom)), 2)
        pygame.draw.line(self.screen, (246, 224, 180), (center[0] - 18, center[1] + 5), (center[0] + 18, center[1] + 5), max(2, int(3 * self.camera_zoom)))
        pygame.draw.line(self.screen, (225, 235, 226), (center[0], center[1] + 4), (center[0], center[1] - 19), max(2, int(2 * self.camera_zoom)))
        pygame.draw.polygon(self.screen, (173, 57, 42), [center, (center[0] + 15, center[1] - 15), (center[0], center[1] - 12)])
        if self.camera_zoom > 0.55:
            label = self.tiny_font.render("STRANDED CREW", True, (255, 235, 191))
            rect = label.get_rect(center=(center[0], center[1] - 34))
            pygame.draw.rect(self.screen, (40, 30, 22), rect.inflate(10, 5), border_radius=3)
            self.screen.blit(label, rect)

    def complete_day_job_at_port(self, port):
        job = self.active_day_job
        if not job or job.stage != "deliver" or port.name != job.destination:
            return
        self.gold += job.reward
        self.completed_day_jobs += 1
        self.add_journal(f"Completed day work: {job.title}. Earned {job.reward} gold.")
        self.toast_message(f"Day work complete: {job.title}. +{job.reward} gold", 4.5)
        self.active_day_job = None

    def day_job_hud_text(self):
        job = self.active_day_job
        if not job:
            return None
        if job.kind == "rescue" and not job.rescued:
            return f"FIND THE DRIFTING CREW  |  TARGET MARKED"
        labels = {"cargo": "CARGO", "letter": "SEALED LETTER", "passenger": "PASSENGER"}
        return f"DELIVER TO {job.destination.upper()}  |  {labels.get(job.kind, 'DELIVERY')}"
