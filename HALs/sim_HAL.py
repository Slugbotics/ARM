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

# this function is super important for performance reasons
# Warning Chat GPT is great
def unpack_uint8_table(image_data):
    # Assuming image_data is a byte array
    return struct.unpack(f'{len(image_data)}B', image_data)

class sim_HAL(HAL_base):

    # create a lock object
    lock = threading.Lock()

    motorCount = 4
    
    host: str = None

    client = None
    sim = None
    mtr = None
    sensorHandle = None
    
    def __init__(self, host: str):
        super().__init__()
        self.lock = threading.Lock()
        self.host = host
        self.gripper_closed = False        

    def start_arm(self) -> bool:

        print("Connecting to CoppeliaSim...")
        if self.sim is None:
            with self.lock:
                # remote API init
                self.client = RemoteAPIClient(host=self.host)
                self.sim = self.client.require('sim')
                
                # motor ids
                self.mtr = [i for i in range(self.motorCount)]
                self.mtr[0] = self.sim.getObjectHandle('/Base/BaseRevolute')
                self.mtr[1] = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute')
                self.mtr[2] = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute')
                self.mtr[3] = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute')

                for i in range(self.motorCount):
                    print("Motor " + str(i) + ": " + str(self.mtr[i]))            

                # camera
                self.sensorHandle = self.sim.getObjectHandle('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute/Vision_sensor')


                # gripper rotator
                self.gripper_rotatorHandle = None # ensure the field exists
                try:                    
                    self.gripper_rotatorHandle = self.sim.getObject('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute')
                except Exception as e:
                    print("Gripper rotator joint not found: " + str(e))


                # gripper claw joint
                self.gripper_claw_jointHandle = None # ensure the field exists
                try:                    
                    self.gripper_claw_jointHandle = self.sim.getObject('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute/Crabclaw_0/Revolute_joint')
                except Exception as e:
                    print("Gripper claw joint not found: " + str(e))
                    
                
                 # gripper basic joint
                self.gripper_basic_jointHandle = None # ensure the field exists
                try:                    
                    self.gripper_basic_jointHandle = self.sim.getObject('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute/CrabClaw/Gripper')
                except Exception as e:
                    print("Gripper basic joint not found: " + str(e))
                    
                    
                # camera
                self.sensorHandle_alternate = None # ensure the field exists
                try:
                    self.sensorHandle_alternate = self.sim.getObject('/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute/Crabclaw_0/Revolute_joint/Vision_sesnor')
                except Exception as e:
                    print("Camera alternate not found: " + str(e))
                    

                print("Sensor: " + str(self.sensorHandle))
                print("sensorHandle_alternate: " + str(self.sensorHandle_alternate))
                print("gripper_claw_jointHandle: " + str(self.gripper_claw_jointHandle))
                print("gripper_basic_jointHandle: " + str(self.gripper_basic_jointHandle))
                # get camera resolution
                resolution = self.sim.getVisionSensorResolution(self.sensorHandle)
                print("Resolution: " + str(resolution))
                
                # start sim
                self.sim.startSimulation()
                return True
        else:
            return False
        print("Finished connecting to CoppeliaSim!")

    def stop_arm(self) -> bool:
        # global sim
        with self.lock:
            self.sim.stopSimulation()
            print("--------- Ended ARM_SIM ---------")
            
        return True

    def joint_count(self) -> int:
        return self.motorCount

    def set_joint(self, joint_index, joint_angle) -> bool:
        
        # Check if the joint angle is within the bounds
        if(joint_angle < self.get_joint_min(joint_index)):
            joint_angle = self.get_joint_min(joint_index)
        if(joint_angle > self.get_joint_max(joint_index)):
            joint_angle = self.get_joint_max(joint_index)        
        
        #move the joint
        if(joint_index < self.motorCount):
            with self.lock:
                self.sim.setJointTargetPosition(self.mtr[int(joint_index)], float(joint_angle) * D_TO_R)
            return True
        return False

    def get_joint(self, joint_index) -> float:
        with self.lock:
            return self.sim.getJointPosition(self.mtr[int(joint_index)]) * R_TO_D

    def get_arm_cam_img_rgb(self) -> cv2.typing.MatLike:

        with self.lock:
            image, resolution = self.sim.getVisionSensorImg(self.sensorHandle)
        image_data = unpack_uint8_table(image)
        image_array_rgb = np.array(image_data, dtype=np.uint8)
        image_array_rgb = np.reshape(image_array_rgb, (resolution[1], resolution[0], 3))
        image_array_rgb_vertically_flipped = cv2.flip(image_array_rgb, 0)  # flip image vertically
        # Convert the image from RGB to HSV color space
        # hsv_image = cv2.cvtColor(image_array_rgb, cv2.COLOR_RGB2HSV)

        return image_array_rgb_vertically_flipped
    
    def calculate_focal_length(self, sim, sensor_handle):
        """
        Calculate the focal length of a vision sensor in a CoppeliaSim scene using ZeroMQ-based API.

        Args:
            sim: The CoppeliaSim remote API object.
            sensor_handle: The handle to the vision sensor.

        Returns:
            The calculated focal length.
        """
        # Get the vision sensor resolution
        resolution_x = sim.getObjectInt32Param(sensor_handle, sim.visionintparam_resolution_x)
        resolution_y = sim.getObjectInt32Param(sensor_handle, sim.visionintparam_resolution_y)
        
        if resolution_x is None or resolution_y is None:
            raise RuntimeError("Failed to retrieve sensor resolution.")

        # Get the vision sensor horizontal view angle
        view_angle = sim.getObjectFloatParam(sensor_handle, sim.visionfloatparam_perspective_angle)
        if view_angle is None:
            raise RuntimeError("Failed to retrieve sensor view angle.")

        # Calculate focal length
        focal_length = resolution_x / (2 * math.tan(view_angle / 2))
        
        return focal_length
    
    def get_camera_focal_length(self) -> float:
        with self.lock:            
            return self.calculate_focal_length(self.sim, self.sensorHandle)
    
    def gripper_open(self) -> bool:
        if not self.gripper_closed:
            return False
        self.gripper_closed = False        
        
        if self.gripper_basic_jointHandle is not None:
            with self.lock:
                self.sim.setJointTargetPosition(self.gripper_basic_jointHandle, 0.0)
            return True
        
        if self.gripper_claw_jointHandle is not None:
            with self.lock:
                self.sim.setJointTargetPosition(self.gripper_claw_jointHandle, 0.0)
            return True
        
        return False
    
    def gripper_close(self) -> bool:
        if self.gripper_closed:
            return False
        self.gripper_closed = True
        
        if self.gripper_basic_jointHandle is not None:
            with self.lock:
                self.sim.setJointTargetPosition(self.gripper_basic_jointHandle, -0.300)
            return True
        
        if self.gripper_claw_jointHandle is not None:
            with self.lock:
                self.sim.setJointTargetPosition(self.gripper_claw_jointHandle, -0.300)
            return True
        
        return False
        
        
