from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .led_service import MockLedService


@dataclass
class EventDecision:
    event: dict[str, Any] | None = None
    led_action: dict[str, Any] | None = None


class EventEngine:
    def __init__(self, presence_distance_cm: float, motion_delta_cm: float, led_service: MockLedService):
        self.presence_distance_cm = presence_distance_cm
        self.motion_delta_cm = motion_delta_cm
        self.led_service = led_service
        self._last_distance_cm: float | None = None
        self._last_presence_state: bool | None = None

    def evaluate(self, packet: dict[str, Any], media_path: Path | None = None) -> EventDecision:
        distance = packet.get("distance_cm")
        if distance is None:
            return EventDecision()

        occupancy = bool(packet.get("occupancy"))
        delta = None if self._last_distance_cm is None else abs(distance - self._last_distance_cm)
        self._last_distance_cm = distance

        event = None
        led_action = None
        if occupancy and self._last_presence_state is not True:
            led_action = self.led_service.trigger_motion_alert()
            event = self._build_event(
                event_type="PRESENCE_DETECTED",
                severity="medium",
                message=f"Presence detected at {distance:.1f} cm.",
                media_path=media_path,
                metadata={"distance_cm": round(distance, 1)},
            )
        elif delta is not None and delta >= self.motion_delta_cm:
            led_action = self.led_service.trigger_motion_alert()
            event = self._build_event(
                event_type="MOTION_DETECTED",
                severity="medium",
                message=f"Ultrasonic distance changed by {delta:.1f} cm.",
                media_path=media_path,
                metadata={"distance_cm": round(distance, 1), "delta_cm": round(delta, 1)},
            )

        self._last_presence_state = occupancy
        return EventDecision(event=event, led_action=led_action)

    def _build_event(self, event_type: str, severity: str, message: str, media_path: Path | None, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "media_path": str(media_path) if media_path else "",
            "acknowledged": False,
            "metadata": metadata,
        }
