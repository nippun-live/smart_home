from __future__ import annotations

from .base import SensorAdapter, SensorReading


class DHT11Sensor(SensorAdapter):
    name = "dht11"

    def __init__(self, gpio_pin: int):
        self.gpio_pin = gpio_pin
        self._sensor = None

    def _load(self):
        if self._sensor is None:
            import adafruit_dht
            import board

            pin_name = f"D{self.gpio_pin}"
            pin = getattr(board, pin_name)
            self._sensor = adafruit_dht.DHT11(pin)
        return self._sensor

    def read(self) -> SensorReading:
        sensor = self._load()
        last_error = None
        for _ in range(3):
            try:
                return SensorReading(
                    values={
                        "temperature_c": sensor.temperature,
                        "humidity_percent": sensor.humidity,
                    },
                    health="ok",
                )
            except RuntimeError as error:
                last_error = error
                continue
        if last_error is not None:
            raise last_error
        raise RuntimeError("DHT11 read failed")
