import time
import struct
import threading
from math import pi
# import Simulation.kinematicsPYV1 as kine
import numpy as np
import cv2
import pickle
from picamera2 import Picamera2

# import stepper and servo
from adafruit_servokit import ServoKit
import HALs.logan_hal.stepperMicrostep as stepperMicrostep
# import logan_hal.stepperl289n as stepperl289n
from HALs.logan_hal.gripper_stepper_28BYJ_48 import gripper_stepper_28BYJ

# import HALs.logan_hal.gripper_stepper_28BYJ_48 as gripper_stepper_28BYJ

from HALs.HAL_base import HAL_base

last_gripper_state_file_name = 'last_gripper_position.temp'

GRIPPER_OPEN_VALUE = 0
GRIPPER_CLOSE_VALUE = 1

goto_zero_on_close = False

class physical_HAL(HAL_base):

    kit = ServoKit(channels=16)

    pulse_min = 500
    pulse_max = 2500
    smooth_time = 3

    servos = [(4,0),(5,0)]
    baseStepper = None

    lock = threading.Lock()
    camera_lock = threading.Lock()

    # Initialize the camera
    picam2 = Picamera2()    

    is_started = False
    
    def __init__(self):
        super().__init__()
        self.gripper_control = gripper_stepper_28BYJ()
        self.gripper_state = self.read_gripper_state()

    def start_arm(self) -> bool:
        with self.lock:
            self.baseStepper = stepperMicrostep.Stepper(15,14)
            for servo in self.servos:
                self.kit.servo[servo[0]].set_pulse_width_range(self.pulse_min, self.pulse_max)
                self.kit.servo[servo[0]].actuation_range = 180
                self.kit.servo[servo[0]].angle = servo[1]
            
        with self.camera_lock:
            # Start the camera
            self.picam2.start()

        self.is_started = True
        
        # # Create a simple preview configuration
        # preview_config = picam2.create_preview_configuration(main={"size": (640, 480)})
        # # Configure the camera with the preview configuration
        # picam2.configure(preview_config)
        # # Start the camera
        # picam2.start()

    def stop_arm(self) -> bool:
        if goto_zero_on_close:
            # move the servos back to clean positions.
            self.set_joint(0,0)
            self.set_joint(1,0)
            self.set_joint(2,0)
            # should redundently do this in the other cleanups.
            time.sleep(2)
        
        with self.lock:
            self.baseStepper.cleanup()
            # if(show_video_window):
            #     cam.release() 
            #     cv2.destroyWindow("Vid") 
            self.gripper_control.cleanup()
        self.is_started = False
        #UNDO COMMENT # picam2.stop()

    def get_arm_cam_img_hsv(self) -> cv2.typing.MatLike:
        if not self.is_started:
            return None
        
        with self.camera_lock:
            frame = self.picam2.capture_array()
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # cv2.imshow("Camera", hsv)
        # cv2.waitKey(1)
        return hsv

    def set_joint(self, joint_index, joint_angle) -> bool:
        
        if not self.is_started:
            print("Unable to set joint " + joint_index + " because the arm is not started")
            return

        # Check if the joint angle is within the bounds
        if(joint_angle < self.get_joint_min(joint_index)):
            joint_angle = self.get_joint_min(joint_index)
        if(joint_angle > self.get_joint_max(joint_index)):
            joint_angle = self.get_joint_max(joint_index)
        
        # Move the joint
        try:
            with self.lock:
                if(joint_index == 0):
                    self.baseStepper.setPosition(joint_angle)
                elif(joint_index == 1):
                    self.kit.servo[self.servos[0][0]].angle = joint_angle
                elif(joint_index == 2):
                    self.kit.servo[self.servos[1][0]].angle = joint_angle
                elif(joint_index == 3):
                    raise Exception("gripper not implemeted")
                else:
                    raise Exception("joint index out of bounds")
                    
        except Exception as err:
            print(f"Exeption in moving the arm: {err=}, {type(err)=}")

    def get_joint(self, joint_index) -> float:
        if(joint_index == 0):
            return self.baseStepper.get_current_rotation()
        else:
            return self.kit.servo[self.servos[joint_index - 1][0]].angle
            
    def joint_count(self) -> int:
        return 4
    
    def gripper_open(self) -> bool:
        if self.gripper_state == GRIPPER_OPEN_VALUE:
            return False
        
        with self.lock:
            self.write_gripper_state(GRIPPER_OPEN_VALUE)
            self.gripper_control.open()
        return True
    
    def gripper_close(self) -> bool:
        if self.self.gripper_state == GRIPPER_CLOSE_VALUE:
            return False
        
        with self.lock:
            self.write_gripper_state(GRIPPER_CLOSE_VALUE)
            self.gripper_control.close()
        return True
    
    def read_gripper_state(self):
        try:
            with open(last_gripper_state_file_name, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return 0  # Default value if EEPROM is empty

    def write_gripper_state(self, value):
        with open(last_gripper_state_file_name, 'wb') as f:
            pickle.dump(value, f)
