Comprehensive build plan, Smart Home Edge Monitoring and Security Hub
0. Final project definition
Build a Raspberry Pi based smart home edge hub that centralizes:
Environmental monitoring.
Motion and sound-triggered security events.
Camera snapshots.
Local event storage.
Touchscreen dashboard.
Web dashboard over the local network.
LED/light feedback for physical alerts.
The final one-line pitch:
We are building a Raspberry Pi IoT edge hub that combines environmental sensing, motion/noise-based security detection, camera event capture, local storage, and a unified touchscreen/web dashboard.

1. Compatibility summary
Part
Use in project
Compatible?
Main caveat
Official Raspberry Pi Touch Display
Local dashboard
Yes
Uses DSI plus GPIO power, avoid Pi Zero/Pi 400
External hard drive
Store logs/images/videos
Yes
Use powered drive or powered hub if it draws too much current
Raspberry Pi Camera
Event snapshots/security camera
Yes
Cable depends on Pi model
AHT20 temp/humidity sensor, 2 units
Temperature/humidity
Yes
AHT20 has fixed I2C address, use only one unless using I2C mux
DPS310 barometer, 2 units
Pressure/weather trend
Yes
One works directly over I2C, two can work if address changed or SPI used
CMA-4544PF-W microphone, 4 units
Noise events
Not directly
Bare analog electret mic, needs amplifier plus ADC or USB audio path
NeoPixel LED strip
Status/alert lighting
Yes, with power handling
Needs 5 V power, high current, and level shifting recommended
Standard ultrasonic sensor
Motion/presence
Yes, with protection
Echo is usually 5 V, use voltage divider before Pi GPIO

The official Raspberry Pi Touch Display is 7 inches, 800 × 480, powered from the Pi, and connects using GPIO power plus the DSI ribbon; Raspberry Pi OS includes touchscreen drivers and on-screen keyboard support. (raspberrypi.com) Raspberry Pi camera modules work with Raspberry Pi computers that have CSI connectors; Pi 4 and earlier flagship models use the standard 15-pin camera cable, while Pi 5 and Zero models use the smaller 22-pin connector and may need a standard-to-mini cable. (raspberrypi.com)

2. Hardware decisions
Recommended Raspberry Pi
Use a Raspberry Pi 4B if available.
Why:
Standard 15-pin camera connector.
Standard DSI connector for the official touchscreen.
USB 3.0 for the external hard drive.
Enough compute for FastAPI, dashboard, camera snapshots, SQLite, and sensor polling.
Fewer cable surprises than Pi 5.
A Pi 5 also works, but you must ensure the camera/display cable situation is correct. Raspberry Pi 5 uses mini 22-pin camera/display connectors, unlike Pi 4’s standard 15-pin camera connector. (raspberrypi.com)

3. Required extra parts
Your current parts are enough for most of the project, but not quite enough for safe/reliable integration.
Must-have extras
Extra part
Why you need it
1 kΩ and 2 kΩ resistors, or 10 kΩ and 20 kΩ
Voltage divider for ultrasonic Echo
5 V external power supply for NeoPixel strip
Do not power full LED strip from Pi
74AHCT125 or 74HCT245 level shifter
Reliable 3.3 V Pi GPIO to 5 V NeoPixel data
Microphone amplifier plus ADC, or USB sound card
Bare mic cannot be read directly by Raspberry Pi
Jumper wires/breadboard
Wiring
STEMMA QT/Qwiic cable or JST-to-jumper cable
Clean AHT20/DPS310 wiring

Strong recommendation for microphone path
Choose one of these:
Option
Extra parts
Pros
Cons
USB sound card + microphone input
Cheap USB audio adapter
Fastest, easiest, most reliable
Less embedded-circuit-heavy
Electret mic amplifier + MCP3008 ADC
MAX4466/MAX9814 style amp + MCP3008
Best embedded systems story
More wiring/debugging
Digital sound detector board
Sound sensor board with digital output
Easy event trigger
Less useful for actual noise level

Use the USB sound card route if time matters. Use the amplifier + MCP3008 route if you want a more technically impressive sensing pipeline.
The CMA-4544PF-W is a bare electret condenser microphone with analog electrical specs, including 3 V standard operating voltage, 10 V max, 2.2 kΩ output impedance, and 20 Hz to 20 kHz frequency range. (cdn-shop.adafruit.com) Raspberry Pi does not include a hardware analog-to-digital converter, so analog sensors require an external ADC such as the MCP3008.

4. Final hardware architecture
Raspberry Pi 4B
    |
    |-- DSI ribbon -> Official Raspberry Pi Touch Display
    |-- CSI ribbon -> Raspberry Pi Camera
    |-- USB 3.0 -> External hard drive
    |-- I2C bus -> AHT20 temp/humidity sensor
    |-- I2C bus -> DPS310 pressure sensor
    |-- GPIO23 -> Ultrasonic TRIG
    |-- GPIO24 <- Ultrasonic ECHO through voltage divider
    |-- GPIO18 -> Level shifter -> NeoPixel DIN
    |-- SPI -> MCP3008 ADC -> microphone amplifier -> CMA-4544PF-W
If you choose USB audio instead of the bare mic circuit:
Raspberry Pi 4B
    |
    |-- USB sound card -> microphone

5. Wiring plan
5.1 I2C sensors, AHT20 and DPS310
Use the Pi’s default I2C bus.
Raspberry Pi pin
Signal
AHT20
DPS310
Pin 1
3.3 V
VIN
VIN
Pin 6
GND
GND
GND
Pin 3, GPIO2
SDA
SDA
SDI/SDA
Pin 5, GPIO3
SCL
SCL
SCK/SCL

The AHT20 uses standard I2C, works with Linux/Raspberry Pi boards, has typical accuracy of ±2 percent relative humidity and ±0.3 °C, and has default I2C address 0x38 that cannot be changed. The AHT20 breakout requires 2.7 V to 5.5 V, and its I2C logic level follows VIN, so using Pi 3.3 V for VIN keeps logic safe.
The DPS310 supports I2C or SPI, works from 300 to 1200 hPa, has ±1 hPa absolute accuracy, includes a temperature sensor, and the Adafruit breakout supports 3.3 V/Raspberry Pi logic. (Digi-Key) Its I2C address is normally 0x77, and pulling SDO/ADR low changes it to 0x76, so two DPS310 boards can share I2C if one address is changed. (Adafruit Learning System)
Decision
Use:
AHT20 #1 at 0x38
DPS310 #1 at 0x77
Keep the second AHT20 and second DPS310 as backups or stretch-goal redundancy.
Important: do not put both AHT20 boards on the same I2C bus unless you add an I2C multiplexer, because the AHT20 address cannot be changed.

5.2 Ultrasonic sensor
Assume HC-SR04 or equivalent.
Ultrasonic pin
Raspberry Pi connection
VCC
5 V
GND
GND
TRIG
GPIO23, physical pin 16
ECHO
GPIO24 through voltage divider, physical pin 18

Use a voltage divider:
ECHO pin -> 1 kΩ -> GPIO24
GPIO24 -> 2 kΩ -> GND
This converts:
Vout = 5 V * 2k / (1k + 2k) = 3.33 V
Reason: standard HC-SR04 style sensors commonly return 5 V on Echo, while Raspberry Pi GPIO expects 3.3 V logic, so Echo should not be wired directly to the Pi. (Viam)

5.3 NeoPixel LED strip
Use the NeoPixel strip as a visible smart-home status light.
NeoPixel wire
Connection
+5 V
External 5 V supply
GND
External supply GND and Raspberry Pi GND
DIN
GPIO18 through 74AHCT125/74HCT245 level shifter

The Adafruit strip is a 60 LED/m individually addressable RGB strip, uses one digital data pin, and must be powered from 5 V DC; Adafruit warns not to use more than 6 V. (Adafruit) Because the strip can draw significant current, do not power it from the Pi. Use an external 5 V supply, connect grounds together, and limit brightness in software.
Software brightness limit:
LED_BRIGHTNESS = 0.2
Status colors:
Color
Meaning
Green
System online
Blue
Normal monitoring
Yellow
Environmental warning
Red
Motion/noise security event
Purple
Camera capture
White pulse
User toggled light switch mode


5.4 Microphone
The current CMA-4544PF-W parts are not plug-and-play sensors. They are raw electret microphones. The datasheet shows a measurement circuit using a load resistor and coupling capacitor, which means you need signal conditioning before the Pi can use them.
Recommended plan A, easiest
Use a USB sound card and a microphone input.
Pipeline:
USB audio input -> Python reads audio frames -> compute RMS/amplitude -> detect loud event
Pros: you can finish noise detection quickly.
Recommended plan B, more embedded
Use:
CMA-4544PF-W -> electret mic amplifier -> MCP3008 ADC -> Raspberry Pi SPI
MCP3008 wiring:
MCP3008 pin
Pi connection
VDD
3.3 V
VREF
3.3 V
AGND
GND
DGND
GND
CLK
GPIO11, SCLK
DOUT
GPIO9, MISO
DIN
GPIO10, MOSI
CS
GPIO8, CE0
CH0
Amplified microphone analog output

The MCP3008 acts as a bridge between analog and digital, with 8 analog inputs queried by the Pi using SPI.

5.5 Camera
Use one Pi camera for MVP.
MVP behavior:
Motion/noise event -> capture still image -> save to external drive -> show in dashboard event log
Use still snapshots first, not live streaming. Live streaming is a stretch goal.

5.6 External hard drive
Use the external hard drive for persistent logs and media.
Mount point:
/mnt/homehub
Folder structure:
/mnt/homehub/
    database/
        homehub.db
    media/
        snapshots/
        videos/
    logs/
        system.log
    exports/
Use a powered external drive or powered USB hub if the drive causes undervoltage or disconnects. Raspberry Pi’s official hardware docs recommend checking peripheral power needs and using an externally powered USB hub when unsure; they also list Pi 4 USB peripheral current as 1.2 A and Pi 5 downstream USB current as 1.6 A only with a 5 A supply. (raspberrypi.com)

6. Software architecture
Overall data flow
Sensor drivers
    |
    v
Sensor collector service
    |
    |--> SQLite database
    |--> Event detection engine
    |--> MQTT broker, optional
    |
    v
Backend API
    |
    v
Frontend dashboard
    |
    |--> Pi touchscreen kiosk
    |--> Laptop/phone over LAN
Recommended stack:
Layer
Tool
Sensor drivers
Python
GPIO
gpiozero or lgpio
I2C sensors
Adafruit CircuitPython libraries
Camera
Picamera2 or rpicam-still command wrapper
Backend
FastAPI
Database
SQLite
Frontend
React or plain HTML/CSS/JS
Live updates
Polling first, WebSockets later
Process management
systemd
Local network access
mDNS, raspberrypi.local
Optional IoT messaging
MQTT with Mosquitto

MVP should use REST polling before MQTT/WebSockets. REST polling is easier to debug and sufficient for the dashboard.

7. Repository structure
smart-home-edge-hub/
    README.md
    requirements.txt
    config.yaml

    hardware/
        wiring.md
        pin_map.md
        bringup_checklist.md

    sensors/
        aht20_sensor.py
        dps310_sensor.py
        ultrasonic_sensor.py
        noise_sensor.py
        sensor_collector.py

    events/
        event_engine.py
        led_controller.py
        camera_capture.py
        thresholds.py

    backend/
        server.py
        database.py
        schemas.py
        storage.py
        system_status.py

    frontend/
        index.html
        app.js
        styles.css

    scripts/
        install.sh
        mount_drive.sh
        start_dev.sh
        setup_systemd.sh

    services/
        homehub-backend.service
        homehub-sensors.service
        homehub-events.service
        homehub-kiosk.service

    tests/
        test_aht20.py
        test_dps310.py
        test_ultrasonic.py
        test_noise.py
        test_database.py
        test_api.py

8. Core services
8.1 sensor_collector.py
Responsibilities:
Initialize sensors.
Sample sensors on a schedule.
Write latest readings to a shared in-memory cache or database.
Log readings periodically.
Mark sensors as failed if they stop responding.
Sampling plan:
Signal
Sampling rate
Store rate
Temperature
Every 5 s
Every 10 s
Humidity
Every 5 s
Every 10 s
Pressure
Every 5 s
Every 10 s
Ultrasonic distance
5 Hz
Store only event-relevant values
Noise score
5 to 20 Hz
Store summary every 5 to 10 s
Camera
Event-triggered
Store image path

Data packet:
{
  "timestamp": "2026-05-07T16:30:00",
  "temperature_c": 23.4,
  "humidity_percent": 42.1,
  "pressure_hpa": 1012.8,
  "distance_cm": 84.2,
  "noise_score": 0.63,
  "occupancy": true,
  "sensor_health": {
    "aht20": "ok",
    "dps310": "ok",
    "ultrasonic": "ok",
    "microphone": "ok"
  }
}

8.2 event_engine.py
Responsibilities:
Read latest sensor data.
Detect motion, presence, loud noise, and environmental warnings.
Trigger camera capture.
Set NeoPixel state.
Insert event into database.
Debounce repeated events.
Event types:
SYSTEM_ONLINE
MOTION_DETECTED
PRESENCE_DETECTED
LOUD_NOISE
HIGH_TEMPERATURE
HIGH_HUMIDITY
PRESSURE_DROP
CAMERA_CAPTURED
SENSOR_FAILURE
STORAGE_WARNING
Event rules:
Motion:
    If abs(distance_now - distance_prev) > 25 cm within 1 second
    and cooldown expired:
        create MOTION_DETECTED

Presence:
    If distance_cm < 80 cm for more than 3 seconds:
        occupancy = true

Loud noise:
    If noise_score > threshold for 0.5 seconds:
        create LOUD_NOISE

High temperature:
    If temperature_c > 30 C for 30 seconds:
        create HIGH_TEMPERATURE

High humidity:
    If humidity_percent > 70 percent for 30 seconds:
        create HIGH_HUMIDITY

Pressure drop:
    If pressure drops more than 2 hPa over 30 minutes:
        create PRESSURE_DROP

Storage warning:
    If disk_free_gb < 2 GB:
        create STORAGE_WARNING
Debounce/cooldown:
Motion event cooldown: 10 s
Noise event cooldown: 10 s
Camera capture cooldown: 10 s
Environmental event cooldown: 5 min

8.3 camera_capture.py
MVP function:
def capture_snapshot(event_type: str) -> str:
    """
    Captures one image, saves it to /mnt/homehub/media/snapshots,
    returns the saved file path.
    """
Filename convention:
/mnt/homehub/media/snapshots/motion_2026-05-07_16-30-00.jpg
/mnt/homehub/media/snapshots/noise_2026-05-07_16-31-12.jpg
Do not start with live streaming. First finish snapshots.
Stretch goal:
5-second video clip around event

8.4 led_controller.py
Responsibilities:
Set LED strip color.
Animate alerts.
Return to normal state after alert timeout.
States:
ONLINE_GREEN
NORMAL_BLUE
WARNING_YELLOW
ALERT_RED
CAPTURE_PURPLE
ERROR_ORANGE
Behavior:
System boot:
    orange pulse

Backend online:
    green solid for 2 seconds

Normal:
    dim blue

Motion/noise:
    red pulse for 5 seconds

Camera capture:
    purple flash

Environmental warning:
    yellow slow pulse

Sensor/storage error:
    orange blink

8.5 server.py
Use FastAPI.
Endpoints:
GET  /api/latest
GET  /api/history?hours=24
GET  /api/events?limit=50
GET  /api/events/{event_id}
GET  /api/status
GET  /api/media/{filename}
POST /api/config/thresholds
POST /api/actions/capture
POST /api/actions/test-led
Example /api/latest response:
{
  "timestamp": "2026-05-07T16:30:00",
  "temperature_c": 23.4,
  "humidity_percent": 42.1,
  "pressure_hpa": 1012.8,
  "distance_cm": 84.2,
  "noise_score": 0.63,
  "occupancy": true,
  "last_event": {
    "event_type": "MOTION_DETECTED",
    "timestamp": "2026-05-07T16:29:55",
    "severity": "medium"
  },
  "system": {
    "status": "online",
    "disk_free_gb": 820,
    "ip_address": "192.168.1.42"
  }
}

9. Database schema
Use SQLite.
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    temperature_c REAL,
    humidity_percent REAL,
    pressure_hpa REAL,
    distance_cm REAL,
    noise_score REAL,
    occupancy INTEGER,
    aht20_status TEXT,
    dps310_status TEXT,
    ultrasonic_status TEXT,
    microphone_status TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT,
    media_path TEXT,
    acknowledged INTEGER DEFAULT 0
);

CREATE TABLE system_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    disk_free_gb REAL,
    cpu_temp_c REAL,
    ip_address TEXT,
    uptime_seconds INTEGER,
    status TEXT
);

CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
Default config values:
temperature_high_c = 30
humidity_high_percent = 70
motion_delta_cm = 25
presence_distance_cm = 80
noise_threshold = calibrated dynamically
camera_cooldown_seconds = 10
event_cooldown_seconds = 10

10. Dashboard plan
10.1 Touchscreen dashboard
Run Chromium in kiosk mode on the Pi.
URL:
http://localhost:8000
Main layout:
+------------------------------------------------+
| Smart Home Hub                    Online       |
+-------------------+----------------------------+
| Temp / Humidity   | Pressure                   |
| 23.4 C / 42%      | 1012.8 hPa                 |
+-------------------+----------------------------+
| Occupancy         | Noise                      |
| Detected          | Normal                     |
+-------------------+----------------------------+
| Latest Event: MOTION_DETECTED                  |
| Snapshot preview                                |
+------------------------------------------------+
| Recent Events                                  |
+------------------------------------------------+
| System: disk, IP, uptime, sensor health         |
+------------------------------------------------+
10.2 Web dashboard
Same dashboard should be accessible from laptop/phone:
http://raspberrypi.local:8000
Pages:
/
    Live dashboard

/events
    Event log and snapshots

/history
    Sensor graphs

/settings
    Thresholds and test actions

/status
    System health
10.3 Frontend priority
Build in this order:
Live cards.
Event log.
Latest image preview.
Graphs.
Threshold controls.
Polished styling.
Do not spend Week 2 or Week 3 designing the UI. First get sensors and API working.

11. Networking plan
MVP networking
Use the Pi as a local web server.
Pi runs FastAPI on port 8000
Laptop/phone accesses dashboard over same Wi-Fi
Touchscreen opens localhost dashboard
Enable:
SSH
I2C
SPI
Camera
mDNS hostname
Expected network demo:
Laptop browser -> http://raspberrypi.local:8000
Phone browser -> http://raspberrypi.local:8000
Touchscreen -> http://localhost:8000
Stretch networking
Add MQTT:
homehub/sensors/latest
homehub/events
homehub/status
homehub/actions/capture
homehub/actions/set_led
MQTT makes it more “IoT,” but do not block MVP on it.

12. Setup commands
12.1 Raspberry Pi config
sudo raspi-config
Enable:
Interface Options -> I2C
Interface Options -> SPI
Interface Options -> Camera
Interface Options -> SSH
Install basics:
sudo apt update
sudo apt upgrade -y

sudo apt install -y python3-pip python3-venv git sqlite3 chromium-browser
sudo apt install -y i2c-tools
Check I2C devices:
i2cdetect -y 1
Expected:
0x38 for AHT20
0x77 for DPS310
12.2 Python environment
cd smart-home-edge-hub
python3 -m venv .venv
source .venv/bin/activate

pip install fastapi uvicorn
pip install adafruit-blinka
pip install adafruit-circuitpython-ahtx0
pip install adafruit-circuitpython-dps310
pip install gpiozero
pip install rpi_ws281x adafruit-circuitpython-neopixel
pip install psutil
If using MCP3008:
pip install adafruit-circuitpython-mcp3xxx
If using USB audio:
pip install sounddevice numpy

13. Bring-up checklist
Hardware tests
Create these scripts and do not integrate until each passes.
test_aht20.py
    Prints temperature and humidity every second.

test_dps310.py
    Prints pressure and barometer temperature every second.

test_ultrasonic.py
    Prints distance in cm.
    Confirm no direct 5 V Echo to Pi.

test_camera.py
    Captures one image and saves it.

test_drive.py
    Writes and reads a test file from /mnt/homehub.

test_led.py
    Sets NeoPixel green, yellow, red, off.

test_noise.py
    Prints noise_score or RMS.
Expected pass criteria:
Test
Pass condition
AHT20
Temperature and humidity update reasonably
DPS310
Pressure around local atmospheric pressure
Ultrasonic
Distance changes when hand moves
Camera
Image file saved
Drive
File write/read succeeds
LED
Colors change correctly
Noise
Score spikes when clapping/tapping

14. Two-week implementation plan by person
Because we only have 2 weeks, the project will be built in parallel by ownership area rather than week-by-week. Each person will own a subsystem with clear inputs, outputs, and integration points. The goal is to have each subsystem working independently first, then combine everything during a final consolidation phase.

Nippun, frontend dashboard and application logic
Main ownership
Nippun will own the touchscreen/web dashboard and how users interact with the system. The dashboard should make the hub feel like one centralized smart home product rather than a collection of separate sensors.
Core responsibilities
Touchscreen dashboard
Web dashboard over LAN
API integration
Live sensor display
Event visualization
Camera snapshot viewer
Sensor graphs
Threshold/settings UI
Demo user experience
Concrete tasks
Build the main dashboard layout for 800 x 480 touchscreen.
Display live temperature, humidity, pressure, noise, distance, and occupancy.
Poll /api/latest every 1 second.
Poll /api/events every 5 seconds.
Build event log with event type, timestamp, severity, and snapshot preview.
Build latest camera event card.
Build simple graphs for recent temperature, humidity, pressure, and noise.
Add visual alert states:
    green/normal
    yellow/environment warning
    red/security event
    gray/sensor offline
Add a settings/control page for:
    test camera capture
    test LED
    update alert thresholds, if backend supports it
Make dashboard usable both on:
    http://localhost:8000 on the Pi touchscreen
    http://raspberrypi.local:8000 from laptop/phone
Deliverables
frontend/index.html
frontend/app.js
frontend/styles.css
Live dashboard page
Events page
History/graphs section
System status panel
Touchscreen-friendly UI
Exit criteria
Dashboard shows real or mocked data from the backend.
Dashboard updates without manual refresh.
Motion/noise events appear in the event log.
Latest camera snapshot appears in the UI.
Dashboard is readable on the Raspberry Pi touchscreen.
Dashboard is accessible from another device on the same Wi-Fi network.

Nicky, backend API and database
Main ownership
Nicky will own the backend communication layer that connects the hardware/event system to the dashboard. The backend should expose clean API endpoints so the frontend does not need to know hardware details.
Core responsibilities
FastAPI backend
SQLite database
API endpoints
Database queries
Media serving
Backend tests
API contract
Concrete tasks
Create the SQLite database schema.
Implement database.py for insert/query helpers.
Implement backend/server.py using FastAPI.
Create endpoint for latest readings:
    GET /api/latest

Create endpoint for recent history:
    GET /api/history?hours=24

Create endpoint for recent events:
    GET /api/events?limit=50

Create endpoint for system status:
    GET /api/status

Create endpoint for media:
    GET /api/media/{filename}

Optional control endpoints:
    POST /api/actions/capture
    POST /api/actions/test-led
    POST /api/config/thresholds

Serve frontend static files from the backend.
Make sure media files from external hard drive can be served to dashboard.
Write simple backend tests using sample database rows.
Deliverables
backend/server.py
backend/database.py
backend/schemas.py
backend/storage.py
backend/system_status.py
SQLite schema
Working API endpoints
Sample API responses for frontend testing
Exit criteria
/api/latest returns latest sensor data.
/api/history returns graphable historical data.
/api/events returns recent event rows.
/api/media/{filename} serves saved snapshots.
/api/status returns disk, IP, uptime, and system health.
Frontend can run against backend using either real or mocked data.

Hugh, hardware bring-up and sensor drivers
Main ownership
Hugh will own physical hardware setup, wiring safety, and individual hardware test scripts. The priority is making sure every part works safely before full integration.
Core responsibilities
Wiring
Power safety
Sensor bring-up
Touchscreen/camera mounting
External drive mounting
NeoPixel power setup
Hardware documentation
Standalone test scripts
Concrete tasks
Set up Raspberry Pi OS.
Enable SSH, I2C, SPI, and camera.
Mount and verify the Raspberry Pi touchscreen.
Connect and verify Raspberry Pi camera.
Mount external hard drive at /mnt/homehub.
Create the external drive folder structure:
    /mnt/homehub/database
    /mnt/homehub/media/snapshots
    /mnt/homehub/media/videos
    /mnt/homehub/logs

Wire AHT20 and DPS310 on I2C:
    AHT20 at 0x38
    DPS310 at 0x77

Run i2cdetect and document detected addresses.
Wire ultrasonic sensor:
    TRIG to GPIO23
    ECHO to GPIO24 through voltage divider

Wire NeoPixel strip:
    external 5 V supply
    common ground with Pi
    GPIO18 through level shifter to DIN

Set up microphone path:
    preferred fast option, USB audio input
    embedded option, mic amplifier plus MCP3008 ADC

Create individual hardware test scripts:
    test_aht20.py
    test_dps310.py
    test_ultrasonic.py
    test_camera.py
    test_drive.py
    test_led.py
    test_noise.py
Deliverables
hardware/wiring.md
hardware/pin_map.md
hardware/bringup_checklist.md
test_aht20.py
test_dps310.py
test_ultrasonic.py
test_camera.py
test_drive.py
test_led.py
test_noise.py
Exit criteria
Touchscreen works.
Camera captures a test image.
External drive can read/write files.
AHT20 prints temperature and humidity.
DPS310 prints pressure.
Ultrasonic distance changes when an object moves.
Noise score spikes when sound occurs.
NeoPixel changes color safely.
No Pi GPIO receives unsafe 5 V input.
No undervoltage warning during normal operation.

Siddarth, system integration and event engine
Main ownership
Siddarth will own the software layer that turns raw sensor readings into smart home events. This includes the unified sensor collector, event detection, camera triggers, LED state machine, and boot reliability.
Core responsibilities
Unified sensor collector
Event detection engine
Camera trigger logic
LED control logic
Sensor failure handling
Systemd services
End-to-end integration
Concrete tasks
Build sensors/sensor_collector.py.
Import or call Hugh's tested sensor drivers.
Create one unified JSON packet containing:
    timestamp
    temperature_c
    humidity_percent
    pressure_hpa
    distance_cm
    noise_score
    occupancy
    sensor_health

Write sensor readings to SQLite every 10 seconds.
Maintain latest reading for /api/latest.
Implement events/event_engine.py.
Detect motion using ultrasonic distance change:
    if abs(distance_now - distance_prev) > threshold

Detect presence:
    if distance_cm remains below threshold for several seconds

Detect loud noise:
    if noise_score exceeds calibrated threshold

Detect environmental warnings:
    high temperature
    high humidity
    pressure drop

Implement event cooldowns to avoid spam.
Trigger camera snapshot on motion/noise.
Save camera snapshot path into event row.
Set NeoPixel state based on event severity.
Implement led_controller.py states:
    normal
    warning
    alert
    camera capture
    error

Create systemd services:
    homehub-backend.service
    homehub-sensors.service
    homehub-events.service
    homehub-kiosk.service
Deliverables
sensors/sensor_collector.py
events/event_engine.py
events/camera_capture.py
events/led_controller.py
events/thresholds.py
services/homehub-backend.service
services/homehub-sensors.service
services/homehub-events.service
services/homehub-kiosk.service
Exit criteria
sensor_collector.py produces full JSON readings.
Event engine detects motion.
Event engine detects loud noise.
Motion/noise triggers camera snapshot.
Event rows are written to database.
NeoPixel changes state on events.
Services can start automatically on boot.
System keeps running if one sensor temporarily fails.

Shared interface contract
To make parallel work possible, everyone should agree on the same data format early. The frontend, backend, and sensor system should all use this shape.
Latest sensor packet
{
  "timestamp": "2026-05-07T16:30:00",
  "temperature_c": 23.4,
  "humidity_percent": 42.1,
  "pressure_hpa": 1012.8,
  "distance_cm": 84.2,
  "noise_score": 0.63,
  "occupancy": true,
  "sensor_health": {
    "aht20": "ok",
    "dps310": "ok",
    "ultrasonic": "ok",
    "microphone": "ok",
    "camera": "ok",
    "storage": "ok"
  }
}
Event packet
{
  "id": 17,
  "timestamp": "2026-05-07T16:32:10",
  "event_type": "MOTION_DETECTED",
  "severity": "medium",
  "message": "Motion detected from ultrasonic distance change.",
  "media_url": "/api/media/motion_2026-05-07_16-32-10.jpg",
  "acknowledged": false
}
System status packet
{
  "status": "online",
  "ip_address": "192.168.1.42",
  "disk_free_gb": 820,
  "cpu_temp_c": 48.2,
  "uptime_seconds": 5421
}

Consolidation and final integration phase
The final consolidation phase should happen after each person’s subsystem works independently. This is where the project becomes one complete product.
Step 1, freeze interfaces
Before merging everything, freeze:
API endpoint names
JSON response formats
Database schema
Pin map
Storage paths
Event type names
Threshold config names
No one should keep changing these casually during final integration.

Step 2, connect hardware to backend
Integration path:
Hugh's hardware test scripts
        |
        v
Siddarth's sensor_collector.py
        |
        v
Nicky's SQLite database and FastAPI backend
        |
        v
Nippun's dashboard
First test with only one sensor, then add sensors one by one:
AHT20 only
AHT20 + DPS310
AHT20 + DPS310 + ultrasonic
AHT20 + DPS310 + ultrasonic + noise
Full system with camera and NeoPixel

Step 3, run end-to-end event test
Test sequence:
1. Start backend.
2. Start sensor collector.
3. Start event engine.
4. Open dashboard on laptop.
5. Open dashboard on touchscreen.
6. Move hand near ultrasonic sensor.
7. Confirm motion event appears.
8. Confirm NeoPixel turns red.
9. Confirm camera snapshot is saved.
10. Confirm snapshot appears in dashboard.
11. Make loud noise.
12. Confirm noise event appears.
13. Confirm database stores sensor readings and events.

Step 4, boot automation
Once the manual flow works, add boot automation.
Required behavior:
Power on Raspberry Pi.
External drive mounts.
Backend starts.
Sensor collector starts.
Event engine starts.
Touchscreen opens dashboard in kiosk mode.
Laptop can access dashboard over LAN.
Services:
homehub-backend.service
homehub-sensors.service
homehub-events.service
homehub-kiosk.service
Exit criteria:
One reboot brings the full system back online without manually starting scripts.

Step 5, reliability pass
Run a 30 to 60 minute test.
Check:
No crashes.
No database write errors.
No missing media paths.
No repeated event spam.
No Pi undervoltage warning.
No sensor read failure crashes the whole system.
No dashboard freeze.
Add fallback behavior:
If a sensor fails:
    mark it as offline in sensor_health
    keep dashboard running

If camera fails:
    create event without media_path
    show "snapshot unavailable"

If external drive is missing:
    write to local fallback folder
    show storage warning

If backend is down:
    dashboard shows disconnected state

Step 6, final demo script
Use this exact final demo sequence:
1. Power on the Pi.
2. Show the touchscreen dashboard opening automatically.
3. Show live temperature, humidity, pressure, noise, distance, and occupancy.
4. Open the same dashboard from a laptop or phone using raspberrypi.local.
5. Point out the Pi is acting as a local IoT edge server.
6. Move a hand or object in front of the ultrasonic sensor.
7. Show the NeoPixel strip turning red.
8. Show the camera snapshot being captured.
9. Show the motion event appearing in the dashboard event log.
10. Make a loud sound.
11. Show the noise event appearing.
12. Show the external hard drive folder containing saved snapshots and database/log files.
13. Explain that the system centralizes sensing, security, storage, and dashboarding into one smart home hub.

Final 2-week priority order
If time gets tight, follow this priority order:
1. Touchscreen/dashboard works with mocked data.
2. Backend API works with mocked data.
3. AHT20 and DPS310 real readings work.
4. Ultrasonic motion detection works.
5. Camera snapshot on motion works.
6. Event log shows snapshots.
7. External hard drive stores snapshots/database.
8. NeoPixel status/alert lighting works.
9. Noise detection works.
10. Boot automation works.
11. Graphs and settings polish.
12. MQTT, live video, anomaly detection, and advanced features only if time remains.
The non-negotiable MVP should be:
Live dashboard
Temperature/humidity/pressure readings
Ultrasonic motion event
Camera snapshot on event
Event log
External storage
LAN access
Basic LED alert


16. MVP versus stretch goals
Must-have MVP
Touchscreen dashboard
Web dashboard over LAN
AHT20 temperature/humidity
DPS310 pressure
Ultrasonic motion/presence
Noise event detection
Camera snapshot on event
External HDD storage
NeoPixel alert/status lighting
SQLite logging
High-value stretch goals
MQTT broker
Live camera stream
Short video clips on event
Email/Discord/Telegram alert
Samba shared folder for logs/media
Face/person detection
Anomaly detection model
Weather API comparison with local pressure trend
Multiple sensor nodes
User login
My recommendation: only add MQTT after the REST dashboard is working. Only add live streaming after event snapshots are working.

17. Risk register
Risk
Impact
Fix
AHT20 duplicate address
Cannot use both AHT20s on same I2C bus
Use one AHT20, or add TCA9548A mux
Bare mic not directly readable
Noise feature blocked
Use USB audio or amplifier + MCP3008
Ultrasonic Echo is 5 V
Could damage Pi GPIO
Use voltage divider
NeoPixel current draw
Pi resets or strip flickers
External 5 V supply, common ground
NeoPixel data level mismatch
Unreliable LED behavior
Use 74AHCT125/74HCT245
External HDD draws too much current
Drive disconnects, Pi undervoltage
Powered drive/hub
Camera/display cable mismatch
Camera/display unavailable
Prefer Pi 4 or get correct Pi 5 cables
Dashboard too ambitious
Wasted time
MVP first: live cards, events, snapshot
Event spam
Too many alerts
Add cooldowns/debounce
Sensor failures crash system
Bad demo
Catch exceptions and mark sensor unhealthy


18. Final deliverable checklist
By the end, you should be able to show:
Hardware:
    Touchscreen mounted
    Camera working
    AHT20 working
    DPS310 working
    Ultrasonic working safely
    Noise path working
    NeoPixel alert strip working
    External drive mounted

Software:
    Sensor collector running
    Event engine running
    Backend API running
    SQLite logging
    Dashboard running locally
    Dashboard accessible over LAN
    Camera snapshots stored
    systemd boot services working

Demo:
    Motion triggers event
    Noise triggers event
    Camera snapshot appears
    LED changes state
    Sensor graphs update
    Files are saved to external drive

19. Best final architecture diagram for your report
                 +-----------------------+
                 |  Phone / Laptop       |
                 |  Web Dashboard        |
                 +-----------+-----------+
                             |
                             | LAN / Wi-Fi
                             |
+----------------------------v-----------------------------+
|                    Raspberry Pi Edge Hub                  |
|                                                          |
|  +----------------+      +----------------------------+   |
|  | FastAPI Server |<---->| SQLite + External HDD       |   |
|  +-------+--------+      +----------------------------+   |
|          ^                                               |
|          |                                               |
|  +-------+--------+      +----------------------------+   |
|  | Event Engine   |----->| Camera Snapshot Service     |   |
|  +-------+--------+      +----------------------------+   |
|          |                                               |
|          v                                               |
|  +----------------+                                      |
|  | NeoPixel LEDs  |                                      |
|  +----------------+                                      |
|                                                          |
|  +----------------------------------------------------+  |
|  | Sensor Collector                                   |  |
|  | AHT20, DPS310, Ultrasonic, Microphone              |  |
|  +----------------------------------------------------+  |
|                                                          |
|  +--------------------------+                           |
|  | Touchscreen Dashboard    |                           |
|  +--------------------------+                           |
+----------------------------------------------------------+
This plan gives you a realistic MVP, a technically strong systems story, and a clean demo path.

