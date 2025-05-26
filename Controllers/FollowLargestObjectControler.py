from typing import List
from typing import Tuple
import asyncio
import threading
import cv2

from HALs.HAL_base import HAL_base
from Vision.VisionObject import VisionObject
from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Modules.Base.ImageProducer import ImageProducer
from Controllers.Base.Controller import Controller

from Controllers.Base.VisionControllerBase import VisionBaseController
from Controllers.Base.MoveToPointOnScreenController import MoveToPointOnScreenController
from Config.ArmPhysicalParameters import ArmPhysicalParameters

class FollowLargestObjectControler(MoveToPointOnScreenController, VisionBaseController):
    def __init__(
        self,
        selected_HAL: HAL_base,
        vision: VisualObjectIdentifier,
        target_label: str = None,
        arm_params: ArmPhysicalParameters = None
    ):

        VisionBaseController.__init__(self, vision, target_label)
        MoveToPointOnScreenController.__init__(self, selected_HAL)

        self.selected_HAL: HAL_base = selected_HAL
        self.vision: VisualObjectIdentifier = vision
        self.imageGetter: ImageProducer = selected_HAL

        self.arm_params: ArmPhysicalParameters = arm_params  # Store ArmPhysicalParameters

        # Apply joint limits from ArmPhysicalParameters if provided
        if self.arm_params is not None:
            self.selected_HAL.set_joint_min(0, self.arm_params.base_min)
            self.selected_HAL.set_joint_max(0, self.arm_params.base_max)
            self.selected_HAL.set_joint_min(1, self.arm_params.joint1_min)
            self.selected_HAL.set_joint_max(1, self.arm_params.joint1_max)
            self.selected_HAL.set_joint_min(2, self.arm_params.joint2_min)
            self.selected_HAL.set_joint_max(2, self.arm_params.joint2_max)

        self.keep_running = False    

    def get_error(self, frame_center, center):
        return center - frame_center   
    
    def get_object_center_in_screen_space(self, obj: VisionObject) -> Tuple[int, int]:
        #calculate the distance from the centmessage.params[1]er of the frame
        frame_center_x = obj.frame_width // 2
        frame_center_y = obj.frame_height // 2
        distance_from_center_x = self.get_error(frame_center_x, obj.get_center_x())
        distance_from_center_y = self.get_error(frame_center_y, obj.get_center_y())        

        return (distance_from_center_x, distance_from_center_y)

    async def update_frame(self) -> bool:
        frame = self.imageGetter.capture_image()
            
        detected_objects: List[VisionObject] = self.vision.process_frame(frame) 
        
        target_object: VisionObject = self.select_largest_target_object(detected_objects)   
        
        self.object_found = (target_object is not None)
        if(self.object_found):
            distance_from_center_x, distance_from_center_y = self.get_object_center_in_screen_space(target_object)
            MoveToPointOnScreenController.set_target_position_on_screen(distance_from_center_x, distance_from_center_y, target_object.radius)

            if self.verbose_logging:
                print(f"Error X: {distance_from_center_x}, Error Y: {distance_from_center_y}, Radius: {target_object.radius}")

            #draw the bounding circle and the center of it
            if frame is not None:
                center = (target_object.get_center_x(), target_object.get_center_y())
                cv2.circle(frame, center, target_object.radius, (0, 255, 0), 2)
                cv2.circle(frame, center, 7, (255, 255, 255), -1)

            flipped_source_frame_rgb = cv2.flip(target_object.source_frame_rgb, 0)
            bgr_image = cv2.cvtColor(flipped_source_frame_rgb, cv2.COLOR_RGB2BGR)
            cv2.imshow('Frame', bgr_image)
            if target_object.mask is not None:
                # flipped_mask = cv2.flip(target_object.mask, 0)
                # cv2.imshow('Mask', flipped_mask)
                cv2.imshow('Mask', target_object.mask)
        # check if the user pressed 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            await asyncio.sleep(0.03)  # wait and exit
            return False
        
        self.set_last_frame_objects(detected_objects)
                
        return True

#regon Threadding stuff

    async def update_vision_loop(self):
        while self.keep_running:
            self.keep_running = await self.update_frame()
            await asyncio.sleep(0.03)  #run detection every 1/30 seconds

    async def update_movment_loop(self):
        while self.keep_running:
            if self.object_found:
                await MoveToPointOnScreenController.apply_movment()
            await asyncio.sleep(0.03)  #run movment every 1/30 seconds

    async def start_async(self):
        await asyncio.gather(
            self.update_vision_loop(),
            self.update_movment_loop(),
        )

    def thread_main(self):
        asyncio.run(self.start_async())
        
    def start(self):
        self.keep_running = True
        self.thread = threading.Thread(target=self.thread_main)
        self.thread.start()
    
    def stop(self):
        self.keep_running = False

#endregon Threadding stuff