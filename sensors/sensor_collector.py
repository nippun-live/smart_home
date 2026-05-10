"""
Unified sensor collector.
- Reads AHT20 (temp/humidity), DPS310 (pressure), HC-SR04 (distance) at 1 Hz
- Keeps the latest reading in memory for instant /api/latest responses
- Writes to SQLite every 10 s
- Detects MOTION_DETECTED, PRESENCE_DETECTED, HIGH_TEMPERATURE, HIGH_HUMIDITY events
- Triggers camera snapshot on motion events
- Designed to run as a daemon thread started by backend/server.py
"""

import time
import threading
from datetime import datetime

from backend.database import insert_reading, insert_event
from events.camera_capture import capture_snapshot

# --- shared in-memory state -------------------------------------------------

_latest: dict | None = None
_latest_lock = threading.Lock()


def get_latest() -> dict | None:
    with _latest_lock:
        return dict(_latest) if _latest else None


# --- mutable thresholds (updated live via POST /api/config/thresholds) ------

thresholds: dict = {
    "temperature_high_c":      30.0,
    "humidity_high_percent":   70.0,
    "motion_delta_cm":         25.0,
    "presence_distance_cm":    80.0,
    "noise_threshold":         0.7,
    "camera_cooldown_seconds": 10.0,
    "event_cooldown_seconds":  10.0,
}


def update_thresholds(new_values: dict) -> None:
    for key, raw in new_values.items():
        if key in thresholds:
            try:
                thresholds[key] = float(raw)
            except (TypeError, ValueError):
                pass


# --- collector loop ---------------------------------------------------------

SAMPLE_INTERVAL_S = 1.0
DB_WRITE_INTERVAL_S = 10.0

# Sustained duration required before firing an environmental event
_ENV_SUSTAINED_S = 30.0
# Minimum gap between repeated environmental events of the same type
_ENV_COOLDOWN_S = 300.0
# Sustained presence before occupancy flips to True
_PRESENCE_SUSTAINED_S = 3.0


def run() -> None:
    global _latest

    # --- sensor init (soft-fail per sensor) ---------------------------------
    i2c = None
    aht = None
    dps = None
    ultrasonic = None

    try:
        import board
        import adafruit_ahtx0
        i2c = board.I2C()
        aht = adafruit_ahtx0.AHTx0(i2c)
        print("[collector] AHT20 OK")
    except Exception as exc:
        print(f"[collector] AHT20 init failed: {exc}")

    try:
        import adafruit_dps310
        if i2c is None:
            import board
            i2c = board.I2C()
        dps = adafruit_dps310.DPS310(i2c)
        print("[collector] DPS310 OK")
    except Exception as exc:
        print(f"[collector] DPS310 init failed: {exc}")

    try:
        from gpiozero import DistanceSensor
        ultrasonic = DistanceSensor(echo=17, trigger=23, max_distance=4.0)
        print("[collector] HC-SR04 OK")
    except Exception as exc:
        print(f"[collector] HC-SR04 init failed: {exc}")

    # --- loop state ---------------------------------------------------------
    last_db_write = 0.0
    last_camera_ts = 0.0
    last_motion_ts = 0.0
    last_temp_event_ts = 0.0
    last_humidity_event_ts = 0.0

    prev_distance_cm: float | None = None
    presence_since: float | None = None
    occupancy = False

    high_temp_since: float | None = None
    high_humidity_since: float | None = None

    print("[collector] loop started")

    while True:
        iter_start = time.monotonic()
        now_iso = datetime.now().isoformat(timespec="milliseconds")
        now_ts = time.time()

        # --- read sensors (each wrapped independently) ----------------------
        temp_c = None
        humidity = None
        pressure = None
        distance_cm = None
        aht_status = "offline" if aht is None else "ok"
        dps_status = "offline" if dps is None else "ok"
        ultrasonic_status = "offline" if ultrasonic is None else "ok"

        if aht is not None:
            try:
                temp_c = round(float(aht.temperature), 2)
                humidity = round(float(aht.relative_humidity), 2)
            except Exception as exc:
                print(f"[collector] AHT20 read: {exc}")
                aht_status = "error"

        if dps is not None:
            try:
                pressure = round(float(dps.pressure), 2)
            except Exception as exc:
                print(f"[collector] DPS310 read: {exc}")
                dps_status = "error"

        if ultrasonic is not None:
            try:
                distance_cm = round(float(ultrasonic.distance) * 100, 1)
                # gpiozero returns 0 when sensor times out — treat as no reading
                if distance_cm <= 0:
                    distance_cm = None
                    ultrasonic_status = "warning"
            except Exception as exc:
                print(f"[collector] HC-SR04 read: {exc}")
                ultrasonic_status = "error"

        # --- presence / occupancy -------------------------------------------
        if distance_cm is not None:
            if distance_cm < thresholds["presence_distance_cm"]:
                if presence_since is None:
                    presence_since = now_ts
                elif now_ts - presence_since >= _PRESENCE_SUSTAINED_S:
                    if not occupancy:
                        occupancy = True
                        insert_event({
                            "timestamp": now_iso,
                            "event_type": "PRESENCE_DETECTED",
                            "severity": "low",
                            "message": f"Object within {distance_cm:.0f} cm for >{_PRESENCE_SUSTAINED_S:.0f} s.",
                            "media_path": "",
                        })
            else:
                presence_since = None
                occupancy = False

        # --- motion detection -----------------------------------------------
        if distance_cm is not None and prev_distance_cm is not None:
            delta = abs(distance_cm - prev_distance_cm)
            cooldown = thresholds["event_cooldown_seconds"]
            if delta > thresholds["motion_delta_cm"] and now_ts - last_motion_ts > cooldown:
                last_motion_ts = now_ts
                print(f"[event] MOTION_DETECTED delta={delta:.1f} cm")
                snap_path = ""
                if now_ts - last_camera_ts > thresholds["camera_cooldown_seconds"]:
                    last_camera_ts = now_ts
                    snap_path = capture_snapshot("motion")
                insert_event({
                    "timestamp": now_iso,
                    "event_type": "MOTION_DETECTED",
                    "severity": "medium",
                    "message": f"Distance changed {delta:.1f} cm in one second.",
                    "media_path": snap_path,
                })

        if distance_cm is not None:
            prev_distance_cm = distance_cm

        # --- high temperature -----------------------------------------------
        if temp_c is not None:
            if temp_c > thresholds["temperature_high_c"]:
                if high_temp_since is None:
                    high_temp_since = now_ts
                elif (now_ts - high_temp_since >= _ENV_SUSTAINED_S
                        and now_ts - last_temp_event_ts > _ENV_COOLDOWN_S):
                    last_temp_event_ts = now_ts
                    print(f"[event] HIGH_TEMPERATURE {temp_c}°C")
                    insert_event({
                        "timestamp": now_iso,
                        "event_type": "HIGH_TEMPERATURE",
                        "severity": "medium",
                        "message": (
                            f"Temperature {temp_c}°C exceeded "
                            f"{thresholds['temperature_high_c']}°C for {_ENV_SUSTAINED_S:.0f} s."
                        ),
                        "media_path": "",
                    })
            else:
                high_temp_since = None

        # --- high humidity --------------------------------------------------
        if humidity is not None:
            if humidity > thresholds["humidity_high_percent"]:
                if high_humidity_since is None:
                    high_humidity_since = now_ts
                elif (now_ts - high_humidity_since >= _ENV_SUSTAINED_S
                        and now_ts - last_humidity_event_ts > _ENV_COOLDOWN_S):
                    last_humidity_event_ts = now_ts
                    print(f"[event] HIGH_HUMIDITY {humidity}%")
                    insert_event({
                        "timestamp": now_iso,
                        "event_type": "HIGH_HUMIDITY",
                        "severity": "medium",
                        "message": (
                            f"Humidity {humidity}% exceeded "
                            f"{thresholds['humidity_high_percent']}% for {_ENV_SUSTAINED_S:.0f} s."
                        ),
                        "media_path": "",
                    })
            else:
                high_humidity_since = None

        # --- update in-memory latest ----------------------------------------
        reading = {
            "timestamp": now_iso,
            "temperature_c": temp_c,
            "humidity_percent": humidity,
            "pressure_hpa": pressure,
            "distance_cm": distance_cm,
            "noise_score": None,
            "occupancy": occupancy,
            "sensor_health": {
                "aht20": aht_status,
                "dps310": dps_status,
                "ultrasonic": ultrasonic_status,
                "microphone": "offline",
                "camera": "ok",
                "storage": "ok",
            },
        }
        with _latest_lock:
            _latest = reading

        # --- periodic DB write ----------------------------------------------
        if now_ts - last_db_write >= DB_WRITE_INTERVAL_S:
            last_db_write = now_ts
            try:
                insert_reading({
                    "timestamp": now_iso,
                    "temperature_c": temp_c,
                    "humidity_percent": humidity,
                    "pressure_hpa": pressure,
                    "distance_cm": distance_cm,
                    "noise_score": None,
                    "occupancy": 1 if occupancy else 0,
                    "aht20_status": aht_status,
                    "dps310_status": dps_status,
                    "ultrasonic_status": ultrasonic_status,
                    "microphone_status": "offline",
                })
            except Exception as exc:
                print(f"[collector] DB write error: {exc}")

        # --- cadence-corrected sleep ----------------------------------------
        elapsed = time.monotonic() - iter_start
        if elapsed < SAMPLE_INTERVAL_S:
            time.sleep(SAMPLE_INTERVAL_S - elapsed)
