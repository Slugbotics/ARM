import cv2

class VisionObject():
    frame_height: int = 0
    frame_width: int = 0
    
    label : str = "unknown"
    
    top_left_x : int = 0
    top_left_y : int = 0
    
    width : int = 0
    height : int = 0
    
    source_frame_rgb: cv2.typing.MatLike = None
    
    mask: cv2.typing.MatLike = None
    
    def __init__(self, label : str, frame_height: int, frame_width: int, top_left_x : int, top_left_y :int, width: int, height: int, radius: float, source_frame_rgb: cv2.typing.MatLike = None, mask: cv2.typing.MatLike = None) -> None:
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.label = label
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.width = width
        self.height = height
        self.radius = radius
        
        self.source_frame_rgb = source_frame_rgb
        self.metadata = {}
        self.mask = mask        
        
    def get_center_x(self):
        return self.top_left_x + self.width // 2    
    
    def get_center_y(self):
        return self.top_left_y + self.height // 2
        
    def get_metadata(self, key: str):
        """ Retrieves metadata by key."""
        if key not in self.metadata:
            return None
        return self.metadata[key]
    
    def set_metadata(self, key: str, value) -> None:
        """ Sets metadata by key."""
        self.metadata[key] = value
        
    def get_all_key_value_pairs(self): 
        """ Retrieves all key-value pairs as a dictionary. 
        
        :return: Dictionary of all key-value pairs. 
        """ 
        return self.metadata
