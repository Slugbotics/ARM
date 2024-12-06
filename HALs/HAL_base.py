import cv2
import numpy as np
from Modules.Base.ImageProducer import ImageProducer

DEFAULT_MIN_JOINT_ANGLE = 0
DEFAULT_MAX_JOINT_ANGLE = 360

# All joint angles are in degrees
class HAL_base(ImageProducer):  
    
    joint_limits: list[(int, int)] = []

    def start_arm(self) -> bool: ...
        #return False
    
    def stop_arm(self) -> bool: ...
        #return False

    # Degrees in Degrees
    def set_joint(self, joint_index: int, joint_angle: float) -> bool: ...
        #return False
    
    # Degrees in Degrees
    def get_joint(self, joint_index: int) -> float: ...
        #return 0

    def joint_count(self) -> int: ...
        #return 0
    
    def get_arm_cam_img_hsv(self) -> cv2.typing.MatLike: ...
        #return None   
    
    def capture_image(self) -> cv2.typing.MatLike:
        return self.get_arm_cam_img_hsv()
    
    """This function will give the focal length of the camera in pixels, this is required for distance calculation"""
    def get_camera_focal_length(self) -> float: ...        
    
    def gripper_open(self) -> bool: ...
        #return False
        
    def gripper_close(self) -> bool: ...
        #return False
    
    # angle limit things - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def get_joint_min(self, joint_index: int) -> float:
        if 0 <= joint_index < len(self.joint_limits):
            return self.joint_limits[joint_index][0]
        else:
            return DEFAULT_MIN_JOINT_ANGLE
        
    def get_joint_max(self, joint_index: int) -> float:
        if 0 <= joint_index < len(self.joint_limits):
            return self.joint_limits[joint_index][1]
        else:
            return DEFAULT_MAX_JOINT_ANGLE
    
    def set_joint_limits(self, joint_index: int, min_angle: float, max_angle: float) -> None:
        if 0 <= joint_index < len(self.joint_limits):
            self.joint_limits[joint_index] = (min_angle, max_angle)
        else:
            while len(self.joint_limits) <= joint_index:
                self.joint_limits.append((DEFAULT_MIN_JOINT_ANGLE, DEFAULT_MAX_JOINT_ANGLE))
            self.joint_limits[joint_index] = (min_angle, max_angle)
    
    def set_joint_min(self, joint_index: int, min_angle: float) -> None:
        if 0 <= joint_index < len(self.joint_limits):
            _, max_angle = self.joint_limits[joint_index]
            self.joint_limits[joint_index] = (min_angle, max_angle)
        else:
            self.set_joint_limits(joint_index, min_angle, DEFAULT_MAX_JOINT_ANGLE)

    def set_joint_max(self, joint_index: int, max_angle: float) -> None:
        if 0 <= joint_index < len(self.joint_limits):
            min_angle, _ = self.joint_limits[joint_index]
            self.joint_limits[joint_index] = (min_angle, max_angle)
        else:
            self.set_joint_limits(joint_index, DEFAULT_MIN_JOINT_ANGLE, max_angle)
