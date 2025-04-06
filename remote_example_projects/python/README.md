# 🦾 Robotic Arm Desktop Controller

A Python PyQt6 desktop application to control a robotic arm remotely using an HTTP API.

---

## 📦 Requirements

- Python 3.10+
- `PyQt6`
- `opencv-python`
- `requests`
- A running Robotic Arm HTTP API server (see example FastAPI interface)

---

## 📥 Installation

```bash
# Clone this repo
git clone https://github.com/yourname/robotic-arm-controller.git
cd robotic-arm-controller

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

Ensure the robotic arm HTTP server is running and accessible (default: http://127.0.0.1:8000)

then run the project with:
```bash
python main.py
```