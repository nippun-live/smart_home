import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "smart-hub" / "data" / "homehub.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT    NOT NULL,
    temperature_c    REAL,
    humidity_percent REAL,
    pressure_hpa     REAL,
    distance_cm      REAL,
    noise_score      REAL,
    occupancy        INTEGER,
    aht20_status     TEXT,
    dps310_status    TEXT,
    ultrasonic_status TEXT,
    microphone_status TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    severity     TEXT NOT NULL,
    message      TEXT,
    media_path   TEXT,
    acknowledged INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_DEFAULT_CONFIG = {
    "temperature_high_c":      "30",
    "humidity_high_percent":   "70",
    "motion_delta_cm":         "25",
    "presence_distance_cm":    "80",
    "noise_threshold":         "0.7",
    "camera_cooldown_seconds": "10",
    "event_cooldown_seconds":  "10",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        for key, value in _DEFAULT_CONFIG.items():
            conn.execute(
                "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value)
            )


def insert_reading(r: dict) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sensor_readings
                (timestamp, temperature_c, humidity_percent, pressure_hpa,
                 distance_cm, noise_score, occupancy,
                 aht20_status, dps310_status, ultrasonic_status, microphone_status)
            VALUES
                (:timestamp, :temperature_c, :humidity_percent, :pressure_hpa,
                 :distance_cm, :noise_score, :occupancy,
                 :aht20_status, :dps310_status, :ultrasonic_status, :microphone_status)
            """,
            r,
        )


def get_history(hours: int = 24) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT timestamp, temperature_c, humidity_percent, pressure_hpa, noise_score
            FROM sensor_readings
            WHERE timestamp >= datetime('now', ? || ' hours')
            ORDER BY timestamp ASC
            """,
            (f"-{hours}",),
        ).fetchall()
    return [dict(r) for r in rows]


def insert_event(e: dict) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO events (timestamp, event_type, severity, message, media_path)
            VALUES (:timestamp, :event_type, :severity, :message, :media_path)
            """,
            e,
        )


def get_events(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_config(key: str, default: str | None = None) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def set_config(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
        )
