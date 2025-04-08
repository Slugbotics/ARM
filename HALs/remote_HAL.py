import threading
import cv2
import numpy as np
from typing import Optional
import requests
from HALs.HAL_base import HAL_base
from HALs.http_remote.remote_arm_interface import RemoteArmInterface

# RemoteHAL inherits from HAL_base and bridges it with RemoteArmInterface
class RemoteHAL(HAL_base):
    """
    This class connects the robot control layer (HAL_base) with the remote robotic arm
    through the RemoteArmInterface. It handles joint control, gripper actions, and camera streaming.
    """

    def __init__(self, ip_address="127.0.0.1", port=8000):
        super().__init__()
        self.remote_address = "http://" + ip_address + ":" + str(port)
        self.remote = RemoteArmInterface(self.remote_address)
        self.latest_frame: Optional[cv2.typing.MatLike] = None
        

    def _start_camera_thread(self):
        """
        Starts the camera stream in a background thread and saves the latest frame.
        This ensures get_arm_cam_img_rgb always returns the most recent frame.
        """
        def on_new_frame(frame):
            # Save the latest frame in a thread-safe way
            self.latest_frame = frame

        self.remote.stream_camera(on_new_frame)

    def start_arm(self) -> bool:
        """
        This function can be expanded to handle any startup procedures for the arm.
        Currently just returns True to indicate success.
        """
        self._start_camera_thread()
        return True

    def stop_arm(self) -> bool:
        """
        This function can be expanded to handle any shutdown procedures for the arm.
        Currently just returns True to indicate success.
        """
        self.remote.st
        return True

    def set_joint(self, joint_index: int, joint_angle: float) -> bool:
        """
        Sends a command to set the angle of a specific joint on the robotic arm.
        """
        return self.remote.set_joint(joint_index, joint_angle)

    def get_joint(self, joint_index: int) -> float:
        """
        Returns the current angle of a specific joint from the robotic arm.
        """
        return self.remote.get_joint(joint_index)

    def joint_count(self) -> int:
        """
        Returns the number of joints in the robotic arm.
        """
        return self.remote.get_joint_count()

    def gripper_open(self) -> bool:
        """
        Sends a command to open the robotic gripper.
        """
        return self.remote.gripper_open()

    def gripper_close(self) -> bool:
        """
        Sends a command to close the robotic gripper.
        """
        return self.remote.gripper_close()

    def get_arm_cam_img_rgb(self) -> Optional[cv2.typing.MatLike]:
        """
        Returns the most recent RGB camera frame captured from the robot's camera.
        This frame is updated in the background thread.
        """
        return self.latest_frame

    def get_camera_focal_length(self) -> float:
        """
        Returns the camera focal length in pixels.
        You should calibrate your camera and return the actual focal length here.
        This is used in 3D reconstruction and distance estimation.
        """
        # Example placeholder value; replace with actual calibration data
        return 800.0
