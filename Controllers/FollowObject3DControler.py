"""
FollowObject3DControler.py

Summary:
    This script implements a controller for a robotic arm that visually tracks and follows a 3D object using computer vision.
    It integrates with a hardware abstraction layer (HAL), vision modules, and arm kinematics to compute and command joint movements
    based on the detected position of a target object in camera frames. The controller supports asynchronous operation, 
    object selection by label, and provides utility methods for interacting with detected objects and arm state.

Author:
    UCSC Slugbotics Club, Arm Team
"""

import threading
from threading import Lock
import math
from typing import List
import cv2
import asyncio
import numpy as np
import sympy as sym
#import RPi.GPIO as GPIO
import time
import logging

from HALs.HAL_base import HAL_base
from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Modules.Base.ImageProducer import ImageProducer
from Controllers.Base.Controller import Controller
from Config.ArmPhysicalParameters import ArmPhysicalParameters

# --- Constants for Magic Numbers ---
SMOOTHING_FACTOR = 0.1
ANGLE_OFFSET_90 = 90
ANGLE_OFFSET_180 = 180
FRAME_SLEEP_SECONDS = 0.03
HARD_CODED_ANGLE_RAD = math.radians(22.5)
A6_EPSILON = 0.0001
M_TO_CM = 100
PIXEL_TO_METER = 0.01
resize_fx = 0.25
resize_fy = 0.25

def set_arm_target_position(
    x: float,
    y: float,
    z: float,
    hal,
    arm_params: ArmPhysicalParameters,
    smoothing_factor: float = 0.1
) -> bool:
    """
    Calculates and commands the arm to reach the given (x, y, z) position.

    Args:
        x (float): Target x coordinate.
        y (float): Target y coordinate.
        z (float): Target z coordinate.
        hal: Hardware abstraction layer for controlling the arm.
        arm_params (ArmPhysicalParameters): Arm physical parameters (required).
        smoothing_factor (float): Smoothing factor for joint movement.

    Returns:
        bool: True if the position is reachable and command sent, False if fallback was used.

    Raises:
        ValueError: If arm_params is not provided.
        Exception: For unexpected errors.
    """

    try:
        angles = _calculate_kinematics(x, y, z, arm_params)
        if angles is None:
            logging.warning("Target position unreachable, using fallback kinematics.")
            _fallback_kinematics(x, y, z, hal, arm_params, smoothing_factor)
            return False
        else:
            _command_hardware(angles, x, y, z, hal, arm_params, smoothing_factor)
            return True
    except Exception as err:
        logging.exception(f"Exception in set_arm_target_position: {err}")
        raise

def _calculate_kinematics(
    x: float,
    y: float,
    z: float,
    arm_params: 'ArmPhysicalParameters'
):
    """
    Calculates joint angles using the arm's kinematics.

    Returns:
        tuple or None: (theta1_deg, theta2_deg, theta3_deg) if reachable, else None.
    """
    robot_arm = Three_Degree_Arm(
        arm_params.a1, arm_params.a2, arm_params.a3,
        arm_params.a4, arm_params.a5, arm_params.a6
    )
    return robot_arm.calculate_angles(sym.Matrix([x, y, z, 1]))

def _fallback_kinematics(
    x: float,
    y: float,
    z: float,
    hal,
    arm_params: ArmPhysicalParameters,
    smoothing_factor: float
) -> None:
    """
    Fallback for unreachable positions: computes simple base and shoulder angles.
    """
    a1 = arm_params.a1
    ANGLE_OFFSET_90 = 90
    ANGLE_OFFSET_180 = 180

    theta = sym.atan2(y, x) if (x != 0 or y != 0) else 0
    opp = z - a1
    dist = sym.sqrt(x ** 2 + y ** 2)
    t0deg = float(sym.deg(theta).evalf()) + ANGLE_OFFSET_180
    t0deg = (t0deg + 360) % 360
    theta1 = sym.atan(opp / dist) if dist != 0 else ANGLE_OFFSET_90
    t1deg = ANGLE_OFFSET_90 - (float(sym.deg(theta1).evalf()))
    t0n = hal.get_joint(0)
    t1n = hal.get_joint(1)
    t0n = t0n + (t0deg - t0n) * smoothing_factor
    t1n = t1n + (t1deg - t1n) * smoothing_factor
    hal.set_joint(0, t0n)
    hal.set_joint(1, t1n)
    hal.set_joint(2, 0)
    logging.info(f"Fallback kinematics used: base={t0n:.2f}, shoulder={t1n:.2f}, elbow=0")

def _command_hardware(
    angles,
    x: float,
    y: float,
    z: float,
    hal,
    arm_params: ArmPhysicalParameters,
    smoothing_factor: float
) -> None:
    """
    Sends calculated joint angles to the hardware, with optional smoothing.
    """
    ANGLE_OFFSET_90 = 90
    ANGLE_OFFSET_180 = 180

    theta = sym.atan2(y, x) if (x != 0 or y != 0) else 0
    t0deg = float(sym.deg(theta).evalf()) + ANGLE_OFFSET_180
    t0deg = (t0deg + 360) % 360
    angle_base = t0deg
    angle_base = (angle_base + 360) % 360
    angle_1 = -(angles[1] - ANGLE_OFFSET_90)
    angle_2 = -(angles[2] - ANGLE_OFFSET_90)

    # Always use smoothing for consistency
    base_val = hal.get_joint(0) + smoothing_factor * (angle_base - hal.get_joint(0))
    shoulder_val = hal.get_joint(1) + smoothing_factor * (angle_1 - hal.get_joint(1))
    elbow_val = hal.get_joint(2) + smoothing_factor * (angle_2 - hal.get_joint(2))
    hal.set_joint(0, base_val)
    hal.set_joint(1, shoulder_val)
    hal.set_joint(2, elbow_val)
    logging.info(f"Smooth move: base={base_val:.2f}, shoulder={shoulder_val:.2f}, elbow={elbow_val:.2f}")

class Three_Degree_Arm:
    def __init__(self, a1, a2, a3, a4, a5, a6) -> None:
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.a4 = a4
        self.a5 = a5
        self.a6 = a6

    def DH_matrix(self, theta, alpha, r, d):
        return sym.Matrix([
            [sym.cos(theta), -sym.sin(theta) * sym.cos(alpha), sym.sin(theta) * sym.sin(alpha), r * sym.cos(theta)],
            [sym.sin(theta), sym.cos(theta) * sym.cos(alpha), -sym.cos(theta) * sym.sin(alpha), r * sym.sin(theta)],
            [0, sym.sin(alpha), sym.cos(alpha), d],
            [0, 0, 0, 1]
        ])

    def calculate_angles(self, EE) -> bool:
        x, y, z = EE[0], EE[1], EE[2]

        # Condition checks
        cond1 = (np.abs(x) - self.a3) ** 2 + (z - self.a1) ** 2 < (self.a5 + self.a6) ** 2 and np.abs(
            x) > self.a3 and 0 < z < self.a1
        cond2 = np.abs(x) ** 2 + (z - self.a1) ** 2 < (self.a3 + self.a5 + self.a6) ** 2 and np.abs(x) ** 2 + (
                z - self.a1) ** 2 > self.a3 ** 2 and np.abs(x) > 0 and z > self.a1

        isInRegion = cond1 or cond2

        if isInRegion:
            print('The point is inside the region.')
            print(EE)
            theta1 = sym.atan2(y, x)

            H0_1 = self.DH_matrix(theta1, sym.pi / 2, 0, self.a1)
            EE_local_H0_1 = H0_1.inv() * EE

            EE_x_H0_1 = EE_local_H0_1[0]
            # not used in this context
            # EE_y_H0_1 = EE_local_H0_1[2]
            EE_z_H0_1 = EE_local_H0_1[1]

            l1 = self.a3
            l2 = self.a5 + self.a6
            R = sym.sqrt(EE_x_H0_1 ** 2 + EE_z_H0_1 ** 2)
            theta = sym.atan(EE_z_H0_1 / EE_x_H0_1)

            beta = sym.acos((R ** 2 - l1 ** 2 - l2 ** 2) / (-2 * l1 * l2))
            if not beta.is_real:
                return None
            alpha = sym.asin((l2 * sym.sin(beta)) / R)
            print(alpha)
            theta2 = theta + alpha
            theta3 = beta - sym.pi / 2

            theta4 = 0

            print(theta2.evalf())
            print(theta3.evalf())

            H1_2 = self.DH_matrix(theta2, 0, self.a3, -self.a2)
            H2_3 = self.DH_matrix(theta3, sym.pi / 2, 0, self.a4)
            H3_4 = self.DH_matrix(theta4, 0, 0, self.a5 + self.a6)

            H0_2 = H0_1 * H1_2
            H0_3 = H0_2 * H2_3
            H0_4 = H0_3 * H3_4

            EE_position = H0_4[:3, 3]
            print('EE Position (CM):')
            # print(f'x: {float(EE_position[0].evalf()):.2f}')
            # print(f'y: {float(EE_position[1].evalf()):.2f}')
            # print(f'z: {float(EE_position[2].evalf()):.2f}')

            theta1_deg = sym.deg(theta1.evalf())
            theta2_deg = sym.deg(theta2.evalf())
            theta3_deg = sym.deg(theta3.evalf())

            print('\nTheta Angles:')
            print(f'Base: {theta1_deg.evalf():.2f} degrees')
            print(f'1: {theta2_deg.evalf():.2f} degrees')
            print(f'2: {theta3_deg.evalf():.2f} degrees')
            return theta1_deg, theta2_deg, theta3_deg
        else:
            print('This point is not feasible')
        return isInRegion

class FollowObject3DControler(Controller):
    def __init__(self, selected_HAL: HAL_base, vision: VisualObjectIdentifier, arm_params: ArmPhysicalParameters, target_label: str = None):
        self.selected_HAL: HAL_base = selected_HAL
        self.vision: VisualObjectIdentifier = vision
        self.imageGetter: ImageProducer = selected_HAL
        self.arm_params: ArmPhysicalParameters = arm_params  # Save ArmPhysicalParameters

        self._task = None  # To keep track of the running task
        self.keep_running = False
        self.thread = None
        self.verbose_logging = False
        self.target_label = target_label

        self.last_frame_objects: List[VisionObject] = []
        self.last_frame_objects_lock: Lock = threading.Lock()

        # Use arm_params for all relevant parameters
        self.K = 1
        self.lambda_ = 3          # change (3 is smooth in sim) increase number to go slower
        self.error_tolerance_coord = 5  # change for error precision
        self.dia_target = 50    # change for error precision
        self.error_x_distance = 0
        self.error_y_distance = 0
        self.pixel_dia = 0
        self.max_pixel_dia = 18     ### CHANGES ACCORDING TO CAMERA
        self.contours = False
        self.object_found = False
        self.theta_base = 0
        self.servo_1 = 90
        self.servo_2 = 0
        self.movement_speed = 1       # 1/10 seconds
        self.servo1_constraint = 45
        self.init = False
        self.frame=False
        self.mask=False
        self.paused = False
        self.use_controller = False

        # Camera calibration from arm_params
        self.sensor_size = arm_params.sensor_size
        self.focal_length = arm_params.focal_length
        self.sensor_res = arm_params.sensor_res
        self.fov = math.radians(arm_params.fov)

        self.contours = False
        selected_HAL.set_joint_min(0, arm_params.base_min)
        selected_HAL.set_joint_max(0, arm_params.base_max)        
        selected_HAL.set_joint_min(1, arm_params.joint1_min)
        selected_HAL.set_joint_max(1, arm_params.joint1_max)      
        selected_HAL.set_joint_min(2, arm_params.joint2_min)  
        selected_HAL.set_joint_max(2, arm_params.joint2_max)        

    def get_error(self, frame_center, center):
        return center - frame_center

    def convert(self, T):
        return np.array([
            T[0][3],
            T[1][3],
            T[2][3],
        ])

    def merge(self, FK, BP):
        FK = FK * PIXEL_TO_METER
        print(FK)
        print(BP)
        return np.array([
            FK[0] + BP[0],
            FK[1] - BP[1],
            FK[2] + BP[2],
        ])

    def DH(self, theta, alpha, r, d):
        return np.array([
            [np.cos(theta), -np.sin(theta) * round(np.cos(alpha)), np.sin(theta) * round(np.sin(alpha)),
             r * np.cos(theta)],
            [np.sin(theta), np.cos(theta) * round(np.cos(alpha)), -np.cos(theta) * round(np.sin(alpha)),
             r * np.sin(theta)],
            [0, round(np.sin(alpha)), round(np.cos(alpha)), d],
            [0, 0, 0, 1]
        ])
    def calculate_theta(self):
        # Stage 1: Check if an object is found
        if self.object_found:
            # Stage 2: Camera and pixel calculations
            # Calculate camera intrinsics and estimate distance to the object using its pixel diameter
            focal_len = self.sensor_size / (2 * math.tan(self.fov / 2))
            focal_len_pixels = focal_len * (self.sensor_res / self.sensor_size)
            distance_to_object = focal_len_pixels * .02 / (2 * self.pixel_dia)
            x_norm = self.error_x_distance / focal_len_pixels
            y_norm = self.error_y_distance / focal_len_pixels
            x_off = -math.tan(x_norm) * distance_to_object
            y_off = math.tan(y_norm) * distance_to_object
            print (f"x_off: {x_off}, y_off: {y_off}, depth: {math.pow(distance_to_object, 2) - math.pow(x_off, 2) - math.pow(y_off, 2)}")
            # Calculate the depth (z) using the Pythagorean theorem
            depth = math.sqrt(math.pow(distance_to_object, 2) - math.pow(x_off, 2) - math.pow(y_off, 2))

            # Stage 3: Compute rotation matrices for current arm joint angles
            # These matrices represent the orientation of the arm's end effector
            b = -np.deg2rad(self.selected_HAL.get_joint(1)) - np.deg2rad(self.selected_HAL.get_joint(2))  # around y
            a = -HARD_CODED_ANGLE_RAD  # around x
            c = np.deg2rad(self.selected_HAL.get_joint(0))  # around z
            print(f"Around Y = {b}, Around Z = {c}")
            R_x = np.array([
                [1, 0, 0],
                [0, np.cos(a), -np.sin(a)],
                [0, np.sin(a), np.cos(a)]
            ])
            R_y = np.array([
                [np.cos(b), 0, -np.sin(b)],
                [0, 1, 0],
                [np.sin(b), 0, np.cos(b)]
            ])
            R_z = np.array([
                [np.cos(c), np.sin(c), 0],
                [-np.sin(c), np.cos(c), 0],
                [0, 0, 1]
            ])

            # Stage 4: Transform the offset to the arm's base frame
            # Convert the camera offset into the arm's coordinate system
            offset_matrix = np.array([
                x_off,
                y_off,
                depth
            ])
            # First order matrix and transformation (apply R_x)
            l1rot = R_x
            l1inv = np.linalg.inv(l1rot)
            l1sol = np.matmul(l1inv, offset_matrix)
            l1tr = np.array([
                l1sol[0],
                l1sol[1] + self.arm_params.kinematic_offset_y,
                l1sol[2] + self.arm_params.kinematic_offset_z
            ])
            # Second order matrix (apply R_y and R_z)
            matrix = np.matmul(R_y, R_z)
            inv_rot = np.linalg.inv(matrix)
            solution = np.matmul(inv_rot, l1tr)
            # Negate y to match arm's coordinate system
            print(f"x:{solution[0]}, y: {solution[1]},z: {solution[2]}")
            solution[1] = -solution[1]

            # Stage 5: Forward kinematics for current arm position
            # Compute the current end effector position using DH parameters
            a1 = self.arm_params.a1
            a2 = self.arm_params.a2
            a3 = self.arm_params.a3
            a4 = self.arm_params.a4
            a5 = self.arm_params.a5
            a6 = A6_EPSILON  # keep as before for calculation stability
            theta1 = round(np.deg2rad(self.selected_HAL.get_joint(0)), 5) if np.abs(np.deg2rad(self.selected_HAL.get_joint(0))) > .001 else 0
            theta2 = round(np.deg2rad(self.selected_HAL.get_joint(1)), 5) + math.radians(ANGLE_OFFSET_90) if np.abs(np.deg2rad(self.selected_HAL.get_joint(1))) > .001 else math.radians(ANGLE_OFFSET_90)
            theta3 = round(np.deg2rad(self.selected_HAL.get_joint(2)), 5) + math.radians(ANGLE_OFFSET_90) if np.abs(np.deg2rad(self.selected_HAL.get_joint(2))) > .001 else math.radians(ANGLE_OFFSET_90)
            theta4 = 0
            H0_1 = self.DH(theta1, np.pi / 2, 0, a1)
            H1_2 = self.DH(theta2, 0, a3, -a2)
            H2_3 = self.DH(theta3, np.pi / 2, 0, a4)
            H3_4 = self.DH(theta4, 0, 0, a5 + a6)
            H0_2 = np.matmul(H0_1, H1_2)
            H0_3 = np.matmul(H0_2, H2_3)
            H0_4 = np.matmul(H0_3, H3_4)
            print(f"t1: {theta1}, t2: {theta2}, t3: {theta3}")
            print(f"FK: {self.convert(H0_4)}")

            # Stage 6: Compute the target position for the arm
            # Merge the current end effector position and the computed offset, convert to centimeters
            ballPosition = self.merge(self.convert(H0_4), solution) * M_TO_CM
            print(f"Final Ball Position (cm) {ballPosition}")

            # Stage 7: Command the arm to move to the computed position
            set_arm_target_position(ballPosition[0], ballPosition[1], ballPosition[2], self.selected_HAL, self.arm_params)

            # Stage 8: Sleep briefly to control update rate (should be awaited if in async context)
            asyncio.sleep(FRAME_SLEEP_SECONDS)  #run detection every 1/30 seconds

    def select_largest_target_object(self, detected_objects: List[VisionObject]) -> VisionObject:
        # print("found: " + str(len(detected_objects)) + " objects")
        
        # # print the labels of all visible objects on one line
        # for obj in detected_objects:
        #     print(obj.label, end=", ")
        # print()
        
        if detected_objects:
            found_target = None
            for obj in detected_objects:
                if obj.label == self.target_label:
                    if found_target is not None:
                        if obj.radius > found_target.radius:
                            found_target = obj
                    else:
                        found_target = obj
            
            # print("largest object: " + str(found_target.label))
            return found_target
        else:
            return None
        
    async def move_towards_object(self, obj: VisionObject, draw_frame: cv2.typing.MatLike = None) -> None:
        #calculate the distance from the centmessage.params[1]er of the frame
        frame_center_x = obj.frame_width // 2
        frame_center_y = obj.frame_height // 2
        self.error_x_distance = self.get_error(frame_center_x, obj.x)
        self.error_y_distance = self.get_error(frame_center_y, obj.y)
        self.pixel_dia = obj.radius
        if self.verbose_logging:
            print(f"Error X: {self.error_x_distance}, Error Y: {self.error_y_distance}, Radius: {self.pixel_dia}")

        #draw the bounding circle and the center of it
        if draw_frame is not None:
            center = (obj.x, obj.y)
            cv2.circle(draw_frame, center, obj.radius, (0, 255, 0), 2)
            cv2.circle(draw_frame, center, 7, (255, 255, 255), -1)

    async def update_frame_loop(self):
        while self.keep_running:
            if self.paused:
                await self.update_frame()
            if self.use_controller:
                await self.update_controller()

    def get_frame_mask(self):
        return cv2.resize(self.imageGetter.capture_image(), (0,0), fx=resize_fx, fy=resize_fy) , self.mask
    
    def calculate_sam_theta(self): 
        if self.object_found:
            self.calculate_base_theta()
            self.calculate_servo_1_theta()
            self.calculate_servo_2_theta()
            if(self.theta_base < 0):
                self.theta_base = 0
            if(self.servo_2 < 0):
                self.servo_2 = 0

            print('theta_base: ' + str(self.theta_base))
            # print('servo_1: ' + str(self.servo_1))
            print('servo_2: ' + str(self.servo_2))
            print('------------------------------------------------------')

            self.selected_HAL.set_joint(0, self.theta_base)
            # set_joint(1, self.servo_1)
            self.selected_HAL.set_joint(2, self.servo_2)


    async def update_frame(self) -> bool:
        print("x")
        frame = cv2.resize(self.imageGetter.capture_image(), (0,0), fx=resize_fx, fy=resize_fy) 
        # pframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # # For Sam Code ON physical****
        # pframe = cv2.flip(pframe, -1)

        detected_objects: List[VisionObject] = self.vision.process_frame(frame) 
        
        largest_object: VisionObject = self.select_largest_target_object(detected_objects)   
        
        self.object_found = (largest_object is not None)
        if(self.object_found):
            await self.move_towards_object(largest_object, frame)
        
            self.frame = cv2.flip(cv2.cvtColor(largest_object.source_frame_rgb, cv2.COLOR_RGB2BGR),0)
            amask = cv2.cvtColor(largest_object.source_frame_rgb, cv2.COLOR_RGB2BGR)
            self.calculate_sam_theta()
            #self.calculate_theta()
            center = (largest_object.x, largest_object.y)
            cv2.circle(amask, center, largest_object.radius, (0, 255, 0), 2)
            cv2.circle(amask, center, 7, (255, 255, 255), -1)
            self.mask = cv2.flip(amask,-1)
            print('Object Found!')
        else: 
            self.mask = cv2.resize(self.imageGetter.capture_image(), (0,0), fx=resize_fx, fy=resize_fy) 
        if cv2.waitKey(1) & 0xFF == ord('q'):
            await asyncio.sleep(0.03)  #run detection every 1/30 seconds
            return False
        
        with self.last_frame_objects_lock:
            self.last_frame_objects = detected_objects
        
        await asyncio.sleep(0.03)  #run detection every 1/30 seconds
    def calculate_base_theta(self):
        if abs(self.error_x_distance) > self.error_tolerance_coord:
            self.theta_base = self.selected_HAL.get_joint(0) - self.K * self.error_x_distance * math.exp(-self.lambda_)

            #move without slow decient
            # self.theta_base = self.theta_base - self.K * (1 - math.exp(-self.lambda_ * self.error_x_distance))

    def calculate_servo_1_theta(self):
        if abs(self.pixel_dia) < self.dia_target:
            self.servo_1 = self.servo_1 + 3 * self.pixel_dia * math.exp(-self.lambda_)
        if abs(self.pixel_dia) > self.dia_target:
            self.servo_1 = self.servo_1 - 3 * self.pixel_dia * math.exp(-self.lambda_)

        #constrain servo
        if self.servo_1 < -self.servo1_constraint:
            self.servo_1 = -self.servo1_constraint
        if self.servo_1 > self.servo1_constraint:
            self.servo_1 = self.servo1_constraint

    def calculate_servo_2_theta(self):
        if abs(self.error_y_distance) > self.error_tolerance_coord:
            self.servo_2 = self.selected_HAL.get_joint(2) - self.K * self.error_y_distance * math.exp(-self.lambda_)
    
    async def start_async(self):
        await asyncio.gather(
            self.update_frame_loop()
        )
        
    def thread_main(self):
        asyncio.run(self.start_async())
        
    def start(self):
        self.keep_running = True
        self.paused = True
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()
    def pause_state(self,state):
        self.paused = state
    
    def stop(self):
        self.keep_running = False
        
    #region Controler Base Interface
    def set_target_label(self, label: str) -> bool:
        """This controller will only target objects with the specified label."""
        if self.is_label_in_universe(label):
            self.target_label = label
            return True
        else:
            print(f"Label {label} is not in the universe of {self.__name__}.")
            print(f"Please select a lable that is in universe: {self.vision.get_all_potential_labels()}")
            return False
        
    def get_target_label(self) -> str:
        """Returns the label of the object that the controller is currently targeting."""
        return self.target_label
        
    def is_label_in_universe(self, label: str) -> bool:
        """Returns True if the label is something this controler can see, else false."""
        all_labels = self.vision.get_all_potential_labels()
        return (label in all_labels)
    
    def get_visible_object_labels(self) -> list[str]:
        """Returns a list of identifiers of objects that are visible to the arm"""
        with self.last_frame_objects_lock:
            if self.last_frame_objects is None:
                return []
            return [obj.label for obj in self.last_frame_objects]
        
    def get_visible_object_labels_detailed(self) -> list[str]:
        """Returns a list of objects that are visible to the arm, including metadata"""
        with self.last_frame_objects_lock:
            if self.last_frame_objects is None:
                return []
            # return a series of string that represent the object, starting withe object's label, then radius, then metadata
            return [f"{obj.label} radius: {obj.radius} {obj.metadata}" for obj in self.last_frame_objects]
            #return [f"{obj.label}_object" for obj in self.last_frame_objects]
    
    def get_all_posible_labels(self) -> list[str]:
        """Returns a list of all possible labels that this controller can see, even if they are not currently visible."""
        return self.vision.get_all_potential_labels()
    #endregion Controler Base Interface