import threading
import math
from typing import List
import cv2
import asyncio
import numpy as np
import sympy as sym
#import RPi.GPIO as GPIO
import time

from HALs.HAL_base import HAL_base
from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Modules.Base.ImageProducer import ImageProducer
from Controllers.Controller import Controller

def coordinate_input(x, y, z,hal,vision=False):
    global mtr
    global sim
    try:
        a1 = 13.1
        a2 = 3.25
        a3 = 11.4
        a4 = 3.25
        a5 = 5.8
        a6 = 11.11
        robot_arm1 = Three_Degree_Arm(a1, a2, a3, a4, a5, a6)
        # caluclate angles
        angles = robot_arm1.calculate_angles(sym.Matrix([x, y, z, 1]))

        if angles is None:
            EE = sym.Matrix([x, y, z, 1])
            x, y, z, t = EE
            if x != 0 or y != 0:
                theta = sym.atan2(y, x)
            else:
                theta = 0
            print(theta)
            opp = z - a1
            dist = sym.sqrt(x ** 2 + y ** 2)
            t0deg = float(sym.deg(theta).evalf()) + 180
            t0deg = (t0deg + 360) % 360
            if dist == 0:
                theta1 = 90
            else:
                theta1 = sym.atan(opp / dist)
            t1deg = 90 - (float(sym.deg(theta1).evalf()))
            t0n = hal.get_joint(0)

            t1n = hal.get_joint(1)
            t0n = t0n + (t0deg - t0n) * .1
            t1n = t1n + (t1deg - t1n) * .1
            hal.set_joint(0, t0deg)
            hal.set_joint(1, t1deg)
            hal.set_joint(2, 0)


        else:
            # ANGLES: angle[0]=base angle[1]=servo1 angle[2]=servo2

            # what is BASE ANGLE?

            EE = sym.Matrix([x, y, z, 1])
            x, y, z, t = EE
            if x != 0 or y != 0:
                theta = sym.atan2(y, x)
            else:
                theta = 0
            print(theta)
            opp = z - a1
            dist = sym.sqrt(x ** 2 + y ** 2)
            t0deg = float(sym.deg(theta).evalf()) + 180
            t0deg = (t0deg + 360) % 360
            angle_base = t0deg
            angle_base = (angle_base + 360) % 360

            # theta 1 output : -90 to 90
            angle_1 = -(angles[1]-90)

            # theta 2 output : 0 to 180
            angle_2 =-(angles[2]-90)

            print("--------- Moving ARM ---------")
            if vision:
                print(f"joint:{hal.get_joint(0)}, new: {angle_base}, mid: {hal.get_joint(0)+0.1*(angle_base-hal.get_joint(0))}")
                hal.set_joint(0,angle_base)
                hal.set_joint(1, hal.get_joint(1)+0.1*(angle_1-hal.get_joint(1)))
                hal.set_joint(2, hal.get_joint(2)+0.1*(angle_2-hal.get_joint(2)))
            else:
                hal.set_joint(0, angle_base)
                hal.set_joint(1, angle_1)
                hal.set_joint(2, angle_2)

    except Exception as err:
        print(f"Exeption in moving the arm (coordinate_input): {err=}, {type(err)=}")


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

    def calculate_angles(self, EE):
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

class FollowClawController(Controller):
    def __init__(self, selected_HAL: HAL_base, vision: VisualObjectIdentifier):
        self.selected_HAL: HAL_base = selected_HAL
        self.vision: VisualObjectIdentifier = vision
        self.imageGetter: ImageProducer = selected_HAL
        
        self._task = None  # To keep track of the running task
        self.keep_running = False
        self.thread = None
        self.verbose_logging = False
        
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
        # in m
        self.sensor_size = .006
        self.focal_length = .0063
        # in pixels
        self.sensor_res = 1257
        # in radians
        self.fov = math.radians(60)
        self.contours = False
        selected_HAL.set_joint_min(0, 0) # set_base_min_degree(0)
        selected_HAL.set_joint_max(0, 270) # set_base_max_degree(270)
        selected_HAL.set_joint_max(2, 75) # set_joint_2_max(75)
        
    def get_error(self, frame_center, center):
        return center - frame_center
    
    def convert(self, T):
        return np.array([
            T[0][3],
            T[1][3],
            T[2][3],
        ])

    def merge(self, FK, BP):
        FK = FK * .01
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
        # if there is an object found
        if self.object_found:
            focal_len = self.sensor_size / (2 * math.tan(self.fov / 2))
            f_pixels = self.focal_length * (self.sensor_res / self.sensor_size)
            distance = f_pixels * .02 / (2 * self.pixel_dia)
            x_norm = self.error_x_distance / f_pixels
            y_norm = self.error_y_distance / f_pixels
            x_off = -math.tan(x_norm) * distance
            y_off = math.tan(y_norm) * distance
            print (f"x_off: {x_off}, y_off: {y_off}, depth: {math.pow(distance, 2) - math.pow(x_off, 2) - math.pow(y_off, 2)}")
            depth = math.sqrt(math.pow(distance, 2) - math.pow(x_off, 2) - math.pow(y_off, 2))
        # around y
            b = -np.deg2rad(self.selected_HAL.get_joint(1)) - np.deg2rad(self.selected_HAL.get_joint(2))
            # around x
            a = -math.radians(22.5)
            # around z
            c = np.deg2rad(self.selected_HAL.get_joint(0))
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
            ]
            )
            R_z = np.array([
                [np.cos(c), np.sin(c), 0],
                [-np.sin(c), np.cos(c), 0],
                [0, 0, 1]
            ])

            offset_matrix = np.array([
                x_off,
                y_off,
                depth
            ])
            # First order matrix and transformation
            l1rot = R_x
            l1inv = np.linalg.inv(l1rot)
            l1sol = np.matmul(l1inv, offset_matrix)
            l1tr = np.array([
                l1sol[0],
                l1sol[1] + (52.454 / 1000),
                l1sol[2] + (33.704 / 1000)
            ])
                # Second order matrix
            matrix = np.matmul(R_y, R_z)
            inv_rot = np.linalg.inv(matrix)
            solution = np.matmul(inv_rot, l1tr)
            # print(f"xOffset: {x_off}, yOffset: {y_off}, zOffset: {depth}")
            print(f"x:{solution[0]}, y: {solution[1]},z: {solution[2]}")
            solution[1] = -solution[1]
            
            a1 = 13.1
            a2 = 3.25
            a3 = 11.4
            a4 = 3.25
            a5 = 5.8
            a6 = .0001
            theta1 = round(np.deg2rad(self.selected_HAL.get_joint(0)), 5) if np.abs(np.deg2rad(self.selected_HAL.get_joint(0))) > .001 else 0
            theta2 = round(np.deg2rad(self.selected_HAL.get_joint(1)), 5) + math.radians(90) if np.abs(np.deg2rad(self.selected_HAL.get_joint(1))) > .001 else math.radians(90)
            theta3 = round(np.deg2rad(self.selected_HAL.get_joint(2)), 5) + math.radians(90) if np.abs(np.deg2rad(self.selected_HAL.get_joint(2))) > .001 else math.radians(90)
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
            ballPosition = self.merge(self.convert(H0_4), solution) * 100
            print(f"Final Ball Position (cm) {ballPosition}")
            coordinate_input(ballPosition[0], ballPosition[1], ballPosition[2], self.selected_HAL,True)
            asyncio.sleep(0.03)  #run detection every 1/30 seconds
        
    def select_largest_object(self, detected_objects: List[VisionObject]) -> VisionObject:
        if detected_objects:
            return max(detected_objects, key=lambda obj: obj.radius)
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

    def controller_state(self,state):
        self.use_controller = state

    async def update_frame_loop(self):
        while self.keep_running:
            if self.paused:
                await self.update_frame()
            if self.use_controller:
                await self.update_controller()

    

    def get_frame_mask(self):
        return cv2.resize(self.imageGetter.capture_image(), (0,0), fx=0.25, fy=0.25) , self.mask
    
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

    async def update_controller(self) -> bool:
        # CLOCK = 12
        # LATCH = 16
        # DATA = 18
        # GPIO.output(LATCH, GPIO.HIGH) 
        # asyncio.sleep(0.000012)
        # GPIO.output(LATCH, GPIO.LOW) 
        # asyncio.sleep(0.000006)
        
        # arr = [0,0,0,0,0,0,0,0]
        # for i in range(8):
        #     if (not GPIO.input(DATA)):
        #         arr[i] = 1


        #     GPIO.output(CLOCK, GPIO.HIGH) 
        #     asyncio.sleep(0.000006)
        #     GPIO.output(CLOCK, GPIO.LOW) 
        #     asyncio.sleep(0.000006)
        # if arr[0] == 1:
        #     self.selected_HAL.set_joint(0, ((self.hal.get_joint(0)+360)%360) + .01)
        # elif arr[1] == 1:
        #     self.selected_HAL.set_joint(0, ((self.hal.get_joint(0)+360)%360) -.01)
        # if arr[4] == 1:
        #     self.selected_HAL.set_joint(1, self.hal.get_joint(1) +.01)
        # elif arr[5] == 1:
        #     self.selected_HAL.set_joint(1, self.hal.get_joint(1) -.01)
        # if arr[6] == 1:
        #     self.selected_HAL.set_joint(1, self.hal.get_joint(2) +.01)
        # elif arr[7] == 1:
        #     self.selected_HAL.set_joint(2, self.hal.get_joint(2) -.01)
        pass

    async def update_frame(self) -> bool:
        print("x")
        frame = cv2.resize(self.imageGetter.capture_image(), (0,0), fx=0.25, fy=0.25) 
        pframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # For Sam Code ON physical****
        pframe = cv2.flip(pframe, -1)

        detected_objects: List[VisionObject] = self.vision.process_frame(pframe) 
        
        largest_object: VisionObject = self.select_largest_object(detected_objects)   
        
        self.object_found = (largest_object is not None)
        if(self.object_found):
            await self.move_towards_object(largest_object, frame)
        
            self.frame = cv2.flip(cv2.cvtColor(largest_object.source_frame_hsv, cv2.COLOR_HSV2BGR),0)
            amask = cv2.cvtColor(largest_object.source_frame_hsv, cv2.COLOR_HSV2BGR)
            self.calculate_sam_theta()
            #self.calculate_theta()
            center = (largest_object.x, largest_object.y)
            cv2.circle(amask, center, largest_object.radius, (0, 255, 0), 2)
            cv2.circle(amask, center, 7, (255, 255, 255), -1)
            self.mask = cv2.flip(amask,-1)
            print('Object Found!')
        else: 
            self.mask = cv2.resize(self.imageGetter.capture_image(), (0,0), fx=0.25, fy=0.25) 
        if cv2.waitKey(1) & 0xFF == ord('q'):
            await asyncio.sleep(0.03)  #run detection every 1/30 seconds
            return False
        
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