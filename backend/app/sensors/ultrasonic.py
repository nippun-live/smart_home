from __future__ import annotations

from .base import SensorAdapter, SensorReading


class UltrasonicSensor(SensorAdapter):
    name = "ultrasonic"

    def __init__(self, trigger_pin: int, echo_pin: int, max_distance_m: float = 4.0):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.max_distance_m = max_distance_m
        self._sensor = None

    def _load(self):
        if self._sensor is None:
            from gpiozero import DistanceSensor

            self._sensor = DistanceSensor(
                echo=self.echo_pin,
                trigger=self.trigger_pin,
                max_distance=self.max_distance_m,
            )
        return self._sensor

    def read(self) -> SensorReading:
        sensor = self._load()
        return SensorReading(values={"distance_cm": sensor.distance * 100.0}, health="ok")
