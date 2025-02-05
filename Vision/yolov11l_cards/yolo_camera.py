import os
import time
import cv2
import numpy as np
from ultralytics import YOLO

# Set model path (Ensure this path is correct)
MODEL_PATH = "runs/detect/train/weights/best.pt"

# Load YOLO model
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model file '{MODEL_PATH}' not found!")
    exit(1)

model = YOLO(MODEL_PATH)

# Initialize webcam (0 for default laptop camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open laptop camera. Make sure it's not being used by another application.")
    exit(1)

# Set frame width and height (optional, can be adjusted)
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
cap.set(3, FRAME_WIDTH)
cap.set(4, FRAME_HEIGHT)

# Define bounding box colors
bbox_colors = [(164, 120, 87), (68, 148, 228), (93, 97, 209), (178, 182, 133),
               (88, 159, 106), (96, 202, 231), (159, 124, 168), (169, 162, 241),
               (98, 118, 150), (172, 176, 184)]

# Start real-time detection
print("Starting camera stream... Press 'q' to exit.")

while True:
    t_start = time.perf_counter()

    ret, frame = cap.read()
    if not ret:
        print("ERROR: Failed to capture image from webcam.")
        break

    # Run YOLO inference on the frame
    results = model(frame, verbose=False)

    # Extract detections
    detections = results[0].boxes

    # Object counting
    object_count = 0

    # Process detections
    for i in range(len(detections)):
        xyxy_tensor = detections[i].xyxy.cpu()  # Bounding box coordinates (Tensor)
        xyxy = xyxy_tensor.numpy().squeeze()  # Convert to numpy array
        xmin, ymin, xmax, ymax = xyxy.astype(int)  # Convert to int

        # Get class and confidence
        classidx = int(detections[i].cls.item())
        classname = model.names[classidx]
        conf = detections[i].conf.item()

        # Draw bounding box if confidence is high enough
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

    # Show frame with detections
    cv2.imshow("YOLO Detection", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("Camera stream closed.")
