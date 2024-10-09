import threading
import math
from typing import List
import cv2
import asyncio

from HALs.HAL_base import HAL_base
from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Modules.Base.ImageProducer import ImageProducer
from Controllers.Controller import Controller

class FollowLargestObjectControler(Controller):
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
        selected_HAL.set_joint_min(0, 0) # set_base_min_degree(0)
        selected_HAL.set_joint_max(0, 270) # set_base_max_degree(270)
        selected_HAL.set_joint_max(2, 75) # set_joint_2_max(75)
        
    def get_error(self, frame_center, center):
        return center - frame_center

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
        
    async def calculate_theta(self):
        while self.keep_running:
            # if there is an object found
            if self.object_found:
                self.calculate_base_theta()
                self.calculate_servo_1_theta()
                self.calculate_servo_2_theta()

                # if self.theta_base > 359:
                #     self.theta_base = 359
                # if self.theta_base < 0:
                #     self.theta_base = 0
                
                # if self.servo_1 < -90:
                #     self.servo_1 = -90
                # if self.servo_1 > 90:
                #     self.servo_1 = 90

                # if self.servo_2 < 0:
                #     self.servo_2 = 0
                # if self.servo_2 > 180:
                #     self.servo_2 = 180
            
                

                if(self.theta_base < 0):
                    self.theta_base = 0
                if(self.servo_2 < 0):
                    self.servo_2 = 0

                if self.verbose_logging:
                    print('theta_base: ' + str(self.theta_base))
                    #print('servo_1: ' + str(self.servo_1))
                    print('servo_2: ' + str(self.servo_2))
                    print('------------------------------------------------------')

                self.selected_HAL.set_joint(0, self.theta_base)
                #self.selected_HAL.set_joint(1, self.servo_1)
                self.selected_HAL.set_joint(2, self.servo_2)
                
            await asyncio.sleep(0.03)  #run detection every 1/30 seconds
        
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

    async def update_frame_loop(self):
        while self.keep_running:
            await self.update_frame()

    async def update_frame(self) -> bool:
        frame = self.imageGetter.capture_image()
            
        detected_objects: List[VisionObject] = self.vision.process_frame(frame) 
        
        largest_object: VisionObject = self.select_largest_object(detected_objects)   
        
        self.object_found = (largest_object is not None)
        if(self.object_found):
            await self.move_towards_object(largest_object, frame)
        
            cv2.imshow('Frame', cv2.flip(largest_object.source_frame_hsv, 0))
            cv2.imshow('Mask', cv2.flip(largest_object.mask, 0))
            # cv2.imshow('Mask', mask)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            await asyncio.sleep(0.03)  #run detection every 1/30 seconds
            return False
        
        await asyncio.sleep(0.03)  #run detection every 1/30 seconds
        
        return True
    
    async def start_async(self):
        await asyncio.gather(
            self.update_frame_loop(),
            self.calculate_theta(),
        )
        
    def thread_main(self):
        asyncio.run(self.start_async())
        
    def start(self):
        self.keep_running = True
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()
    
    def stop(self):
        self.keep_running = False