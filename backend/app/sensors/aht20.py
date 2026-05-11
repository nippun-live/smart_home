from __future__ import annotations

from .base import SensorAdapter, SensorReading


class AHT20Sensor(SensorAdapter):
    name = "aht20"

    def __init__(self):
        self._sensor = None

    def _load(self):
        if self._sensor is None:
            import adafruit_ahtx0
            import board

            self._sensor = adafruit_ahtx0.AHTx0(board.I2C())
        return self._sensor

    def read(self) -> SensorReading:
        sensor = self._load()
        return SensorReading(
            values={
                "temperature_c": sensor.temperature,
                "humidity_percent": sensor.relative_humidity,
            },
            health="ok",
        )
