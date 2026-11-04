import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from ..common import *


class SaveLoadMixin:
    SAVE_FORMAT = "TIDEBOUND_VOYAGE"
    SAVE_VERSION = 1

    def save_directory(self):
        directory = Path(__file__).resolve().parents[2] / "saves"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def save_files(self):
        files = list(self.save_directory().glob("*.tide"))
        return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)

    def default_save_name(self):
        existing = {path.stem for path in self.save_files()}
        number = 1
        while f"Voyage {number}" in existing:
            number += 1
        return f"Voyage {number}"

    @staticmethod
    def clean_save_name(name):
        cleaned = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
        return cleaned[:36] or "Unnamed Voyage"

    def save_game(self, slot_name):
        last_port_name = getattr(self, "last_docked_port", None) or self.docked_port
        port = self.ports_by_name.get(last_port_name)
        if port is None:
            raise ValueError("No previous harbour is recorded. Dock at a port before saving.")

        safe_name = self.clean_save_name(slot_name)
        path = self.save_directory() / f"{safe_name}.tide"
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        data = {
            "format": self.SAVE_FORMAT,
            "version": self.SAVE_VERSION,
            "description": "Human-readable Tidebound voyage record. Values may be edited while the game is closed.",
            "saved_at": timestamp,
            "captain": {
                "gold": self.gold,
                "journal": list(self.journal),
                "relics": list(self.relics),
                "world_time": self.world_time,
                "completed_day_jobs": self.completed_day_jobs,
            },
            "ship": {
                "name": self.player_ship_name,
                "class": self.current_ship,
                "livery": self.player_livery,
                "upgrades": dict(self.upgrades),
                "hull": self.player_hull,
                "maximum_hull": self.player_max_hull,
                "sail_setting": self.sail_setting,
                "oars_deployed": self.oars_deployed,
                "fleet_order": self.fleet_order,
                "fleet_serial": self.fleet_serial,
            },
            "last_berth": {
                "port": port.name,
                "region": port.region,
                "note": "Loading this save places the flagship at this berth, even if it was saved while sailing.",
            },
            "story": {
                "mission_states": dict(self.mission_states),
                "active_mission_id": self.active_mission_id,
                "mission_kills": self.mission_kills,
                "mission_returning": self.mission_returning,
                "mission_fleet_spawned": self.mission_fleet_spawned,
                "mission_completion_started": self.mission_completion_started,
                "mission_result_title": self.mission_result_title,
                "mission_result_reward": self.mission_result_reward,
            },
            "treasure": [
                {
                    "id": site.treasure_id,
                    "map_found": site.map_found,
                    "island_revealed": site.revealed,
                    "chest_claimed": site.dug,
                }
                for site in self.treasure_sites
            ],
            "fleet": [asdict(ship) for ship in self.fleet],
            "pirate_ships": [asdict(ship) for ship in self.pirates],
            "other_ships": [asdict(ship) for ship in self.traffic_ships],
            "day_work": {
                "serial": self.day_job_serial,
                "active_jobs": [asdict(job) for job in self.active_day_jobs],
                "port_boards": {
                    port_name: [asdict(job) for job in jobs]
                    for port_name, jobs in self.day_job_offers.items()
                },
            },
            "world": {
                "reinforcement_number": self.reinforcement_number,
                "reinforcement_timer": self.reinforcement_timer,
                "traffic_spawn_timer": self.traffic_spawn_timer,
                "traffic_serial": self.traffic_serial,
                "camera_zoom": self.camera_zoom,
                "random_state": json.loads(json.dumps(self.rng.getstate())),
            },
        }
        text = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_text(text + "\n", encoding="utf-8")
        self.toast_message(f"Voyage saved as '{safe_name}' at {port.name}.", 4.5)
        return path

    def load_game_file(self, path):
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("format") != self.SAVE_FORMAT:
            raise ValueError("This file is not a recognised Tidebound voyage.")
        if int(data.get("version", 0)) > self.SAVE_VERSION:
            raise ValueError("This save was made by a newer version of Tidebound.")

        captain = data.get("captain", {})
        ship = data.get("ship", {})
        story = data.get("story", {})
        world = data.get("world", {})
        berth = data.get("last_berth", {})
        port = self.ports_by_name.get(berth.get("port"))
        if port is None:
            raise ValueError(f"The saved harbour '{berth.get('port', 'unknown')}' is not present in this game version.")

        self.last_docked_port = port.name
        self.docked_port = port.name
        self.near_port = port
        self.ship_x, self.ship_y = float(port.x), float(port.y)
        self.ship_heading = float(port.exit_heading)
        self.ship_vx = self.ship_vy = 0.0
        self.gold = max(0, int(captain.get("gold", 0)))
        self.journal = list(captain.get("journal", []))[-24:]
        self.relics = list(captain.get("relics", []))
        self.world_time = max(0.0, float(captain.get("world_time", 0.0)))
        self.completed_day_jobs = max(0, int(captain.get("completed_day_jobs", 0)))

        self.player_ship_name = str(ship.get("name", "The Wayward Gull"))[:24]
        known_ship_types = {"Sloop", "Cutter", "Schooner", "Brigantine", "Frigate"}
        self.current_ship = ship.get("class", "Sloop")
        if self.current_ship not in known_ship_types:
            self.current_ship = "Sloop"
        self.player_livery = max(0, min(len(SHIP_LIVERIES) - 1, int(ship.get("livery", 0))))
        self.upgrades = {key: max(0, int(value)) for key, value in ship.get("upgrades", {}).items()}
        for key in ("cannons", "hull", "rigging", "rudder"):
            self.upgrades.setdefault(key, 0)
        self.player_max_hull = max(1, int(ship.get("maximum_hull", PLAYER_HULL)))
        self.player_hull = max(1, min(self.player_max_hull, int(ship.get("hull", self.player_max_hull))))
        self.sail_setting = max(0.0, min(1.0, float(ship.get("sail_setting", 0.72))))
        self.oars_deployed = False
        self.fleet_order = ship.get("fleet_order", "follow")
        if self.fleet_order not in {"fight", "hold_fire", "gather", "follow"}:
            self.fleet_order = "follow"
        self.fleet_serial = max(1, int(ship.get("fleet_serial", 1)))

        self.mission_states = {mission.mission_id: "available" for mission in self.missions}
        self.mission_states.update({key: value for key, value in story.get("mission_states", {}).items() if key in self.mission_states})
        self.active_mission_id = story.get("active_mission_id")
        if self.active_mission_id not in self.mission_states:
            self.active_mission_id = None
        self.mission_kills = max(0, int(story.get("mission_kills", 0)))
        self.mission_returning = bool(story.get("mission_returning", False))
        self.mission_fleet_spawned = bool(story.get("mission_fleet_spawned", False))
        self.mission_completion_started = bool(story.get("mission_completion_started", False))
        self.mission_result_title = str(story.get("mission_result_title", ""))
        self.mission_result_reward = max(0, int(story.get("mission_result_reward", 0)))
        self.mission_result_timer = 0.0

        treasure_flags = {entry.get("id"): entry for entry in data.get("treasure", [])}
        for site in self.treasure_sites:
            flags = treasure_flags.get(site.treasure_id, {})
            site.map_found = bool(flags.get("map_found", False))
            site.revealed = bool(flags.get("island_revealed", False))
            site.dug = bool(flags.get("chest_claimed", False))

        self.fleet = [FleetShip(**entry) for entry in data.get("fleet", [])]
        formation = "gather" if self.fleet_order == "gather" else "follow"
        for index, escort in enumerate(self.fleet):
            escort.x, escort.y = self.fleet_formation_target(index, len(self.fleet), formation)
            escort.vx = escort.vy = 0.0
            escort.anchor_x, escort.anchor_y = escort.x, escort.y
        self.pirates = [PirateShip(**entry) for entry in data.get("pirate_ships", [])]
        self.traffic_ships = [TrafficShip(**entry) for entry in data.get("other_ships", [])]

        day_work = data.get("day_work", {})
        self.day_job_serial = max(1, int(day_work.get("serial", 1)))
        self.active_day_jobs = [DayJob(**entry) for entry in day_work.get("active_jobs", [])]
        self.day_job_offers = {
            port_name: [DayJob(**entry) for entry in jobs]
            for port_name, jobs in day_work.get("port_boards", {}).items()
            if port_name in self.ports_by_name
        }
        self.reinforcement_number = max(1, int(world.get("reinforcement_number", 1)))
        self.reinforcement_timer = max(1.0, float(world.get("reinforcement_timer", 30.0)))
        self.traffic_spawn_timer = max(1.0, float(world.get("traffic_spawn_timer", 20.0)))
        self.traffic_serial = max(1, int(world.get("traffic_serial", 1)))
        self.camera_zoom = max(0.55, min(2.4, float(world.get("camera_zoom", 1.0))))
        if "random_state" in world:
            def restore_tuple(value):
                if isinstance(value, list):
                    return tuple(restore_tuple(item) for item in value)
                return value
            self.rng.setstate(restore_tuple(world["random_state"]))

        self.projectiles = []
        self.cannon_held = {-1: False, 1: False}
        self.cannon_first_volley_fired = {-1: False, 1: False}
        self.cannon_battery_timers = {-1: [], 1: []}
        self.cannon_battery_rates = {-1: [], 1: []}
        self.ship_surface_cache = {}
        self.conversation = None
        self.shipyard_open = False
        self.job_board_open = False
        self.journal_open = False
        self.treasure_chart_open = False
        self.world_map_open = False
        self.camera_follow = True
        self.recenter_camera()
        self.toast_message(f"Welcome back, captain. Your ship is berthed at {port.name}.", 5.0)
        return port

    def begin_save_dialog(self, return_to_pause=False):
        self.cannon_held[-1] = False
        self.cannon_held[1] = False
        self.save_dialog_open = True
        self.save_dialog_return_to_pause = return_to_pause
        self.save_name_input = self.default_save_name()
        pygame.key.start_text_input()

    def finish_save_dialog(self):
        name = self.clean_save_name(self.save_name_input)
        try:
            self.save_game(name)
        except (OSError, ValueError) as error:
            self.toast_message(f"Could not save this voyage: {error}", 5.0)
            return
        self.save_dialog_open = False
        pygame.key.stop_text_input()
        self.menu_mode = "pause" if self.save_dialog_return_to_pause else None

    def cancel_save_dialog(self):
        self.save_dialog_open = False
        pygame.key.stop_text_input()
        self.menu_mode = "pause" if self.save_dialog_return_to_pause else None

    def start_new_voyage(self):
        self.__init__()
        self.menu_mode = None
        self.show_help = True

    def menu_visible_count(self, option_count):
        width, height = self.screen.get_size()
        panel_height = min(max(410, 230 + option_count * 58), height - 40)
        return max(1, min(option_count, (panel_height - 200) // 56))

    def update_menu_scroll(self, option_count):
        visible = self.menu_visible_count(option_count)
        if self.menu_selection < self.menu_scroll:
            self.menu_scroll = self.menu_selection
        elif self.menu_selection >= self.menu_scroll + visible:
            self.menu_scroll = self.menu_selection - visible + 1
        self.menu_scroll = max(0, min(self.menu_scroll, max(0, option_count - visible)))

    def menu_option_rects(self, option_count):
        width, height = self.screen.get_size()
        panel_width = min(860, width - 50)
        panel_height = min(max(410, 230 + option_count * 58), height - 40)
        panel = pygame.Rect((width - panel_width) // 2, (height - panel_height) // 2, panel_width, panel_height)
        visible = self.menu_visible_count(option_count)
        start = max(0, min(self.menu_scroll, max(0, option_count - visible)))
        return [pygame.Rect(panel.x + 42, panel.y + 150 + row * 54, panel.width - 84, 48)
                for row in range(min(visible, option_count - start))], start

    def handle_menu_click(self, position):
        if self.save_dialog_open:
            return False
        if self.menu_mode == "main":
            options = ["New Voyage", "Load Voyage", "Quit"]
        elif self.menu_mode == "pause":
            options = ["Resume Sailing", "Save Voyage", "Load Voyage", "Main Menu", "Quit"]
        elif self.menu_mode == "load":
            options = self.save_files()
        else:
            return False
        rects, start = self.menu_option_rects(len(options))
        for offset, rect in enumerate(rects):
            if rect.collidepoint(position):
                self.menu_selection = start + offset
                self.handle_menu_key(pygame.K_RETURN)
                return True
        return True

    def open_load_menu(self, return_mode="main"):
        self.cannon_held[-1] = False
        self.cannon_held[1] = False
        self.load_return_mode = return_mode
        self.menu_mode = "load"
        self.menu_selection = 0
        self.menu_scroll = 0
        self.load_scroll = 0

    def load_selected_save(self):
        saves = self.save_files()
        if not saves:
            self.toast_message("No saved voyages yet. Start a voyage and press F5 to save.", 4.0)
            return
        index = max(0, min(self.menu_selection, len(saves) - 1))
        try:
            self.load_game_file(saves[index])
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            self.toast_message(f"Could not load that voyage: {error}", 6.0)
            return
        self.menu_mode = None
        self.save_dialog_open = False
        self.add_journal(f"Loaded voyage '{saves[index].stem}' from {self.last_docked_port}.")

    def handle_menu_key(self, key):
        if self.save_dialog_open:
            if key == pygame.K_ESCAPE:
                self.cancel_save_dialog()
            elif key == pygame.K_BACKSPACE:
                self.save_name_input = self.save_name_input[:-1]
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.finish_save_dialog()
            return

        if self.menu_mode == "pause" and key in (pygame.K_ESCAPE, pygame.K_F9):
            self.menu_mode = None
            return

        if self.menu_mode == "main":
            options = ["New Voyage", "Load Voyage", "Quit"]
        elif self.menu_mode == "pause":
            options = ["Resume Sailing", "Save Voyage", "Load Voyage", "Main Menu", "Quit"]
        elif self.menu_mode == "load":
            options = self.save_files()
            if key == pygame.K_ESCAPE:
                self.menu_mode = self.load_return_mode or "main"
                return
            if not options:
                if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.menu_mode = self.load_return_mode or "main"
                return
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selection = (self.menu_selection - 1) % len(options)
                self.update_menu_scroll(len(options))
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = (self.menu_selection + 1) % len(options)
                self.update_menu_scroll(len(options))
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.load_selected_save()
            return
        else:
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.menu_selection = (self.menu_selection - 1) % len(options)
            self.update_menu_scroll(len(options))
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_selection = (self.menu_selection + 1) % len(options)
            self.update_menu_scroll(len(options))
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            choice = options[self.menu_selection]
            if self.menu_mode == "main":
                if choice == "New Voyage":
                    self.start_new_voyage()
                elif choice == "Load Voyage":
                    self.open_load_menu("main")
                else:
                    self.running = False
            elif self.menu_mode == "pause":
                if choice == "Resume Sailing":
                    self.menu_mode = None
                elif choice == "Save Voyage":
                    self.begin_save_dialog(return_to_pause=True)
                elif choice == "Load Voyage":
                    self.open_load_menu("pause")
                elif choice == "Main Menu":
                    self.menu_mode = "main"
                    self.menu_selection = 0
                else:
                    self.running = False

    def draw_main_menu(self):
        self.draw_menu_panel("TIDEBOUND", "A Caribbean life under sail", ["New Voyage", "Load Voyage", "Quit"],
                             selected=self.menu_selection, footer="Up / Down: choose    Enter: select")

    def draw_pause_menu(self):
        self.draw_menu_panel("PAUSED", "The sea can wait a moment, captain.",
                             ["Resume Sailing", "Save Voyage", "Load Voyage", "Main Menu", "Quit"],
                             selected=self.menu_selection, footer="Esc / F9: pause menu    Enter: select")

    def draw_load_menu(self):
        saves = self.save_files()
        labels = []
        for save in saves:
            try:
                data = json.loads(save.read_text(encoding="utf-8"))
                port = data.get("last_berth", {}).get("port", "Unknown harbour")
                captain = data.get("captain", {})
                gold = captain.get("gold", 0)
                labels.append(f"{save.stem}   —   {port}   —   {gold} gold")
            except Exception:
                labels.append(f"{save.stem}   —   unreadable save")
        if not labels:
            labels = ["No saved voyages found"]
        self.draw_menu_panel("LOAD A VOYAGE", "Choose a saved captain's log.", labels,
                             selected=self.menu_selection, footer="Up / Down: choose    Enter: load    Esc: back")

    def draw_save_dialog(self):
        self.draw_menu_panel("SAVE VOYAGE", "Choose a name for this captain's log.",
                             [f"Name: {self.save_name_input}_", "Press Enter to save    Esc to cancel"],
                             selected=0, footer=f"Your ship will be berthed at {self.last_docked_port} when loaded.")

    def draw_menu_panel(self, title_text, subtitle, options, selected=0, footer=""):
        width, height = self.screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((8, 17, 21, 205))
        self.screen.blit(shade, (0, 0))
        panel_width = min(860, width - 50)
        panel_height = min(max(410, 230 + len(options) * 58), height - 40)
        panel = pygame.Rect((width - panel_width) // 2, (height - panel_height) // 2, panel_width, panel_height)
        pygame.draw.rect(self.screen, (35, 24, 18), panel.inflate(12, 12), border_radius=12)
        pygame.draw.rect(self.screen, (111, 72, 41), panel, border_radius=9)
        pygame.draw.rect(self.screen, (229, 199, 145), panel.inflate(-8, -8), 2, border_radius=7)
        title = self.big_font.render(title_text, True, (248, 220, 169))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 58)))
        sub = self.small_font.render(subtitle, True, (234, 215, 182))
        self.screen.blit(sub, sub.get_rect(center=(panel.centerx, panel.y + 112)))
        row_height = 48
        visible_count = max(1, min(len(options), (panel.height - 200) // 56))
        start = max(0, min(getattr(self, "menu_scroll", 0), max(0, len(options) - visible_count)))
        for row in range(visible_count):
            index = start + row
            if index >= len(options):
                break
            y = panel.y + 150 + row * 54
            rect = pygame.Rect(panel.x + 42, y, panel.width - 84, row_height)
            if index == selected:
                pygame.draw.rect(self.screen, (219, 185, 126), rect, border_radius=5)
                color = (43, 29, 20)
            else:
                pygame.draw.rect(self.screen, (69, 48, 33), rect, border_radius=5)
                color = (246, 227, 190)
            label = self.small_font.render(str(options[index])[:78], True, color)
            self.screen.blit(label, label.get_rect(midleft=(rect.x + 16, rect.centery)))
        foot = self.tiny_font.render(footer, True, (225, 205, 169))
        self.screen.blit(foot, foot.get_rect(center=(panel.centerx, panel.bottom - 32)))
