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
        self.loop_base_targets = {}
        self.effects_volume = 1.0
        self.ambience_volume = 1.0
        self._sail_timer = random.uniform(4.0, 8.0)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(max(24, pygame.mixer.get_num_channels()))
            self.enabled = True
            for index, name in enumerate(("wind_at_sea", "rolling_waves", "harbour_ambience")):
                self.loop_channels[name] = pygame.mixer.Channel(index)
            directory = Path(audio_directory)
            # These four sound categories are intentionally excluded from
            # this release following player feedback.
            sound_names = (
                "wind_at_sea", "rolling_waves", "sails_flapping",
                "cannon_fire", "cannon_impact", "harbour_ambience",
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

    def set_volumes(self, effects, ambience):
        self.effects_volume = max(0.0, min(1.0, float(effects)))
        self.ambience_volume = max(0.0, min(1.0, float(ambience)))
        if not self.enabled:
            return
        for name, base in self.loop_base_targets.items():
            effective = base * self.ambience_volume
            self.loop_targets[name] = effective
            channel = self.loop_channels.get(name)
            if channel:
                if effective <= 0.003:
                    channel.set_volume(0.0)
                else:
                    if not channel.get_busy() and name in self.sounds:
                        channel.play(self.sounds[name], loops=-1, fade_ms=400)
                    channel.set_volume(effective)

    def _start_loop(self, name, volume):
        if not self.enabled or name not in self.loop_channels or name not in self.sounds:
            return
        channel = self.loop_channels[name]
        if not channel.get_busy():
            channel.play(self.sounds[name], loops=-1, fade_ms=700)
        base = max(0.0, min(1.0, volume))
        effective = base * self.ambience_volume
        channel.set_volume(effective)
        self.loop_base_targets[name] = base
        self.loop_targets[name] = effective

    def _loop_volume(self, name, volume):
        if not self.enabled or name not in self.loop_channels:
            return
        base = max(0.0, min(1.0, volume))
        self.loop_base_targets[name] = base
        volume = base * self.ambience_volume
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
                channel.set_volume(max(0.0, min(1.0, volume * self.effects_volume)))
                channel.play(sound)
        except Exception:
            pass

    def update(self, dt, *, docked=False, near_port_distance=None, speed=0.0,
               wind_strength=1.0):
        if not self.enabled:
            return
        wind_volume = 0.13 + max(0.0, min(1.0, wind_strength)) * 0.12
        self._loop_volume("wind_at_sea", wind_volume if not docked else 0.085)
        self._loop_volume("rolling_waves", 0.20 if not docked else 0.13)

        harbour_factor = 1.0 if docked else 0.0
        if near_port_distance is not None and near_port_distance < 1800.0:
            harbour_factor = max(harbour_factor, 1.0 - near_port_distance / 1800.0)
        self._loop_volume("harbour_ambience", 0.31 * harbour_factor)

        underway = not docked and speed > 8.0
        if underway:
            self._sail_timer -= dt
            if self._sail_timer <= 0.0 and wind_strength > 0.45:
                self.play("sails_flapping", 0.08 + 0.11 * wind_strength)
                self._sail_timer = random.uniform(5.0, 12.0)
        else:
            self._sail_timer = min(self._sail_timer, 2.5)

    def close(self):
        if not self.enabled:
            return
        try:
            for channel in self.loop_channels.values():
                channel.fadeout(400)
        except Exception:
            pass
