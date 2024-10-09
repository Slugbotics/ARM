# Install dependencies
import subprocess
subprocess.check_call(["pip", "install", "torch", "torchvision", "opencv-python"])

from camera_ports_list import open_camera

import cv2
import torch
from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large
from torchvision.transforms import functional as F
import numpy as np

default_camera_port = 0

# Load the pre-trained DeepLabV3 model
model = deeplabv3_mobilenet_v3_large(pretrained=True)
model.eval()

# Define a function to get predictions
def get_predictions(frame):
    transform = F.to_tensor(frame).unsqueeze(0)
    with torch.no_grad():
        output = model(transform)['out'][0]
    return output.argmax(0).byte().cpu().numpy()

# Define a function to apply random color masks
def apply_color_mask(frame, mask):
    unique_classes = np.unique(mask)
    colors = {cls: np.random.randint(0, 255, (3,), dtype=np.uint8) for cls in unique_classes}
    
    color_mask = np.zeros_like(frame)
    for cls, color in colors.items():
        color_mask[mask == cls] = color
    
    return cv2.addWeighted(frame, 0.5, color_mask, 0.5, 0)

# Capture video from the webcam
cap = open_camera(default_camera_port)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Resize frame for faster processing
    small_frame = cv2.resize(frame, (320, 240))
    
    # Get predictions and apply color mask
    mask = get_predictions(small_frame)
    mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
    frame = apply_color_mask(frame, mask)
    
    cv2.imshow('Semantic Segmentation', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
