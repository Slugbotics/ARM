import cv2

class VisionObject():
    frame_height: int = 0
    frame_width: int = 0
    
    name : str = ""
    
    x : int = 0
    y : int = 0
    radius : int = 0
    
    source_frame_hsv: cv2.typing.MatLike = None
    mask: cv2.typing.MatLike = None
    
    def __init__(self, frame_height: int, frame_width: int, name : str,  x : int, y : int, radius : int, source_frame_hsv: cv2.typing.MatLike = None, mask: cv2.typing.MatLike = None) -> None:
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        
        self.source_frame_hsv = source_frame_hsv
        self.mask = mask