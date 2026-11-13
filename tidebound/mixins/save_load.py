import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from ..common import *


class SaveLoadMixin:
    def settings_path(self):
        return PROJECT_ROOT / SETTINGS_FILE_NAME

    def load_user_settings(self):
        self.text_scale = DEFAULT_TEXT_SCALE
        self.effects_volume = DEFAULT_EFFECTS_VOLUME
        self.ambience_volume = DEFAULT_AMBIENCE_VOLUME
        path = self.settings_path()
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
            self.text_scale = max(MIN_TEXT_SCALE, min(MAX_TEXT_SCALE, float(settings.get("text_scale", DEFAULT_TEXT_SCALE))))
            self.effects_volume = max(0.0, min(1.0, float(settings.get("effects_volume", DEFAULT_EFFECTS_VOLUME))))
            self.ambience_volume = max(0.0, min(1.0, float(settings.get("ambience_volume", DEFAULT_AMBIENCE_VOLUME))))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # A missing or malformed preference file should never stop a voyage.
            pass

    def save_user_settings(self):
        path = self.settings_path()
        data = {
            "text_scale": round(self.text_scale, 2),
            "effects_volume": round(self.effects_volume, 2),
            "ambience_volume": round(self.ambience_volume, 2),
        }
        try:
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(path)
            return True
        except OSError:
            # Read-only installs or restricted folders should not interrupt play.
            return False

    def apply_text_scale(self):
        scale = max(MIN_TEXT_SCALE, min(MAX_TEXT_SCALE, float(getattr(self, "text_scale", DEFAULT_TEXT_SCALE))))
        self.text_scale = scale
        self.font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["normal"], round(FONT_BASE_SIZES["normal"] * scale)))
        self.small_font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["small"], round(FONT_BASE_SIZES["small"] * scale)))
        self.tiny_font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["tiny"], round(FONT_BASE_SIZES["tiny"] * scale)))
        self.title_font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["title"], round(FONT_BASE_SIZES["title"] * scale)), bold=True)
        self.big_font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["big"], round(FONT_BASE_SIZES["big"] * scale)), bold=True)
        self.map_font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["map"], round(FONT_BASE_SIZES["map"] * scale)))
        self.map_heading_font = pygame.font.SysFont(FONT_FAMILY, max(FONT_MIN_SIZES["map_heading"], round(FONT_BASE_SIZES["map_heading"] * scale)), bold=True)

    def adjust_text_scale(self, amount):
        self.text_scale = max(MIN_TEXT_SCALE, min(MAX_TEXT_SCALE, round(self.text_scale + amount, 2)))
        self.apply_text_scale()
        self.save_user_settings()

    def apply_audio_settings(self):
        audio = getattr(self, "audio", None)
        if audio is not None:
            audio.set_volumes(self.effects_volume, self.ambience_volume)

    def adjust_audio_volume(self, setting, amount):
        attribute = "effects_volume" if setting == "effects" else "ambience_volume"
        value = max(0.0, min(1.0, round(getattr(self, attribute, DEFAULT_EFFECTS_VOLUME) + amount, 2)))
        setattr(self, attribute, value)
        self.apply_audio_settings()
        self.save_user_settings()

    def reset_user_settings(self):
        self.text_scale = DEFAULT_TEXT_SCALE
        self.effects_volume = DEFAULT_EFFECTS_VOLUME
        self.ambience_volume = DEFAULT_AMBIENCE_VOLUME
        self.apply_text_scale()
        self.apply_audio_settings()
        self.save_user_settings()
        self.toast_message("Display and sound settings restored to their defaults.", 3.5)

    def save_directory(self):
        directory = Path(__file__).resolve().parents[2] / "saves"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def save_files(self):
        files = list(self.save_directory().glob(f"*{SAVE_FILE_EXTENSION}"))
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

    def save_game(self, slot_name, notify=True):
        if getattr(self, "player_sinking_active", False) or getattr(self, "player_lost", False):
            raise ValueError("A sinking or lost flagship cannot create a new save. Load a previous voyage instead.")
        last_port_name = getattr(self, "last_docked_port", None) or self.docked_port
        port = self.ports_by_name.get(last_port_name)
        if port is None:
            raise ValueError("No previous harbour is recorded. Dock at a port before saving.")

        safe_name = self.clean_save_name(slot_name)
        path = self.save_directory() / f"{safe_name}{SAVE_FILE_EXTENSION}"
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        data = {
            "format": SAVE_FORMAT_IDENTIFIER,
            "description": "Human-readable Mare Liberum voyage record.",
            "saved_at": timestamp,
            "captain": {
                "gold": self.gold,
                "journal": list(self.journal),
                "relics": list(self.relics),
                "unique_items": list(getattr(self, "unique_items", [])),
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
                "damage_marks": list(getattr(self, "player_damage_marks", [])),
                "sail_setting": self.sail_setting,
                "oars_deployed": self.oars_deployed,
                "fleet_order": self.fleet_order,
                "fleet_serial": self.fleet_serial,
            },
            "last_berth": {
                "port": port.name,
                "region": port.region,
                "slot": int(getattr(self, "player_berth_slot", getattr(self, "last_docked_port_slot", PORT_BERTH_CENTER_SLOT)))
                        if self.docked_port == port.name else int(getattr(self, "last_docked_port_slot", PORT_BERTH_CENTER_SLOT)),
                "note": "Loading this save places the flagship in its last occupied harbour slot, even if it was saved while sailing.",
            },
            "story": {
                "mission_states": dict(self.mission_states),
                "active_mission_id": self.active_mission_id,
                "mission_kills": self.mission_kills,
                "mission_waypoint_index": int(getattr(self, "mission_waypoint_index", 0)),
                "mission_returning": self.mission_returning,
                "mission_fleet_spawned": self.mission_fleet_spawned,
                "mission_completion_started": self.mission_completion_started,
                "mission_result_title": self.mission_result_title,
                "mission_result_reward": self.mission_result_reward,
                "mission_event_states": getattr(self, "mission_event_states", {}),
                "world_flags": getattr(self, "world_flags", {}),
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
            "shipwrecks": [
                {
                    "id": site.wreck_id,
                    "discovered": site.discovered,
                    "surface_salvaged": site.surface_salvaged,
                    "deep_attempted": site.deep_attempted,
                    "rare_found": site.rare_found,
                }
                for site in self.shipwrecks
            ],
            "fleet": [asdict(ship) for ship in self.fleet],
            "pirate_ships": [asdict(ship) for ship in self.pirates],
            "other_ships": [asdict(ship) for ship in self.traffic_ships],
            "trade": self.trade_state_for_save(),
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
                "port_defence_cooldowns": dict(getattr(self, "port_defence_cooldowns", {})),
                "camera_zoom": self.camera_zoom,
                "random_state": json.loads(json.dumps(self.rng.getstate())),
                "commander_records": getattr(self, "commander_records", {}),
                "commander_fleets": getattr(self, "commander_fleets", {}),
                "floating_debris": list(getattr(self, "floating_debris", [])),
                "diplomacy": {
                    "faction_relations": dict(getattr(self, "faction_relations", {})),
                    "port_standings": dict(getattr(self, "port_standings", {})),
                    "commander_relations": dict(getattr(self, "commander_relations", {})),
                },
            },
        }
        text = json.dumps(data, ensure_ascii=False, indent=2)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text + "\n", encoding="utf-8")
        temporary.replace(path)
        if notify:
            self.toast_message(f"Voyage saved as '{safe_name}' at {port.name}.", 4.5)
        return path

    def load_game_file(self, path):
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("format") != SAVE_FORMAT_IDENTIFIER:
            raise ValueError("This file is not a Mare Liberum voyage save.")
        required_sections = (
            "captain", "ship", "last_berth", "story", "treasure", "shipwrecks",
            "fleet", "pirate_ships", "other_ships", "trade", "day_work", "world",
        )
        missing = [section for section in required_sections if section not in data]
        if missing:
            raise ValueError("The voyage save is incomplete: " + ", ".join(missing))

        captain = data["captain"]
        ship = data["ship"]
        story = data["story"]
        world = data["world"]
        berth = data["last_berth"]
        if "port" not in berth or "slot" not in berth:
            raise ValueError("The voyage save does not record a valid harbour berth.")
        port = self.ports_by_name.get(berth["port"])
        if port is None:
            raise ValueError(f"The saved harbour '{berth['port']}' is not present on this chart.")

        saved_player_slot = int(berth["slot"])
        if saved_player_slot not in range(PORT_BERTH_COUNT):
            raise ValueError("The saved harbour berth is outside the available quay slots.")
        self.player_berth_slot = saved_player_slot
        self.last_docked_port_slot = saved_player_slot
        self.last_docked_port = port.name
        self.docked_port = port.name
        self.near_port = port
        self.ship_x, self.ship_y = self.harbour_berth_position(port, self.player_berth_slot)
        self.ship_heading = float(port.exit_heading)
        self.ship_vx = self.ship_vy = 0.0
        self.gold = max(0, int(captain.get("gold", 0)))
        self.journal = list(captain.get("journal", []))[-24:]
        self.relics = list(captain.get("relics", []))
        self.unique_items = list(captain.get("unique_items", []))
        self.world_time = max(0.0, float(captain.get("world_time", 0.0)))
        self.completed_day_jobs = max(0, int(captain.get("completed_day_jobs", 0)))

        self.player_ship_name = str(ship.get("name", "The Wayward Gull"))[:24]
        known_ship_types = {"Sloop", "Cutter", "Schooner", "Brigantine", "Frigate"}
        self.current_ship = ship.get("class", "Sloop")
        if self.current_ship not in known_ship_types:
            self.current_ship = "Sloop"
        self.player_livery = max(0, min(len(SHIP_LIVERIES) - 1, int(ship.get("livery", 0))))
        self.upgrades = {key: max(0, int(value)) for key, value in ship.get("upgrades", {}).items()}
        for key in ("cannons", "hull", "rigging", "rudder", "cargo"):
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
        active_record = next((item for item in self.missions if item.mission_id == self.active_mission_id), None)
        maximum_waypoint = len(getattr(active_record, "waypoints", [])) if active_record else 0
        self.mission_waypoint_index = max(0, min(maximum_waypoint, int(story.get("mission_waypoint_index", 0))))
        self.mission_returning = bool(story.get("mission_returning", False))
        self.mission_fleet_spawned = bool(story.get("mission_fleet_spawned", False))
        self.mission_completion_started = bool(story.get("mission_completion_started", False))
        self.mission_result_title = str(story.get("mission_result_title", ""))
        self.mission_result_reward = max(0, int(story.get("mission_result_reward", 0)))
        self.mission_result_timer = 0.0
        if hasattr(self, "restore_mission_event_state"):
            self.restore_mission_event_state(story.get("mission_event_states", {}), story.get("world_flags", {}))

        treasure_flags = {entry.get("id"): entry for entry in data["treasure"]}
        for site in self.treasure_sites:
            flags = treasure_flags.get(site.treasure_id, {})
            site.map_found = bool(flags.get("map_found", False))
            site.revealed = bool(flags.get("island_revealed", False))
            site.dug = bool(flags.get("chest_claimed", False))

        wreck_flags = {entry["id"]: entry for entry in data["shipwrecks"]}
        for site in self.shipwrecks:
            flags = wreck_flags.get(site.wreck_id, {})
            site.discovered = bool(flags.get("discovered", False))
            site.surface_salvaged = bool(flags.get("surface_salvaged", False))
            site.deep_attempted = bool(flags.get("deep_attempted", False))
            site.rare_found = bool(flags.get("rare_found", False))

        self.player_hit_flash = 0.0
        self.player_damage_marks = []
        for mark in ship.get("damage_marks", [])[-18:]:
            try:
                self.player_damage_marks.append({
                    "x": max(-48.0, min(48.0, float(mark.get("x", 0.0)))),
                    "y": max(-27.0, min(27.0, float(mark.get("y", 0.0)))),
                    "angle": float(mark.get("angle", 0.0)),
                    "length": max(3.0, min(20.0, float(mark.get("length", 10.0)))),
                    "size": max(1.5, min(6.0, float(mark.get("size", 3.0)))),
                })
            except (AttributeError, TypeError, ValueError):
                continue
        self.player_sinking_active = False
        self.player_sink_elapsed = 0.0
        self.player_lost = False
        self.floating_debris = []
        for piece in world.get("floating_debris", []):
            try:
                self.floating_debris.append({
                    "x": float(piece["x"]), "y": float(piece["y"]),
                    "vx": float(piece.get("vx", 0.0)), "vy": float(piece.get("vy", 0.0)),
                    "angle": float(piece.get("angle", 0.0)), "spin": float(piece.get("spin", 0.0)),
                    "length": max(3.0, float(piece.get("length", 15.0))),
                    "width": max(2.0, float(piece.get("width", 5.0))),
                    "cloth": bool(piece.get("cloth", False)),
                    "life": max(0.0, float(piece.get("life", 0.0))),
                    "max_life": max(1.0, float(piece.get("max_life", 58.0))),
                })
            except (KeyError, TypeError, ValueError):
                continue
        fleet_entries = []
        for entry in data["fleet"]:
            entry = dict(entry)
            entry.setdefault("upgrades", {"cannons": 0, "hull": 0, "rigging": 0, "rudder": 0})
            fleet_entries.append(FleetShip(**entry))
        self.fleet = fleet_entries
        formation = "gather" if self.fleet_order == "gather" else "follow"
        for index, escort in enumerate(self.fleet):
            escort.x, escort.y = self.fleet_formation_target(index, len(self.fleet), formation)
            escort.vx = escort.vy = 0.0
            escort.anchor_x, escort.anchor_y = escort.x, escort.y
        self.pirates = [PirateShip(**entry) for entry in data["pirate_ships"]]
        self.traffic_ships = [TrafficShip(**entry) for entry in data["other_ships"]]
        # Re-seat traffic ships using the current quay geometry and keep the
        # player's actual saved slot clear without reserving a fixed quay position.
        occupied_saved_berths = {}
        for npc_ship in self.traffic_ships:
            if npc_ship.hull <= 0 or npc_ship.port_dwell <= 0.0 or not npc_ship.berth_port:
                continue
            berth_port = self.ports_by_name.get(npc_ship.berth_port)
            if berth_port is None:
                npc_ship.berth_port = ""
                npc_ship.berth_slot = -1
                npc_ship.port_dwell = 0.0
                continue
            used_slots = occupied_saved_berths.setdefault(berth_port.name, set())
            requested_slot = int(getattr(npc_ship, "berth_slot", -1))
            player_reserved = (berth_port.name == port.name and requested_slot == self.player_berth_slot)
            if requested_slot not in range(PORT_BERTH_COUNT) or requested_slot in used_slots or player_reserved:
                alternatives = [slot for slot in range(PORT_BERTH_COUNT)
                                if slot not in used_slots
                                and not (berth_port.name == port.name and slot == self.player_berth_slot)]
                if not alternatives:
                    npc_ship.berth_port = ""
                    npc_ship.berth_slot = -1
                    npc_ship.port_dwell = 0.0
                    continue
                requested_slot = min(alternatives, key=lambda slot: abs(slot - PORT_BERTH_CENTER_SLOT))
                npc_ship.berth_slot = requested_slot
            used_slots.add(requested_slot)
            npc_ship.x, npc_ship.y = self.harbour_berth_position(berth_port, requested_slot)
            npc_ship.vx = npc_ship.vy = 0.0

        # Keep saved traffic clear of reefs if a save was made during a close pass.
        for npc in self.pirates:
            if npc.dead:
                continue
            if not self.reef_clear_at(npc.x, npc.y, 90.0):
                safe = self.find_safe_water_position(npc.x, npc.y, clearance=105.0)
                if safe:
                    npc.x, npc.y = safe
                    npc.vx = npc.vy = 0.0
                else:
                    npc.dead = True
                    npc.hull = 0
        for npc in self.traffic_ships:
            if npc.hull <= 0 or (npc.port_dwell > 0.0 and npc.berth_port):
                continue
            if not self.reef_clear_at(npc.x, npc.y, 90.0):
                safe = self.find_safe_water_position(npc.x, npc.y, clearance=105.0)
                if safe:
                    npc.x, npc.y = safe
                    npc.vx = npc.vy = 0.0
                else:
                    npc.hull = 0
        self.commander_records = dict(world["commander_records"])
        self.commander_fleets = dict(world["commander_fleets"])
        saved_diplomacy = world["diplomacy"]
        self.faction_relations = {
            faction: self.clamp_relation(saved_diplomacy["faction_relations"][faction])
            for faction in FACTION_NAMES
        }
        self.commander_relations = {
            str(name): self.clamp_relation(value)
            for name, value in saved_diplomacy["commander_relations"].items()
        }
        self.port_standings = dict(saved_diplomacy["port_standings"])
        self.refresh_port_standings()
        self.restore_trade_state(data["trade"])
        self.commander_ledger_open = False
        self.commander_ledger_scroll = 0
        self.diplomacy_open = False

        day_work = data["day_work"]
        self.day_job_serial = max(1, int(day_work["serial"]))
        self.active_day_jobs = [DayJob(**entry) for entry in day_work["active_jobs"]]
        self.day_job_offers = {
            port_name: [DayJob(**entry) for entry in jobs]
            for port_name, jobs in day_work["port_boards"].items()
            if port_name in self.ports_by_name
        }
        self.reinforcement_number = max(1, int(world["reinforcement_number"]))
        self.reinforcement_timer = max(1.0, float(world["reinforcement_timer"]))
        self.traffic_spawn_timer = max(1.0, float(world["traffic_spawn_timer"]))
        self.traffic_serial = max(1, int(world["traffic_serial"]))
        saved_defence = world["port_defence_cooldowns"]
        self.port_defence_cooldowns = {
            port.name: max(0.0, float(saved_defence.get(port.name, 0.25)))
            for port in self.ports
        }
        self.port_defence_notice_timer = 0.0
        self.camera_zoom = max(0.30, min(2.4, float(world.get("camera_zoom", 1.0))))
        def restore_tuple(value):
            if isinstance(value, list):
                return tuple(restore_tuple(item) for item in value)
            return value
        self.rng.setstate(restore_tuple(world["random_state"]))
        self.refresh_npc_attitudes()

        self.projectiles = []
        self.cannon_smoke = []
        self.cannon_held = {-1: False, 1: False}
        self.cannon_first_volley_fired = {-1: False, 1: False}
        self.cannon_battery_timers = {-1: [], 1: []}
        self.cannon_battery_rates = {-1: [], 1: []}
        self.ship_surface_cache = {}
        self.conversation = None
        self.shipyard_open = False
        self.job_board_open = False
        self.market_open = False
        self.diplomacy_open = False
        if hasattr(self, "open_port_menu"):
            self.open_port_menu("overview")
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
        self.open_port_menu("overview")

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
            options = ["New Voyage", "Load Voyage", "Captain's Guide", "Text & Sound Settings", "Quit"]
        elif self.menu_mode == "settings":
            options = self.settings_menu_options()
        elif self.menu_mode == "pause":
            options = ["Resume Sailing", "Save Voyage", "Load Voyage", "Captain's Guide", "Text & Sound Settings", "Main Menu", "Quit"]
        elif self.menu_mode == "game_over":
            options = ["Load Last Save", "Choose a Save", "Return to Main Menu", "Quit"]
        elif self.menu_mode == "load":
            options = self.save_files()
        else:
            return False
        rects, start = self.menu_option_rects(len(options))
        for offset, rect in enumerate(rects):
            if rect.collidepoint(position):
                self.menu_selection = start + offset
                if self.menu_mode == "settings" and self.menu_selection in (0, 1, 2):
                    direction = -0.05 if position[0] < rect.centerx else 0.05
                    self.adjust_selected_setting(direction)
                else:
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

    def load_last_save(self):
        saves = self.save_files()
        if not saves:
            self.toast_message("There is no saved voyage to return to. Choose New Voyage or return to the main menu.", 5.0)
            return False
        latest = saves[0]
        try:
            self.load_game_file(latest)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            self.toast_message(f"Could not load your last saved voyage: {error}", 6.0)
            return False
        self.menu_mode = None
        self.save_dialog_open = False
        self.add_journal(f"After losing the flagship, you returned to the last saved voyage '{latest.stem}' at {self.last_docked_port}.")
        self.toast_message(f"Last saved voyage restored: {latest.stem}.", 5.0)
        return True

    def handle_menu_key(self, key):
        if self.save_dialog_open:
            if key == pygame.K_ESCAPE:
                self.cancel_save_dialog()
            elif key == pygame.K_BACKSPACE:
                self.save_name_input = self.save_name_input[:-1]
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.finish_save_dialog()
            return

        if self.menu_mode == "game_over":
            options = ["Load Last Save", "Choose a Save", "Return to Main Menu", "Quit"]
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selection = (self.menu_selection - 1) % len(options)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = (self.menu_selection + 1) % len(options)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                choice = options[self.menu_selection]
                if choice == "Load Last Save":
                    self.load_last_save()
                elif choice == "Choose a Save":
                    self.open_load_menu("game_over")
                elif choice == "Return to Main Menu":
                    self.menu_mode = "main"
                    self.menu_selection = 0
                    self.menu_scroll = 0
                else:
                    self.running = False
            return

        if self.menu_mode == "pause" and key in (pygame.K_ESCAPE, pygame.K_F9):
            self.menu_mode = None
            return

        if self.menu_mode == "guide":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_g):
                self.menu_mode = self.guide_return_mode or "main"
                return
            if key in (pygame.K_LEFT, pygame.K_a):
                self.guide_page_index = (self.guide_page_index - 1) % len(self.guide_pages())
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.guide_page_index = (self.guide_page_index + 1) % len(self.guide_pages())
            elif key in (pygame.K_UP, pygame.K_w):
                self.guide_scroll = max(0, self.guide_scroll - 1)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.guide_scroll += 1
            return

        if self.menu_mode == "main":
            options = ["New Voyage", "Load Voyage", "Captain's Guide", "Text & Sound Settings", "Quit"]
        elif self.menu_mode == "settings":
            options = self.settings_menu_options()
        elif self.menu_mode == "pause":
            options = ["Resume Sailing", "Save Voyage", "Load Voyage", "Captain's Guide", "Text & Sound Settings", "Main Menu", "Quit"]
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

        if self.menu_mode == "settings":
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selection = (self.menu_selection - 1) % len(options)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = (self.menu_selection + 1) % len(options)
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.adjust_selected_setting(-0.05)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.adjust_selected_setting(0.05)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                choice = options[self.menu_selection]
                if self.menu_selection in (0, 1, 2):
                    self.adjust_selected_setting(0.05)
                elif choice == "Reset defaults":
                    self.reset_user_settings()
                elif choice == "Back":
                    self.close_settings_menu()
            elif key == pygame.K_ESCAPE:
                self.close_settings_menu()
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
                elif choice == "Captain's Guide":
                    self.open_guide("main")
                elif choice == "Text & Sound Settings":
                    self.open_settings("main")
                else:
                    self.running = False
            elif self.menu_mode == "pause":
                if choice == "Resume Sailing":
                    self.menu_mode = None
                elif choice == "Save Voyage":
                    self.begin_save_dialog(return_to_pause=True)
                elif choice == "Load Voyage":
                    self.open_load_menu("pause")
                elif choice == "Captain's Guide":
                    self.open_guide("pause")
                elif choice == "Text & Sound Settings":
                    self.open_settings("pause")
                elif choice == "Main Menu":
                    self.menu_mode = "main"
                    self.menu_selection = 0
                else:
                    self.running = False

    def settings_menu_options(self):
        return [
            f"Text size: {round(self.text_scale * 100)}%",
            f"Sound effects: {round(self.effects_volume * 100)}%",
            f"Sea ambience: {round(self.ambience_volume * 100)}%",
            "Reset defaults",
            "Back",
        ]

    def adjust_selected_setting(self, amount):
        if self.menu_selection == 0:
            self.adjust_text_scale(amount)
        elif self.menu_selection == 1:
            self.adjust_audio_volume("effects", amount)
        elif self.menu_selection == 2:
            self.adjust_audio_volume("ambience", amount)

    def open_settings(self, return_mode="main"):
        self.settings_return_mode = return_mode
        self.menu_mode = "settings"
        self.menu_selection = 0

    def close_settings_menu(self):
        return_mode = getattr(self, "settings_return_mode", "main") or "main"
        self.menu_mode = return_mode
        self.menu_selection = 3 if return_mode == "main" else 4

    def open_guide(self, return_mode="main"):
        self.guide_return_mode = return_mode
        self.guide_page_index = 0
        self.guide_scroll = 0
        self.menu_mode = "guide"

    def guide_pages(self):
        return [
            ("GETTING UNDER WAY", [
                "Your first voyage begins at Port Royal. The old captain nearby introduces the basics; talk to him with Q while docked.",
                "W sets more sail; S reefs it. A and D steer. O deploys oars when the wind is unhelpful. Momentum matters, so slow down before entering a harbour.",
                "E casts off or takes the nearest available harbour berth. When close to a pier, the prompt tells you when docking is possible.",
                "Use the mouse wheel to zoom around the pointer, drag the chart to look around, and press C to centre the view on your ship.",
            ]),
            ("COMBAT & YOUR FLEET", [
                "Hold Z to fire the port-side guns; hold X for starboard. Keep the enemy on the correct side of your ship and allow each gun time to reload.",
                "Powder smoke, recoil and impact sounds help show when a broadside has fired or landed. Watch your hull indicator and repair at a shipyard.",
                "Your escorts obey F (fight), H (hold fire), G (gather) and V (follow). Hold fire is useful around neutral traffic and friendly convoys.",
                "A stray cannonball can turn a friendly ship hostile. Its faction and surviving squadron may remember the attack, so check your target before firing.",
            ]),
            ("CHARTS & DISCOVERIES", [
                "M opens the full atlas. Gold route markers show your active story objective; discovered wrecks and reefs are marked on the chart.",
                "Some voyages require several port calls. Dock at each marked waypoint in order; the compass and gold marker advance after every completed stop. Reaching the final port too early will not complete the contract.",
                "Red shaded water marks reefs. Give them room: crossing a reef damages hull, and NPC captains try to steer clear of them.",
                "Approach a shipwreck and press R to inspect it. Surface cargo is safer; deep salvage can be more rewarding but may damage your ship.",
                "Bottles, treasure charts and riddles can lead to hidden cays. Press T to review charts you have recovered; use R at the marked beach.",
            ]),
            ("PEOPLE, PORTS & SAVES", [
                "Q opens local conversations. Not every conversation is a job: people may offer rumours, introductions, unusual goods, secrets or dishonest bargains.",
                "The harbour office has authored stories and an ordinary job board. Several routine jobs can be active together; the main story is tracked separately.",
                "B opens the shipyard. Y opens the port market: compare changing prices, buy and sell cargo, and plan profitable routes. Your hold has a fixed capacity, improved by cargo refits.",
                "I opens faction diplomacy; N follows named admirals, pirate captains and merchant commanders. Supplying scarce goods can help a faction, while contraband may anger customs officers.",
                "J opens your journal. F5 saves a named voyage at your last docked port, even while at sea. Esc or F9 pauses; Load Voyage offers your saved slots.",
            ]),
        ]

    def draw_main_menu(self):
        self.draw_menu_panel("MARE LIBERUM", "A Caribbean life under sail", 
                             ["New Voyage", "Load Voyage", "Captain's Guide", "Text & Sound Settings", "Quit"],
                             selected=self.menu_selection, footer="Up / Down: choose    Enter: select")

    def draw_settings_menu(self):
        self.draw_menu_panel("TEXT & SOUND", "Choose comfortable text and sound levels. Changes are saved automatically.",
                             self.settings_menu_options(), selected=self.menu_selection,
                             footer="Select a level; use Left / Right or click either side of its row    Esc: back")

    def draw_pause_menu(self):
        self.draw_menu_panel("PAUSED", "The sea can wait a moment, captain.",
                             ["Resume Sailing", "Save Voyage", "Load Voyage", "Captain's Guide", "Text & Sound Settings", "Main Menu", "Quit"],
                             selected=self.menu_selection, footer="Esc / F9: resume    Enter: select")

    def draw_guide_menu(self):
        width, height = self.screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((8, 17, 21, 220))
        self.screen.blit(shade, (0, 0))
        panel_width = min(980, width - 48)
        panel_height = min(690, height - 44)
        panel = pygame.Rect((width - panel_width) // 2, (height - panel_height) // 2, panel_width, panel_height)
        pygame.draw.rect(self.screen, (35, 24, 18), panel.inflate(12, 12), border_radius=12)
        pygame.draw.rect(self.screen, (111, 72, 41), panel, border_radius=9)
        pygame.draw.rect(self.screen, (229, 199, 145), panel.inflate(-8, -8), 2, border_radius=7)
        pages = self.guide_pages()
        page_index = max(0, min(self.guide_page_index, len(pages) - 1))
        title, paragraphs = pages[page_index]
        heading = fit_text_surface(self.big_font, "CAPTAIN'S GUIDE", (248, 220, 169), panel.width - 70, 58)
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 52)))
        subtitle = fit_text_surface(self.small_font, title, (246, 210, 151), panel.width - 70, 32)
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 105)))
        pygame.draw.line(self.screen, (151, 111, 69), (panel.x + 32, panel.y + 132), (panel.right - 32, panel.y + 132), 2)
        content = pygame.Rect(panel.x + 38, panel.y + 154, panel.width - 76, panel.height - 215)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(content)
        font = self.small_font
        line_step = max(24, font.get_linesize() + 6)
        rows = []
        for paragraph in paragraphs:
            rows.extend(wrap_text(font, paragraph, content.width - 18))
            rows.append("")
        max_rows = max(1, content.height // line_step)
        self.guide_scroll = max(0, min(self.guide_scroll, max(0, len(rows) - max_rows)))
        for row_index, line in enumerate(rows[self.guide_scroll:self.guide_scroll + max_rows]):
            y = content.y + row_index * line_step
            if line:
                surf = fit_text_surface(font, line, (245, 232, 202), content.width - 18, line_step - 2)
                self.screen.blit(surf, (content.x + 8, y))
        self.screen.set_clip(previous_clip)
        footer = f"Page {page_index + 1} of {len(pages)}    Left / Right: sections    Up / Down: scroll    Esc / Enter: back"
        foot = fit_text_surface(self.tiny_font, footer, (225, 205, 169), panel.width - 50, 25)
        self.screen.blit(foot, foot.get_rect(center=(panel.centerx, panel.bottom - 28)))

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
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(panel)
        title = fit_text_surface(self.big_font, title_text, (248, 220, 169), panel.width - 70, 58)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 57)))
        sub = fit_text_surface(self.small_font, subtitle, (234, 215, 182), panel.width - 70, 34)
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
            label = fit_text_surface(self.small_font, str(options[index]), color, rect.width - 32, rect.height - 8)
            self.screen.blit(label, label.get_rect(midleft=(rect.x + 16, rect.centery)))
        foot = fit_text_surface(self.tiny_font, footer, (225, 205, 169), panel.width - 60, 25)
        self.screen.blit(foot, foot.get_rect(center=(panel.centerx, panel.bottom - 29)))
        self.screen.set_clip(previous_clip)
