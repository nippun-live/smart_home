"""
Logs AHT20 (temp/humidity), DPS310 (pressure/altitude), and HC-SR04 (distance)
once per second for 60 seconds, writing each sample to a timestamped CSV.
"""

import time
import csv
from datetime import datetime
from pathlib import Path

import board
import adafruit_ahtx0
import adafruit_dps310
from gpiozero import DistanceSensor

# --- config ---
DURATION_SEC = 180
SAMPLE_INTERVAL_SEC = 1.0
DATA_DIR = Path.home() / "smart-hub" / "data"

# --- sensor init ---
print("Initializing sensors...")
i2c = board.I2C()
aht = adafruit_ahtx0.AHTx0(i2c)
dps = adafruit_dps310.DPS310(i2c)
ultrasonic = DistanceSensor(echo=17, trigger=23, max_distance=4.0)

# --- output file ---
DATA_DIR.mkdir(parents=True, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = DATA_DIR / f"sensor_log_{ts}.csv"

print(f"Logging {DURATION_SEC}s @ {1/SAMPLE_INTERVAL_SEC:.0f} Hz")
print(f"Output: {csv_path}\n")

# --- main loop ---
start = time.time()
sample_count = 0

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "timestamp",
        "temp_aht_c", "humidity_pct",
        "pressure_hpa", "temp_dps_c", "altitude_m",
        "distance_cm",
    ])

    try:
        while time.time() - start < DURATION_SEC:
            iter_start = time.time()
            now = datetime.now().isoformat(timespec="milliseconds")

            try:
                temp_aht = aht.temperature
                humidity = aht.relative_humidity
                pressure = dps.pressure
                temp_dps = dps.temperature
                altitude = dps.altitude
                distance_cm = ultrasonic.distance * 100

                writer.writerow([
                    now,
                    f"{temp_aht:.2f}", f"{humidity:.2f}",
                    f"{pressure:.2f}", f"{temp_dps:.2f}", f"{altitude:.2f}",
                    f"{distance_cm:.1f}",
                ])
                f.flush()  # write to disk immediately so Ctrl+C doesn't lose data

                sample_count += 1
                elapsed = time.time() - start
                print(
                    f"[{sample_count:3d}] {elapsed:5.1f}s  "
                    f"T={temp_aht:5.2f}°C  RH={humidity:5.2f}%  "
                    f"P={pressure:7.2f}hPa  D={distance_cm:6.1f}cm"
                )
            except Exception as e:
                print(f"  ! read error: {e}")

            # sleep just enough to keep cadence steady
            elapsed_iter = time.time() - iter_start
            if elapsed_iter < SAMPLE_INTERVAL_SEC:
                time.sleep(SAMPLE_INTERVAL_SEC - elapsed_iter)

    except KeyboardInterrupt:
        print("\nInterrupted — partial data saved.")

print(f"\nDone. {sample_count} samples written to:")
print(f"  {csv_path}")