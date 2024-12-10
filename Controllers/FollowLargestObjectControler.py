import threading
import math
from typing import List
import cv2
import asyncio
from threading import Lock

from HALs.HAL_base import HAL_base
from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Modules.Base.ImageProducer import ImageProducer
from Controllers.Controller import Controller

class FollowLargestObjectControler(Controller):
    def __init__(self, selected_HAL: HAL_base, vision: VisualObjectIdentifier, target_label: str = None):
        self.selected_HAL: HAL_base = selected_HAL
        self.vision: VisualObjectIdentifier = vision
        self.imageGetter: ImageProducer = selected_HAL
        
        self._task = None  # To keep track of the running task
        self.keep_running = False
        self.thread = None
        self.verbose_logging = False
        self.target_label = target_label
        if self.target_label is not None:
            self.target_label = self.target_label.lower()
        
        self.last_frame_objects: List[VisionObject] = []
        self.last_frame_objects_lock: Lock = threading.Lock()
        
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
        selected_HAL.set_joint_min(0, 0)   # set_base_min_degree(0)
        selected_HAL.set_joint_max(0, 270) # set_base_max_degree(270)
        selected_HAL.set_joint_max(2, 75)  # set_joint_2_max(75)
        
        if self.target_label is None:
            all_labels = self.vision.get_all_potential_labels()
            if len(all_labels) > 0:
                self.target_label = all_labels[0].lower()
                
    def set_target_label(self, label: str) -> bool:
        """This controller will only target objects with the specified label."""
        if self.is_label_in_universe(label):
            self.target_label = label.lower()
            return True
        else:
            print(f"Label \"{label}\" is not in the universe of {type(self).__name__}.")
            print(f"Please select a lable that is in universe: {self.vision.get_all_potential_labels()}")
            return False   
        
    def get_target_label(self) -> str:
        """Returns the label of the object that the controller is currently targeting."""
        return self.target_label
        
    def is_label_in_universe(self, label: str) -> bool:
        """Returns True if the label is something this controler can see, else false."""
        all_labels = self.vision.get_all_potential_labels()
        return label.lower() in (l.lower() for l in all_labels)

    
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
        
    def select_largest_target_object(self, detected_objects: List[VisionObject]) -> VisionObject:
        # print("found: " + str(len(detected_objects)) + " objects")
        
        # # print the labels of all visible objects on one line
        # for obj in detected_objects:
        #     print(obj.label, end=", ")
        # print()
        
        if detected_objects:
            found_target = None
            for obj in detected_objects:
                if obj.label.lower() == self.target_label:
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
        self.error_x_distance = self.get_error(frame_center_x, obj.get_center_x())
        self.error_y_distance = self.get_error(frame_center_y, obj.get_center_y())
        self.pixel_dia = obj.radius
        if self.verbose_logging:
            print(f"Error X: {self.error_x_distance}, Error Y: {self.error_y_distance}, Radius: {self.pixel_dia}")

        #draw the bounding circle and the center of it
        if draw_frame is not None:
            center = (obj.get_center_x(), obj.get_center_y())
            cv2.circle(draw_frame, center, obj.radius, (0, 255, 0), 2)
            cv2.circle(draw_frame, center, 7, (255, 255, 255), -1)

    async def update_frame_loop(self):
        while self.keep_running:
            await self.update_frame()

    async def update_frame(self) -> bool:
        frame = self.imageGetter.capture_image()
            
        detected_objects: List[VisionObject] = self.vision.process_frame(frame) 
        
        target_object: VisionObject = self.select_largest_target_object(detected_objects)   
        
        self.object_found = (target_object is not None)
        if(self.object_found):
            await self.move_towards_object(target_object, frame)

            flipped_source_frame_hsv = cv2.flip(target_object.source_frame_hsv, 0)
            rgb_image = cv2.cvtColor(flipped_source_frame_hsv, cv2.COLOR_HSV2BGR)
            cv2.imshow('Frame', rgb_image)
            if target_object.mask is not None:
                # flipped_mask = cv2.flip(target_object.mask, 0)
                # cv2.imshow('Mask', flipped_mask)
                cv2.imshow('Mask', target_object.mask)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            await asyncio.sleep(0.03)  #run detection every 1/30 seconds
            return False
        
        with self.last_frame_objects_lock:
            self.last_frame_objects = detected_objects
        
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