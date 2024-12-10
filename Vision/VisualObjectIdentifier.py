import cv2
from typing import List

from Vision.VisionObject import VisionObject

#cv2.typing.MatLike, List[VisionObject]
# processes a frame and returns a list of Visually identified objects
class VisualObjectIdentifier:
    def process_frame(self, frame: cv2.typing.MatLike) -> List[VisionObject]: ...
    """ Processes a frame and returns a list of visually identified objects in screen space. """
    
    def get_all_potential_labels(self) -> List[str]: ...
    """ Retrieves all potential labels that can be identified by this object identifier. """