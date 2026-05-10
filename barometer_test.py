import time
import board
import adafruit_dps310

i2c = board.I2C()
dps = adafruit_dps310.DPS310(i2c)

print("DPS310 ready. Reading every 2s. Ctrl+C to stop.\n")

while True:
    pressure_hpa = dps.pressure          # hectopascals (= mbar)
    temp_c = dps.temperature             # internal temp, used for compensation
    altitude_m = dps.altitude            # meters above sea level
    print(f"Pressure: {pressure_hpa:7.2f} hPa   Temp: {temp_c:5.2f} °C   Altitude: {altitude_m:6.1f} m")
    time.sleep(2)