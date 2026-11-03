from ..common import *


class ControlsMixin:
    def handle_keydown(self, event):
        key = event.key
        if self.shipyard_open:
            if self.ship_rename_mode:
                if key == pygame.K_ESCAPE:
                    self.ship_rename_mode = False
                    pygame.key.stop_text_input()
                elif key == pygame.K_BACKSPACE:
                    self.ship_name_input = self.ship_name_input[:-1]
                elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    clean_name = self.ship_name_input.strip()[:24]
                    if clean_name:
                        self.player_ship_name = clean_name
                        self.add_journal(f"Renamed your flagship to {clean_name}.")
                        self.toast_message(f"Your ship shall be known as {clean_name}.", 3.0)
                    self.ship_rename_mode = False
                    pygame.key.stop_text_input()
                return
            if key in (pygame.K_ESCAPE, pygame.K_b):
                self.shipyard_open = False
                return
            if key in (pygame.K_LEFT, pygame.K_a, pygame.K_TAB):
                self.shipyard_tab = (self.shipyard_tab - 1) % len(self.shipyard_tabs)
                self.shipyard_selection = 0
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.shipyard_tab = (self.shipyard_tab + 1) % len(self.shipyard_tabs)
                self.shipyard_selection = 0
            elif key in (pygame.K_UP, pygame.K_w):
                items = self.shipyard_items()
                if items:
                    self.shipyard_selection = (self.shipyard_selection - 1) % len(items)
            elif key in (pygame.K_DOWN, pygame.K_s):
                items = self.shipyard_items()
                if items:
                    self.shipyard_selection = (self.shipyard_selection + 1) % len(items)
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.execute_shipyard_selection()
            return
        if self.conversation:
            if key == pygame.K_ESCAPE:
                self.conversation.finish()
            else:
                self.conversation.handle_key(key)
            return
        if self.journal_open:
            if key in (pygame.K_ESCAPE, pygame.K_j):
                self.journal_open = False
            return
        if self.treasure_chart_open:
            if key in (pygame.K_ESCAPE, pygame.K_t):
                self.treasure_chart_open = False
            return
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_F1:
            self.show_help = not self.show_help
        elif key == pygame.K_j:
            self.journal_open = True
        elif key == pygame.K_t:
            self.treasure_chart_open = True
        elif key == pygame.K_r:
            if not self.try_interact_day_job():
                self.interact_treasure()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.zoom(1.12)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.zoom(1 / 1.12)
        elif key == pygame.K_c:
            self.recenter_camera()
        elif key == pygame.K_o:
            if self.docked_port:
                self.toast_message("The oarsmen are ashore while the ship is moored.", 2.8)
            else:
                self.oars_deployed = not self.oars_deployed
                if self.oars_deployed:
                    rowers = self.player_ship_stats().get("rowers", 8)
                    self.toast_message(f"OARS OUT! {rowers} oarsmen take their benches. Pull against the wind!", 3.6)
                else:
                    self.toast_message("Oars shipped. Let the canvas carry you.", 2.8)
        elif key == pygame.K_q and self.docked_port:
            self.open_port_talk()
        elif key == pygame.K_b:
            if self.docked_port:
                self.open_shipyard()
            else:
                self.toast_message("The shipyard is in port, captain. Make fast alongside first.", 3.0)
        elif key == pygame.K_e:
            if self.docked_port:
                self.undock()
            elif self.near_port:
                speed = math.hypot(self.ship_vx, self.ship_vy)
                if speed > 62:
                    self.toast_message("Too much way on! Reef the sails and come alongside slowly.", 3.0)
                else:
                    self.dock(self.near_port)
            else:
                self.toast_message("No pier nearby. Find a harbour and come in slowly.", 2.5)
        elif key == pygame.K_z:
            self.fire_broadside(-1)
        elif key == pygame.K_x:
            self.fire_broadside(1)
        elif key == pygame.K_f:
            self.set_fleet_order("fight")
        elif key == pygame.K_h:
            self.set_fleet_order("hold_fire")
        elif key == pygame.K_g:
            self.set_fleet_order("gather")
        elif key == pygame.K_v:
            self.set_fleet_order("follow")

    def handle_event(self, event):
        if event.type == pygame.TEXTINPUT and self.shipyard_open and self.ship_rename_mode:
            allowed = "".join(character for character in event.text if character.isprintable())
            self.ship_name_input = (self.ship_name_input + allowed)[:24]
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3):
            if not self.conversation and not self.journal_open and not self.treasure_chart_open and not self.shipyard_open:
                self.camera_dragging = True
                self.camera_drag_last = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 2, 3):
            self.camera_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.camera_dragging:
            if not self.conversation and not self.journal_open and not self.treasure_chart_open and not self.shipyard_open:
                dx = event.pos[0] - self.camera_drag_last[0]
                dy = event.pos[1] - self.camera_drag_last[1]
                self.camera_x -= dx / self.camera_zoom
                self.camera_y -= dy / self.camera_zoom
                self.camera_follow = False
                self.camera_drag_last = event.pos
        elif event.type == pygame.MOUSEWHEEL and not self.conversation and not self.journal_open and not self.treasure_chart_open and not self.shipyard_open:
            anchor = getattr(event, "mouse_pos", None)
            if anchor is None and hasattr(event, "mouse_x") and hasattr(event, "mouse_y"):
                anchor = (event.mouse_x, event.mouse_y)
            if anchor is None:
                anchor = pygame.mouse.get_pos()
            self.zoom(1.12 ** event.y, anchor)
        elif event.type == pygame.QUIT:
            self.running = False
