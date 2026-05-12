from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .led_service import MockLedService


@dataclass
class EventDecision:
    events: list[dict[str, Any]]
    should_capture_snapshot: bool = False


class EventEngine:
    def __init__(self, settings, led_service: MockLedService):
        self.settings = settings
        self.led_service = led_service
        self._last_distance_cm: float | None = None
        self._presence_started_at: datetime | None = None
        self._last_event_at: dict[str, datetime] = {}
        self._last_noise_event_at: datetime | None = None
        self._last_motion_event_at: datetime | None = None

    def evaluate(self, packet: dict[str, Any], status: dict[str, Any]) -> EventDecision:
        now = datetime.now(timezone.utc)
        events: list[dict[str, Any]] = []
        should_capture_snapshot = False

        distance = packet.get("distance_cm")
        if distance is not None:
            occupancy = bool(packet.get("occupancy"))
            if occupancy:
                if self._presence_started_at is None:
                    self._presence_started_at = now
                held_seconds = (now - self._presence_started_at).total_seconds()
                if held_seconds >= 3 and self._cooldown_ok("PRESENCE_DETECTED", now, self.settings.presence_cooldown_seconds):
                    events.append(self._build_event(now, "PRESENCE_DETECTED", "medium", f"Presence detected at {distance:.1f} cm.", {"distance_cm": round(distance, 1)}))
                    self._last_motion_event_at = now
                    should_capture_snapshot = True
                    self.led_service.trigger_motion_alert()
            else:
                self._presence_started_at = None

            delta = None if self._last_distance_cm is None else abs(distance - self._last_distance_cm)
            self._last_distance_cm = distance
            if delta is not None and delta >= self.settings.motion_delta_cm and self._cooldown_ok("MOTION_DETECTED", now, self.settings.motion_cooldown_seconds):
                severity = "high" if self._within_window(self._last_noise_event_at, now, self.settings.event_combination_window_seconds) else "medium"
                events.append(self._build_event(now, "MOTION_DETECTED", severity, f"Ultrasonic distance changed by {delta:.1f} cm.", {"distance_cm": round(distance, 1), "delta_cm": round(delta, 1)}))
                self._last_motion_event_at = now
                should_capture_snapshot = True
                self.led_service.trigger_motion_alert()

        noise_score = packet.get("noise_score")
        if noise_score is not None and noise_score >= self.settings.noise_threshold and self._cooldown_ok("LOUD_NOISE", now, self.settings.noise_cooldown_seconds):
            severity = "high" if self._within_window(self._last_motion_event_at, now, self.settings.event_combination_window_seconds) else "medium"
            events.append(self._build_event(now, "LOUD_NOISE", severity, f"Noise score exceeded threshold at {noise_score:.2f}.", {"noise_score": round(noise_score, 3)}))
            self._last_noise_event_at = now
            should_capture_snapshot = True
            self.led_service.trigger_motion_alert()

        temperature_c = packet.get("temperature_c")
        if temperature_c is not None and temperature_c >= self.settings.temperature_high_c and self._cooldown_ok("HIGH_TEMPERATURE", now, self.settings.environmental_cooldown_seconds):
            events.append(self._build_event(now, "HIGH_TEMPERATURE", "medium", f"Temperature reached {temperature_c:.1f} °C.", {"temperature_c": round(temperature_c, 1)}))

        humidity_percent = packet.get("humidity_percent")
        if humidity_percent is not None and humidity_percent >= self.settings.humidity_high_percent and self._cooldown_ok("HIGH_HUMIDITY", now, self.settings.environmental_cooldown_seconds):
            events.append(self._build_event(now, "HIGH_HUMIDITY", "medium", f"Humidity reached {humidity_percent:.1f}%.", {"humidity_percent": round(humidity_percent, 1)}))

        disk_free_gb = status.get("disk_free_gb")
        if disk_free_gb is not None and disk_free_gb <= self.settings.storage_warning_gb and self._cooldown_ok("STORAGE_WARNING", now, self.settings.environmental_cooldown_seconds):
            events.append(self._build_event(now, "STORAGE_WARNING", "high", f"Disk free space is low at {disk_free_gb:.1f} GB.", {"disk_free_gb": round(disk_free_gb, 1)}))

        for sensor_name, sensor_health in packet.get("sensor_health", {}).items():
            if sensor_health == "error" and self._cooldown_ok(f"SENSOR_FAILURE:{sensor_name}", now, self.settings.environmental_cooldown_seconds):
                events.append(self._build_event(now, "SENSOR_FAILURE", "high", f"Sensor {sensor_name} reported an error.", {"sensor": sensor_name}))

        return EventDecision(events=events, should_capture_snapshot=should_capture_snapshot)

    def _cooldown_ok(self, event_key: str, now: datetime, cooldown_seconds: float) -> bool:
        last = self._last_event_at.get(event_key)
        if last and (now - last).total_seconds() < cooldown_seconds:
            return False
        self._last_event_at[event_key] = now
        return True

    def _within_window(self, instant: datetime | None, now: datetime, window_seconds: float) -> bool:
        return instant is not None and (now - instant).total_seconds() <= window_seconds

    def _build_event(self, now: datetime, event_type: str, severity: str, message: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "timestamp": now.isoformat(),
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "media_path": "",
            "acknowledged": False,
            "metadata": metadata,
        }
