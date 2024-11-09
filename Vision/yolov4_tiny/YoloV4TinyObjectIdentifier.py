from typing import List

import cv2

from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Vision.VisionObject import VisionObject

#cv2.typing.MatLike, List[VisionObject]
# processes a frame and returns a list of Visually identified objects
class YoloV4TinyObjectIdentifier(VisualObjectIdentifier):

    def __init__(self, weights_path: str = "Vision/yolov4_tiny/yolov4-tiny.weights", cfg_path: str = "Vision/yolov4_tiny/yolov4-tiny.cfg", classes_path: str = "Vision/yolov4_tiny/classes.txt") -> None:
        VisualObjectIdentifier.__init__(self) 
              
        self.weights_path = weights_path
        self.cfg_path = cfg_path
        self.classes_path = classes_path
        self.font = cv2.FONT_HERSHEY_TRIPLEX
        self.draw_image = True
        
        self.class_names = self.load_class_names(self.classes_path)
        self.yoloNet = cv2.dnn.readNet(self.weights_path, self.cfg_path)
        
        self.model = cv2.dnn_DetectionModel(self.yoloNet)
        self.model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)
        
    def load_class_names(self, classes_path: str):
        """ Loads class names from a file. """
        found_class_names = []
        with open(classes_path, "r") as objects_file:
            found_class_names = [e_g.strip() for e_g in objects_file.readlines()]
        return found_class_names

    def process_frame(self, hsv_image: cv2.typing.MatLike) -> List[VisionObject]: 
        """ Processes a frame and returns a list of visually identified objects in screen space. """
        
        flipped_source_frame_hsv = cv2.flip(hsv_image, 0)
        rgb_image = cv2.cvtColor(flipped_source_frame_hsv, cv2.COLOR_HSV2BGR)
        
        image_height: int = rgb_image.shape[0]
        image_width: int = rgb_image.shape[1]
        
        image_with_boxes = None
        if self.draw_image:
            image_with_boxes = rgb_image.copy()           
        
        
        classes, scores, boxes = self.model.detect(rgb_image,0.4,0.3)
        
        objects = []
        
        # print("Identified objects: " + str(len(classes)) + " " + str(len(scores)) + " " + str(len(boxes)) + "   <---------------------")
        
        for (classid, score, box) in zip(classes, scores, boxes):
            class_label = self.class_names[classid]
            top_left_x, top_left_y, obj_width, obj_height = box
            largest_size = max(obj_width, obj_height)
            
            if self.draw_image:
                cv2.rectangle(image_with_boxes, box,(0,0,255), 2)
                cv2.putText(image_with_boxes,"{}:{}".format(self.class_names[classid],format(score,'.2f')), (box[0], box[1]-14), self.font, 0.6, (0,255,0), 3)
                
            new_object = VisionObject(class_label, image_height, image_width, top_left_x, top_left_y, obj_width, obj_height, largest_size, hsv_image, image_with_boxes)
            new_object.set_metadata("score", score)
            new_object.set_metadata("classid", classid)
            new_object.set_metadata("box", box)      
            objects.append(new_object)        
            
        return objects 
    
    def get_all_potential_labels(self) -> List[str]: 
        """ Retrieves all potential labels that can be identified by this object identifier. """
        return self.class_names