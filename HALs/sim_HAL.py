from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import cv2
import threading
import math
import numpy as np
import struct

from HALs.HAL_base import HAL_base

# degrees to radians
D_TO_R = math.pi / 180
R_TO_D = 180 / math.pi

# this function is super importent for performance reasons
# Warning Chat GPT is great
def unpack_uint8_table(image_data):
    # Assuming image_data is a byte array
    return struct.unpack(f'{len(image_data)}B', image_data)

class sim_HAL(HAL_base):

    # create a lock object
    lock = threading.Lock()

    motorCount = 4
    
    client = None
    sim = None
    mtr = None
    sensorHandle = None
    
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def start_arm(self):

        if self.sim is None:
            with self.lock:
                # remote API init
                self.client = RemoteAPIClient()
                self.sim = self.client.require('sim')
                
                # motor ids
                self.mtr = [i for i in range(self.motorCount)]
                self.mtr[0] = self.sim.getObjectHandle('/Base/BaseRevolute')
                self.mtr[1] = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute')
                self.mtr[2] = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute')
                self.mtr[3] = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute')

                # camera
                self.sensorHandle = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute/Vision_sensor')

                # start sim
                self.sim.startSimulation()

    def stop_arm(self):
        # global sim
        with self.lock:
            self.sim.stopSimulation()
            print("--------- Ended ARM_SIM ---------")

    def joint_count(self):
        return self.motorCount

    def set_joint(self, joint_index, joint_angle):
        
        # Check if the joint angle is within the bounds
        if(joint_angle < self.get_joint_min(joint_index)):
            joint_angle = self.get_joint_min(joint_index)
        if(joint_angle > self.get_joint_max(joint_index)):
            joint_angle = self.get_joint_max(joint_index)        
        
        #move the joint
        if(joint_index < self.motorCount):
            with self.lock:
                self.sim.setJointTargetPosition(self.mtr[int(joint_index)], float(joint_angle) * D_TO_R)

    def get_joint(self, joint_index):
        with self.lock:
            return self.sim.getJointPosition(self.mtr[int(joint_index)]) * R_TO_D

    def get_arm_cam_img_hsv(self):

        with self.lock:
            image, resolution = self.sim.getVisionSensorImg(self.sensorHandle)
        image_data = unpack_uint8_table(image)
        image_array = np.array(image_data, dtype=np.uint8)
        image_array = np.reshape(image_array, (resolution[1], resolution[0], 3))

        # Convert the image from RGB to HSV color space
        hsv_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)

        return hsv_image
    
    def gripper_open(self):
        return False
    
    def gripper_close(self):
        return False
