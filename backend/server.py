"""
FastAPI backend for the Smart Home Hub.
- Serves the frontend static files at /
- Exposes /api/* endpoints consumed by the dashboard
- Spawns the sensor collector as a daemon thread on startup
Run from ~/smart-hub:
    uvicorn backend.server:app --host 0.0.0.0 --port 8000
"""

import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend import database, system_status
from events import camera_manager
from sensors import sensor_collector

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshots"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    database.insert_event({
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        "event_type": "SYSTEM_ONLINE",
        "severity": "low",
        "message": "Smart Home Hub backend started.",
        "media_path": "",
    })

    camera_manager.start()

    thread = threading.Thread(target=sensor_collector.run, daemon=True)
    thread.start()
    yield

    camera_manager.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/latest")
def get_latest():
    reading = sensor_collector.get_latest()
    events = database.get_events(limit=1)
    status = system_status.get_status()

    last_event = _enrich_event(events[0]) if events else None
    media_url = last_event.get("media_url") if last_event else None

    if reading is None:
        return {
            "timestamp": None,
            "temperature_c": None,
            "humidity_percent": None,
            "pressure_hpa": None,
            "distance_cm": None,
            "noise_score": None,
            "occupancy": None,
            "last_event": last_event,
            "latest_media_url": media_url,
            "system": status,
            "sensor_health": {},
        }

    return {
        **reading,
        "last_event": last_event,
        "latest_media_url": media_url,
        "system": status,
    }


@app.get("/api/history")
def get_history(hours: int = 24):
    return database.get_history(hours)


@app.get("/api/events")
def get_events(limit: int = 50):
    return [_enrich_event(e) for e in database.get_events(limit)]


@app.get("/api/events/{event_id}")
def get_event(event_id: int):
    event = database.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _enrich_event(event)


@app.get("/api/status")
def get_status():
    return system_status.get_status()


@app.get("/api/media/{filename}")
def get_media(filename: str):
    # Use .name to strip any path traversal attempts
    path = SNAPSHOT_DIR / Path(filename).name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(path)


@app.post("/api/actions/capture")
def trigger_capture():
    from events.camera_capture import capture_snapshot

    snap_path = capture_snapshot("manual")
    database.insert_event({
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        "event_type": "CAMERA_CAPTURED",
        "severity": "low",
        "message": "Manual capture triggered from dashboard.",
        "media_path": snap_path,
    })
    media_url = f"/api/media/{Path(snap_path).name}" if snap_path else None
    return {"ok": True, "media_url": media_url}


@app.post("/api/actions/test-led")
def test_led():
    return {
        "ok": True,
        "message": "NeoPixel LED not yet wired. Endpoint is ready for integration.",
    }


@app.get("/stream")
def stream_camera():
    return StreamingResponse(
        camera_manager.stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/config/thresholds")
def update_thresholds(body: dict):
    sensor_collector.update_thresholds(body)
    for key, value in body.items():
        database.set_config(key, str(value))
    return {"ok": True, "thresholds": sensor_collector.thresholds}


def _enrich_event(event: dict) -> dict:
    """Add media_url field derived from the stored media_path."""
    media_path = event.get("media_path") or ""
    if media_path:
        event["media_url"] = f"/api/media/{Path(media_path).name}"
    else:
        event["media_url"] = None
    return event


# --- static frontend (must be mounted last so /api/* routes take priority) --
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
