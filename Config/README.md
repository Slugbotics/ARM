# Config

The `Config` folder contains all configuration-related files and modules for the UCSC Slugbotics robotic arm project. Its purpose is to centralize and manage the various settings, parameters, and runtime options that control how the robotic arm system operates.

## Purpose

- **Centralized Configuration:**  
  All settings that affect the behavior of the arm, such as which hardware interface to use, which modules to enable, and runtime options, are managed here.
- **Easy Customization:**  
  By editing configuration files or using the provided configuration classes, users can easily switch between simulation and physical hardware, enable or disable features, and adjust system parameters without changing the main codebase.
- **Runtime Management:**  
  The configuration system also helps manage which modules are loaded and how they interact at runtime.

## Contents

- **ArmConfig.py**  
  Handles loading, saving, and parsing of configuration settings.  
  - Loads default settings and merges them with user-provided settings from `config.json`.
  - Provides command-line argument parsing to override config values at startup.
  - Ensures new configuration options are automatically added to the config file if missing.

- **ArmRuntime.py**  
  Manages the initialization and connection of all major modules (HAL, controllers, vision, server, app, etc.) based on the configuration.  
  - Applies the loaded configuration to set up the system.
  - Handles the startup and shutdown of modules.
  - Provides a summary of the current runtime configuration.

## How to Use

1. **Edit `config.json`:**  
   Most configuration options are stored in `config.json`. You can edit this file directly to change settings such as which HAL to use, whether to enable the server, or which language model file to load.

2. **Use Command-Line Arguments:**  
   You can override certain settings at startup using command-line arguments. For example:
   ```
   python main.py --simulator
   python main.py --disable_server
   python main.py --twitch_chat mychannel
   ```

3. **Add New Configuration Options:**  
   To add a new setting, update the `CONFIG_DEFAULT_DICT` in `ArmConfig.py`. The system will automatically add it to `config.json` if it is missing.

4. **Runtime Management:**  
   The `ArmRuntime` class is responsible for applying the configuration and initializing all modules. You usually do not need to modify this unless you are adding new modules or changing how the system is initialized.

## Typical Workflow

- On first run, the system will create a `config.json` file with default values if it does not exist.
- You can edit `config.json` or use command-line arguments to change settings.
- When the program starts, it loads the configuration and initializes all modules accordingly.

## Example Configuration Options

- `use_simulator_hal`: Use the CoppeliaSim simulator as the hardware interface.
- `use_physical_hal`: Use the physical robotic arm hardware.
- `use_server`: Enable or disable the HTTP server for remote control.
- `use_tts`: Enable text-to-speech output.
- `use_language_model`: Enable the language model for natural language commands.
- `twitch_channel_name`: Set the Twitch channel for chat integration.

---

For more details, see the docstrings and comments in `ArmConfig.py` and `ArmRuntime.py`.
