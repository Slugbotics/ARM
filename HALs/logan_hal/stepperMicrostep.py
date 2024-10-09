from gpiozero import OutputDevice
from time import sleep
import threading
import numpy as np

# Constants
STEPPER_CW = 1
STEPPER_CCW = 0
# STEPPER_steps2deg = 400/90 #320/90
STEPPER_steps2deg = 6400/360


class Stepper:    
    def __init__(self, dir_pin, step_pin):
        # Initialize pins using gpiozero
        self.dir_pin = OutputDevice(dir_pin)
        self.step_pin = OutputDevice(step_pin)
        self.current_rot = 0
        self.thread = None
        self.running = False
        self.current_target_degrees = 0

    def setPosition(self, deg):
        ''' Updates the rotation of the stepper with degrees being the new rotation '''
        # Check if a thread is already running
        if self.thread is not None and self.thread.is_alive():
            # Wait for the current thread to finish (blocks execution)
            self.running = False
            self.thread.join()
            self.step_pin.off()
            
        self.current_target_degrees = deg

        delta = deg - self.current_rot
        # Create a new thread for the update function
        self.thread = threading.Thread(target=self.updateStepper, args=(delta,))
        # Start the thread
        self.thread.start()

    def updateStepper(self, deg):
        '''INTERNAL rotates the stepper by deg, don't use as it doesn't follow the rotation. '''
        dir = STEPPER_CW if deg >= 0 else STEPPER_CCW
        self.dir_pin.value = dir
        self.running = True
        # Run for a number of steps based on the degree change
        steps = abs(int(deg * STEPPER_steps2deg))
        for _ in range(steps):
            if not self.running:
                break
            # Set one coil winding to high
            self.step_pin.on()
            # Allow it to get there
            sleep(0.001)  # Dictates how fast the stepper motor will run
            # Set coil winding to low
            self.step_pin.off()
            sleep(0.001)  # Dictates how fast the stepper motor will run
            self.current_rot += (np.sign(deg)) / STEPPER_steps2deg
        self.running = False
        print("thread complete: " + str(self.current_rot))

    def cleanup(self):
        self.updateStepper(0 - self.current_rot)
        self.dir_pin.close()
        self.step_pin.close()
        
    def get_current_rotation(self):
        return self.current_rot
        
    def get_target_degrees(self):
        return self.current_target_degrees

# Example usage:
# stepper = Stepper(dir_pin=15, step_pin=14)
# stepper.setPosition(90)
# sleep(2)
# stepper.cleanup()


# import RPi.GPIO as GPIO
# from time import sleep
# import threading
# import numpy as np

# # Direction pin from controller
# # DIR = 10
# # STEPPER_DIR = 15
# # Step pin from controller
# # STEP = 8
# # STEPPER_STEP=14
# # 0/1 used to signify clockwise or counterclockwise.
# STEPPER_CW = 1
# STEPPER_CCW = 0
# STEPPER_steps2deg = 320/90

# class Stepper:
#     def __init__(self, dir_pin, step_pin):
#         # Setup pin layout on PI
#         # GPIO.setmode(GPIO.BOARD)
#         GPIO.setmode(GPIO.BCM)

#         # Establish Pins in software
#         GPIO.setup(dir_pin, GPIO.OUT)
#         GPIO.setup(step_pin, GPIO.OUT)  
#         self.current_rot = 0
#         self.dir_pin = dir_pin
#         self.step_pin = step_pin
#         self.thread = None
#         self.running = False

#     def setPosition(self, deg):
#         ''' Updates the rotation of the stepper with degrees being the new rotation '''
#         # Check if a thread is already running
#         if self.thread is not None and self.thread.is_alive():
#             # Wait for the current thread to finish (blocks execution)
#             self.running = False
#             self.thread.join()
#             GPIO.output(self.step_pin, GPIO.LOW)

#         delta = deg - self.current_rot
#         # Create a new thread for the update function
#         self.thread = threading.Thread(target=self.updateStepper, args=(delta,))
#         # Start the thread
#         self.thread.start()

#     def updateStepper(self, deg):
#         '''INTERNAL rotates the stepper by deg, dont use as it doesnt follow the rotation. '''
#         dir = 1
#         if deg < 0: 
#             dir = 0
#         GPIO.output(self.dir_pin,dir)
#         self.running = True
#         # Run for 200 steps. This will change based on how you set you controller
#         for x in range(abs(int(deg*STEPPER_steps2deg))):
#             if not self.running:
#                 break
#             # Set one coil winding to high
#             GPIO.output(self.step_pin,GPIO.HIGH)
#             # Allow it to get there.
#             sleep(.005) # Dictates how fast stepper motor will run
#             # Set coil winding to low
#             GPIO.output(self.step_pin,GPIO.LOW)
#             sleep(.005) # Dictates how fast stepper motor will run
#             self.current_rot += (np.sign(deg))/STEPPER_steps2deg
#         self.running = False
#         print("thread complete: " + str(self.current_rot))

#     def cleanup(self):
#         self.updateStepper(0 - self.current_rot)
#         GPIO.cleanup()