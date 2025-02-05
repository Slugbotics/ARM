import os
import time
import cv2
import numpy as np
from ultralytics import YOLO

# Hardcoded values (No need for argparse)
MODEL_PATH = "my_model.pt"  # Change if the file is in another directory
CAMERA_INDEX = 0  # 'usb0' is usually index 0 on a laptop
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Check if model file exists
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model file '{MODEL_PATH}' not found!")
    exit(1)

# Load YOLO model
model = YOLO(MODEL_PATH)

# Open laptop webcam (Framework 13 Camera)
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("ERROR: Could not open laptop camera. Make sure it's not being used by another application.")
    exit(1)

# Set camera resolution
cap.set(3, FRAME_WIDTH)
cap.set(4, FRAME_HEIGHT)

# Define bounding box colors
bbox_colors = [(164, 120, 87), (68, 148, 228), (93, 97, 209), (178, 182, 133),
               (88, 159, 106), (96, 202, 231), (159, 124, 168), (169, 162, 241),
               (98, 118, 150), (172, 176, 184)]

print("Starting camera stream... Press 'q' to exit.")

while True:
    t_start = time.perf_counter()

    ret, frame = cap.read()
    if not ret:
        print("ERROR: Failed to capture image from webcam.")
        break

    # Run YOLO inference
    results = model(frame, verbose=False)

    # Extract detections
    detections = results[0].boxes

    # Object counting
    object_count = 0

    for i in range(len(detections)):
        xyxy_tensor = detections[i].xyxy.cpu()
        xyxy = xyxy_tensor.numpy().squeeze()
        xmin, ymin, xmax, ymax = xyxy.astype(int)

        classidx = int(detections[i].cls.item())
        classname = model.names[classidx]
        conf = detections[i].conf.item()

        if conf > 0.5:
            color = bbox_colors[classidx % 10]
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
            label = f"{classname}: {int(conf * 100)}%"
            cv2.putText(frame, label, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            object_count += 1

    # Display FPS and object count
    fps = 1 / (time.perf_counter() - t_start)
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"Objects: {object_count}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("YOLO Detection", frame)

    # Exit with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Camera stream closed.")