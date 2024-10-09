import time

from DistanceByObject import DistanceByObject

detection = DistanceByObject()

detection.start_detect()

print("Startup.")
keep_running = True
while(keep_running):
    data = detection.get_data()
    print("Data: ")
    print(data)
    time.sleep(0.25)
    keep_running = detection.is_running()
    print("keep_running: " + str(keep_running))