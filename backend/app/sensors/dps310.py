from __future__ import annotations

from .base import SensorAdapter, SensorReading


class DPS310Sensor(SensorAdapter):
    name = "dps310"

    def __init__(self):
        self._sensor = None

    def _load(self):
        if self._sensor is None:
            import adafruit_dps310
            import board

            self._sensor = adafruit_dps310.DPS310(board.I2C())
        return self._sensor

    def read(self) -> SensorReading:
        sensor = self._load()
        return SensorReading(
            values={"pressure_hpa": sensor.pressure},
            health="ok",
        )
