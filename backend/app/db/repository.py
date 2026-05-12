from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature_c REAL,
                    humidity_percent REAL,
                    pressure_hpa REAL,
                    distance_cm REAL,
                    noise_score REAL,
                    occupancy INTEGER,
                    sensor_health_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp);

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    media_path TEXT NOT NULL DEFAULT '',
                    acknowledged INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);

                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    ip_address TEXT,
                    disk_free_gb REAL,
                    cpu_temp_c REAL,
                    uptime_seconds INTEGER
                );

                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def save_sensor_reading(self, packet: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sensor_readings (
                    timestamp, temperature_c, humidity_percent, pressure_hpa,
                    distance_cm, noise_score, occupancy, sensor_health_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    packet["timestamp"],
                    packet.get("temperature_c"),
                    packet.get("humidity_percent"),
                    packet.get("pressure_hpa"),
                    packet.get("distance_cm"),
                    packet.get("noise_score"),
                    int(packet["occupancy"]) if packet.get("occupancy") is not None else None,
                    json.dumps(packet.get("sensor_health", {})),
                ),
            )

    def latest_reading(self) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1").fetchone()
        return self._row_to_sensor(row) if row else None

    def history(self, hours: int, limit: int = 500) -> list[dict[str, Any]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=max(1, hours))).isoformat()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT timestamp, temperature_c, humidity_percent, pressure_hpa, noise_score
                FROM sensor_readings
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_event(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO events (timestamp, event_type, severity, message, media_path, acknowledged, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["timestamp"],
                    event["event_type"],
                    event["severity"],
                    event["message"],
                    event.get("media_path", ""),
                    int(bool(event.get("acknowledged", False))),
                    json.dumps(event.get("metadata", {})),
                ),
            )
            event_id = cursor.lastrowid
        created = self.get_event(event_id)
        assert created is not None
        return created

    def list_events(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_event(self, event_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return self._row_to_event(row) if row else None

    def latest_event(self) -> dict[str, Any] | None:
        events = self.list_events(limit=1)
        return events[0] if events else None

    def save_status(self, status: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO system_status (timestamp, status, ip_address, disk_free_gb, cpu_temp_c, uptime_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    status["timestamp"],
                    status["status"],
                    status.get("ip_address"),
                    status.get("disk_free_gb"),
                    status.get("cpu_temp_c"),
                    status.get("uptime_seconds"),
                ),
            )

    def latest_status(self) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT timestamp, status, ip_address, disk_free_gb, cpu_temp_c, uptime_seconds FROM system_status ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def upsert_config(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            for key, value in values.items():
                connection.execute(
                    "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, str(value)),
                )
        return self.load_config()

    def load_config(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute("SELECT key, value FROM config").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def _row_to_sensor(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "timestamp": row["timestamp"],
            "temperature_c": row["temperature_c"],
            "humidity_percent": row["humidity_percent"],
            "pressure_hpa": row["pressure_hpa"],
            "distance_cm": row["distance_cm"],
            "noise_score": row["noise_score"],
            "occupancy": None if row["occupancy"] is None else bool(row["occupancy"]),
            "sensor_health": json.loads(row["sensor_health_json"]),
        }

    def _row_to_event(self, row: sqlite3.Row) -> dict[str, Any]:
        media_path = row["media_path"] or ""
        filename = Path(media_path).name if media_path else ""
        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "severity": row["severity"],
            "message": row["message"],
            "media_url": f"/api/media/{filename}" if filename else "",
            "acknowledged": bool(row["acknowledged"]),
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "media_path": media_path,
        }
