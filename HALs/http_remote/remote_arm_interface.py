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
        self._streaming_thread = None
        self._streaming_event = threading.Event()

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
        """Get the current status string from the arm."""
        response = requests.get(f"{self.base_url}/status_string")
        return response.json().get("status_string", "Unknown")

    def stream_camera(self, on_frame_callback):
        """
        Start streaming MJPEG camera feed and call the given function on each frame.
        This runs in a background thread. Call stop_camera_stream() to stop it.
        """
        self._streaming_event.clear()

        def stream_thread():
            response = requests.get(f"{self.base_url}/get_arm_cam_stream", stream=True)
            bytes_data = b''
            for chunk in response.iter_content(chunk_size=1024):
                if self._streaming_event.is_set():
                    break  # Exit the loop when stop signal is set
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        on_frame_callback(img)

        self._streaming_thread = threading.Thread(target=stream_thread, daemon=True)
        self._streaming_thread.start()
        
    def stop_camera_stream(self):
        """
        Signal the camera stream thread to stop and wait for it to exit.
        """
        self._streaming_event.set()
        if self._streaming_thread and self._streaming_thread.is_alive():
            self._streaming_thread.join()
        self._streaming_thread = None