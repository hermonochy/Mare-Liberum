"""Small, resilient Pygame audio layer for Mare Liberum."""
from pathlib import Path
import random

import pygame


class AudioEngine:
    def __init__(self, audio_directory):
        self.enabled = False
        self.sounds = {}
        self.loop_channels = {}
        self.loop_targets = {}
        self.music_channel = None
        self._bird_timer = random.uniform(4.0, 9.0)
        self._creak_timer = random.uniform(3.0, 7.0)
        self._sail_timer = random.uniform(4.0, 8.0)
        self._last_music_state = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(max(24, pygame.mixer.get_num_channels()))
            self.enabled = True
            for index, name in enumerate(("wind_at_sea", "rolling_waves", "harbour_ambience", "port_activity")):
                self.loop_channels[name] = pygame.mixer.Channel(index)
            self.music_channel = pygame.mixer.Channel(5)
            directory = Path(audio_directory)
            sound_names = (
                "wind_at_sea", "rolling_waves", "wooden_hull_creak", "sails_flapping",
                "cannon_fire", "cannon_impact", "harbour_ambience", "port_activity",
                "seabirds", "important_encounter_music",
            )
            for name in sound_names:
                path = directory / f"{name}.wav"
                if path.is_file():
                    self.sounds[name] = pygame.mixer.Sound(str(path))
            self._start_loop("wind_at_sea", 0.19)
            self._start_loop("rolling_waves", 0.21)
        except Exception:
            # Sound hardware, codecs, and mixer availability vary between systems.
            # The game remains fully playable without an audio device.
            self.enabled = False
            self.sounds.clear()
            self.loop_channels.clear()
            self.music_channel = None

    def _start_loop(self, name, volume):
        if not self.enabled or name not in self.loop_channels or name not in self.sounds:
            return
        channel = self.loop_channels[name]
        if not channel.get_busy():
            channel.play(self.sounds[name], loops=-1, fade_ms=700)
        channel.set_volume(max(0.0, min(1.0, volume)))
        self.loop_targets[name] = max(0.0, min(1.0, volume))

    def _loop_volume(self, name, volume):
        if not self.enabled or name not in self.loop_channels:
            return
        volume = max(0.0, min(1.0, volume))
        previous = self.loop_targets.get(name, 0.0)
        channel = self.loop_channels[name]
        if volume > 0.003:
            # A channel returning from a fade-out is restarted so a stale fade
            # envelope cannot silence an ambience that has become audible again.
            if previous <= 0.003 and channel.get_busy():
                channel.stop()
            if not channel.get_busy() and name in self.sounds:
                channel.play(self.sounds[name], loops=-1, fade_ms=700)
            channel.set_volume(volume)
        elif previous > 0.003 and channel.get_busy():
            channel.fadeout(900)
        self.loop_targets[name] = volume

    def play(self, name, volume=0.7):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        try:
            channel = pygame.mixer.find_channel(True)
            if channel:
                channel.set_volume(max(0.0, min(1.0, volume)))
                channel.play(sound)
        except Exception:
            pass

    def set_encounter_music(self, active):
        if not self.enabled or self.music_channel is None:
            return
        active = bool(active and "important_encounter_music" in self.sounds)
        if active and not self._last_music_state:
            if self.music_channel.get_busy():
                self.music_channel.stop()
            self.music_channel.play(self.sounds["important_encounter_music"], loops=-1, fade_ms=1800)
            self.music_channel.set_volume(0.33)
        elif not active and self._last_music_state and self.music_channel.get_busy():
            self.music_channel.fadeout(1800)
        self._last_music_state = active

    def update(self, dt, *, docked=False, near_port_distance=None, speed=0.0,
               wind_strength=1.0, important_encounter=False):
        if not self.enabled:
            return
        underway = not docked and speed > 8.0
        wind_volume = 0.13 + max(0.0, min(1.0, wind_strength)) * 0.12
        self._loop_volume("wind_at_sea", wind_volume if not docked else 0.085)
        self._loop_volume("rolling_waves", 0.20 if not docked else 0.13)

        harbour_factor = 1.0 if docked else 0.0
        if near_port_distance is not None and near_port_distance < 900.0:
            harbour_factor = max(harbour_factor, 1.0 - near_port_distance / 900.0)
        self._loop_volume("harbour_ambience", 0.31 * harbour_factor)
        self._loop_volume("port_activity", 0.25 * (1.0 if docked else max(0.0, harbour_factor - 0.25) / 0.75))

        self._bird_timer -= dt
        if self._bird_timer <= 0.0:
            self.play("seabirds", 0.12 + 0.16 * (1.0 if docked else harbour_factor + 0.25))
            self._bird_timer = random.uniform(7.0, 17.0)

        if underway:
            self._creak_timer -= dt
            if self._creak_timer <= 0.0:
                self.play("wooden_hull_creak", 0.12 + min(0.14, speed / 1200.0))
                self._creak_timer = random.uniform(4.0, 10.0)
            self._sail_timer -= dt
            if self._sail_timer <= 0.0 and wind_strength > 0.45:
                self.play("sails_flapping", 0.08 + 0.11 * wind_strength)
                self._sail_timer = random.uniform(5.0, 12.0)
        else:
            self._creak_timer = min(self._creak_timer, 2.0)
            self._sail_timer = min(self._sail_timer, 2.5)

        self.set_encounter_music(important_encounter)

    def close(self):
        if not self.enabled:
            return
        try:
            for channel in self.loop_channels.values():
                channel.fadeout(400)
            if self.music_channel:
                self.music_channel.fadeout(400)
        except Exception:
            pass
