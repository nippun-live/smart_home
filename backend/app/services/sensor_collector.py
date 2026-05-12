from __future__ import annotations

import logging
import math
import threading
from datetime import datetime, timezone
from typing import Any

from ..core.config import Settings
from ..db.repository import Repository
from ..sensors.aht20 import AHT20Sensor
from ..sensors.base import SensorAdapter, SensorReading
from ..sensors.dht11 import DHT11Sensor
from ..sensors.dps310 import DPS310Sensor
from ..sensors.ultrasonic import UltrasonicSensor
from .audio_service import AudioService
from .event_engine import EventEngine
from .media_service import MediaService
from .status_service import StatusService

LOGGER = logging.getLogger(__name__)


class FakeSensor(SensorAdapter):
    def __init__(self, name: str, values: dict[str, Any]):
        self.name = name
        self.values = values
        self._tick = 0

    def read(self) -> SensorReading:
        self._tick += 1
        values = dict(self.values)
        if "distance_cm" in values:
            values["distance_cm"] = 120.0 if self._tick % 4 else 45.0
        if "temperature_c" in values:
            values["temperature_c"] = round(float(values["temperature_c"]) + math.sin(self._tick / 4.0) * 0.4, 1)
        if "humidity_percent" in values:
            values["humidity_percent"] = round(float(values["humidity_percent"]) + math.cos(self._tick / 5.0) * 1.5, 1)
        return SensorReading(values=values, health="ok")


class SensorCollector:
    def __init__(
        self,
        settings: Settings,
        repository: Repository,
        status_service: StatusService,
        event_engine: EventEngine,
        media_service: MediaService,
        audio_service: AudioService,
    ):
        self.settings = settings
        self.repository = repository
        self.status_service = status_service
        self.event_engine = event_engine
        self.media_service = media_service
        self.audio_service = audio_service
        self.latest_packet: dict[str, Any] | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.sensors = self._build_sensors()

    def _build_sensors(self) -> list[SensorAdapter]:
        if self.settings.fake_hardware:
            sensors: list[SensorAdapter] = [FakeSensor("dht11", {"temperature_c": 25.1, "humidity_percent": 50.0})]
            if self.settings.pressure_sensor != "none":
                sensors.append(FakeSensor("dps310", {"pressure_hpa": 1012.8}))
            if self.settings.ultrasonic_enabled:
                sensors.append(FakeSensor("ultrasonic", {"distance_cm": 120.0}))
            return sensors

        sensors: list[SensorAdapter] = []
        if self.settings.temp_humidity_sensor == "dht11":
            sensors.append(DHT11Sensor(self.settings.dht11_gpio_pin))
        elif self.settings.temp_humidity_sensor == "aht20":
            sensors.append(AHT20Sensor())

        if self.settings.pressure_sensor == "dps310":
            sensors.append(DPS310Sensor())

        if self.settings.ultrasonic_enabled:
            sensors.append(
                UltrasonicSensor(
                    trigger_pin=self.settings.ultrasonic_trigger_pin,
                    echo_pin=self.settings.ultrasonic_echo_pin,
                    max_distance_m=self.settings.ultrasonic_max_distance_m,
                )
            )
        return sensors

    def start(self) -> None:
        self.sample_once()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop_event.wait(self.settings.sensor_interval_seconds):
            self.sample_once()

    def sample_once(self) -> dict[str, Any]:
        packet: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature_c": None,
            "humidity_percent": None,
            "pressure_hpa": None,
            "distance_cm": None,
            "noise_score": None,
            "occupancy": None,
            "sensor_health": dict(self.settings.sensor_health_defaults),
        }

        for sensor in self.sensors:
            try:
                reading = sensor.read()
                packet.update(reading.values)
                packet["sensor_health"][sensor.name] = reading.health
                LOGGER.debug("Sensor %s reading: %s", sensor.name, reading.values)
            except Exception as error:
                LOGGER.warning("Sensor %s read failed: %s", sensor.name, error)
                packet["sensor_health"][sensor.name] = "error"

        audio_reading = self.audio_service.read_noise_score()
        packet["noise_score"] = audio_reading.noise_score
        packet["sensor_health"]["microphone"] = audio_reading.health

        if packet.get("distance_cm") is not None:
            packet["occupancy"] = packet["distance_cm"] < self.settings.presence_distance_cm

        status = self.status_service.read_status()
        packet["sensor_health"]["storage"] = "warning" if (status.get("disk_free_gb") or 9999) <= self.settings.storage_warning_gb else "ok"
        packet["sensor_health"]["camera"] = "ok" if self.settings.camera_enabled else "offline"
        packet["sensor_health"]["led"] = "ok"

        self.repository.save_status(status)
        self.repository.save_sensor_reading(packet)

        decision = self.event_engine.evaluate(packet, status)
        for event in decision.events:
            if decision.should_capture_snapshot and event["event_type"] in {"PRESENCE_DETECTED", "MOTION_DETECTED", "LOUD_NOISE"}:
                snapshot = self.media_service.capture_snapshot(prefix=event["event_type"].lower())
                event["media_path"] = str(snapshot)
            self.repository.create_event(event)

        latest_event = self.repository.latest_event()
        packet["last_event"] = latest_event
        packet["latest_media_url"] = latest_event["media_url"] if latest_event else ""
        packet["system"] = {key: value for key, value in status.items() if key != "timestamp"}
        self.latest_packet = packet
        return packet
