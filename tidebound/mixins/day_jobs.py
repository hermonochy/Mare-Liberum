from ..common import *


class DayJobsMixin:
    DAY_JOB_BOARD_SIZE = 5

    def initialise_day_jobs(self):
        self.day_job_offers = {}
        self.active_day_jobs = []
        self.day_job_serial = 1
        self.completed_day_jobs = 0
        self.job_board_open = False
        self.job_board_selected_index = 0
        self.job_board_selected_ids = set()

    @property
    def active_day_job(self):
        return self.active_day_jobs[0] if self.active_day_jobs else None

    def make_day_job(self, source_name, kind=None, exclude_destinations=None):
        excluded = set(exclude_destinations or ())
        destinations = [
            port for port in self.ports
            if port.name != source_name and port.name not in excluded
        ]
        if not destinations:
            destinations = [port for port in self.ports if port.name != source_name]
        destination = self.rng.choice(destinations)
        source = self.ports_by_name[source_name]
        distance = math.hypot(destination.x - source.x, destination.y - source.y)
        if kind is None:
            kind = self.rng.choices(
                ["cargo", "letter", "passenger", "rescue"],
                weights=[34, 24, 24, 18],
                k=1,
            )[0]
        serial = self.day_job_serial
        self.day_job_serial += 1
        rescue_x = None
        rescue_y = None

        if kind == "cargo":
            goods = self.rng.choice(["coffee sacks", "sugar barrels", "indigo crates", "lime casks", "sailcloth bales", "salted fish"])
            amount = self.rng.randint(4, 9)
            reward = 38 + round(distance * 0.004) + self.rng.randint(0, 5)
            title = "A Few Honest Barrels"
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
            reward = 25 + round(distance * 0.003) + self.rng.randint(0, 4)
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
            reward = 43 + round(distance * 0.004) + self.rng.randint(0, 5)
            title = "Passage for a Passenger"
            speaker = "A tavern keeper"
            offer_text = (
                f"The tavern keeper introduces you to {passenger} who needs passage to {destination.name}. "
                f"\"They have paid their fare and travel with one sea chest. A calm voyage is all they ask. "
                f"No need to hurry, and no need to go looking for trouble.\""
            )
            payload = passenger
        else:
            reward = 48 + round(distance * 0.004) + self.rng.randint(0, 5)
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

        if kind == "rescue":
            objective = f"Find the drifting longboat, rescue the crew with R, then deliver them to {destination.name}."
        else:
            objective = f"Carry {payload} from {source_name} to {destination.name}."

        return DayJob(
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

    def ensure_day_job_board(self, source_name):
        offers = self.day_job_offers.setdefault(source_name, [])
        missing = max(0, self.DAY_JOB_BOARD_SIZE - len(offers))
        kinds = ["cargo", "letter", "passenger", "rescue"]
        self.rng.shuffle(kinds)
        kinds.extend(self.rng.choice(["cargo", "letter", "passenger", "rescue"]) for _ in range(missing))
        used_destinations = {job.destination for job in offers}
        for kind in kinds[:missing]:
            job = self.make_day_job(source_name, kind, used_destinations)
            offers.append(job)
            used_destinations.add(job.destination)
        return offers

    def find_day_job_rescue_position(self, source_name, destination_name):
        source = self.ports_by_name[source_name]
        destination = self.ports_by_name[destination_name]
        dx = destination.x - source.x
        dy = destination.y - source.y
        length = max(1.0, math.hypot(dx, dy))
        perpendicular = (-dy / length, dx / length)
        candidates = []
        polygons = self.land + [site.polygon for site in self.treasure_sites]
        for fraction in (0.28, 0.38, 0.48, 0.58, 0.68, 0.76):
            base_x = source.x + dx * fraction
            base_y = source.y + dy * fraction
            for offset in (0, 170, -170, 330, -330, 500, -500):
                x = base_x + perpendicular[0] * offset
                y = base_y + perpendicular[1] * offset
                if any(point_in_polygon((x, y), polygon) for polygon in polygons):
                    continue
                if any(math.hypot(x - port.x, y - port.y) < 245 for port in self.ports):
                    continue
                candidates.append((x, y))
        if candidates:
            return self.rng.choice(candidates)
        return (source.x + dx * 0.5, source.y + dy * 0.5)

    def open_day_job_board(self):
        if not self.docked_port:
            self.toast_message("The harbour job board is ashore. Make fast at a port first.", 3.0)
            return
        offers = self.ensure_day_job_board(self.docked_port)
        self.job_board_selected_ids.clear()
        self.job_board_selected_index = 0
        self.job_board_open = True
        self.toast_message(f"{len(offers)} harbour jobs are posted at {self.docked_port}. Select any number to take aboard.", 4.0)

    def job_board_layout(self):
        width, height = self.screen.get_size()
        panel_width = min(930, width - 48)
        panel_height = min(660, height - 40)
        panel = pygame.Rect((width - panel_width) // 2, (height - panel_height) // 2, panel_width, panel_height)
        row_stride = min(78, max(40, (panel_height - 245) // self.DAY_JOB_BOARD_SIZE))
        row_height = max(34, row_stride - 7)
        rows_top = panel.y + 122
        rows = [pygame.Rect(panel.x + 28, rows_top + index * row_stride, panel.width - 56, row_height) for index in range(self.DAY_JOB_BOARD_SIZE)]
        button_y = panel.bottom - 66
        accept = pygame.Rect(panel.right - 260, button_y, 224, 42)
        close = pygame.Rect(panel.x + 36, button_y, 170, 42)
        return panel, rows, accept, close

    def handle_day_job_board_click(self, position):
        offers = self.day_job_offers.get(self.docked_port, [])
        panel, rows, accept_rect, close_rect = self.job_board_layout()
        if accept_rect.collidepoint(position):
            self.accept_selected_day_jobs()
            return True
        if close_rect.collidepoint(position) or not panel.collidepoint(position):
            self.close_day_job_board()
            return True
        for index, row in enumerate(rows[:len(offers)]):
            if row.collidepoint(position):
                self.job_board_selected_index = index
                self.toggle_day_job_selection(index)
                return True
        return True

    def toggle_day_job_selection(self, index):
        offers = self.day_job_offers.get(self.docked_port, [])
        if not 0 <= index < len(offers):
            return
        job_id = offers[index].job_id
        if job_id in self.job_board_selected_ids:
            self.job_board_selected_ids.remove(job_id)
        else:
            self.job_board_selected_ids.add(job_id)

    def close_day_job_board(self):
        self.job_board_open = False
        self.job_board_selected_ids.clear()

    def accept_selected_day_jobs(self):
        if not self.docked_port:
            self.close_day_job_board()
            return
        offers = self.day_job_offers.get(self.docked_port, [])
        selected = [job for job in offers if job.job_id in self.job_board_selected_ids]
        if not selected:
            self.toast_message("Tick one or more jobs before accepting them.", 3.0)
            return
        for job in selected:
            job.stage = "rescue" if job.kind == "rescue" else "deliver"
            self.active_day_jobs.append(job)
            self.add_journal(f"Accepted day work: {job.title}. {job.objective}")
        selected_ids = {job.job_id for job in selected}
        self.day_job_offers[self.docked_port] = [job for job in offers if job.job_id not in selected_ids]
        titles = ", ".join(job.title for job in selected[:3])
        if len(selected) > 3:
            titles += f", and {len(selected) - 3} more"
        self.close_day_job_board()
        self.toast_message(f"Accepted {len(selected)} job(s): {titles}.", 5.0)

    def accept_day_job(self):
        offers = self.day_job_offers.get(self.docked_port, []) if self.docked_port else []
        if offers and not self.job_board_selected_ids:
            self.job_board_selected_ids.add(offers[0].job_id)
        self.accept_selected_day_jobs()

    def day_job_objective(self, job=None):
        job = job or self.active_day_job
        if not job:
            return "No day work accepted."
        if job.kind == "rescue" and not job.rescued:
            return f"Find the drifting longboat; press R nearby, then sail to {job.destination}."
        return f"Deliver {job.payload} to {job.destination}."

    def day_job_rescue_distance(self, job=None):
        if job is not None:
            if job.kind != "rescue" or job.rescued or job.target_x is None:
                return float("inf")
            return math.hypot(self.ship_x - job.target_x, self.ship_y - job.target_y)
        distances = [
            self.day_job_rescue_distance(active)
            for active in self.active_day_jobs
            if active.kind == "rescue" and not active.rescued
        ]
        return min(distances, default=float("inf"))

    def try_interact_day_job(self):
        candidates = [
            job for job in self.active_day_jobs
            if job.kind == "rescue" and not job.rescued and job.target_x is not None
        ]
        candidates.sort(key=self.day_job_rescue_distance)
        for job in candidates:
            if self.day_job_rescue_distance(job) <= 135:
                job.rescued = True
                job.stage = "deliver"
                self.add_journal(f"Recovered {job.payload}. Take them safely to {job.destination}.")
                self.toast_message(f"The stranded crew for {job.destination} are aboard. Deliver them safely.", 4.2)
                return True
        return False

    def draw_day_job_target(self):
        for job in self.active_day_jobs:
            if job.kind == "rescue" and not job.rescued and job.target_x is not None:
                center = self.world_to_screen(job.target_x, job.target_y)
                pygame.draw.circle(self.screen, (244, 211, 142), center, max(12, int(18 * self.camera_zoom)), 2)
                pygame.draw.line(self.screen, (246, 224, 180), (center[0] - 18, center[1] + 5), (center[0] + 18, center[1] + 5), max(2, int(3 * self.camera_zoom)))
                pygame.draw.line(self.screen, (225, 235, 226), (center[0], center[1] + 4), (center[0], center[1] - 19), max(2, int(2 * self.camera_zoom)))
                pygame.draw.polygon(self.screen, (173, 57, 42), [center, (center[0] + 15, center[1] - 15), (center[0], center[1] - 12)])
                if self.camera_zoom > 0.55:
                    label = fit_text_surface(self.tiny_font, f"RESCUE: {job.destination.upper()}", (255, 235, 191), 260, 20)
                    rect = label.get_rect(center=(center[0], center[1] - 34)).clamp(self.screen.get_rect())
                    pygame.draw.rect(self.screen, (40, 30, 22), rect.inflate(10, 5), border_radius=3)
                    self.screen.blit(label, rect)
            elif job.stage == "deliver":
                port = self.ports_by_name.get(job.destination)
                if port:
                    sx, sy = self.world_to_screen(port.x, port.y)
                    if -45 <= sx <= self.screen.get_width() + 45 and -45 <= sy <= self.screen.get_height() + 45:
                        pygame.draw.circle(self.screen, (238, 197, 119), (sx, sy), max(8, int(12 * self.camera_zoom)), 2)

    def complete_day_job_at_port(self, port):
        completed = [job for job in self.active_day_jobs if job.stage == "deliver" and job.destination == port.name]
        if not completed:
            return
        self.active_day_jobs = [job for job in self.active_day_jobs if job not in completed]
        total_reward = sum(job.reward for job in completed)
        self.gold += total_reward
        for job in completed:
            self.completed_day_jobs += 1
            self.add_journal(f"Completed day work: {job.title}. Earned {job.reward} gold at {port.name}.")
            self.reward_day_job_diplomacy(port)
        if len(completed) == 1:
            self.toast_message(f"DAY JOB COMPLETE: {completed[0].title}. +{total_reward} gold", 4.8)
        else:
            self.toast_message(f"{len(completed)} DAY JOBS COMPLETE at {port.name}. +{total_reward} gold", 5.2)

    def day_job_hud_texts(self):
        lines = []
        for job in self.active_day_jobs[:3]:
            if job.kind == "rescue" and not job.rescued:
                lines.append(f"RESCUE CREW EN ROUTE TO {job.destination.upper()}")
            else:
                kind = {"cargo": "CARGO", "letter": "LETTER", "passenger": "PASSENGER", "rescue": "RESCUED CREW"}.get(job.kind, "DELIVERY")
                lines.append(f"{kind} → {job.destination.upper()}  |  {job.reward}g")
        if len(self.active_day_jobs) > 3:
            lines.append(f"...and {len(self.active_day_jobs) - 3} more active jobs")
        return lines

    def day_job_hud_text(self):
        lines = self.day_job_hud_texts()
        return "  •  ".join(lines[:2]) if lines else None
