from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class EventModel(BaseModel):
    id: int
    timestamp: str
    event_type: str
    severity: str
    message: str
    media_url: str = ""
    acknowledged: bool = False


class SystemStatusModel(BaseModel):
    status: str
    ip_address: str | None = None
    disk_free_gb: float | None = None
    cpu_temp_c: float | None = None
    uptime_seconds: int | None = None


class LatestPacketModel(BaseModel):
    timestamp: str
    temperature_c: float | None = None
    humidity_percent: float | None = None
    pressure_hpa: float | None = None
    distance_cm: float | None = None
    noise_score: float | None = None
    occupancy: bool | None = None
    last_event: EventModel | None = None
    latest_media_url: str = ""
    system: SystemStatusModel
    sensor_health: dict[str, str]


class HistoryPointModel(BaseModel):
    timestamp: str
    temperature_c: float | None = None
    humidity_percent: float | None = None
    pressure_hpa: float | None = None
    noise_score: float | None = None


class ThresholdConfigModel(BaseModel):
    temperature_high_c: float
    humidity_high_percent: float
    motion_delta_cm: float
    presence_distance_cm: float
    noise_threshold: float
    model_config = ConfigDict(extra="ignore")


class ThresholdPayloadModel(BaseModel):
    temperature_high_c: float | str
    humidity_high_percent: float | str
    motion_delta_cm: float | str
    presence_distance_cm: float | str
    noise_threshold: float | str


class ActionResponseModel(BaseModel):
    ok: bool = True
    message: str
    details: dict[str, Any] = {}
