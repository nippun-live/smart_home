from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.config import Settings
from .core.logging import configure_logging
from .db.repository import Repository
from .services.audio_service import AudioService
from .services.event_engine import EventEngine
from .services.led_service import MockLedService
from .services.media_service import MediaService
from .services.sensor_collector import SensorCollector
from .services.status_service import StatusService


@dataclass
class Container:
    settings: Settings
    repository: Repository
    status_service: StatusService
    media_service: MediaService
    led_service: MockLedService
    audio_service: AudioService
    event_engine: EventEngine
    collector: SensorCollector

    def current_thresholds(self) -> dict[str, float]:
        stored = self.repository.load_config()
        return {
            "temperature_high_c": float(stored.get("temperature_high_c", self.settings.temperature_high_c)),
            "humidity_high_percent": float(stored.get("humidity_high_percent", self.settings.humidity_high_percent)),
            "motion_delta_cm": float(stored.get("motion_delta_cm", self.settings.motion_delta_cm)),
            "presence_distance_cm": float(stored.get("presence_distance_cm", self.settings.presence_distance_cm)),
            "noise_threshold": float(stored.get("noise_threshold", self.settings.noise_threshold)),
        }

    def update_thresholds(self, payload: dict[str, str | float]) -> dict[str, float]:
        normalized = {
            "temperature_high_c": float(payload["temperature_high_c"]),
            "humidity_high_percent": float(payload["humidity_high_percent"]),
            "motion_delta_cm": float(payload["motion_delta_cm"]),
            "presence_distance_cm": float(payload["presence_distance_cm"]),
            "noise_threshold": float(payload["noise_threshold"]),
        }
        self.repository.upsert_config(normalized)
        self.settings.temperature_high_c = normalized["temperature_high_c"]
        self.settings.humidity_high_percent = normalized["humidity_high_percent"]
        self.settings.motion_delta_cm = normalized["motion_delta_cm"]
        self.settings.presence_distance_cm = normalized["presence_distance_cm"]
        self.settings.noise_threshold = normalized["noise_threshold"]
        self.event_engine.settings.temperature_high_c = normalized["temperature_high_c"]
        self.event_engine.settings.humidity_high_percent = normalized["humidity_high_percent"]
        self.event_engine.settings.motion_delta_cm = normalized["motion_delta_cm"]
        self.event_engine.settings.presence_distance_cm = normalized["presence_distance_cm"]
        self.event_engine.settings.noise_threshold = normalized["noise_threshold"]
        return normalized

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def build_container(settings: Settings) -> Container:
    repository = Repository(settings.db_path)
    status_service = StatusService(root_path=settings.db_path.parent)
    media_service = MediaService(
        settings.media_dir,
        camera_enabled=settings.camera_enabled,
        mock_fallback=settings.mock_camera_writes_files,
        resolution=(settings.camera_resolution_width, settings.camera_resolution_height),
        fake_hardware=settings.fake_hardware,
    )
    led_service = MockLedService()
    audio_service = AudioService(settings)
    event_engine = EventEngine(settings=settings, led_service=led_service)
    collector = SensorCollector(
        settings=settings,
        repository=repository,
        status_service=status_service,
        event_engine=event_engine,
        media_service=media_service,
        audio_service=audio_service,
    )
    return Container(
        settings=settings,
        repository=repository,
        status_service=status_service,
        media_service=media_service,
        led_service=led_service,
        audio_service=audio_service,
        event_engine=event_engine,
        collector=collector,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container = build_container(settings)
        app.state.container = container
        container.repository.upsert_config(container.current_thresholds())
        container.collector.start()
        yield
        container.collector.stop()

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    if settings.frontend_dir.exists():
        app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
    return app


app = create_app()
