import cv2
import numpy as np
from camera_ports_list import open_camera

default_camera_port = 0

capture = open_camera(default_camera_port)

# Get the width and height of the frame
width = int(capture.get(3))  # 3 corresponds to CV_CAP_PROP_FRAME_WIDTH
height = int(capture.get(4))  # 4 corresponds to CV_CAP_PROP_FRAME_HEIGHT

print("cap width: " + str(width))
print("cap height: " + str(height))
print("  ---------------------  ")

params = cv2.SimpleBlobDetector_Params()
# Change thresholds
params.minThreshold = 10
params.maxThreshold = 200

# Filter by Area.
params.filterByArea = True
params.minArea = 400

# Filter by Circularity
params.filterByCircularity = True
params.minCircularity = 0.1

# Filter by Convexity
params.filterByConvexity = True
params.minConvexity = 0.87

# Filter by Inertia
params.filterByInertia = False
params.minInertiaRatio = 0.01

detector = cv2.SimpleBlobDetector_create(params)

while True:
    capture_sucess, frame = capture.read()

    # if frame is read correctly ret is True
    if not capture_sucess:
        print("Can't receive frame (stream end?). Exiting ...")
        continue

    # Convert BGR to grayscale
    gray_image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Detect blobs.
    keypoints = detector.detect(gray_image)

    im_with_keypoints = cv2.drawKeypoints(
        frame,
        keypoints,
        np.array([]),
        (0, 0, 255),
        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
    )

    cv2.imshow("Blob Detector", im_with_keypoints)

    exit_key_press = cv2.waitKey(1)

    if exit_key_press == ord("q"):
        break

capture.release()
cv2.waitKey(0)
cv2.destroyAllWindows()
