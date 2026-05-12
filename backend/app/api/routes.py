from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..core.config import PROJECT_ROOT
from ..schemas.models import (
    ActionResponseModel,
    EventModel,
    HistoryPointModel,
    LatestPacketModel,
    SystemStatusModel,
    ThresholdConfigModel,
    ThresholdPayloadModel,
)
from .deps import get_container

router = APIRouter(prefix="/api")


@router.get("/latest", response_model=LatestPacketModel)
def latest(container=Depends(get_container)):
    return container.collector.latest_packet or container.collector.sample_once()


@router.get("/events", response_model=list[EventModel])
def events(limit: int = 50, container=Depends(get_container)):
    return container.repository.list_events(limit=limit)


@router.get("/events/{event_id}", response_model=EventModel)
def event_detail(event_id: int, container=Depends(get_container)):
    event = container.repository.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/history", response_model=list[HistoryPointModel])
def history(hours: int = 24, container=Depends(get_container)):
    return container.repository.history(hours=hours)


@router.get("/status", response_model=SystemStatusModel)
def status(container=Depends(get_container)):
    latest_status = container.repository.latest_status() or container.status_service.read_status()
    latest_status.pop("timestamp", None)
    return latest_status


@router.get("/config/thresholds", response_model=ThresholdConfigModel)
def get_thresholds(container=Depends(get_container)):
    return container.current_thresholds()


@router.post("/config/thresholds", response_model=ThresholdConfigModel)
def set_thresholds(payload: ThresholdPayloadModel, container=Depends(get_container)):
    return container.update_thresholds(payload.model_dump())


@router.post("/actions/capture", response_model=ActionResponseModel)
def capture(container=Depends(get_container)):
    path = container.media_service.capture_snapshot(prefix="manual_capture")
    event = container.repository.create_event(
        {
            "timestamp": container.now(),
            "event_type": "CAMERA_CAPTURED",
            "severity": "low",
            "message": "Manual capture requested from frontend.",
            "media_path": str(path),
            "acknowledged": False,
            "metadata": {},
        }
    )
    return {"ok": True, "message": "Capture request completed.", "details": {"media_url": event["media_url"]}}


@router.post("/actions/test-led", response_model=ActionResponseModel)
def test_led(container=Depends(get_container)):
    result = container.led_service.test()
    container.repository.create_event(
        {
            "timestamp": container.now(),
            "event_type": "SYSTEM_ONLINE",
            "severity": "low",
            "message": "Mock LED test executed.",
            "media_path": "",
            "acknowledged": True,
            "metadata": result,
        }
    )
    return {"ok": True, "message": "Mock LED test executed.", "details": result}


@router.get("/media/{filename}")
def media(filename: str, container=Depends(get_container)):
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid media filename")

    candidates = [
        Path(container.settings.media_dir) / filename,
        Path(container.settings.db_path).parent / "media" / filename,
        PROJECT_ROOT / "data" / "media" / filename,
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Media file not found")
    media_type = "image/svg+xml" if path.suffix == ".svg" else ("image/jpeg" if path.suffix in {'.jpg', '.jpeg'} else None)
    return FileResponse(path, media_type=media_type)


@router.get("/health")
def health(container=Depends(get_container)):
    latest = container.collector.latest_packet
    return {
        "status": "ok",
        "latest_packet_available": latest is not None,
        "db_path": str(container.settings.db_path),
        "media_dir": str(container.settings.media_dir),
        "camera_enabled": container.settings.camera_enabled,
        "microphone_enabled": container.settings.microphone_enabled,
        "last_noise_score": None if latest is None else latest.get("noise_score"),
    }
