# Modules

The `Modules` folder contains the various software modules that enable the robotic arm to function. According to the Arm Team codebase standards, each distinct module of software is placed in its own subfolder under the `Modules` directory. This modular structure promotes separation of concerns, maintainability, and ease of development.

## Structure and Purpose

- Each subfolder in `Modules` represents a self-contained component or service that provides a specific capability for the robotic arm system.
- Modules may include hardware abstraction, vision processing, application logic, language processing, server APIs, and more.

## Module Descriptions

- **App/**  
  Contains Kivy based UI for the arm.

- **Base/**  
  Provides base classes and interfaces shared by other modules, supporting code reuse and consistency.

- **Language/**  
  Contains modules related to language processing or natural language interfaces for the robotic arm.

- **server/**  
  Implements the HTTP API and web server for the robotic arm, including endpoints for control, monitoring, and video streaming. Uses FastAPI for serving requests and providing a web interface.

- **HotkeyManager.py**  
  Provides a utility for managing keyboard hotkeys and callbacks, useful for manual control or debugging.

---

For details about each module, refer to the README or documentation within each subfolder, or review the code and docstrings in the respective files.
