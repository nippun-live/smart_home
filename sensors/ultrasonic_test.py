import time
from gpiozero import DistanceSensor

# echo on GPIO17, trigger on GPIO4
sensor = DistanceSensor(echo=17, trigger=23, max_distance=4.0)

print("HC-SR04 ready. Reading every 0.5s. Ctrl+C to stop.\n")

while True:
    distance_m = sensor.distance          # meters, 0.0 to max_distance
    distance_cm = distance_m * 100
    print(f"Distance: {distance_cm:6.1f} cm")
    time.sleep(0.5)