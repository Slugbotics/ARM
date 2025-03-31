import cv2
import numpy as np
from typing import List

from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier

class ColorObjectIdentifier(VisualObjectIdentifier):
    def __init__(self, color_lower_bound: np.array, color_upper_bound: np.array):
        self.color_lower_bound = color_lower_bound
        self.color_upper_bound = color_upper_bound
        # lower_blue = np.array([100, 150, 50])
        # upper_blue = np.array([140, 255, 255])

    def update_range(self,lb,ub):
        self.color_lower_bound=lb
        self.color_upper_bound=ub

    def set_color_lower_bound(self, color_lower_bound: np.array):
        self.color_lower_bound = color_lower_bound

    def set_color_upper_bound(self, color_upper_bound: np.array):
        self.color_upper_bound = color_upper_bound

    def extract_objects(self, image_rgb: cv2.typing.MatLike) -> List[VisionObject]:
        
        image_hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        
        image_height: int = image_hsv.shape[0]
        image_width: int = image_hsv.shape[1]
        
        #simulation
        mask = cv2.inRange(image_hsv, self.color_lower_bound, self.color_upper_bound)

        # #morphological operations to remove noise and fill gaps
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        #find largest contour in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:            
            #find the largest contour and create its bounding box
            largest_contour = max(contours, key=cv2.contourArea)
            (center_x, center_y), radius = cv2.minEnclosingCircle(largest_contour)
            center = (int(center_x), int(center_y))
            radius = int(radius)
            # Calculate the bounding box for each object
            x, y, w, h = cv2.boundingRect(contour)
                
            new_object = VisionObject("blue_object", image_height, image_width, x, y, w, h, radius, image_rgb, mask)
            new_object.set_metadata("radius", radius)
            new_object.set_metadata("mask", mask)
            return [new_object]                
        else:
            return []
    
        # hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # mask = cv2.inRange(hsv, self.color_lower_bound, self.color_upper_bound)
        # contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # objects = []
        # for contour in contours:
        #     area = cv2.contourArea(contour)
        #     if area > 100:
        #         x, y, w, h = cv2.boundingRect(contour)
        #         objects.append(VisionObject.VisionObject(x, y, w, h, self.color_lower_bound))
        # return objects

    def process_frame(self, image_rgb: cv2.typing.MatLike) -> List[VisionObject]:
        return self.extract_objects(image_rgb)
    
    def get_all_potential_labels(self) -> List[str]: 
        return ["blue_object"]
        