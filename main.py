# This is the main file for the ArmTeam project. It initializes and runs the arm control system.
# It sets up the arm hardware interface, the controler, the server, and the app. It also handles command line arguments and configuration settings.

import subprocess
import sys

from Config.ArmRuntime import ArmRuntime
from Config.ArmConfig import ArmConfig

if __name__ == "__main__":
    # ----------------- SETUP -----------------
    print("Arm startup")
    
    keep_running = True
    
    armConfig = ArmConfig() # class that will load the config file and parse the args
    armRuntime = ArmRuntime() # class that will hold all the modules and handle the commands

    config = armConfig.load_config('config.json') # load the config file
    armConfig.parse_args(config) # parse the command line args and update the config file if needed
    armRuntime.apply_config(config) # apply the config to the armRuntime class
    
    print(armRuntime.modules_to_string()) # print loaded modules to the console

    # Start arm, could mean connecting to the simulator or the real arm
    armRuntime.selected_HAL.start_arm()    

    print("Controler Startup")
    # Start the Controler
    if armRuntime.selected_controller is not None:
        armRuntime.selected_controller.start()
    
    armRuntime.start(config) # start the rest of the modules

    # start listening to speech
    if armRuntime.selected_stt is not None and not config["stt_push_to_talk"]:
        armRuntime.selected_stt.activate()
    
    if armRuntime.selected_tts is not None:
        armRuntime.selected_tts.say("Arm startup.")   
        
    # ----------------- END SETUP -----------------
    
    # ----------------- MAIN PROGRAM LOOP -----------------
    # will capture main thread and run the input loop in a separate thread
    if config["use_server"]:
        print("Server Startup")
        armRuntime.selected_server.start_server()

    # will capture main thread and run the input loop in a separate thread
    if config["use_app"]:
        try:
            armRuntime.console_input.run_input_looping_async()
            armRuntime.selected_app.start_app()
        except KeyboardInterrupt:
                keep_running = False
        
    # if we are not using the server or the app, we will run the input loop in the main thread
    if not config["use_app"]:
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
    
    # stop listening to speech
    if armRuntime.selected_stt is not None:
        armRuntime.selected_stt.stop()
        
    # stop the server
    if armRuntime.selected_server is not None:
        armRuntime.selected_server.stop_server()
        
    # stop the controller
    if armRuntime.selected_controller is not None:
        armRuntime.selected_controller.stop()
        
    # stop the HAL interface, could mean disconnecting from the simulator or the real arm
    armRuntime.selected_HAL.stop_arm()
    
    armRuntime.stop(config) # stop the rest of the modules      
    
    # speak a shutdown message
    if armRuntime.selected_tts is not None:
        armRuntime.selected_tts.say("Arm shutdown.")
        
    print("Arm shutdown complete")
    
    # Reopen Startup page
    if config["open_startup_page"]:
        subprocess.Popen(['python', 'ArmTeam/startup.py'])

    # ----------------- END CLEAUP / SHUTDOWN -----------------
