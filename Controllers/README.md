# ARM Controllers

This directory contains controller modules for the UCSC Slugbotics robotic arm project. Each controller implements a specific control strategy or interface for the robotic arm, integrating with hardware abstraction layers (HAL), vision modules, and kinematics.

## File Overview

### Controllers

- **FollowObject3DControler.py**  
  Implements a controller for visually tracking and following a 3D object using computer vision. Integrates with the HAL, vision modules, and arm kinematics to compute and command joint movements based on the detected position of a target object in camera frames. Supports asynchronous operation and object selection by label.

- **FollowLargestObjectControler.py**  
  Implements a controller that detects, tracks, and follows the largest object in the camera's view using computer vision. Integrates with HAL, vision modules, and arm kinematics. Supports asynchronous operation and real-time visualization.

### Controllers/Base

- **Controller.py**  
  Defines the base interface for all controllers, specifying required methods for starting, stopping, and interacting with object labels.

- **MoveToPointInSpaceController.py**  
  Provides a controller for moving the robotic arm to a specified point in 3D space using inverse kinematics and arm parameters. Includes methods for stepping toward a target and testing workspace limits.

- **MoveToPointOnScreenController.py**  
  Provides a controller for moving the arm to a specific point on the camera screen, using screen-space coordinates and error-based servo adjustments.

- **VisionControllerBase.py**  
  Supplies a base class for vision-based controllers, handling label selection, object tracking, and thread-safe access to detected objects.

- **__init__.py**  
  Marks the `Controllers.Base` directory as a Python package.

### Controllers/legacy

- **FollowClaw_old.py**  
  Legacy controller for following an object with the arm's claw using computer vision and direct kinematics. Contains older kinematic and control logic.

- **FollowLargestObjectControler_old.py**  
  Legacy controller for following the largest detected object. Contains earlier implementations of object tracking and servo control.

---

## TODO

- [ ] Test and refine **MoveToPointInSpaceController** for accuracy and robustness.
- [ ] Test and refine **FollowObject3DControler** for reliable object tracking and following.
- [ ] Add more detailed usage examples for each controller.
- [ ] Improve documentation and code comments for clarity.
- [ ] Integrate error handling and logging improvements across all controllers.

---

For more information about each controller, refer to the docstrings and comments within each file.
