from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SensorReading:
    values: dict[str, Any]
    health: str = "ok"


class SensorAdapter:
    name: str = "sensor"

    def read(self) -> SensorReading:
        raise NotImplementedError
