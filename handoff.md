# Smart Home Edge Hub Handoff

## Purpose

This document is the technical handoff for the current `smart_home` project state.

It is written to support three goals:

1. explain the architecture clearly to teammates and graders
2. define the MVP end-to-end system shape
3. provide a practical demo path that highlights the backend work and real hardware integration

This handoff reflects the current working backend, the frontend contract it supports, the hardware that is real today, and the remaining work required to present the project as one coherent product.

---

## Project Summary

The project is a Raspberry Pi based smart home edge hub that combines:

- environmental sensing
- motion and presence detection
- noise-triggered security detection
- camera snapshots
- local data persistence
- a touchscreen-friendly dashboard
- a LAN-accessible web dashboard

The core design decision is to keep sensing, event detection, storage, API serving, and UI rendering local to the Raspberry Pi. This gives the project a clear edge-computing story: the Pi acts as the single local smart home node and does not depend on a cloud backend to function.

In one sentence:

> The Raspberry Pi collects sensor data, detects meaningful events locally, stores them in SQLite, and serves them through a FastAPI backend to a dashboard UI.

---

## Current End Goal

The full MVP should demonstrate this flow:

1. sensors produce live readings
2. the backend collects and normalizes those readings
3. the backend stores readings and events in SQLite
4. the event engine detects motion, presence, loud noise, and threshold violations
5. the camera captures snapshots for relevant events
6. the backend serves the latest state, history, events, and media through REST endpoints
7. the frontend dashboard polls those endpoints and renders the system in real time

This is the correct product-level story for the demo:

- a local smart home edge server
- real sensors
- event-driven behavior
- persistent logging
- dashboard visibility

---

## What Is Working Now

### Real hardware currently integrated

- `DHT11` temperature/humidity sensor
- ultrasonic distance sensor
- Raspberry Pi camera
- USB microphone

### Backend capabilities currently implemented

- FastAPI app with stable REST routes
- SQLite database for readings, events, status, and config
- live sensor collection loop
- event generation from ultrasonic and microphone signals
- real camera snapshot capture via `picamera2`
- media serving for captured images
- threshold configuration endpoint
- status/health reporting

### Frontend compatibility currently implemented

The backend supports the JSON contract already expected by the frontend:

- `GET /api/latest`
- `GET /api/events?limit=50`
- `GET /api/events/{event_id}`
- `GET /api/history?hours=24`
- `GET /api/status`
- `GET /api/media/{filename}`
- `POST /api/config/thresholds`
- `POST /api/actions/capture`
- `POST /api/actions/test-led`

The backend is intentionally designed so the frontend does not need to know:

- which exact temperature sensor is active
- whether camera output is real or mocked
- whether LED behavior is real or mocked
- whether microphone input comes from USB or another path

This separation is one of the main strengths of the current implementation.

---

## Current Architecture

### High-level architecture

```text
Sensors / Devices
  - DHT11
  - Ultrasonic
  - USB Microphone
  - Pi Camera
        |
        v
Sensor Collector
  - reads sensors
  - computes packet
  - records health
        |
        +--> SQLite
        |
        +--> Event Engine
                - motion
                - presence
                - loud noise
                - environmental warnings
                - sensor/storage failures
                |
                +--> camera snapshot
                +--> mock LED action
        |
        v
FastAPI Backend
  - latest
  - history
  - events
  - status
  - media
  - config/actions
        |
        v
Frontend Dashboard
  - dashboard
  - events
  - history
  - settings
  - status
```

### Backend structure

Current backend package:

```text
smart_home/backend/app/
  api/
  core/
  db/
  schemas/
  sensors/
  services/
  main.py
```

### Key backend modules

- `backend/app/main.py`
  - app creation
  - dependency container
  - startup/shutdown lifecycle
  - optional static frontend serving

- `backend/app/core/config.py`
  - runtime settings
  - environment-variable overrides
  - sensor thresholds
  - camera/microphone/sampling parameters

- `backend/app/db/repository.py`
  - SQLite schema
  - insert/query methods
  - event/history/status/config persistence

- `backend/app/services/sensor_collector.py`
  - central read loop
  - unified latest packet creation
  - sensor health tracking
  - event engine invocation

- `backend/app/services/event_engine.py`
  - motion detection
  - presence detection
  - loud noise detection
  - high temperature/humidity warnings
  - storage warning
  - sensor failure events
  - cooldown logic

- `backend/app/services/audio_service.py`
  - USB mic integration
  - real-time noise score generation
  - safe fallback behavior

- `backend/app/services/media_service.py`
  - real snapshot capture using `picamera2`
  - mock snapshot fallback if needed

---

## Current Database Design

SQLite is already integrated and is the correct MVP persistence layer.

Current logical tables:

- `sensor_readings`
- `events`
- `system_status`
- `config`

### Why SQLite is the correct choice

- local
- lightweight
- easy to demo
- good enough for a single Pi edge node
- easy to inspect directly with `sqlite3`
- maps cleanly to frontend polling use cases

### What is stored

#### `sensor_readings`

Stores:

- timestamp
- temperature
- humidity
- pressure
- ultrasonic distance
- noise score
- occupancy
- serialized sensor health

#### `events`

Stores:

- timestamp
- event type
- severity
- message
- media path
- acknowledged flag
- metadata JSON

#### `system_status`

Stores:

- timestamp
- system status
- IP address
- free disk
- CPU temperature
- uptime

#### `config`

Stores:

- thresholds and similar runtime settings

### Recommendation

Do not replace SQLite right now.

The correct move is to keep SQLite as the main store and continue building around it. A second storage system would add complexity without helping the MVP.

---

## Current Hardware Reality

### Working now

- `DHT11`
  - real readings working
  - occasional checksum errors are normal for this sensor class
  - backend now retries reads before marking failure

- ultrasonic sensor
  - real readings working
  - used for motion and occupancy logic

- Pi camera
  - real camera detected
  - real snapshots confirmed through backend

- USB microphone
  - detected as USB audio input
  - backend computes a real `noise_score`

### Mocked or partial now

- LED strip logic
  - API and service abstraction exist
  - current implementation is mock-only

- pressure sensor
  - backend supports `DPS310`
  - may be disabled depending on the demo hardware setup

### Why this is acceptable

The current setup is enough for a strong MVP because the most important system story is already present:

- environmental signal
- security signal
- audio signal
- image capture
- local storage
- API delivery
- dashboard consumption

That is already a legitimate end-to-end smart home edge hub.

---

## API Contract

The backend should continue treating the frontend contract as frozen.

### `GET /api/latest`

Must return:

- timestamp
- temperature/humidity/pressure
- distance
- noise score
- occupancy
- last event
- latest media URL
- system status
- sensor health

### `GET /api/events`

Must return event list with:

- id
- timestamp
- event type
- severity
- message
- media URL
- acknowledged

### `GET /api/history`

Must return time-series points suitable for graphs.

### `GET /api/status`

Must return:

- status
- IP
- disk free
- CPU temp
- uptime

### `POST /api/config/thresholds`

Must accept string-valued numeric config payloads because that is what the frontend currently sends.

### `POST /api/actions/capture`

Manual capture endpoint for settings/demo use.

### `POST /api/actions/test-led`

Manual LED test endpoint for the frontend even before real LED hardware is attached.

---

## Current Event Model

The backend now supports the following meaningful event classes:

- `PRESENCE_DETECTED`
- `MOTION_DETECTED`
- `LOUD_NOISE`
- `HIGH_TEMPERATURE`
- `HIGH_HUMIDITY`
- `STORAGE_WARNING`
- `SENSOR_FAILURE`
- `CAMERA_CAPTURED`

### Event severity behavior

- `medium`
  - normal motion/noise/environment conditions
- `high`
  - sensor failures
  - storage warning
  - combined motion/noise timing

### Current rule behavior

- motion:
  - ultrasonic delta exceeds configured threshold

- presence:
  - object remains below presence distance for several seconds

- loud noise:
  - computed `noise_score` exceeds configured threshold

- high temperature:
  - `temperature_c > threshold`

- high humidity:
  - `humidity_percent > threshold`

- storage warning:
  - free disk below configured limit

- sensor failure:
  - a sensor reports `error`

### Snapshot behavior

Relevant security-style events can trigger a camera snapshot automatically:

- `PRESENCE_DETECTED`
- `MOTION_DETECTED`
- `LOUD_NOISE`

This is exactly the kind of coupling that makes the project feel like one integrated system rather than disconnected scripts.

---

## Current Frontend Situation

The frontend already has the right structure:

- dashboard view
- events view
- history view
- settings view
- status view

The frontend also already has:

- polling logic
- mock mode
- event rendering
- chart rendering
- settings/actions UI
- connection state handling

### What the frontend should become for the final demo

The frontend should be treated as the presentation layer for the backend, not the place where system logic lives.

That means the backend remains responsible for:

- sensor normalization
- event detection
- persistence
- media handling
- health states

The frontend remains responsible for:

- polling
- rendering
- view organization
- user controls
- live demo readability

This split is correct and should not be changed.

---

## Proposed Full Frontend MVP Outline

The frontend MVP should be presented as five views.

### 1. Dashboard

Primary goal:

- one glance summary of the whole home hub

Should show:

- temperature card
- humidity card
- pressure card
- noise score card
- distance card
- occupancy card
- latest event highlight
- latest snapshot preview
- system summary
- sensor health summary

### 2. Events

Primary goal:

- show recent activity in a security/log format

Should show:

- event cards
- severity
- timestamp
- message
- snapshot preview if present

### 3. History

Primary goal:

- prove that the backend stores time-series data

Should show:

- temperature trend
- humidity trend
- pressure trend
- noise score trend

### 4. Settings

Primary goal:

- show controllability

Should show:

- threshold form
- manual capture trigger
- manual LED test trigger
- refresh action

### 5. Status

Primary goal:

- make system health/debugging visible

Should show:

- backend connectivity state
- latest packet timestamp
- history count
- event count
- sensor health
- system health

---

## End-to-End MVP Demo Story

This is the best demo narrative because it highlights the backend work while still showing the full product.

### Demo framing

Start with the dashboard, not the code.

Reason:

- it makes the system feel complete immediately
- it shows the product before the implementation details
- it keeps the audience focused on system behavior

### Recommended demo order

1. open the dashboard on the Pi or browser
2. explain that the Pi is acting as a local edge hub
3. point out the live cards:
   - temperature
   - humidity
   - distance
   - noise score
   - occupancy
4. show that the backend is serving current system state
5. move a hand in front of the ultrasonic sensor
6. show occupancy/event changes
7. make a loud sound
8. show a loud noise event appear
9. trigger a snapshot and show it in the UI
10. open the events page and show persisted history
11. open the history page and show graph data from SQLite
12. open the settings page and trigger capture/test-led
13. open the status page and point out sensor/system health
14. then pivot into the backend implementation details

### Backend-focused explanation after the demo

After the dashboard demo, explain:

- the backend owns sensor collection
- the backend stores readings/events in SQLite
- the backend computes event logic
- the backend captures media
- the frontend only consumes stable REST endpoints

That cleanly highlights your contribution.

---

## How To Explain Your Backend Contribution

The simplest and strongest explanation is:

> I built the local FastAPI backend that turns raw hardware into a stable API the frontend can consume.

Then break that into four parts:

### 1. Hardware abstraction

The backend hides hardware details behind services and sensor adapters.

This means the frontend does not care whether:

- temperature comes from `DHT11` or `AHT20`
- noise comes from a USB microphone or a different input path
- snapshots are real or mocked

### 2. Event logic

The backend interprets raw sensor streams and turns them into meaningful events:

- motion
- presence
- loud noise
- threshold warnings

### 3. Persistence

The backend stores:

- current and historical readings
- event records
- media file paths
- system health
- config thresholds

### 4. API stability

The backend presents all of that through a stable REST interface so the frontend can remain simple and mostly unchanged.

That is the right engineering story.

---

## Remaining Work To Reach the Cleanest Demo

### High priority

1. run frontend cleanly from FastAPI on port `8000`
2. verify the frontend is consuming live backend data in all views
3. tune microphone threshold using real claps/taps/voice
4. tune ultrasonic thresholds to reduce noisy event spam
5. verify automatic snapshot creation for security events

### Medium priority

1. add `DPS310` live pressure if that hardware is available
2. improve event filtering/cooldowns if too noisy
3. improve `sensor_health` wording for partial failures
4. make settings load saved thresholds on page load

### Lower priority

1. real LED strip integration
2. external drive mount path integration
3. systemd startup
4. more formal backend test coverage

---

## Recommended Demo Configuration

If the goal is the most reliable demo, use this setup:

- real `DHT11`
- real ultrasonic
- real USB microphone
- real Pi camera
- mock LED
- pressure optional

This is the best tradeoff between reliability and feature coverage.

It demonstrates:

- real sensing
- real eventing
- real media capture
- real persistence
- real API integration

without depending on unfinished LED or pressure hardware.

---

## Recommended Talking Points for the Report / Presentation

### Systems story

- the Raspberry Pi acts as a local IoT edge server
- sensing, storage, event logic, and UI all run locally

### Software story

- FastAPI provides the integration layer
- SQLite provides local persistence
- the frontend is decoupled through a stable JSON contract

### Hardware story

- DHT11 provides environmental monitoring
- ultrasonic provides presence/motion
- USB microphone provides audio-triggered events
- Pi camera provides event snapshots

### Product story

- the dashboard is the single interface
- the backend unifies all hardware under one API

---

## Known Limitations

These are acceptable to acknowledge in the demo/report.

- `DHT11` can produce occasional transient checksum failures
- LED behavior is still mocked
- pressure may be absent depending on the live setup
- noise detection is threshold-based, not a sophisticated classifier
- camera currently captures snapshots, not video clips

These do not undermine the MVP. They are normal scope boundaries for a course edge-systems project.

---

## Recommended Immediate Next Step

The next best move is:

1. connect the frontend fully to the live FastAPI backend on `:8000`
2. test the five dashboard views against real backend data
3. tune thresholds for a stable live demo

That gives the strongest final presentation because it starts with a working product view and then lets you explain the backend implementation as the technical core.

---

## Bottom Line

The project already has the correct backend architecture and enough real hardware to support a credible end-to-end MVP.

The main product claim is now defensible:

> the Raspberry Pi collects real sensor data, detects meaningful local events, stores them in SQLite, captures event media, and serves everything to a dashboard through a stable FastAPI backend

For demo purposes, the best presentation strategy is:

- show the full dashboard first
- demonstrate real events live
- then explain the backend as the integration layer that makes the system work

That puts the focus on your strongest contribution while still presenting the project as one complete smart home edge hub.
