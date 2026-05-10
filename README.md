# Smart Home Edge Hub

This directory is the working project scaffold for the final project. The full source specification is in [../spec.md](../spec.md), but this README is the shorter implementation-facing version for actual team integration.

The project goal is to build a Raspberry Pi smart home edge hub that combines:

- environmental sensing
- motion and noise security events
- camera snapshots
- local storage
- a touchscreen dashboard
- a web dashboard on the same LAN

## Current focus

The frontend is already scaffolded in [frontend](./frontend). It is designed to work in two modes:

- `live` mode: real backend endpoints respond at `/api/*`
- `mock` mode: static frontend falls back to built-in sample data when backend is missing

That means frontend development can continue before backend integration is complete.

## Ownership summary

- `Nippun`: frontend dashboard, graphs, event views, settings UI, API integration
- `Nicky`: FastAPI backend, SQLite access, media serving, API responses
- `Hugh`: hardware bring-up, wiring, individual sensor tests
- `Siddarth`: sensor collector, event engine, LED logic, camera triggers, service integration

## Repository layout

Recommended project layout:

```text
smart_home/
  README.md
  frontend/
    index.html
    app.js
    styles.css
    events/
    history/
    settings/
    status/
  backend/
  sensors/
  events/
  hardware/
  services/
  tests/
```

Only `frontend/` exists right now. The rest should be added to match the spec once implementation starts.

## Frontend implementation notes

The frontend is plain HTML/CSS/JS. No framework is required for MVP.

Implemented pages/views:

- `/` live dashboard
- `/events/` event feed
- `/history/` sensor trend graphs
- `/settings/` thresholds and test actions
- `/status/` system health

Important frontend behavior:

- polls `/api/latest` every 1 second
- polls `/api/events?limit=50` every 5 seconds
- polls `/api/status` every 5 seconds
- polls `/api/history?hours=24` every 15 seconds
- falls back to mock data if requests fail
- shows a connection state so demos still work before backend exists

Important frontend files:

- [frontend/index.html](./frontend/index.html)
- [frontend/app.js](./frontend/app.js)
- [frontend/styles.css](./frontend/styles.css)

## Running the frontend now

Use a static server:

```powershell
cd "C:\Users\nippu\Documents\Coding\437\final project\smart_home\frontend"
python -m http.server 4173 --bind 127.0.0.1
```

Then open:

- `http://127.0.0.1:4173/`
- `http://127.0.0.1:4173/events/`
- `http://127.0.0.1:4173/history/`
- `http://127.0.0.1:4173/settings/`
- `http://127.0.0.1:4173/status/`

In mock mode, `python -m http.server` will print `404` lines for `/api/*`. That is normal because there is no backend yet. The frontend catches those failures and renders mock data.

## Integration contract

This is the important part to keep stable across sensors, backend, and frontend. If these shapes stay stable, everyone can work in parallel.

### 1. Latest sensor packet

Returned by:

- `GET /api/latest`

Expected shape:

```json
{
  "timestamp": "2026-05-07T16:30:00",
  "temperature_c": 23.4,
  "humidity_percent": 42.1,
  "pressure_hpa": 1012.8,
  "distance_cm": 84.2,
  "noise_score": 0.63,
  "occupancy": true,
  "last_event": {
    "id": 17,
    "event_type": "MOTION_DETECTED",
    "timestamp": "2026-05-07T16:29:55",
    "severity": "medium",
    "message": "Motion detected from ultrasonic distance change.",
    "media_url": "/api/media/motion_2026-05-07_16-29-55.jpg",
    "acknowledged": false
  },
  "latest_media_url": "/api/media/motion_2026-05-07_16-29-55.jpg",
  "system": {
    "status": "online",
    "disk_free_gb": 820,
    "ip_address": "192.168.1.42",
    "cpu_temp_c": 48.2,
    "uptime_seconds": 5421
  },
  "sensor_health": {
    "aht20": "ok",
    "dps310": "ok",
    "ultrasonic": "ok",
    "microphone": "ok",
    "camera": "ok",
    "storage": "ok"
  }
}
```

Notes:

- `last_event` should be present if an event exists
- `latest_media_url` should point to the most recent snapshot if one exists
- `sensor_health` should never be omitted; missing sensors should be marked `"offline"` or `"error"`

### 2. Event packet

Returned by:

- `GET /api/events?limit=50`
- `GET /api/events/{event_id}`

Expected shape:

```json
{
  "id": 17,
  "timestamp": "2026-05-07T16:32:10",
  "event_type": "MOTION_DETECTED",
  "severity": "medium",
  "message": "Motion detected from ultrasonic distance change.",
  "media_url": "/api/media/motion_2026-05-07_16-32-10.jpg",
  "acknowledged": false
}
```

If `/api/events` returns a list directly, that is fine:

```json
[
  {
    "id": 17,
    "timestamp": "2026-05-07T16:32:10",
    "event_type": "MOTION_DETECTED",
    "severity": "medium",
    "message": "Motion detected from ultrasonic distance change.",
    "media_url": "/api/media/motion_2026-05-07_16-32-10.jpg",
    "acknowledged": false
  }
]
```

The frontend also accepts:

```json
{
  "events": [
    {
      "id": 17,
      "timestamp": "2026-05-07T16:32:10",
      "event_type": "MOTION_DETECTED",
      "severity": "medium",
      "message": "Motion detected from ultrasonic distance change.",
      "media_url": "/api/media/motion_2026-05-07_16-32-10.jpg",
      "acknowledged": false
    }
  ]
}
```

### 3. History packet

Returned by:

- `GET /api/history?hours=24`

Expected graphable shape:

```json
[
  {
    "timestamp": "2026-05-07T15:00:00",
    "temperature_c": 22.8,
    "humidity_percent": 44.2,
    "pressure_hpa": 1013.7,
    "noise_score": 0.21
  },
  {
    "timestamp": "2026-05-07T16:00:00",
    "temperature_c": 23.4,
    "humidity_percent": 42.1,
    "pressure_hpa": 1012.8,
    "noise_score": 0.63
  }
]
```

The frontend also accepts:

```json
{
  "history": [
    {
      "timestamp": "2026-05-07T15:00:00",
      "temperature_c": 22.8,
      "humidity_percent": 44.2,
      "pressure_hpa": 1013.7,
      "noise_score": 0.21
    }
  ]
}
```

### 4. System status packet

Returned by:

- `GET /api/status`

Expected shape:

```json
{
  "status": "online",
  "ip_address": "192.168.1.42",
  "disk_free_gb": 820,
  "cpu_temp_c": 48.2,
  "uptime_seconds": 5421
}
```

### 5. Media route

Returned by:

- `GET /api/media/{filename}`

Behavior:

- should return the actual image bytes for the snapshot
- media URLs included in event packets should be directly usable by `<img src="...">`

Example:

- `/api/media/motion_2026-05-07_16-32-10.jpg`

## Event naming contract

These event type strings should stay frozen:

- `SYSTEM_ONLINE`
- `MOTION_DETECTED`
- `PRESENCE_DETECTED`
- `LOUD_NOISE`
- `HIGH_TEMPERATURE`
- `HIGH_HUMIDITY`
- `PRESSURE_DROP`
- `CAMERA_CAPTURED`
- `SENSOR_FAILURE`
- `STORAGE_WARNING`

Frontend expects `severity` values like:

- `low`
- `medium`
- `high`

## Sensor health contract

Each service should expose health in a predictable way:

```json
{
  "aht20": "ok",
  "dps310": "ok",
  "ultrasonic": "ok",
  "microphone": "ok",
  "camera": "ok",
  "storage": "ok"
}
```

Recommended states:

- `ok`
- `warning`
- `offline`
- `error`

Avoid custom one-off strings unless everyone agrees to them.

## Backend endpoints required for MVP

Required:

- `GET /api/latest`
- `GET /api/history?hours=24`
- `GET /api/events?limit=50`
- `GET /api/events/{event_id}`
- `GET /api/status`
- `GET /api/media/{filename}`

Recommended for controls:

- `POST /api/config/thresholds`
- `POST /api/actions/capture`
- `POST /api/actions/test-led`

## Settings payload contract

The frontend sends the thresholds form as JSON. Backend should accept keys exactly like this:

```json
{
  "temperature_high_c": "30",
  "humidity_high_percent": "70",
  "motion_delta_cm": "25",
  "presence_distance_cm": "80",
  "noise_threshold": "0.7"
}
```

Backend can coerce these string values into numeric values internally.

## Suggested database alignment

The backend does not need to return raw SQLite rows, but the API layer should map cleanly from the spec schema:

- `sensor_readings`
- `events`
- `system_status`
- `config`

Recommended frontend-facing field mapping:

- `sensor_readings.temperature_c` -> `temperature_c`
- `sensor_readings.humidity_percent` -> `humidity_percent`
- `sensor_readings.pressure_hpa` -> `pressure_hpa`
- `sensor_readings.distance_cm` -> `distance_cm`
- `sensor_readings.noise_score` -> `noise_score`
- `sensor_readings.occupancy` -> `occupancy`
- `events.media_path` -> `media_url` after conversion to `/api/media/...`

## Sensor -> backend -> frontend flow

End-to-end data flow should look like this:

```text
sensor drivers
  -> sensor_collector.py
  -> latest reading cache + SQLite
  -> event_engine.py
  -> events table + media snapshot path
  -> FastAPI backend
  -> frontend polling /api/*
```

More explicitly:

1. Sensors produce readings.
2. `sensor_collector.py` normalizes them into one packet.
3. Backend stores the latest reading and history rows.
4. `event_engine.py` generates event records when rules trigger.
5. Camera snapshot path is attached to the event if applicable.
6. FastAPI converts database rows into the JSON shapes above.
7. Frontend polls and renders those packets.

## Frontend integration expectations for backend

To avoid UI breakage, backend should follow these rules:

- always return JSON for API routes
- always include timestamps in ISO 8601 form
- use numeric values for sensor readings
- return `null` for missing numeric data instead of string placeholders
- keep event type strings stable
- keep `media_url` browser-usable
- keep `sensor_health` present even if some sensors fail

## Recommended backend mock responses

Before the real sensor pipeline is ready, backend can hardcode these routes and return fixed JSON matching the contract. That is enough for frontend integration and demo prep.

Priority order:

1. `/api/latest`
2. `/api/events`
3. `/api/status`
4. `/api/history`
5. `/api/media/...`

## MVP demo checklist

Minimum complete path:

- frontend loads on touchscreen and laptop
- `/api/latest` returns real readings
- `/api/events` returns motion/noise events
- `/api/status` returns system info
- camera snapshots resolve via `/api/media/...`
- motion event appears in frontend
- latest snapshot appears in frontend

## Practical next steps

For frontend:

- keep polishing layout only after backend contract is stable
- test against hardcoded FastAPI responses as soon as possible
- switch from mock mode to live API testing once `/api/latest` and `/api/events` exist

For backend:

- implement exact JSON contracts from this README first
- serve static frontend files after API routes exist
- return stable dummy data before sensor integration is complete

For sensors/events:

- normalize all data into the `latest` packet shape early
- avoid changing field names during integration week

## Important rule for final integration

Freeze these before merging subsystems:

- endpoint names
- JSON field names
- event type strings
- media URL conventions
- threshold config keys
- sensor health keys

If these stay stable, the frontend, backend, and sensor/event code can be developed independently without breaking each other.
