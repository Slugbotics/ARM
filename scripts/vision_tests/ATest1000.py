import cv2
from camera_ports_list import open_camera

default_camera_port = 0

capture = open_camera(0)
            
# Get the width and height of the frame
width = int(capture.get(3))  # 3 corresponds to CV_CAP_PROP_FRAME_WIDTH
height = int(capture.get(4))  # 4 corresponds to CV_CAP_PROP_FRAME_HEIGHT

print("cap width: " + str(width))
print("cap height: " + str(height))
print("  ---------------------  ");

while True:
    _,frame = capture.read()
    cv2.imshow('ATest 1000',frame)
    
    exit_key_press = cv2.waitKey(1)
    
    if exit_key_press == ord('q'):
        break
    
capture.release()
cv2.waitKey(0)
cv2.destroyAllWindows()