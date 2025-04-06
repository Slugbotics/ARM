
# 🤖 Robotic Arm Client Examples

Welcome to the **Robotic Arm Client Examples** directory! This folder contains beginner-friendly example projects in various programming languages to help you interact with and control the robotic arm over its HTTP API.

Whether you're using **Python**, **TypeScript**, **C++**, or another supported language, each subfolder here shows how to:

- Connect to the robotic arm over the network
- Send joint control commands
- Read joint states and arm status
- Stream the camera feed (where supported)
- Control the gripper

---

## 🧠 Prerequisites

Before using any of these example projects, you must **start the main robotic arm backend project** with a configuration that enables only the simulator or physical interface and the HTTP server.

This ensures a clean environment where the API is accessible without interference from other modules like speech recognition, Twitch chat, or the desktop app.

---

## ✅ Required Main Project Configuration

Here's the **minimum configuration** you should use when running the main robotic arm project:

```json
{
    "use_simulator": true,
    "use_physical": false,
    "use_app": false,
    "use_server": true,
    "use_twitch": false,
    "use_stt": false,
    "stt_model_large": false,
    "open_startup_page": false,
    "write_logs": true,
    "use_tts": false,
    "use_language_model": false,
    "stt_push_to_talk": false,
    "server_host_port": "8000"
}
```

> ✅ **Note**: If you're testing with a real robotic arm, set `"use_simulator": false` and `"use_physical": true`.


---

## 📁 Folder Structure

Each language has its own subfolder:

```
examples/
├── python/       # Python example project
├── typescript/   # TypeScript example project
├── cpp/          # C++ example project
...
```

Each subfolder includes:

- 📄 `README.md` – Instructions for that language
- 🧪 Code examples – Demonstrating how to interact with the API
- 🔧 Setup scripts – If required for dependencies

---

## 🧭 Getting Started

1. Clone the main robotic arm repository:

   ```bash
   git clone https://github.com/slugbotics/arm.git
   cd arm
   ```

2. Edit your configuration file (usually `config.json`) to match the **minimal setup** shown above.

3. Start the main application with the updated configuration:

   ```bash
   python main.py
   ```

4. Go into the language folder of your choice under `examples/`, and follow the README there to run the demo project.

---

## 📡 API Information

All examples use the RESTful HTTP API hosted by the main project. The default address is:

```
http://127.0.0.1:8000
```

Each example shows how to:

- GET joint data
- POST joint control commands
- Stream camera data (where supported)
- Open or close the gripper
- Retrieve arm status

---

## 💬 Contributing

Want to contribute an example in another language? Add a new folder and submit a pull request! We'd love to see your work.

---

## 🙋 Need Help?

If you get stuck, feel free to open an issue or reach out on our discord channel. We're here to help!
