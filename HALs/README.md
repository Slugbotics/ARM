# Hardware Abstraction Layers (HALs)

The `HALs` folder contains all Hardware Abstraction Layer (HAL) implementations for the UCSC Slugbotics robotic arm project. A HAL provides a unified interface for controlling different types of robotic arm hardware (real or simulated), abstracting away the hardware-specific details and exposing a consistent API to the rest of the software stack.

## What is a HAL?

A Hardware Abstraction Layer (HAL) is a software component that allows the main control code to interact with different hardware platforms (e.g., physical arms, simulators, remote arms) using the same set of methods. This enables rapid switching between hardware backends for development, testing, and deployment.

All HALs inherit from `HAL_base`, which defines the required interface for arm control, camera access, and gripper manipulation.

## Existing HALs

- **HAL_base.py**  
  The abstract base class for all HALs. Defines the required interface for joint control, camera access, gripper operations, and joint limits.

- **sim_HAL.py**  
  HAL for the CoppeliaSim robotic arm simulator, using the ZeroMQ Remote API. Allows simulation-based development and testing.

- **physical_HAL.py**  
  HAL for the physical robotic arm hardware, using the Adafruit ServoKit, stepper drivers, and PiCamera2 for camera input.

- **laptop_test_HAL.py**  
  HAL for development and testing on a laptop using a standard webcam. No joint control; only provides camera frames.

- **remote_HAL.py**  
  HAL for controlling a remote robotic arm via HTTP API (using FastAPI). Bridges to a remote server running the arm.

- **logan_hal/**  
  Contains hardware-specific drivers and helpers for the Logan arm design, such as stepper and gripper drivers.

## How to Use a HAL

1. **Select the HAL**  
   In your main application or controller, instantiate the desired HAL class. For example:
   ```python
   from HALs.sim_HAL import sim_HAL
   hal = sim_HAL(host="127.0.0.1")
   hal.start_arm()
   ```

2. **Use the Unified API**  
   All HALs provide the same methods for joint control, camera access, and gripper operation:
   - `set_joint(joint_index, joint_angle)`
   - `get_joint(joint_index)`
   - `joint_count()`
   - `get_arm_cam_img_rgb()`
   - `get_camera_focal_length()`
   - `gripper_open()`
   - `gripper_close()`
   - `start_arm()`
   - `stop_arm()`

3. **Switching HALs**  
   To switch hardware backends, simply change which HAL class you instantiate. The rest of your code should not need to change.

## How to Write a New HAL

1. **Inherit from HAL_base**  
   Create a new Python file in the `HALs` directory (or a subdirectory) and define a class that inherits from `HAL_base`.

2. **Implement Required Methods**  
   Implement all abstract methods from `HAL_base`, including:
   - `start_arm`, `stop_arm`
   - `set_joint`, `get_joint`, `joint_count`
   - `get_arm_cam_img_rgb`, `get_camera_focal_length`
   - `gripper_open`, `gripper_close`

3. **Handle Joint Limits**  
   Use the joint limit methods (`set_joint_min`, `set_joint_max`, etc.) to enforce hardware safety.

4. **Thread Safety**  
   If your HAL interacts with hardware or external APIs, use locks to ensure thread safety.

5. **Test Your HAL**  
   Test your HAL implementation with the main application and controllers to ensure compatibility.

## Example: Minimal HAL Skeleton

```python
from HALs.HAL_base import HAL_base

class MyCustomHAL(HAL_base):
    def __init__(self):
        super().__init__()
        # Initialize hardware here

    def start_arm(self) -> bool:
        # Initialize hardware
        return True

    def stop_arm(self) -> bool:
        # Cleanup hardware
        return True

    def set_joint(self, joint_index, joint_angle) -> bool:
        # Set joint position
        return True

    def get_joint(self, joint_index) -> float:
        # Get joint position
        return 0.0

    def joint_count(self) -> int:
        return 3

    def get_arm_cam_img_rgb(self):
        # Return camera frame as RGB numpy array
        pass

    def get_camera_focal_length(self) -> float:
        # Return camera focal length in pixels
        return 800.0

    def gripper_open(self) -> bool:
        # Open gripper
        return True

    def gripper_close(self) -> bool:
        # Close gripper
        return True
```

---

For more details, see the docstrings in `HAL_base.py` and the example implementations in this folder.
