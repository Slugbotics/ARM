import cv2
import threading
import math
import numpy as np
import struct

from scripts.vision_tests.camera_ports_list import open_camera

from HALs.HAL_base import HAL_base

class laptop_HAL(HAL_base):

    default_camera_port = 0
        
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.motorCount = 0
        self.capture = open_camera(laptop_HAL.default_camera_port)

    def start_arm(self) -> bool:
        with self.lock:
            print("--------- Started LAPTOP_SIM ---------")
        return True
        

    def stop_arm(self) -> bool:
        with self.lock:
            print("--------- Ended LAPTOP_SIM ---------")
        return True

    def joint_count(self) -> int:
        return self.motorCount

    def set_joint(self, joint_index, joint_angle) -> bool:
        return False        

    def get_joint(self, joint_index) -> float:
        return 0

    def get_arm_cam_img_hsv(self) -> cv2.typing.MatLike:

        frame = None
        with self.lock:
            _,frame = self.capture.read()

        # Convert the image from RGB to HSV color space
        flipped_image = cv2.flip(frame, 0)
        hsv_image = cv2.cvtColor(flipped_image, cv2.COLOR_BGR2HSV)

        return hsv_image
    
    def gripper_open(self) -> bool:
        return False
    
    def gripper_close(self) -> bool:
        return False
