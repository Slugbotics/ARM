import threading
import math
import asyncio

from HALs.HAL_base import HAL_base
from Controllers.Base.Controller import Controller

class MoveToPointOnScreenController(Controller):

    def __init__(self, selected_HAL: HAL_base):
        super().__init__(selected_HAL)
        self.selected_HAL = selected_HAL

        self.target_positional_tolerance = 5 # acceptable distance from the target screen position (was named error_tolerance_coord)
        self.target_diameter_pixels = 0 # diameter of the target in screenspace pixels (was pixel_dia)
        self.target_actual_diameter_pixels = 50 # actual diameter of the target in screenspace pixels (used to navigate closer) (was dia_target)
        self.smoothness = 3 # how smooth the movements should be, higher is smoother and slower (was called lambda_)
        self.error_movment_intensity = 1 # how much the servos should move when the error is detected (was called K)

        self.verbose_logging = False # if True, will print out the theta values to the console

    def start(self) -> None:
        self.horizontal_distance_from_center = 0
        self.vertical_distance_from_center = 0

    def stop(self) -> None:
        pass

    def calculate_base_theta(self):
        if abs(self.horizontal_distance_from_center) > self.target_positional_tolerance:
            self.theta_base = self.selected_HAL.get_joint(0) - self.error_movment_intensity * self.horizontal_distance_from_center * math.exp(-self.smoothness)

            #move without slow decient
            # self.theta_base = self.theta_base - self.error_movment_intensity * (1 - math.exp(-self.smoothness * self.horizontal_distance_from_center))
            return self.theta_base

    def calculate_servo_1_theta(self):
        if abs(self.target_diameter_pixels) < self.target_actual_diameter_pixels:
            self.servo_1 = self.servo_1 + 3 * self.target_diameter_pixels * math.exp(-self.smoothness)
        if abs(self.target_diameter_pixels) > self.target_actual_diameter_pixels:
            self.servo_1 = self.servo_1 - 3 * self.target_diameter_pixels * math.exp(-self.smoothness)

    def calculate_servo_2_theta(self):
        if abs(self.vertical_distance_from_center) > self.target_positional_tolerance:
            self.servo_2 = self.selected_HAL.get_joint(2) - self.K * self.vertical_distance_from_center * math.exp(-self.smoothness)
        
    async def calculate_theta(self):
        while self.keep_running:
            # if there is an object found
            if self.object_found:
                self.calculate_base_theta()
                self.calculate_servo_1_theta()
                self.calculate_servo_2_theta()                

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