from picamera2 import Picamera2
import time

cam = Picamera2()
cam.configure(cam.create_still_configuration(main={"size": (1280, 720)}))
cam.start()
time.sleep(2)  # let AE/AWB settle

cam.capture_file("/home/hpalin/smart-hub/data/snapshot.jpg")
cam.stop()
print("Saved snapshot.jpg")
