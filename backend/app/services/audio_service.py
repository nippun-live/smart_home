from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class AudioReading:
    noise_score: float | None
    health: str


class AudioService:
    def __init__(self, settings):
        self.settings = settings
        self._device = None
        self._device_info = None
        self._tick = 0

    def read_noise_score(self) -> AudioReading:
        if not self.settings.microphone_enabled:
            return AudioReading(noise_score=None, health="offline")
        if self.settings.fake_hardware:
            self._tick += 1
            value = 0.18 + abs(math.sin(self._tick / 3.0)) * 0.7
            return AudioReading(noise_score=round(value, 2), health="ok")

        try:
            import numpy as np
            import sounddevice as sd

            device = self._resolve_device(sd)
            sample_rate = self._resolve_sample_rate()
            frames = max(1, int(sample_rate * self.settings.microphone_sample_window_seconds))
            recording = self._record(sd, device, sample_rate, frames)
            samples = np.asarray(recording).reshape(-1)
            if samples.size == 0:
                return AudioReading(noise_score=0.0, health="warning")
            rms = float(np.sqrt(np.mean(np.square(samples))))
            peak = float(np.max(np.abs(samples)))
            score = min(1.0, max(rms * 8.0, peak * 2.0))
            return AudioReading(noise_score=round(score, 3), health="ok")
        except Exception:
            return AudioReading(noise_score=None, health="error")

    def _resolve_device(self, sounddevice_module):
        if self._device is not None:
            return self._device

        requested = (self.settings.microphone_device or "").strip().lower()
        for index, device in enumerate(sounddevice_module.query_devices()):
            if device.get("max_input_channels", 0) < 1:
                continue
            name = str(device.get("name", "")).lower()
            if requested and requested in name:
                self._device = index
                self._device_info = device
                return self._device

        default_in, _default_out = sounddevice_module.default.device
        self._device = default_in
        self._device_info = sounddevice_module.query_devices(default_in)
        return self._device

    def _resolve_sample_rate(self) -> int:
        default_rate = None
        if self._device_info:
            default_rate = int(float(self._device_info.get("default_samplerate", 0)) or 0)
        for candidate in (
            self.settings.microphone_sample_rate,
            default_rate,
            48000,
            44100,
            16000,
            8000,
        ):
            if candidate and candidate > 0:
                return int(candidate)
        return 44100

    def _record(self, sounddevice_module, device: int, sample_rate: int, frames: int):
        last_error = None
        for candidate_rate in dict.fromkeys([sample_rate, 48000, 44100, 16000, 8000]):
            try:
                return sounddevice_module.rec(
                    frames if candidate_rate == sample_rate else max(1, int(candidate_rate * self.settings.microphone_sample_window_seconds)),
                    samplerate=candidate_rate,
                    channels=1,
                    dtype="float32",
                    device=device,
                    blocking=True,
                )
            except Exception as error:
                last_error = error
                continue
        raise last_error or RuntimeError("Unable to read microphone")
