from typing import List
import threading
from threading import Lock

from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier

class VisionBaseController():

    def __init__(self, vision: VisualObjectIdentifier, target_label: str = None):
        self.vision: VisualObjectIdentifier = vision

        self.target_label = target_label
        if self.target_label is not None:
            self.target_label = self.target_label.lower()

        self.last_frame_objects: List[VisionObject] = []
        self.last_frame_objects_lock: Lock = threading.Lock()

    def set_last_frame_objects(self, objects: List[VisionObject]) -> None:
        """Sets the last frame objects to the given list of objects."""
        with self.last_frame_objects_lock:
            self.last_frame_objects = objects

    def set_target_label(self, label: str) -> bool:
        """This controller will only target objects with the specified label."""
        if self.is_label_in_universe(label):
            self.target_label = label.lower()
            return True
        else:
            print(f"Label \"{label}\" is not in the universe of {type(self).__name__}.")
            print(f"Please select a lable that is in universe: {self.vision.get_all_potential_labels()}")
            return False   
        
    def get_target_label(self) -> str:
        """Returns the label of the object that the controller is currently targeting."""
        return self.target_label
        
    def is_label_in_universe(self, label: str) -> bool:
        """Returns True if the label is something this controler can see, else false."""
        all_labels = self.vision.get_all_potential_labels()
        return label.lower() in (l.lower() for l in all_labels)

    
    def get_visible_object_labels(self) -> list[str]:
        """Returns a list of identifiers of objects that are visible to the arm"""
        with self.last_frame_objects_lock:
            if self.last_frame_objects is None:
                return []
            return [obj.label for obj in self.last_frame_objects]
        
    def get_visible_object_labels_detailed(self) -> list[str]:
        """Returns a list of objects that are visible to the arm, including metadata"""
        with self.last_frame_objects_lock:
            if self.last_frame_objects is None:
                return []
            # return a series of string that represent the object, starting withe object's label, then radius, then metadata
            return [f"{obj.label} radius: {obj.radius} {obj.metadata}" for obj in self.last_frame_objects]
            #return [f"{obj.label}_object" for obj in self.last_frame_objects]
    
    def get_all_posible_labels(self) -> list[str]:
        """Returns a list of all possible labels that this controller can see, even if they are not currently visible."""
        return self.vision.get_all_potential_labels()

    def select_largest_target_object(self, detected_objects: List[VisionObject]) -> VisionObject:
        # print("found: " + str(len(detected_objects)) + " objects")
        
        # # print the labels of all visible objects on one line
        # for obj in detected_objects:
        #     print(obj.label, end=", ")
        # print()
        
        if detected_objects:
            found_target = None
            for obj in detected_objects:
                if obj.label.lower() == self.target_label:
                    if found_target is not None:
                        if obj.radius > found_target.radius:
                            found_target = obj
                    else:
                        found_target = obj
            
            # print("largest object: " + str(found_target.label))
            return found_target
        else:
            return None
    