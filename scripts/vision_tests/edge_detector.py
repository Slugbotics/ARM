import cv2
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from camera_ports_list import open_camera

default_camera_port = 0

capture = open_camera(default_camera_port)
            
# Get the width and height of the frame
width = int(capture.get(3))  # 3 corresponds to CV_CAP_PROP_FRAME_WIDTH
height = int(capture.get(4))  # 4 corresponds to CV_CAP_PROP_FRAME_HEIGHT

print("cap width: " + str(width))
print("cap height: " + str(height))
print("  ---------------------  ");

while True:
    _,frame = capture.read()
    

    edges = cv.Canny(frame,100,200)

    cv2.imshow('Edge Detector',edges)
    
    exit_key_press = cv2.waitKey(1)
    
    if exit_key_press == ord('q'):
        break
    
capture.release()
cv2.waitKey(0)
cv2.destroyAllWindows()