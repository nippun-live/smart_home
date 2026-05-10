# Smart Home Monitoring Hub

CS437 final project — Raspberry Pi 5 smart home hub aggregating environmental sensors, motion/distance detection, camera, and a touchscreen dashboard into one centralized system.

## Team

- **Hugh Palin** (`hpalin2`) — hardware integration, ordering, RPi host owner
- **Siddarth Natarajan** (`sn28`) — embedded software, sensor integration
- **Nicky Chen** (`nickywc2`) — backend API
- **Nippun Sabharwal** (`nippuns2`) — frontend dashboard

## Platform

- Raspberry Pi 5, Pi OS Bookworm (Debian 12, kernel 6.12, aarch64)
- Hostname `hraspi`, user `hpalin`, IP `192.168.0.100` (DHCP)
- SSH via shared `raspkey` keypair (held by team Macs)
- Project root: `~/smart-hub`

## Hardware pinout

I2C bus 1 (shared) — SDA = GPIO 2 / pin 3, SCL = GPIO 3 / pin 5.

| Component | Type | Address / GPIO | Power | GND |
|---|---|---|---|---|
| AHT20 (Adafruit 4566) | I2C temp/humidity | `0x38` | pin 1 (3.3V) | pin 6 |
| DPS310 (Adafruit 4494) | I2C pressure/altitude | `0x77` | pin 17 (3.3V) | pin 9 |
| HC-SR04 | Ultrasonic distance | Trig=GPIO 23 (pin 16), Echo=GPIO 17 (pin 11) | pin 2 (5V) | pin 14 |
| Pi Camera | CSI via 22→15-pin adapter | `CAM/DISP 0` | — | — |
| Pi 7" Touch Display v1 | DSI via 22→15-pin adapter (SC1119) | `CAM/DISP 1` | GPIO 5V/GND | — |

DPS310 breakout pin labels: `SDI` = SDA, `SCK` = SCL. `3Vo`, `SDO`, `CS` left floating.

HC-SR04 Echo line goes through a **10kΩ + 20kΩ voltage divider** to drop the sensor's 5V output to ~3.33V before reaching GPIO 17. Direct connection will degrade the GPIO clamp diodes over time.

## Hardware gotchas (already resolved — don't relitigate)

- Pi 5 uses 22-pin FPC connectors for DSI and CSI. 15-pin cables shipped with older Pi cameras and the Touch Display v1 don't fit and need adapter cables.
- GPIO 4 is claimed by the 1-Wire kernel module by default. Use other GPIOs for new digital pins, or disable 1-Wire via `raspi-config` → Interface Options → 1-Wire.
- HC-SR04 outputs 5V on Echo. Always voltage-divide before GPIO.

## Hardware not yet wired

- **Microphone** (CUI CMA-4544PF-W, ×4) — bare analog electret capsules. Pi has no ADC. Need either MAX9814 + USB sound card (best for FFT/audio classification) or MAX9814 + MCP3008 SPI ADC. Parts not yet ordered.
- **LED strip** (Adafruit 2541, NeoPixel-family) — needs 74AHCT125 level shifter on data line and a separate 5V/3A+ supply (do not power from Pi rail).

## Software environment

Python venv at `~/smart-hub/venv`, **must be created with `--system-site-packages`** so it can see `picamera2` (apt-installed system-wide; not pip-installable cleanly).

Conda's `(base)` was disabled with `conda config --set auto_activate_base false` because it shadows the system Python and breaks venv `--system-site-packages` inheritance. If `(base)` ever appears in the prompt, run `conda deactivate` before creating any venv.

### Recreating the venv (use `/usr/bin/python3` explicitly):

```bash
cd ~/smart-hub
rm -rf venv
/usr/bin/python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install adafruit-circuitpython-ahtx0 adafruit-circuitpython-dps310 gpiozero lgpio
```

### Common commands

```bash
source ~/smart-hub/venv/bin/activate   # always activate first
python log_all.py                       # 60s logger, all 3 sensors → CSV
python sensors/_test.py           # individual sensor test
i2cdetect -y 1                          # confirm 0x38 + 0x77 on bus
rpicam-hello -t 5000                    # camera CLI smoke test
rpicam-still -o data/snap.jpg           # CLI still capture
```

## Project layout

```
~/smart-hub/
├── CLAUDE.md             # this file
├── log_all.py            # main: 1 Hz logger of all 3 sensors for 60s → CSV
├── sensors/
│   ├── aht20_test.py
│   ├── dps310_test.py
│   ├── ultrasonic_test.py
│   └── camera_test.py
├── data/                 # CSVs, snapshots (gitignore)
└── venv/                 # gitignore
```

## Code conventions

- Individual sensor test scripts in `sensors/`. Integration / main scripts at project root.
- CSV timestamps: ISO format with milliseconds, `datetime.now().isoformat(timespec="milliseconds")`.
- All sensor reads wrapped in `try`/`except`; one bad read should never kill a long run.
- `f.flush()` after every CSV row so Ctrl+C never loses partial data.
- Cadence-corrected sleep (`time.sleep(interval - elapsed_iter)`) to keep sample rate steady, not drift.
- gpiozero needs the `lgpio` backend on Pi 5. RPi.GPIO does not work on Pi 5.

## Status

**Working:** AHT20 + DPS310 + HC-SR04 logging to CSV at 1 Hz; Pi camera capturing stills via picamera2.

**Open work:**
1. Microphone integration (parts pending)
2. Frontend bridge — Nippun's dashboard. Likely path: Flask server on Pi exposing `/snapshot.jpg` (latest camera frame) and `/sensors.json` (latest reading), plus an MJPEG `/stream` endpoint for live camera.
3. Backend API contract with Nicky — agree on JSON schema for sensor payloads.
4. Persistent storage decision — stick with CSV vs SQLite for queryability.
5. Wrap `log_all.py` in a systemd service so it runs on boot.

## Notes for Claude Code

- When adding a new GPIO peripheral, check the pinout table above for free pins.
- When debugging a sensor that "stopped working," first run `i2cdetect -y 1` to confirm bus presence.
- Don't suggest `RPi.GPIO` — Pi 5 uses `gpiozero` + `lgpio` only.
- Don't `pip install picamera2` — it's apt-installed and the venv inherits it via `--system-site-packages`.
- No test suite or linter configured yet.