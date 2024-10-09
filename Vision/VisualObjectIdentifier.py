import cv2
from typing import List

from Vision.VisionObject import VisionObject

#cv2.typing.MatLike, List[VisionObject]
# processes a frame and returns a list of Visually identified objects
class VisualObjectIdentifier:
    def process_frame(self, frame: cv2.typing.MatLike) -> List[VisionObject]: ...