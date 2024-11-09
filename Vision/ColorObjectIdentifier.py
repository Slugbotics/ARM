import cv2
import numpy as np
from typing import List

from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier

# Define color boundaries in HSV space for distinct colors
COLOR_RANGES = {
    "Red": [(0, 50, 50), (10, 255, 255)],
    "Orange": [(10, 50, 50), (20, 255, 255)],
    "Yellow": [(20, 50, 50), (35, 255, 255)],
    "Green": [(35, 50, 50), (85, 255, 255)],
    "Cyan": [(85, 50, 50), (100, 255, 255)],
    "Blue": [(100, 50, 50), (125, 255, 255)],
    "Purple": [(125, 50, 50), (145, 255, 255)],
    "Magenta": [(145, 50, 50), (160, 255, 255)],
    "Red2": [(160, 50, 50), (180, 255, 255)],  # Wraparound for red
}

# Predefined color mappings for consistency
COLOR_MAP = {
    "Red": (0, 0, 255),        # BGR format for red
    "Orange": (0, 165, 255),    # BGR format for orange
    "Yellow": (0, 255, 255),    # BGR format for yellow
    "Green": (0, 255, 0),       # BGR format for green
    "Cyan": (255, 255, 0),      # BGR format for cyan
    "Blue": (255, 0, 0),        # BGR format for blue
    "Purple": (255, 0, 255),    # BGR format for purple
    "Magenta": (255, 0, 128),   # BGR format for magenta
    "Gray": (128, 128, 128),    # BGR format for gray
    "White": (255, 255, 255),   # BGR format for white
    "Black": (0, 0, 0),         # BGR format for black (border outline in white to show visibility)
    "Unknown": (128, 128, 128)  # Default for any unknown color
}

def visualize_contours(image, objects):
    # Copy the original image to avoid modifying it directly
    output_image = image.copy()
    
    for obj in objects:
        color_name = obj.get_metadata("color")
        contour = obj.get_metadata("contour")

        # Get color from the COLOR_MAP or use a default color if undefined
        color = COLOR_MAP.get(color_name, COLOR_MAP["Unknown"])
        
        # Draw contour with thickness for visibility
        cv2.drawContours(output_image, [contour], -1, color, 3)

        # Calculate the center of the object to label it
        M = cv2.moments(contour)
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
        else:
            center_x, center_y = 0, 0

        # Draw the label on the object
        label = f"{color_name} Object"
        cv2.putText(output_image, label, (center_x - 40, center_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        
    return output_image

class ColorObjectIdentifier(VisualObjectIdentifier):
    def __init__(self):
        pass
    
    def identify_shape(self, contour) -> str:
        # Approximate the contour to reduce vertices, useful for shape recognition
        approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
        num_vertices = len(approx)
        
        # Determine shape based on the number of vertices
        if num_vertices == 3:
            return "Triangle"
        elif num_vertices == 4:
            # Check for square vs rectangle by aspect ratio
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            if 0.9 <= aspect_ratio <= 1.1:
                return "Square"
            else:
                return "Rectangle"
        elif num_vertices == 5:
            return "Pentagon"
        elif num_vertices == 6:
            return "Hexagon"
        else:
            # For shapes with many vertices, assume a circle
            return "Circle"

    def identify_color(self, image_hsv, contour) -> str:
        # Create a mask for the object
        mask = np.zeros(image_hsv.shape[:2], dtype="uint8")
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Compute the mean color of the masked region
        mean_color_hsv = cv2.mean(image_hsv, mask=mask)[:3]
        hue, sat, val = mean_color_hsv

        # Refined color boundaries in HSV space with more colors
        if sat < 30:
            # Very low saturation indicates shades of gray/black/white
            if val > 200:
                return "White"
            elif val > 60:
                return "Gray"
            else:
                return "Black"
        
        if 0 <= hue < 10 or 160 <= hue <= 180:
            return "Red"
        elif 10 <= hue < 20:
            return "Orange"
        elif 20 <= hue < 35:
            return "Yellow"
        elif 35 <= hue < 85:
            return "Green"
        elif 85 <= hue < 100:
            return "Cyan"
        elif 100 <= hue < 125:
            return "Blue"
        elif 125 <= hue < 145:
            return "Purple"
        elif 145 <= hue < 160:
            return "Magenta"
        
        return "Unknown"

    def separate_objects_by_color(self, hsv_image: cv2.typing.MatLike) -> dict:
        contours_by_color = {}

        # Iterate over each color range, threshold the image, and find contours
        for color_name, (lower, upper) in COLOR_RANGES.items():
            # Create a mask for each color
            mask = cv2.inRange(hsv_image, np.array(lower), np.array(upper))

            # Clean up the mask using morphological operations
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

            # Find contours for the current color mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Store contours under the color name
            contours_by_color[color_name] = (contours, mask)

        return contours_by_color

    def extract_objects(self, hsv_image: cv2.typing.MatLike) -> List[VisionObject]:
        
        image_height: int = hsv_image.shape[0]
        image_width: int = hsv_image.shape[1]
        
        contours_by_color = self.separate_objects_by_color(hsv_image)

        objects = []
        for color, (contours, mask) in contours_by_color.items():
            for contour in contours:
                # Process each contour for the detected color
                # cv2.drawContours(image, [contour], -1, (255, 255, 255), 2)  # Example: Draw in white for visibility
                # print(f"Detected {color} object with contour area: {cv2.contourArea(contour)}")
                
                shape = self.identify_shape(contour)
                color = self.identify_color(hsv_image, contour)
                    
                #find the largest contour and create its bounding box
                (center_x, center_y), radius = cv2.minEnclosingCircle(contour)
                center = (int(center_x), int(center_y))
                radius = int(radius)
                # Calculate the bounding box for each object
                x, y, w, h = cv2.boundingRect(contour)
                    
                object_name: str = f"{color} object"
                new_object = VisionObject(object_name, image_height, image_width, x, y, w, h, radius, hsv_image, mask)
                new_object.set_metadata("radius", radius)
                new_object.set_metadata("shape", shape)
                new_object.set_metadata("color", color)
                new_object.set_metadata("center", center)
                new_object.set_metadata("contour", contour)
                
                objects.append(new_object)
                
        # visualized_objects_img = visualize_contours(hsv_image, objects)
        # cv2.imshow('Region', cv2.flip(visualized_objects_img, 0))        
        # cv2.waitKey(1)
        
        return objects        

    def process_frame(self, image: cv2.typing.MatLike) -> List[VisionObject]:
        return self.extract_objects(image)
    
    def get_all_potential_labels(self) -> List[str]: 
        # return the keys from COLOR_RANGES with _object appended as potential labels
        all_colors = list(COLOR_RANGES.keys())
        return [f"{color} object" for color in all_colors]
        
        