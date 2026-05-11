from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    app_name: str = "Smart Home Edge Hub API"
    app_version: str = "0.1.0"
    db_path: Path = Path("data/smart_home.db")
    media_dir: Path = Path("data/media")
    sensor_interval_seconds: float = 1.0
    temp_humidity_sensor: str = "dht11"
    pressure_sensor: str = "none"
    dht11_gpio_pin: int = 4
    ultrasonic_enabled: bool = True
    ultrasonic_trigger_pin: int = 23
    ultrasonic_echo_pin: int = 24
    ultrasonic_max_distance_m: float = 4.0
    presence_distance_cm: float = 80.0
    motion_delta_cm: float = 25.0
    noise_threshold: float = 0.7
    temperature_high_c: float = 30.0
    humidity_high_percent: float = 70.0
    mock_camera_writes_files: bool = True
    fake_hardware: bool = False
    sensor_health_defaults: dict[str, str] = field(
        default_factory=lambda: {
            "dht11": "offline",
            "aht20": "offline",
            "dps310": "offline",
            "ultrasonic": "offline",
            "microphone": "offline",
            "camera": "offline",
            "storage": "ok",
            "led": "offline",
        }
    )

    @classmethod
    def from_env(cls) -> "Settings":
        def get_bool(name: str, default: bool) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        def get_float(name: str, default: float) -> float:
            raw = os.getenv(name)
            return float(raw) if raw is not None else default

        def get_int(name: str, default: int) -> int:
            raw = os.getenv(name)
            return int(raw) if raw is not None else default

        settings = cls()
        settings.db_path = Path(os.getenv("SMART_HOME_DB_PATH", str(settings.db_path)))
        settings.media_dir = Path(os.getenv("SMART_HOME_MEDIA_DIR", str(settings.media_dir)))
        settings.sensor_interval_seconds = get_float("SMART_HOME_SENSOR_INTERVAL", settings.sensor_interval_seconds)
        settings.temp_humidity_sensor = os.getenv("SMART_HOME_TEMP_HUMIDITY_SENSOR", settings.temp_humidity_sensor).lower()
        settings.pressure_sensor = os.getenv("SMART_HOME_PRESSURE_SENSOR", settings.pressure_sensor).lower()
        settings.dht11_gpio_pin = get_int("SMART_HOME_DHT11_GPIO_PIN", settings.dht11_gpio_pin)
        settings.ultrasonic_enabled = get_bool("SMART_HOME_ULTRASONIC_ENABLED", settings.ultrasonic_enabled)
        settings.ultrasonic_trigger_pin = get_int("SMART_HOME_ULTRASONIC_TRIGGER_PIN", settings.ultrasonic_trigger_pin)
        settings.ultrasonic_echo_pin = get_int("SMART_HOME_ULTRASONIC_ECHO_PIN", settings.ultrasonic_echo_pin)
        settings.ultrasonic_max_distance_m = get_float("SMART_HOME_ULTRASONIC_MAX_DISTANCE_M", settings.ultrasonic_max_distance_m)
        settings.presence_distance_cm = get_float("SMART_HOME_PRESENCE_DISTANCE_CM", settings.presence_distance_cm)
        settings.motion_delta_cm = get_float("SMART_HOME_MOTION_DELTA_CM", settings.motion_delta_cm)
        settings.noise_threshold = get_float("SMART_HOME_NOISE_THRESHOLD", settings.noise_threshold)
        settings.temperature_high_c = get_float("SMART_HOME_TEMPERATURE_HIGH_C", settings.temperature_high_c)
        settings.humidity_high_percent = get_float("SMART_HOME_HUMIDITY_HIGH_PERCENT", settings.humidity_high_percent)
        settings.mock_camera_writes_files = get_bool("SMART_HOME_CAMERA_WRITE_FILES", settings.mock_camera_writes_files)
        settings.fake_hardware = get_bool("SMART_HOME_FAKE_HARDWARE", settings.fake_hardware)
        return settings
