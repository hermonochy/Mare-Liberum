from ..common import *


class CameraMixin:
    def screen_to_world(self, screen_x, screen_y):
        width, height = self.screen.get_size()
        world_x = self.camera_x + (screen_x - width / 2) / self.camera_zoom
        world_y = self.camera_y + (screen_y - height / 2) / self.camera_zoom
        return world_x, world_y

    def zoom(self, amount, anchor=None):
        width, height = self.screen.get_size()
        if anchor is None:
            anchor = (width / 2, height / 2)
        world_anchor = self.screen_to_world(anchor[0], anchor[1])
        old_zoom = self.camera_zoom
        self.camera_zoom = clamp(self.camera_zoom * amount, 0.30, 2.4)
        if abs(self.camera_zoom - old_zoom) < 0.000001:
            return
        self.camera_x = world_anchor[0] - (anchor[0] - width / 2) / self.camera_zoom
        self.camera_y = world_anchor[1] - (anchor[1] - height / 2) / self.camera_zoom
        self.camera_follow = False

    def recenter_camera(self):
        self.camera_follow = True
        self.camera_x = self.ship_x
        self.camera_y = self.ship_y
        self.toast_message("Chart centred on your ship. Click and drag to pan.", 3.0)

    def world_to_screen(self, x, y):
        width, height = self.screen.get_size()
        sx = (x - self.camera_x) * self.camera_zoom + width / 2
        sy = (y - self.camera_y) * self.camera_zoom + height / 2
        return int(sx), int(sy)

    def polygon_to_screen(self, polygon):
        return [self.world_to_screen(x, y) for x, y in polygon]

    def update_camera(self):
        if self.camera_follow:
            self.camera_x = self.ship_x
            self.camera_y = self.ship_y
