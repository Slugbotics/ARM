import time 
import RPi.GPIO as GPIO
import pickle

from RpiMotorLib import RpiMotorLib

# EEPROM simulation using a file
motor_move_file_name = 'last_motor_position.temp'

MOTOR_OPEN_VALUE = 0
MOTOR_CLOSE_VALUE = 1

class gripper_stepper_28BYJ:
    def __init__(self, motor_pins = None):
        
        # Declare an named instance of class pass your custom name and type of motor
        self.gripper_motor = RpiMotorLib.BYJMotor("GripperMotorOne", "28BYJ")        
        
        if(motor_pins is not None):
            self.GpioPins = motor_pins
        else:
            # Connect GPIO to [IN1 , IN2 , IN3 ,IN4] on Motor PCB
            self.GpioPins = [18, 23, 24, 25]
        
    def open(self):
        # Rotate Stepper 90 degrees
        self.gripper_motor.motor_run(self.GpioPins, .001, 90, False, False, "half", .05)
        
    def close(self):
        # Rotate Stepper 90 degrees
        self.gripper_motor.motor_run(self.GpioPins, .001, 90, True, False, "half", .05)
        
    def cleanup(self):
        GPIO.cleanup()
        
    # Writes to a temp file for persistent memory
    def read_eeprom(self):
        try:
            with open(motor_move_file_name, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return 0  # Default value if EEPROM is empty

    # read from a temp file for persistent memory
    def write_eeprom(self, value):
        with open(motor_move_file_name, 'wb') as f:
            pickle.dump(value, f)