from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MockLedService:
    last_command: dict[str, str] | None = None
    history: list[dict[str, str]] = field(default_factory=list)

    def _record(self, action: str, reason: str) -> dict[str, str]:
        payload = {
            "action": action,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.last_command = payload
        self.history.append(payload)
        return payload

    def test(self) -> dict[str, str]:
        return self._record("test-led", "manual-test")

    def trigger_motion_alert(self) -> dict[str, str]:
        return self._record("turn-on", "motion-detected")
