import time
import board
import adafruit_ahtx0

i2c = board.I2C()                # uses GPIO2 (SDA) and GPIO3 (SCL) by default
sensor = adafruit_ahtx0.AHTx0(i2c)

print("AHT20 ready. Reading every 2s. Ctrl+C to stop.\n")

while True:
    temp_c = sensor.temperature
    rh = sensor.relative_humidity
    temp_f = temp_c * 9 / 5 + 32
    print(f"Temp: {temp_c:5.2f} °C ({temp_f:5.2f} °F)   RH: {rh:5.2f}%")
    time.sleep(2)
    