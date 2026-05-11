from __future__ import annotations

import tempfile
from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import Settings
from backend.app.main import create_app


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "test.db",
        media_dir=tmp_path / "media",
        fake_hardware=True,
        ultrasonic_enabled=True,
        pressure_sensor="dps310",
        sensor_interval_seconds=60,
    )


def test_frontend_contract_endpoints():
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = build_settings(Path(temp_dir))
        app = create_app(settings)
        with TestClient(app) as client:
            latest = client.get("/api/latest")
            assert latest.status_code == 200
            payload = latest.json()
            assert "temperature_c" in payload
            assert "humidity_percent" in payload
            assert "distance_cm" in payload
            assert "system" in payload
            assert "sensor_health" in payload

            events = client.get("/api/events?limit=50")
            assert events.status_code == 200
            assert isinstance(events.json(), list)

            history = client.get("/api/history?hours=24")
            assert history.status_code == 200
            assert isinstance(history.json(), list)
            assert history.json()

            status = client.get("/api/status")
            assert status.status_code == 200
            assert status.json()["status"] == "online"


def test_thresholds_capture_and_led_actions():
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = build_settings(Path(temp_dir))
        app = create_app(settings)
        with TestClient(app) as client:
            response = client.post(
                "/api/config/thresholds",
                json={
                    "temperature_high_c": "31",
                    "humidity_high_percent": "65",
                    "motion_delta_cm": "12",
                    "presence_distance_cm": "70",
                    "noise_threshold": "0.8",
                },
            )
            assert response.status_code == 200
            assert response.json()["motion_delta_cm"] == 12.0

            capture = client.post("/api/actions/capture", json={})
            assert capture.status_code == 200
            media_url = capture.json()["details"]["media_url"]
            media = client.get(media_url)
            assert media.status_code == 200
            assert "svg" in media.headers["content-type"]

            led = client.post("/api/actions/test-led", json={})
            assert led.status_code == 200
            assert led.json()["ok"] is True


def test_ultrasonic_triggers_mock_led_event():
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = build_settings(Path(temp_dir))
        app = create_app(settings)
        with TestClient(app) as client:
            for _ in range(6):
                client.app.state.container.collector.sample_once()
            events = client.get("/api/events?limit=10").json()
            event_types = {event["event_type"] for event in events}
            assert "PRESENCE_DETECTED" in event_types or "MOTION_DETECTED" in event_types
