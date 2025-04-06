# remote_arm_interface.py
import requests
import threading
import cv2
import numpy as np
from io import BytesIO

class RemoteArmInterface:
    """Handles all direct interaction with the robotic arm over HTTP."""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    def get_joint(self, joint_index: int) -> float:
        """Get the current angle of the specified joint."""
        response = requests.get(f"{self.base_url}/get_joint", params={"joint_index": joint_index})
        return response.json().get("joint_angle", 0.0)

    def set_joint(self, joint_index: int, joint_angle: float) -> bool:
        """Set the angle of the specified joint."""
        response = requests.post(f"{self.base_url}/set_joint", json={
            "joint_index": joint_index,
            "joint_angle": joint_angle
        })
        return response.ok and response.json().get("success", False)

    def get_joint_count(self) -> int:
        """Return how many joints the robot arm has."""
        response = requests.get(f"{self.base_url}/joint_count")
        return response.json().get("joint_count", 0)

    def gripper_open(self) -> bool:
        """Open the gripper."""
        response = requests.post(f"{self.base_url}/gripper_open")
        return response.ok and response.json().get("success", False)

    def gripper_close(self) -> bool:
        """Close the gripper."""
        response = requests.post(f"{self.base_url}/gripper_close")
        return response.ok and response.json().get("success", False)

    def get_status_string(self) -> str:
        """Get the current status string from the robot."""
        response = requests.get(f"{self.base_url}/status_string")
        return response.json().get("status_string", "Unknown")

    def stream_camera(self, on_frame_callback):
        """Start streaming MJPEG camera feed and call the given function on each frame."""

        def stream_thread():
            response = requests.get(f"{self.base_url}/get_arm_cam_stream", stream=True)
            bytes_data = b''
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    on_frame_callback(img)

        threading.Thread(target=stream_thread, daemon=True).start()
