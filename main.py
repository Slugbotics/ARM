# This is the main file for the ArmTeam project. It initializes and runs the arm control system.
# It sets up the arm hardware interface, the controler, the server, and the app. It also handles command line arguments and configuration settings.

import subprocess
import sys

from Config.ArmRuntime import ArmRuntime
from Config.ArmConfig import ArmConfig

from Modules.Commands.Commands import Commands

if __name__ == "__main__":
    # ----------------- SETUP -----------------
    print("Arm startup")
    
    keep_running = True
    
    armConfig = ArmConfig()
    armRuntime = ArmRuntime()

    config = armConfig.load_config('config.json')
    armConfig.parse_args(config)
    armRuntime.apply_config(config)
    
    print(armRuntime.to_string())

    # Remote API init
    armRuntime.selected_HAL.start_arm()    

    print("Controler Startup")
    # Start the Controler
    if armRuntime.selected_controller is not None:
        armRuntime.selected_controller.start()
    
    # Connect to twitch
    if config["use_twitch"]:
        def twitch_input_handeler(input_str: str) -> None:
            armRuntime.commands.user_input(input_str, Commands.Trust.SUS, armRuntime.selected_twitch)
        
        armRuntime.selected_twitch.connect_to_twitch(config["twitch_channel_name"], twitch_input_handeler)

    # start listening to speech
    if armRuntime.selected_stt is not None and not config["stt_push_to_talk"]:
        armRuntime.selected_stt.activate()
    
    if armRuntime.selected_tts is not None:
        armRuntime.selected_tts.say("Arm startup.")
        
    armRuntime.hotkey_manager.start()
        
    # ----------------- END SETUP -----------------
    
    # ----------------- MAIN PROGRAM LOOP -----------------
    if config["use_server"]:
        armRuntime.console_input.run_input_looping_async()
        print("Server Startup")
        armRuntime.selected_server.start_server()

    if config["use_app"]:
        try:
            armRuntime.console_input.run_input_looping_async()
            armRuntime.selected_app.start_app()
        except KeyboardInterrupt:
                keep_running = False
        
    if not config["use_server"] and not config["use_app"]:
        while keep_running:
            print("Arm is running, press 'q' or ctrl-c to quit")
            try:
                armRuntime.console_input.run_input_looping()
            except KeyboardInterrupt:
                keep_running = False
            
        
    # ----------------- END MAIN PROGRAM LOOP -----------------

    # ----------------- CLEAUP / SHUTDOWN -----------------

    print("Arm shutdown")
    keep_running = False
    armRuntime.hotkey_manager.stop()
    if config["use_twitch"]:
        armRuntime.selected_twitch.stop_twitch_chat()
    # stop listening to speech
    if armRuntime.selected_stt is not None:
        armRuntime.selected_stt.stop()
    if armRuntime.selected_server is not None:
        armRuntime.selected_server.stop_server()
    if armRuntime.selected_controller is not None:
        armRuntime.selected_controller.stop()
    armRuntime.selected_HAL.stop_arm()
    
    armRuntime.console_input.cleanup()
    
    if armRuntime.selected_logger is not None:
        armRuntime.selected_logger.stop()
    
    print("Arm shutdown complete")
    
    if armRuntime.selected_tts is not None:
        armRuntime.selected_tts.say("Arm shutdown.")
    
    # Reopen Startup page
    if config["open_startup_page"]:
        subprocess.Popen(['python', 'ArmTeam/startup.py'])

    # ----------------- END CLEAUP / SHUTDOWN -----------------
