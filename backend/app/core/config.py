from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class Settings:
    app_name: str = "Smart Home Edge Hub API"
    app_version: str = "0.2.0"
    db_path: Path = PROJECT_ROOT / "data/smart_home.db"
    media_dir: Path = PROJECT_ROOT / "data/media"
    frontend_dir: Path = PROJECT_ROOT / "frontend"
    sensor_interval_seconds: float = 1.0
    temp_humidity_sensor: str = "dht11"
    pressure_sensor: str = "none"
    dht11_gpio_pin: int = 4
    ultrasonic_enabled: bool = True
    ultrasonic_trigger_pin: int = 23
    ultrasonic_echo_pin: int = 24
    ultrasonic_max_distance_m: float = 4.0
    microphone_enabled: bool = True
    microphone_device: str = "USB PnP Sound Device"
    microphone_sample_rate: int = 44100
    microphone_sample_window_seconds: float = 0.25
    presence_distance_cm: float = 80.0
    motion_delta_cm: float = 25.0
    motion_cooldown_seconds: float = 10.0
    presence_cooldown_seconds: float = 10.0
    noise_threshold: float = 0.7
    noise_cooldown_seconds: float = 10.0
    event_combination_window_seconds: float = 5.0
    temperature_high_c: float = 30.0
    humidity_high_percent: float = 70.0
    environmental_cooldown_seconds: float = 300.0
    storage_warning_gb: float = 2.0
    camera_enabled: bool = True
    camera_resolution_width: int = 1280
    camera_resolution_height: int = 720
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
        def get_path(name: str, default: Path) -> Path:
            raw = os.getenv(name)
            if raw is None:
                return default
            path = Path(raw).expanduser()
            return path if path.is_absolute() else PROJECT_ROOT / path

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
        settings.db_path = get_path("SMART_HOME_DB_PATH", settings.db_path)
        settings.media_dir = get_path("SMART_HOME_MEDIA_DIR", settings.media_dir)
        settings.frontend_dir = get_path("SMART_HOME_FRONTEND_DIR", settings.frontend_dir)
        settings.sensor_interval_seconds = get_float("SMART_HOME_SENSOR_INTERVAL", settings.sensor_interval_seconds)
        settings.temp_humidity_sensor = os.getenv("SMART_HOME_TEMP_HUMIDITY_SENSOR", settings.temp_humidity_sensor).lower()
        settings.pressure_sensor = os.getenv("SMART_HOME_PRESSURE_SENSOR", settings.pressure_sensor).lower()
        settings.dht11_gpio_pin = get_int("SMART_HOME_DHT11_GPIO_PIN", settings.dht11_gpio_pin)
        settings.ultrasonic_enabled = get_bool("SMART_HOME_ULTRASONIC_ENABLED", settings.ultrasonic_enabled)
        settings.ultrasonic_trigger_pin = get_int("SMART_HOME_ULTRASONIC_TRIGGER_PIN", settings.ultrasonic_trigger_pin)
        settings.ultrasonic_echo_pin = get_int("SMART_HOME_ULTRASONIC_ECHO_PIN", settings.ultrasonic_echo_pin)
        settings.ultrasonic_max_distance_m = get_float("SMART_HOME_ULTRASONIC_MAX_DISTANCE_M", settings.ultrasonic_max_distance_m)
        settings.microphone_enabled = get_bool("SMART_HOME_MICROPHONE_ENABLED", settings.microphone_enabled)
        settings.microphone_device = os.getenv("SMART_HOME_MICROPHONE_DEVICE", settings.microphone_device)
        settings.microphone_sample_rate = get_int("SMART_HOME_MICROPHONE_SAMPLE_RATE", settings.microphone_sample_rate)
        settings.microphone_sample_window_seconds = get_float("SMART_HOME_MICROPHONE_WINDOW_SECONDS", settings.microphone_sample_window_seconds)
        settings.presence_distance_cm = get_float("SMART_HOME_PRESENCE_DISTANCE_CM", settings.presence_distance_cm)
        settings.motion_delta_cm = get_float("SMART_HOME_MOTION_DELTA_CM", settings.motion_delta_cm)
        settings.motion_cooldown_seconds = get_float("SMART_HOME_MOTION_COOLDOWN_SECONDS", settings.motion_cooldown_seconds)
        settings.presence_cooldown_seconds = get_float("SMART_HOME_PRESENCE_COOLDOWN_SECONDS", settings.presence_cooldown_seconds)
        settings.noise_threshold = get_float("SMART_HOME_NOISE_THRESHOLD", settings.noise_threshold)
        settings.noise_cooldown_seconds = get_float("SMART_HOME_NOISE_COOLDOWN_SECONDS", settings.noise_cooldown_seconds)
        settings.event_combination_window_seconds = get_float("SMART_HOME_EVENT_COMBINATION_WINDOW_SECONDS", settings.event_combination_window_seconds)
        settings.temperature_high_c = get_float("SMART_HOME_TEMPERATURE_HIGH_C", settings.temperature_high_c)
        settings.humidity_high_percent = get_float("SMART_HOME_HUMIDITY_HIGH_PERCENT", settings.humidity_high_percent)
        settings.environmental_cooldown_seconds = get_float("SMART_HOME_ENVIRONMENTAL_COOLDOWN_SECONDS", settings.environmental_cooldown_seconds)
        settings.storage_warning_gb = get_float("SMART_HOME_STORAGE_WARNING_GB", settings.storage_warning_gb)
        settings.camera_enabled = get_bool("SMART_HOME_CAMERA_ENABLED", settings.camera_enabled)
        settings.camera_resolution_width = get_int("SMART_HOME_CAMERA_RESOLUTION_WIDTH", settings.camera_resolution_width)
        settings.camera_resolution_height = get_int("SMART_HOME_CAMERA_RESOLUTION_HEIGHT", settings.camera_resolution_height)
        settings.mock_camera_writes_files = get_bool("SMART_HOME_CAMERA_WRITE_FILES", settings.mock_camera_writes_files)
        settings.fake_hardware = get_bool("SMART_HOME_FAKE_HARDWARE", settings.fake_hardware)
        return settings
