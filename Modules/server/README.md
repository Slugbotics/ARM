# Robotic Arm HTTP API

A FastAPI-powered HTTP server that exposes control and monitoring endpoints for a robotic arm, including joint control, gripper manipulation, camera image retrieval, and video streaming.

---

## 🚀 Getting Started

### Requirements
- Python 3.9+
- FastAPI
- Uvicorn

### Run the Server
run the main program with the server config option enabled
```bash
python main.py
```

---

## 📚 API Endpoints

### `GET /`
Returns the home page (index.html).

---

### `POST /set_joint`
Set a joint's angle.
```json
{
  "joint_index": 0,
  "joint_angle": 45.0
}
```
**Response:**
```json
{ "success": true }
```

---

### `GET /get_joint?joint_index=0`
Retrieve a joint's current angle.
**Response:**
```json
{ "joint_angle": 45.0 }
```

---

### `GET /joint_count`
Returns the total number of joints.
```json
{ "joint_count": 6 }
```

---

### `GET /get_arm_cam_img_rgb`
Get a single RGB frame from the camera.
```json
{ "image": "<base64-jpeg>" }
```

---

### `GET /get_arm_cam_stream`
Get a live MJPEG stream from the camera.
**Content-Type:** `multipart/x-mixed-replace; boundary=frame`

---

### `GET /get_camera_focal_length`
Returns the detected focal length of the camera.
```json
{ "focal_length": 850.0 }
```

---

### `POST /gripper_open`
Opens the robotic gripper.
```json
{ "success": true }
```

---

### `POST /gripper_close`
Closes the robotic gripper.
```json
{ "success": true }
```

---

### `GET /status_string`
Returns a human-readable status summary.
```json
{
  "status_string": "Controller: JointPIDController can see: ['box', 'screw']\nObject Identifier: YOLOv8Identifier"
}
```

---

## 🧪 Development Notes
- Written in Python using FastAPI.
- MJPEG stream useful for frontend integration.
- Modular HAL allows dynamic hardware integration.
