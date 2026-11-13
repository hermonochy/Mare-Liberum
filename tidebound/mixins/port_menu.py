from ..common import *


class PortMenuMixin:
    PORT_MENU_PAGES = (
        ("PORT", (("overview", "Port Overview"), ("trade", "Trade & Cargo"), ("jobs", "Job Board"), ("harbourmaster", "Special Jobs"))),
        ("VESSELS", (("shipyard", "Shipyard"), ("outfitter", "Outfitter"), ("repairs", "Repairs"), ("fleet", "Fleet Orders"))),
        ("CAPTAIN", (("diplomacy", "Diplomacy"), ("captain", "Captain's Log"))),
    )

    def initialise_port_menu(self):
        self.port_menu_open = False
        self.port_menu_page = "overview"
        self.port_menu_selection = 0
        self.port_menu_fleet_scroll = 0
        self.port_menu_ship_selection = -1
        self.port_menu_list_scroll = 0
        self.port_menu_faction_selection = 0
        self.port_menu_thumbnail_cache = {}
        self.port_menu_nav_group = 0

    def open_port_menu(self, page="overview"):
        if not self.docked_port:
            return False
        page_names = {name for _, entries in self.PORT_MENU_PAGES for name, _ in entries}
        self.port_menu_page = page if page in page_names else "overview"
        self.port_menu_open = True
        self.port_menu_selection = 0
        self.port_menu_fleet_scroll = 0
        self.port_menu_list_scroll = 0
        self.shipyard_open = False
        self.market_open = False
        self.job_board_open = False
        self.diplomacy_open = False
        if self.port_menu_page == "jobs":
            self.ensure_day_job_board(self.docked_port)
        self.cannon_held[-1] = False
        self.cannon_held[1] = False
        return True

    def close_port_menu(self):
        self.port_menu_open = False
        self.port_menu_fleet_scroll = 0

    def port_menu_navigation(self):
        return [(key, label) for _, entries in self.PORT_MENU_PAGES for key, label in entries]

    def port_menu_layout(self):
        width, height = self.screen.get_size()
        panel_width = min(1400, width - 40)
        panel_height = min(860, height - 36)
        panel = pygame.Rect((width - panel_width) // 2, (height - panel_height) // 2, panel_width, panel_height)
        header = pygame.Rect(panel.x + 28, panel.y + 18, panel.width - 56, 82)
        body_y = panel.y + 120
        body_h = panel.bottom - body_y - 48
        nav_w = max(188, min(245, int(panel.width * 0.19)))
        fleet_w = max(246, min(305, int(panel.width * 0.245)))
        nav = pygame.Rect(panel.x + 26, body_y, nav_w, body_h)
        fleet = pygame.Rect(panel.right - 26 - fleet_w, body_y, fleet_w, body_h)
        content = pygame.Rect(nav.right + 24, body_y, fleet.left - nav.right - 48, body_h)
        content_list_w = max(150, int(content.width * 0.405))
        list_rect = pygame.Rect(content.x + 8, content.y + 62, content_list_w - 12, content.height - 78)
        detail_rect = pygame.Rect(list_rect.right + 14, content.y + 62,
                                  content.right - list_rect.right - 22, content.height - 78)
        action_rects = {}
        action_names = self.port_menu_actions()
        action_gap = 8
        if len(action_names) <= 2:
            columns = max(1, len(action_names))
            action_width = max(56, (detail_rect.width - 24 - action_gap * (columns - 1)) // columns)
            total_width = action_width * columns + action_gap * (columns - 1)
            x_start = detail_rect.x + (detail_rect.width - total_width) // 2
            for index, (name, _) in enumerate(action_names):
                action_rects[name] = pygame.Rect(x_start + index * (action_width + action_gap),
                                                  detail_rect.bottom - 41, action_width, 32)
        else:
            columns = 2
            action_width = max(56, (detail_rect.width - 24 - action_gap) // columns)
            rows = (len(action_names) + 1) // 2
            for index, (name, _) in enumerate(action_names):
                row = index // columns
                column = index % columns
                row_count = min(columns, len(action_names) - row * columns)
                row_width = row_count * action_width + (row_count - 1) * action_gap
                x_start = detail_rect.x + (detail_rect.width - row_width) // 2
                action_rects[name] = pygame.Rect(x_start + column * (action_width + action_gap),
                                                  detail_rect.bottom - 40 - (rows - 1 - row) * 38,
                                                  action_width, 32)
        return {"panel": panel, "header": header, "nav": nav, "content": content, "fleet": fleet,
                "list": list_rect, "detail": detail_rect, "actions": action_rects,
                "margin": 20, "body_y": body_y}
    def port_menu_actions(self):
        page = self.port_menu_page
        if page == "overview":
            return [("depart", "Depart")]
        if page == "trade":
            return [("quantity_down", "− Quantity"), ("quantity_up", "+ Quantity"), ("buy", "Buy"), ("sell", "Sell")]
        if page == "jobs":
            return [("toggle_job", "Select / Remove"), ("accept_jobs", "Accept Selected")]
        if page == "shipyard":
            return [("buy_flagship", "Buy as Flagship"), ("hire_escort", "Add as Escort")]
        if page == "outfitter":
            return [("install", "Install Selected Fitting")]
        if page == "repairs":
            return [("repair_selected", "Repair Selected"), ("repair_all", "Repair Entire Fleet")]
        if page == "fleet":
            return [("set_order", "Apply Fleet Order"), ("sell_ship", "Sell Selected Ship"),
                    ("change_livery", "Change Flagship Colours")]
        if page == "diplomacy":
            return [("safe_conduct", "Request Safe Conduct"), ("gift", "Present Gift")]
        if page == "harbourmaster":
            return [("talk", "Special Jobs Ledger")]
        if page == "captain":
            return [("journal", "Open Captain's Log")]
        return []

    def port_menu_ship_records(self):
        records = [{"kind": "flagship", "index": -1, "name": self.player_ship_name,
                    "type": self.current_ship, "hull": self.player_hull,
                    "max_hull": self.player_max_hull, "upgrades": self.upgrades,
                    "customisation": self.ship_customisation}]
        for index, escort in enumerate(self.fleet):
            records.append({"kind": "escort", "index": index, "name": escort.name,
                            "type": escort.ship_type, "hull": escort.hull,
                            "max_hull": escort.max_hull,
                            "upgrades": getattr(escort, "upgrades", {}) or {},
                            "customisation": normalise_ship_customisation(getattr(escort, "customisation", None))})
        return records

    def port_menu_selected_ship(self):
        records = self.port_menu_ship_records()
        selection = max(-1, min(len(records) - 2, int(self.port_menu_ship_selection)))
        self.port_menu_ship_selection = selection
        return records[selection + 1]

    def port_menu_shipyard_items(self):
        items = []
        for name, stats in SHIP_CLASSES.items():
            trade_in = int(SHIP_CLASSES[self.current_ship]["cost"] * 0.48 * (self.player_hull / max(1, self.player_max_hull)))
            flagship_price = max(0, int(stats["cost"]) - trade_in)
            items.append({"key": name, "label": f"{name}  ·  {flagship_price:,}g as flagship",
                          "detail": f"{stats['description']} Hull {stats['hull']}; {stats['guns'] * 2} fitted cannons / {stats['max_cannons']} maximum; cargo {stats['cargo']:.0f}.", "flagship_cost": flagship_price,
                          "escort_cost": max(240, int(stats["cost"] * 0.62))})
        return items

    def port_menu_refit_items(self):
        ship = self.port_menu_selected_ship()
        base_stats = SHIP_CLASSES[ship["type"]]
        upgrades = ship["upgrades"]
        keys = [key for key in base_stats["outfitting"] if key in {"hull", "cannons", "rigging", "rudder", "cargo"}]
        if ship["kind"] == "escort":
            keys = [key for key in keys if key != "cargo"]
        items = []
        titles = {"hull": "Reinforced Hull", "cannons": "Broadside Guns", "rigging": "Fine-cut Rigging",
                  "rudder": "Balanced Rudder", "cargo": "Expanded Cargo Hold"}
        details = {
            "hull": "Strengthens the vessel's maximum hull and restores the added capacity.",
            "cannons": "Adds one gun to each broadside, subject to this class's total cannon limit.",
            "rigging": "Improves sail power and maximum speed.",
            "rudder": "Improves turning response and manoeuvrability.",
            "cargo": "Adds 12 units to the flagship's cargo capacity.",
        }
        for key in keys:
            level = int(upgrades.get(key, 0))
            limit = ship_upgrade_limit(ship["type"], key)
            cost = (self.upgrade_cost(key) if ship["kind"] == "flagship"
                    else ESCORT_UPGRADE_BASE_COSTS.get(key, 300) + level * ESCORT_UPGRADE_COST_STEP)
            fitted = f" Fitted: {base_stats['guns'] * 2 + level * 2}/{base_stats['max_cannons']} cannons." if key == "cannons" else ""
            items.append({"kind": "upgrade", "key": key,
                          "label": f"{titles[key]}  ·  Level {level}/{limit}  ·  {cost:,}g",
                          "detail": details[key] + fitted, "cost": cost, "level": level, "limit": limit,
                          "action": "upgrade" if ship["kind"] == "flagship" else "upgrade_escort"})
        selected = normalise_ship_customisation(ship.get("customisation"))
        for category, title, options in CUSTOMISATION_CATEGORIES:
            for option, values in options.items():
                if not ship_fitting_available(ship["type"], category, option):
                    continue
                installed = selected[category] == option
                price = int(values["price"])
                label = f"{title}: {option}  ·  {'INSTALLED' if installed else f'{price:,}g'}"
                detail = values.get("detail", "A shipwright's custom fitting.")
                if installed:
                    detail = "Currently installed on this vessel. " + detail
                items.append({"kind": "customisation", "category": category, "option": option,
                              "label": label, "detail": detail, "cost": price,
                              "installed": installed, "action": "none" if installed else "customise"})
        return items

    def port_menu_current_items(self):
        page = self.port_menu_page
        if page == "trade":
            return [{"key": good["id"], "label": good["name"], "detail": good["description"]} for good in TRADE_GOODS]
        if page == "jobs":
            return [{"key": job.job_id, "label": job.title,
                     "detail": f"To {job.destination}  ·  {job.reward:,} gold  ·  {job.payload}"} for job in self.day_job_offers.get(self.docked_port, [])]
        if page == "shipyard":
            return self.port_menu_shipyard_items()
        if page == "outfitter":
            return self.port_menu_refit_items()
        if page == "repairs":
            ship = self.port_menu_selected_ship()
            return [{"key": "selected", "label": f"Repair {ship['name']}",
                     "detail": f"Restore hull from {ship['hull']:.0f} to {ship['max_hull']:.0f}.",
                     "cost": max(0, int(ship["max_hull"] - ship["hull"]) * 2)}]
        if page == "fleet":
            orders = (("follow", "Follow in Formation", "Sail in formation and defend the fleet when threatened."),
                      ("gather", "Gather around Flagship", "Regroup in a close protective formation."),
                      ("fight", "Fight Nearby Enemies", "Hunt nearby hostile ships and attack."),
                      ("hold_fire", "Hold Fire", "Maintain formation without shooting or pursuing."))
            return [{"key": key, "label": f"{label}{'  ·  ACTIVE' if self.fleet_order == key else ''}", "detail": detail}
                    for key, label, detail in orders]
        if page == "diplomacy":
            return [{"key": faction, "label": faction,
                     "detail": f"{self.relation_label(self.faction_standing(faction))}  ·  Standing {self.faction_standing(faction):+d}"}
                    for faction in FACTION_NAMES]
        return []

    def port_menu_set_page(self, page):
        if page == "trade" and self.port_attitude(self.ports_by_name[self.docked_port]) == "HOSTILE":
            self.toast_message("The harbour's factors refuse to trade with a hostile captain.", 3.2)
            return
        if page == "jobs":
            self.ensure_day_job_board(self.docked_port)
        self.port_menu_page = page
        self.port_menu_nav_group = next((index for index, (_, entries) in enumerate(self.PORT_MENU_PAGES)
                                         if any(name == page for name, _ in entries)), 0)
        self.port_menu_selection = 0
        self.port_menu_list_scroll = 0
        if page == "diplomacy":
            self.port_menu_faction_selection = max(0, min(len(FACTION_NAMES) - 1, self.port_menu_faction_selection))

    def port_menu_select_ship(self, selection):
        self.port_menu_ship_selection = max(-1, min(len(self.fleet) - 1, selection))
        self.port_menu_selection = 0

    def port_menu_activate_action(self, action):
        page = self.port_menu_page
        items = self.port_menu_current_items()
        selected = items[self.port_menu_selection] if items and self.port_menu_selection < len(items) else None
        if action == "depart":
            self.undock()
            return
        if action == "trade":
            self.port_menu_set_page("trade")
            return
        if action == "jobs":
            self.port_menu_set_page("jobs")
            return
        if action == "shipyard":
            self.port_menu_set_page("shipyard")
            return
        if action == "talk":
            self.open_port_talk()
            return
        if action == "journal":
            self.close_port_menu()
            self.journal_open = True
            return
        if page == "trade" and selected:
            good_id = selected["key"]
            if action == "buy":
                self.buy_trade_cargo(good_id)
            elif action == "sell":
                self.sell_trade_cargo(good_id)
            elif action == "quantity_down":
                self.market_quantity_index = max(0, self.market_quantity_index - 1)
            elif action == "quantity_up":
                self.market_quantity_index = min(2, self.market_quantity_index + 1)
            return
        if page == "jobs":
            if action == "toggle_job" and selected:
                self.toggle_day_job_selection(self.port_menu_selection)
            elif action == "accept_jobs":
                self.accept_selected_day_jobs()
            return
        if page == "shipyard" and selected:
            if action == "buy_flagship":
                if selected["key"] == self.current_ship:
                    self.toast_message("That is already your flagship's ship class.", 2.8)
                    return
                self.execute_shipyard_item({"action": "buy_flagship", "key": selected["key"], "cost": selected["flagship_cost"]})
            elif action == "hire_escort":
                self.execute_shipyard_item({"action": "hire", "key": selected["key"], "cost": selected["escort_cost"]})
            return
        if page == "outfitter" and selected:
            if action == "install":
                ship = self.port_menu_selected_ship()
                if selected.get("kind") == "customisation":
                    self.install_ship_customisation(ship, selected["category"], selected["option"])
                else:
                    key = selected["key"]
                    if selected["level"] >= ship_upgrade_limit(ship["type"], key):
                        self.toast_message("That vessel cannot take another level of this fitting.", 2.8)
                    elif ship["kind"] == "flagship":
                        self.execute_shipyard_item({"action": "upgrade", "key": key})
                    else:
                        self.execute_shipyard_item({"action": "upgrade_escort", "key": f"{ship['index']}:{key}", "cost": selected["cost"]})
            return
        if page == "repairs":
            if action == "repair_selected":
                ship = self.port_menu_selected_ship()
                missing = max(0, int(ship["max_hull"] - ship["hull"]))
                cost = missing * 2
                if not missing:
                    self.toast_message(f"{ship['name']} is already shipshape.", 2.7)
                elif self.gold < cost:
                    self.toast_message(f"Repairs cost {cost} gold. You have {self.gold}.", 3.2)
                elif ship["kind"] == "flagship":
                    self.execute_shipyard_item({"action": "repair_flagship", "key": ""})
                else:
                    escort = self.fleet[ship["index"]]
                    self.gold -= cost
                    escort.hull = escort.max_hull
                    self.toast_message(f"{escort.name} fully repaired for {cost} gold.", 3.0)
                return
            if action == "repair_all":
                missing_flagship = max(0, self.player_max_hull - self.player_hull)
                missing_fleet = sum(max(0, escort.max_hull - escort.hull) for escort in self.fleet)
                total_cost = (missing_flagship + missing_fleet) * 2
                if total_cost == 0:
                    self.toast_message("Your entire fleet is already shipshape.", 2.8)
                elif self.gold < total_cost:
                    self.toast_message(f"Fleet-wide repairs cost {total_cost:,} gold. You have {self.gold:,}.", 3.4)
                else:
                    self.gold -= total_cost
                    self.player_hull = self.player_max_hull
                    for escort in self.fleet:
                        escort.hull = escort.max_hull
                    self.toast_message(f"The entire fleet has been repaired for {total_cost:,} gold.", 3.5)
                return
        if page == "fleet" and selected:
            if action == "set_order":
                self.set_fleet_order(selected["key"])
            elif action == "sell_ship":
                self.port_menu_sell_selected_ship()
            elif action == "change_livery":
                self.player_livery = (self.player_livery + 1) % len(SHIP_LIVERIES)
                self.toast_message(f"New livery: {SHIP_LIVERIES[self.player_livery][0]}.", 2.8)
            return
        if page == "diplomacy" and selected:
            faction = selected["key"]
            self.port_menu_faction_selection = FACTION_NAMES.index(faction)
            if action == "gift":
                self.offer_diplomatic_gift(faction)
            elif action == "safe_conduct":
                self.request_safe_conduct(faction)
            return

    def port_menu_sell_selected_ship(self):
        selected = self.port_menu_selected_ship()
        if selected["kind"] == "escort":
            escort = self.fleet[selected["index"]]
            base = int(SHIP_CLASSES[escort.ship_type]["cost"])
            value = max(90, int(base * 0.56 * max(0.25, escort.hull / max(1, escort.max_hull))))
            self.fleet.remove(escort)
            self.gold += value
            self.port_menu_ship_selection = -1
            self.toast_message(f"Sold {escort.name} for {value:,} gold.", 3.4)
            self.add_journal(f"Sold escort {escort.name} at {self.docked_port} for {value} gold.")
            return
        if not self.fleet:
            self.toast_message("You cannot sell your only ship. Commission a replacement or add an escort first.", 3.5)
            return
        promote_index = next((index for index, escort in enumerate(self.fleet) if escort.hull > 0), None)
        if promote_index is None:
            self.toast_message("No surviving escort can take the flagship's place.", 3.3)
            return
        promoted = self.fleet.pop(promote_index)
        old_name = self.player_ship_name
        port = self.ports_by_name[self.docked_port]
        self.ship_x, self.ship_y = self.harbour_berth_position(port, self.player_berth_slot)
        self.ship_heading = port.exit_heading
        self.ship_vx = 0.0
        self.ship_vy = 0.0
        base = int(SHIP_CLASSES[self.current_ship]["cost"])
        value = max(90, int(base * 0.56 * max(0.25, self.player_hull / max(1, self.player_max_hull))))
        self.current_ship = promoted.ship_type
        self.player_ship_name = promoted.name[:24]
        self.ship_customisation = normalise_ship_customisation(getattr(promoted, "customisation", None))
        self.upgrades = {key: int(value) for key, value in getattr(promoted, "upgrades", {}).items()}
        for key in ("cannons", "hull", "rigging", "rudder", "cargo"):
            self.upgrades.setdefault(key, 0)
            self.upgrades[key] = min(self.upgrades[key], ship_upgrade_limit(self.current_ship, key))
        hull_ratio = max(0.0, min(1.0, promoted.hull / max(1, promoted.max_hull)))
        self.player_max_hull = self.player_ship_stats()["hull"]
        self.player_hull = max(1, min(self.player_max_hull, int(self.player_max_hull * hull_ratio)))
        self.cannon_held = {-1: False, 1: False}
        self.cannon_first_volley_fired = {-1: False, 1: False}
        self.cannon_battery_timers = {-1: [], 1: []}
        self.cannon_battery_rates = {-1: [], 1: []}
        self.chaser_cooldowns = {"bow": 0.0, "stern": 0.0}
        self.ship_surface_cache = {}
        self.gold += value
        self.port_menu_ship_selection = -1
        self.toast_message(f"Sold {old_name}; {promoted.name} has taken the flagship's place. Received {value:,} gold.", 4.5)
        self.add_journal(f"Sold flagship {old_name} for {value} gold and promoted {promoted.name} to flagship.")

    def handle_port_menu_key(self, key):
        if self.conversation:
            if key == pygame.K_ESCAPE:
                self.conversation.finish()
            else:
                self.conversation.handle_key(key)
            return
        if self.ship_rename_mode:
            if key == pygame.K_ESCAPE:
                self.ship_rename_mode = False
                pygame.key.stop_text_input()
            elif key == pygame.K_BACKSPACE:
                self.ship_name_input = self.ship_name_input[:-1]
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                name = self.ship_name_input.strip()[:24]
                if name:
                    ship = self.port_menu_selected_ship()
                    if ship["kind"] == "flagship":
                        self.player_ship_name = name
                    else:
                        self.fleet[ship["index"]].name = name
                    self.used_ship_names.add(name)
                    self.add_journal(f"Renamed a vessel to {name} at {self.docked_port}.")
                    self.toast_message(f"Vessel renamed to {name}.", 3.0)
                self.ship_rename_mode = False
                pygame.key.stop_text_input()
            return
        if key == pygame.K_ESCAPE:
            self.close_port_menu()
            return
        if key in (pygame.K_UP, pygame.K_w):
            items = self.port_menu_current_items()
            self.port_menu_selection = (self.port_menu_selection - 1) % max(1, len(items))
            self.port_menu_ensure_list_visible()
        elif key in (pygame.K_DOWN, pygame.K_s):
            items = self.port_menu_current_items()
            self.port_menu_selection = (self.port_menu_selection + 1) % max(1, len(items))
            self.port_menu_ensure_list_visible()
        elif key in (pygame.K_LEFT, pygame.K_a):
            if self.port_menu_page == "trade":
                self.market_quantity_index = max(0, self.market_quantity_index - 1)
            else:
                pages = [key for key, _ in self.port_menu_navigation()]
                index = pages.index(self.port_menu_page)
                self.port_menu_set_page(pages[(index - 1) % len(pages)])
        elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
            if self.port_menu_page == "trade":
                self.market_quantity_index = min(2, self.market_quantity_index + 1)
            else:
                pages = [key for key, _ in self.port_menu_navigation()]
                index = pages.index(self.port_menu_page)
                self.port_menu_set_page(pages[(index + 1) % len(pages)])
        elif key == pygame.K_SPACE and self.port_menu_page == "jobs":
            self.port_menu_activate_action("toggle_job")
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            defaults = {"overview": "depart", "trade": "buy", "jobs": "accept_jobs", "shipyard": "buy_flagship",
                        "outfitter": "install", "repairs": "repair_selected", "fleet": "set_order",
                        "diplomacy": "gift", "harbourmaster": "talk", "captain": "journal"}
            action = defaults.get(self.port_menu_page)
            if action:
                self.port_menu_activate_action(action)
        elif key == pygame.K_e and self.docked_port:
            self.undock()
        elif key == pygame.K_b:
            self.port_menu_set_page("shipyard")
        elif key == pygame.K_y:
            self.port_menu_set_page("trade")
        elif key == pygame.K_q:
            self.port_menu_set_page("harbourmaster")

    def handle_port_menu_click(self, position):
        if self.conversation:
            return True
        layout = self.port_menu_layout()
        nav = layout["nav"]
        if layout["header"].collidepoint(position):
            return True
        nav_y = nav.y + 55
        for group_index, (group, entries) in enumerate(self.PORT_MENU_PAGES):
            group_row = pygame.Rect(nav.x + 3, nav_y, nav.width - 10, 31)
            if group_row.collidepoint(position):
                self.port_menu_nav_group = group_index
                return True
            nav_y += 34
            if group_index == self.port_menu_nav_group:
                for page, label in entries:
                    row = pygame.Rect(nav.x + 12, nav_y, nav.width - 22, 31)
                    if row.collidepoint(position):
                        self.port_menu_set_page(page)
                        return True
                    nav_y += 34
            nav_y += 6
        fleet = layout["fleet"]
        ship_rows = self.port_menu_ship_row_rects(fleet)
        records = self.port_menu_ship_records()
        visible_ships = max(1, len(ship_rows))
        ship_start = max(0, min(self.port_menu_fleet_scroll, max(0, len(records) - visible_ships)))
        for visible_index, row in enumerate(ship_rows):
            if row.collidepoint(position):
                self.port_menu_select_ship(ship_start + visible_index - 1)
                return True
        sidebar_actions = self.port_menu_sidebar_action_rects(fleet)
        if sidebar_actions["rename"].collidepoint(position):
            selected_ship = self.port_menu_selected_ship()
            self.ship_name_input = selected_ship["name"]
            self.ship_rename_mode = True
            pygame.key.start_text_input()
            return True
        if sidebar_actions["refit"].collidepoint(position):
            self.port_menu_set_page("outfitter")
            return True
        if sidebar_actions["sell"].collidepoint(position):
            self.port_menu_sell_selected_ship()
            return True
        if fleet.collidepoint(position):
            return True
        list_rect = layout["list"]
        items = self.port_menu_current_items()
        rows = self.port_menu_item_row_rects(list_rect, len(items))
        visible_rows = max(1, len(rows))
        list_start = max(0, min(self.port_menu_list_scroll, max(0, len(items) - visible_rows)))
        for visible_index, row in enumerate(rows):
            if row.collidepoint(position):
                index = list_start + visible_index
                self.port_menu_selection = index
                if self.port_menu_page == "jobs":
                    self.toggle_day_job_selection(index)
                return True
        for action, rect in layout["actions"].items():
            if rect.collidepoint(position):
                self.port_menu_activate_action(action)
                return True
        if self.port_menu_page == "shipyard" and layout["detail"].collidepoint(position):
            if len(layout["actions"]) >= 2:
                first_action = next(iter(layout["actions"]))
                self.port_menu_activate_action(first_action)
            return True
        return True

    def port_menu_ensure_list_visible(self):
        items = self.port_menu_current_items()
        list_rect = self.port_menu_layout()["list"]
        row_height = max(36, min(54, (list_rect.height - 8) // max(1, min(len(items), 12))))
        visible = max(1, (list_rect.height - 8) // row_height)
        if self.port_menu_selection < self.port_menu_list_scroll:
            self.port_menu_list_scroll = self.port_menu_selection
        elif self.port_menu_selection >= self.port_menu_list_scroll + visible:
            self.port_menu_list_scroll = self.port_menu_selection - visible + 1
        self.port_menu_list_scroll = max(0, min(self.port_menu_list_scroll, max(0, len(items) - visible)))

    def handle_port_menu_scroll(self, direction, position=None):
        layout = self.port_menu_layout()
        if position and layout["fleet"].collidepoint(position):
            visible = max(1, len(self.port_menu_ship_row_rects(layout["fleet"])))
            records = self.port_menu_ship_records()
            self.port_menu_fleet_scroll = max(0, min(max(0, len(records) - visible), self.port_menu_fleet_scroll + direction))
            return
        items = self.port_menu_current_items()
        self.port_menu_selection = max(0, min(max(0, len(items) - 1), self.port_menu_selection + direction))
        self.port_menu_ensure_list_visible()

    def port_menu_item_row_rects(self, rect, count):
        row_h = max(36, min(54, (rect.height - 8) // max(1, min(count, 12))))
        visible = max(1, (rect.height - 8) // row_h)
        start = max(0, min(self.port_menu_list_scroll, max(0, count - visible)))
        return [pygame.Rect(rect.x + 4, rect.y + 4 + index * row_h, rect.width - 8, row_h - 4)
                for index in range(min(visible, count - start))]

    def port_menu_ship_row_rects(self, rect):
        row_h = 92
        visible = max(1, (rect.height - 196) // row_h)
        records = self.port_menu_ship_records()
        start = max(0, min(self.port_menu_fleet_scroll, max(0, len(records) - visible)))
        return [pygame.Rect(rect.x + 12, rect.y + 56 + index * row_h, rect.width - 24, row_h - 6)
                for index in range(min(visible, len(records) - start))]

    def port_menu_sidebar_action_rects(self, rect):
        gap = 7
        button_width = (rect.width - 24 - gap) // 2
        top = rect.bottom - 86
        rename = pygame.Rect(rect.x + 12, top, button_width, 31)
        refit = pygame.Rect(rename.right + gap, top, button_width, 31)
        sell = pygame.Rect(rect.x + 12, rect.bottom - 47, rect.width - 24, 31)
        return {"rename": rename, "refit": refit, "sell": sell}
    def draw_port_menu_panel(self, rect, fill=(224, 207, 163), border=(144, 105, 66), radius=6):
        pygame.draw.rect(self.screen, (45, 27, 18), rect.inflate(10, 10), border_radius=8)
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        pygame.draw.rect(self.screen, border, rect, 3, border_radius=radius)
        inner = rect.inflate(-8, -8)
        if inner.width > 2 and inner.height > 2:
            pygame.draw.rect(self.screen, (241, 226, 190), inner, 1, border_radius=max(2, radius - 2))
    def draw_port_menu_text(self, text, pos, color=(70, 53, 37), width=None, font=None):
        font = font or self.small_font
        max_width = width or self.screen.get_width()
        lines = wrap_text(font, str(text), max_width)
        step = font.get_linesize() + 3
        for index, line in enumerate(lines):
            self.screen.blit(font.render(line, True, color), (pos[0], pos[1] + index * step))
        return len(lines) * step
    def draw_port_menu(self):
        if not self.port_menu_open or not self.docked_port:
            return
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((9, 17, 19, 190))
        self.screen.blit(overlay, (0, 0))
        layout = self.port_menu_layout()
        port = self.ports_by_name[self.docked_port]
        faction = port.faction
        standing = self.faction_standing(faction)
        panel = layout["panel"]
        self.draw_port_menu_panel(panel)
        header = layout["header"]
        title = fit_text_surface(self.title_font, self.docked_port.upper(), (75, 44, 27), header.width * 0.50, 42)
        self.screen.blit(title, (header.x + 8, header.y + 3))
        subtitle = fit_text_surface(self.small_font,
            f"{port.region}  ·  {faction}  ·  {self.relation_label(standing)} ({standing:+d})",
            (97, 66, 42), header.width * 0.58, 26)
        self.screen.blit(subtitle, (header.x + 10, header.y + 48))
        balance = fit_text_surface(self.font, f"{self.gold:,} gold", (73, 47, 31), 230, 30)
        self.screen.blit(balance, balance.get_rect(topright=(header.right - 9, header.y + 10)))
        cargo_line = fit_text_surface(self.small_font,
            f"Cargo {self.cargo_load():.1f}/{self.cargo_capacity():.0f}  ·  Escorts {sum(1 for ship in self.fleet if ship.hull > 0)}  ·  Hull {self.player_hull:.0f}/{self.player_max_hull}",
            (104, 74, 48), header.width * 0.43, 24)
        self.screen.blit(cargo_line, cargo_line.get_rect(topright=(header.right - 9, header.y + 47)))
        pygame.draw.line(self.screen, (160, 125, 80), (panel.x + 25, header.bottom + 5),
                         (panel.right - 25, header.bottom + 5), 2)
        nav = layout["nav"]
        content = layout["content"]
        fleet = layout["fleet"]
        pygame.draw.line(self.screen, (160, 125, 80), (nav.right + 12, nav.y + 2),
                         (nav.right + 12, nav.bottom - 2), 1)
        pygame.draw.line(self.screen, (160, 125, 80), (fleet.x - 12, fleet.y + 2),
                         (fleet.x - 12, fleet.bottom - 2), 1)
        nav_heading = fit_text_surface(self.small_font, "HARBOUR SERVICES", (83, 52, 32), nav.width - 12, 25)
        self.screen.blit(nav_heading, (nav.x + 5, nav.y + 11))
        pygame.draw.line(self.screen, (177, 143, 96), (nav.x + 4, nav.y + 42),
                         (nav.right - 4, nav.y + 42), 1)
        nav_y = nav.y + 55
        for group_index, (group, entries) in enumerate(self.PORT_MENU_PAGES):
            group_row = pygame.Rect(nav.x + 3, nav_y, nav.width - 10, 31)
            expanded = group_index == self.port_menu_nav_group
            group_label = fit_text_surface(self.font, f"{'▾' if expanded else '▸'}  {group.title()}",
                                           (83, 52, 32) if expanded else (110, 81, 53), nav.width - 26, 25)
            self.screen.blit(group_label, (group_row.x + 5, group_row.centery - group_label.get_height() // 2))
            nav_y += 34
            if expanded:
                for page, label in entries:
                    row = pygame.Rect(nav.x + 12, nav_y, nav.width - 22, 31)
                    selected = self.port_menu_page == page
                    if selected:
                        pygame.draw.rect(self.screen, (193, 171, 130), row, border_radius=4)
                        pygame.draw.rect(self.screen, (144, 105, 66), row, 1, border_radius=4)
                    color = (65, 43, 29) if selected else (92, 68, 45)
                    label_surface = fit_text_surface(self.small_font, label, color, row.width - 16, row.height - 4)
                    self.screen.blit(label_surface, (row.x + 8, row.centery - label_surface.get_height() // 2))
                    nav_y += 34
            pygame.draw.line(self.screen, (194, 168, 124), (nav.x + 8, nav_y),
                             (nav.right - 8, nav_y), 1)
            nav_y += 6
        nav_footer = fit_text_surface(self.tiny_font, "ESC: close  ·  E: depart", (104, 74, 48), nav.width - 12, 22)
        self.screen.blit(nav_footer, nav_footer.get_rect(midbottom=(nav.centerx, nav.bottom - 8)))
        fleet_heading = fit_text_surface(self.small_font, "YOUR SHIPS", (83, 52, 32), fleet.width - 12, 25)
        self.screen.blit(fleet_heading, (fleet.x + 5, fleet.y + 11))
        count = fit_text_surface(self.tiny_font, f"{len(self.port_menu_ship_records())} vessels", (104, 74, 48), fleet.width - 14, 20)
        self.screen.blit(count, count.get_rect(topright=(fleet.right - 5, fleet.y + 15)))
        pygame.draw.line(self.screen, (177, 143, 96), (fleet.x + 4, fleet.y + 42),
                         (fleet.right - 4, fleet.y + 42), 1)
        self.draw_port_menu_content(layout)
        self.draw_port_menu_fleet(layout)
        footer = fit_text_surface(self.tiny_font,
            "Select a service or vessel  ·  Arrow keys / mouse wheel: browse  ·  Enter: confirm  ·  Esc: close",
            (104, 74, 48), panel.width - 52, 22)
        self.screen.blit(footer, footer.get_rect(midbottom=(panel.centerx, panel.bottom - 13)))
        for action, rect in layout["actions"].items():
            pygame.draw.rect(self.screen, (111, 72, 41), rect, border_radius=5)
            pygame.draw.rect(self.screen, (145, 104, 66), rect, 2, border_radius=5)
            label = dict(self.port_menu_actions()).get(action, action.replace("_", " ").title())
            label_surface = fit_text_surface(self.small_font, label, (248, 221, 172), rect.width - 8, rect.height - 6)
            self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def draw_port_menu_content(self, layout):
        content = layout["content"]
        page = self.port_menu_page
        page_titles = {"overview": "HARBOUR OVERVIEW", "trade": "TRADE & CARGO", "jobs": "AVAILABLE WORK",
                       "shipyard": "SHIPYARD", "outfitter": "OUTFITTER", "repairs": "REPAIRS & REFITS",
                       "fleet": "FLEET ORDERS", "diplomacy": "DIPLOMACY", "harbourmaster": "HARBOURMASTER",
                       "captain": "CAPTAIN'S LOG"}
        title = fit_text_surface(self.title_font, page_titles.get(page, page.upper()), (75, 44, 27), content.width - 18, 34)
        self.screen.blit(title, (content.x + 7, content.y + 8))
        pygame.draw.line(self.screen, (177, 143, 96), (content.x + 6, content.y + 45),
                         (content.right - 6, content.y + 45), 1)
        if page == "overview":
            port = self.ports_by_name[self.docked_port]
            y = content.y + 68
            status = f"{port.region}  ·  {port.faction}  ·  {self.relation_label(self.faction_standing(port.faction))}"
            status_surf = fit_text_surface(self.small_font, status, (104, 74, 48), content.width - 20, 25)
            self.screen.blit(status_surf, (content.x + 9, y))
            y += 42
            y += self.draw_port_menu_text(port.description, (content.x + 10, y), (65, 49, 34), content.width - 20, self.font) + 20
            news_heading = fit_text_surface(self.small_font, "HARBOUR NEWS", (83, 52, 32), content.width - 20, 26)
            self.screen.blit(news_heading, (content.x + 10, y))
            y += 34
            pygame.draw.line(self.screen, (177, 143, 96), (content.x + 10, y), (content.right - 10, y), 1)
            y += 13
            news = self.news_by_port.get(port.name, "The harbour is full of rumours, though none worth repeating.")
            self.draw_port_menu_text(news, (content.x + 10, y), (92, 68, 45), content.width - 20, self.small_font)
            return
        if page == "harbourmaster":
            info = "The harbourmaster handles special commissions and unusual contracts. Ordinary repeatable work is listed on the Job Board."
            self.draw_port_menu_text(info, (content.x + 10, content.y + 72), (65, 49, 34), content.width - 20, self.font)
            hint = "Choose the Special Jobs Ledger action below to speak with the harbourmaster."
            self.draw_port_menu_text(hint, (content.x + 10, content.y + 145), (104, 74, 48), content.width - 20, self.small_font)
            return
        if page == "captain":
            active = self.active_mission()
            objective = self.mission_guidance_text(active) if active else "No active story voyage."
            lines = [f"Flagship: {self.player_ship_name} ({self.current_ship})", f"Hull: {self.player_hull:.0f}/{self.player_max_hull}",
                     f"Crew: {self.player_ship_stats().get('crew', 0)}", f"Fleet size: {len(self.fleet)} escorts",
                     f"Cargo: {self.cargo_load():.1f}/{self.cargo_capacity():.0f}", f"Current voyage: {active.name if active else 'None'}",
                     f"Objective: {objective}", f"Completed day jobs: {self.completed_day_jobs}"]
            y = content.y + 67
            for line in lines:
                y += self.draw_port_menu_text(line, (content.x + 10, y), (65, 49, 34), content.width - 20, self.small_font) + 7
            return
        items = self.port_menu_current_items()
        list_rect = layout["list"]
        detail_rect = layout["detail"]
        pygame.draw.rect(self.screen, (213, 195, 157), list_rect, border_radius=4)
        pygame.draw.rect(self.screen, (155, 118, 73), list_rect, 1, border_radius=4)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        row_rects = self.port_menu_item_row_rects(list_rect, len(items))
        start = max(0, min(self.port_menu_list_scroll, max(0, len(items) - len(row_rects))))
        for visible_index, row in enumerate(row_rects):
            index = start + visible_index
            item = items[index]
            selected = index == self.port_menu_selection
            background = (193, 171, 130) if selected else ((225, 210, 177) if index % 2 == 0 else (214, 197, 161))
            pygame.draw.rect(self.screen, background, row, border_radius=4)
            if selected:
                pygame.draw.rect(self.screen, (144, 105, 66), row, 2, border_radius=4)
            label = fit_text_surface(self.small_font, item["label"], (65, 43, 29) if selected else (77, 58, 39), row.width - 18, row.height - 6)
            self.screen.blit(label, (row.x + 9, row.centery - label.get_height() // 2))
            if page == "jobs":
                job = self.day_job_offers.get(self.docked_port, [])[index]
                if job.job_id in self.job_board_selected_ids:
                    mark = self.tiny_font.render("✓", True, (48, 103, 55))
                    self.screen.blit(mark, mark.get_rect(midright=(row.right - 7, row.centery)))
        self.screen.set_clip(previous_clip)
        pygame.draw.line(self.screen, (177, 143, 96), (detail_rect.x - 8, detail_rect.y + 2),
                         (detail_rect.x - 8, detail_rect.bottom - 3), 1)
        if not items:
            self.draw_port_menu_text("No entries are available here just now.",
                                     (detail_rect.x + 13, detail_rect.y + 20), (104, 74, 48), detail_rect.width - 24)
            return
        selected_index = max(0, min(len(items) - 1, self.port_menu_selection))
        selected_item = items[selected_index]
        selected_heading = fit_text_surface(self.title_font, selected_item["label"].split("  ·  ")[0],
                                             (75, 44, 27), detail_rect.width - 22, 34)
        self.screen.blit(selected_heading, (detail_rect.x + 10, detail_rect.y + 10))
        pygame.draw.line(self.screen, (177, 143, 96), (detail_rect.x + 10, detail_rect.y + 47),
                         (detail_rect.right - 9, detail_rect.y + 47), 1)
        details_y = detail_rect.y + 59
        detail_text = selected_item.get("detail", "")
        details_y += self.draw_port_menu_text(detail_text, (detail_rect.x + 12, details_y),
                                               (75, 56, 38), detail_rect.width - 24, self.small_font) + 15
        detail_bottom = detail_rect.bottom - (88 if len(layout["actions"]) > 2 else 50)
        if page == "trade":
            good_id = selected_item["key"]
            good = TRADE_GOODS_BY_ID[good_id]
            buy_price = self.market_buy_price(self.docked_port, good_id)
            sell_price = self.market_sell_price(self.docked_port, good_id)
            stock = (self.market_record(self.docked_port, good_id) or {}).get("stock", 0)
            values = [f"Buy price: {buy_price:,} gold each", f"Sell price: {sell_price:,} gold each",
                      f"Port stock: {stock:.0f}", f"Cargo aboard: {self.cargo_quantity(good_id)}",
                      f"Space per unit: {good['space']:.1f}", f"Selected quantity: {self.selected_trade_quantity()}"]
            for line in values:
                if details_y > detail_bottom:
                    break
                surf = fit_text_surface(self.small_font, line, (73, 47, 31), detail_rect.width - 24, 25)
                self.screen.blit(surf, (detail_rect.x + 12, details_y))
                details_y += 29
        elif page == "jobs":
            job = self.day_job_offers.get(self.docked_port, [])[selected_index]
            details_y += self.draw_port_menu_text(job.offer_text, (detail_rect.x + 12, details_y),
                                                   (75, 56, 38), detail_rect.width - 24, self.small_font) + 12
            for line in (f"Destination: {job.destination}", f"Reward: {job.reward:,} gold", f"Cargo: {job.payload}"):
                if details_y > detail_bottom:
                    break
                surf = fit_text_surface(self.small_font, line, (104, 74, 48), detail_rect.width - 24, 25)
                self.screen.blit(surf, (detail_rect.x + 12, details_y))
                details_y += 27
        elif page == "shipyard":
            stats = SHIP_CLASSES[selected_item["key"]]
            values = [f"Hull: {stats['hull']}", f"Broadside guns: {stats['guns']}",
                      f"Top speed: {stats['speed']:.0f}", f"Escort price: {selected_item['escort_cost']:,} gold",
                      f"Flagship price after trade-in: {selected_item['flagship_cost']:,} gold"]
            for line in values:
                if details_y > detail_bottom:
                    break
                surf = fit_text_surface(self.small_font, line, (73, 47, 31), detail_rect.width - 24, 25)
                self.screen.blit(surf, (detail_rect.x + 12, details_y))
                details_y += 29
        elif page == "outfitter":
            ship = self.port_menu_selected_ship()
            values = [f"Installed on: {ship['name']} ({ship['type']})"]
            if selected_item.get("kind") == "customisation":
                values.extend([f"Category: {dict((key, title) for key, title, _ in CUSTOMISATION_CATEGORIES)[selected_item['category']]}",
                               f"Fitting: {selected_item['option']}",
                               "Already installed" if selected_item["installed"] else f"Installation: {selected_item['cost']:,} gold"])
            else:
                values.extend([f"Current level: {selected_item['level']}/{selected_item['limit']}",
                               f"Next installation: {selected_item['cost']:,} gold"])
            for line in values:
                if details_y > detail_bottom:
                    break
                surf = fit_text_surface(self.small_font, line, (73, 47, 31), detail_rect.width - 24, 25)
                self.screen.blit(surf, (detail_rect.x + 12, details_y))
                details_y += 29
        elif page == "repairs":
            surf = fit_text_surface(self.small_font, f"Repair cost: {selected_item['cost']:,} gold",
                                    (73, 47, 31), detail_rect.width - 24, 25)
            self.screen.blit(surf, (detail_rect.x + 12, details_y))
        elif page == "diplomacy":
            faction = selected_item["key"]
            count = sum(port.faction == faction for port in self.ports)
            econ = self.faction_economy_summary(faction)
            values = [f"Standing: {self.faction_standing(faction):+d}", f"Attitude: {self.faction_attitude(faction)}",
                      f"Harbours: {count}", f"Treasury: {econ['treasury']:,} gold",
                      f"Prosperity: {econ['prosperity']:.0f}/100"]
            for line in values:
                if details_y > detail_bottom:
                    break
                surf = fit_text_surface(self.small_font, line, (73, 47, 31), detail_rect.width - 24, 25)
                self.screen.blit(surf, (detail_rect.x + 12, details_y))
                details_y += 29
        elif page == "fleet":
            values = [f"Current order: {self.fleet_order.replace('_', ' ').title()}",
                      f"Flagship colours: {SHIP_LIVERIES[self.player_livery][0]}",
                      "Select any vessel in Your Ships to sell it. Selling the flagship promotes a surviving escort."]
            for line in values:
                details_y += self.draw_port_menu_text(line, (detail_rect.x + 12, details_y),
                                                       (73, 47, 31), detail_rect.width - 24, self.small_font) + 8
    def draw_port_menu_fleet(self, layout):
        rect = layout["fleet"]
        records = self.port_menu_ship_records()
        row_rects = self.port_menu_ship_row_rects(rect)
        visible = max(1, len(row_rects))
        start = max(0, min(self.port_menu_fleet_scroll, max(0, len(records) - visible)))
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(rect.inflate(-4, -4))
        for visible_index, row in enumerate(row_rects):
            record_index = start + visible_index
            ship = records[record_index]
            selected = record_index - 1 == self.port_menu_ship_selection
            background = (193, 171, 130) if selected else ((225, 210, 177) if record_index % 2 == 0 else (214, 197, 161))
            pygame.draw.rect(self.screen, background, row, border_radius=4)
            if selected:
                pygame.draw.rect(self.screen, (144, 105, 66), row, 2, border_radius=4)
            tag = "FLAGSHIP" if ship["kind"] == "flagship" else "ESCORT"
            customisation = normalise_ship_customisation(ship.get("customisation"))
            customisation_key = tuple(sorted(customisation.items()))
            thumbnail_key = (ship["kind"], ship["type"], self.player_livery if ship["kind"] == "flagship" else None,
                             customisation_key)
            thumbnail = self.port_menu_thumbnail_cache.get(thumbnail_key)
            if thumbnail is None:
                base_thumbnail = self.create_ship_surface(player=ship["kind"] == "flagship",
                    allied=ship["kind"] == "escort", ship_type=ship["type"], customisation=customisation)
                thumbnail = pygame.transform.smoothscale(base_thumbnail, (82, 60))
                self.port_menu_thumbnail_cache[thumbnail_key] = thumbnail
            self.screen.blit(thumbnail, (row.x + 3, row.y + 7))
            text_x = row.x + 90
            tag_surface = fit_text_surface(self.tiny_font, tag, (104, 74, 48), row.width - 98, 18)
            self.screen.blit(tag_surface, (text_x, row.y + 7))
            name = fit_text_surface(self.small_font, ship["name"], (65, 43, 29), row.width - 98, 22)
            self.screen.blit(name, (text_x, row.y + 27))
            condition = max(0.0, min(1.0, ship["hull"] / max(1.0, ship["max_hull"])))
            bar = pygame.Rect(text_x, row.bottom - 16, max(10, row.width - 106), 6)
            pygame.draw.rect(self.screen, (93, 70, 48), bar, border_radius=2)
            pygame.draw.rect(self.screen, (145, 104, 66), pygame.Rect(bar.x, bar.y, int(bar.width * condition), bar.height), border_radius=2)
        self.screen.set_clip(previous_clip)
        selected = self.port_menu_selected_ship()
        info_y = rect.bottom - 124
        pygame.draw.line(self.screen, (177, 143, 96), (rect.x + 5, info_y - 9),
                         (rect.right - 5, info_y - 9), 1)
        selected_label = (f"Rename vessel: {self.ship_name_input or selected['name']}  ·  Enter to confirm" if self.ship_rename_mode
                          else f"{selected['type']}  ·  {selected['hull']:.0f}/{selected['max_hull']:.0f} hull")
        selected_text = fit_text_surface(self.tiny_font, selected_label,
                                          (104, 74, 48), rect.width - 20, 20)
        self.screen.blit(selected_text, (rect.x + 8, info_y))
        actions = self.port_menu_sidebar_action_rects(rect)
        for key, label in (("rename", "Rename"), ("refit", "Outfit / Refit"), ("sell", "Sell Selected Vessel")):
            action_rect = actions[key]
            pygame.draw.rect(self.screen, (111, 72, 41), action_rect, border_radius=5)
            pygame.draw.rect(self.screen, (145, 104, 66), action_rect, 2, border_radius=5)
            label_surface = fit_text_surface(self.small_font, label, (248, 221, 172), action_rect.width - 8, 23)
            self.screen.blit(label_surface, label_surface.get_rect(center=action_rect.center))
