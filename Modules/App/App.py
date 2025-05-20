import colorsys
import math

import cv2
import numpy as np
import sympy as sym
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.lang.builder import Builder

from kivy.properties import ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel

from Controllers import FollowClaw
from Controllers.Base.Controller import Controller
from Controllers.FollowClaw import coordinate_input
from HALs.HAL_base import HAL_base
from Modules.App.AppBase import AppBase
from Vision.ColorObjectIdentifier import ColorObjectIdentifier
from kivy.properties import StringProperty, Clock, NumericProperty, Property, ObjectProperty, BooleanProperty

class Test(TabbedPanel):
    cameraUpdateEvent = 0
    canvas_img_texture = ObjectProperty('')
    canvas_mask_texture = ObjectProperty('')
    colorX = NumericProperty(0)
    colorY = NumericProperty(0)
    value = [0, 0, 0]
    showVal = ['0', '0', '0']
    m1 = StringProperty('0')
    m2 = StringProperty('0')
    m3 = StringProperty('0')
    pressed = False
    red = NumericProperty(1)
    blue = NumericProperty(0)
    green = NumericProperty(0)
    posX = NumericProperty(0)
    addition = 1
    finalRed = NumericProperty(1)
    finalBlue = NumericProperty(0)
    finalGreen = NumericProperty(0)
    light = 0
    theta = math.radians(13.5)
    cost = math.cos(theta)
    sint = math.sin(theta)
    armAngles = [0, 0, 0]
    m2PosStr = StringProperty("0")
    m1PosStr = StringProperty("0")
    basePosStr = StringProperty("0")
    tx = StringProperty("0")
    ty = StringProperty("0")
    tz = StringProperty("0")
    dx = 0
    dy = 0
    dz = 0
    x_direction_x = NumericProperty(0)
    x_direction_y = NumericProperty(0)
    y_direction_x = NumericProperty(0)
    y_direction_y = NumericProperty(0)
    z_direction_z = NumericProperty(0)
    pick_step = StringProperty("Pick Up")
    pick_vision = True
    
    moveEvent = 0

    def __init__(self, hal: HAL_base, controller: FollowClaw, vision: ColorObjectIdentifier, **kwargs, ):


        self.hal = hal
        self.controller = controller
        self.vision = vision

        img = self.hal.get_arm_cam_img_hsv()
        dframe, dmask = self.controller.get_frame_mask()
        w, h, _ = img.shape
        texture = Texture.create(size=(h, w))
        texture2 = Texture.create(size=(h, w))



        texture.blit_buffer(img.flatten(), colorfmt='bgr', bufferfmt='ubyte')
        if isinstance(dmask, bool):
            texture2.blit_buffer(dframe.flatten(), colorfmt='bgr', bufferfmt='ubyte')
        else:
            texture2.blit_buffer(dmask.flatten(), colorfmt='bgr', bufferfmt='ubyte')
        self.canvas_img_texture = texture
        self.canvas_mask_texture = texture2
        Clock.schedule_once(self.posxafterinit, 2)
        print("x")
        super(Test, self).__init__(**kwargs)
        self.cameraUpdateEvent = Clock.schedule_interval(self.updateVision, 0.1)


    def posxafterinit(self, dt):
        self.posX = self.size[0] / 2 / 2

    def pick_task(self):
        if self.pick_step =="Pick Up":
            self.pick_vision = False
        elif self.pick_step =="Place":
            coordinate_input(30,0,15,self.hal,False)
        elif  self.pick_step =="Reset":
            coordinate_input(0,0,40,self.hal,False)
            self.pick_vision = True

    def mod_pick_state(self):
        if self.pick_step == "Reset":
            self.pick_step = "Pick Up"
        elif self.pick_step =="Pick Up":
            self.pick_step = "Place"
        elif self.pick_step =="Place":
            self.pick_step = "Reset"
        

    controller_start=False
    def updateVision(self, dt):
        # if self.tab_list.index(self.get_current_tab()) == 3:
        #     self.controller.controller_state(True)
        # else:
        #     self.controller.controller_state(False)
        if self.tab_list.index(self.get_current_tab()) == 2 and self.pick_vision:
            self.controller.pause_state(True)
            h2, s2, v2 = colorsys.rgb_to_hsv(self.finalRed / 255, self.finalGreen / 255, self.finalBlue / 255)
            print(colorsys.rgb_to_hsv(self.finalRed / 255, self.finalGreen / 255, self.finalBlue / 255))
            # define the range for detecting blue color
            self.vision.update_range(np.array([h2 * 179 - 20, s2 * 255 - 50, 50]),np.array([h2 * 179 + 20, s2 * 255 + 50, 255]))
            if self.controller_start == False:
                self.controller.start()
                self.controller_start=True
            img = cv2.resize(self.hal.get_arm_cam_img_hsv(), (0,0), fx=0.25, fy=0.25) 
            w, h, _ = img.shape
            texture = Texture.create(size=(h, w))
            texture2 = Texture.create(size=(h, w))
            texture.blit_buffer(img.flatten(), colorfmt='bgr', bufferfmt='ubyte')
            self.canvas_img_texture = texture
            dframe, dmask = self.controller.get_frame_mask()
            if isinstance(dmask, bool):
                texture2.blit_buffer(dframe.flatten(), colorfmt='bgr', bufferfmt='ubyte')
            else:
                texture2.blit_buffer(dmask.flatten(), colorfmt='bgr', bufferfmt='ubyte')
            self.canvas_mask_texture = texture2
        else:
            self.controller.pause_state(False)
        pass

    def modX(self, x):
        self.dx = x
        self.tx = str(x)[0:4]
        self.x_direction_x = x * math.cos(self.theta)
        self.x_direction_y = x * math.sin(self.theta)

    def modY(self, y):
        self.dy = y
        self.ty = str(y)[0:4]
        self.y_direction_x = y * math.cos(self.theta)
        self.y_direction_y = y * math.sin(self.theta)

    def modZ(self, z):
        self.dz = z
        self.tz = str(z)[0:4]
        self.z_direction_z = z

    def coords(self):
        coordinate_input(self.dx, self.dy, self.dz,self.hal,False)

    def on_touch_move(self, touch):
        print(str(touch.x) + " " + str(touch.y))
        print((self.size[1]-50-(self.size[1] - 50) * .10-(self.size[1]-50)*.2)/2)
        radius = ((self.size[1]-70-(self.size[1] - 70) * .10-(self.size[1]-70)*.2)/2)
        if (self.tab_list.index(
                self.get_current_tab()) == 2)and touch.y > 0 and touch.y < (self.size[1] - 100) * .10 and touch.x > 0 + (
                self.size[0] * .5 * .05) and touch.x < (self.size[0] * .5) - (self.size[0] * .5 * .05):
            self.posX = touch.x
            self.light = (touch.x - ((self.size[0] / 2) - (self.size[0] * .5 * .05)) / 2) / (
                    (self.size[0] / 2 - (self.size[0] * .5 * .05)) / 2)

            self.finalRed = max(0, min(1, self.red - self.light))
            self.finalBlue = max(0, min(1, self.blue - self.light))
            self.finalGreen = max(0, min(1, self.green - self.light))
        if (self.tab_list.index(
                self.get_current_tab()) == 2) and math.dist(
                [radius, ((self.size[1] - 70) * .10) + radius],
                [touch.x, touch.y]) < radius - 20 and math.dist(
            [radius, (self.size[1] - 70) * .10 + radius], [touch.x, touch.y]) > radius * .35:
            self.colorX = touch.x
            self.colorY = touch.y
            angle_rad = -math.atan2(touch.y - (radius+(self.size[1] - 70) * .10),
                                    touch.x - (radius)) + math.radians(60)
            print(str(touch.x) + " " + str(touch.y))
            self.red = max(0, min(255, int(math.cos(angle_rad - math.pi / 6) * 127 + 128))) / 255
            self.green = max(0, min(255, int(math.cos(angle_rad + 2 * math.pi / 3 - math.pi / 6) * 127 + 128))) / 255
            self.blue = max(0, min(255, int(math.cos(angle_rad + 4 * math.pi / 3 - math.pi / 6) * 127 + 128))) / 255
            self.finalRed = max(0, min(1, self.red - self.light))
            self.finalBlue = max(0, min(1, self.blue - self.light))
            self.finalGreen = max(0, min(1, self.green - self.light))

    def manualMove(self, dt):
        for i in range(len(self.value)):
            self.armAngles[i] = self.hal.get_joint(i)
            self.hal.set_joint(i, self.hal.get_joint(i) + self.value[i])
        self.basePosStr = str(self.armAngles[0])
        self.m1PosStr = str(self.armAngles[1])
        self.m2PosStr = str(self.armAngles[2])

    def open_claw(self):
        print("opening claw")
    def close_claw(self):
        print("closing claw")
    def add(self, index):
        self.value[index] = 1
        self.moveEvent = Clock.schedule_interval(self.manualMove, 0.1)
        self.stringify(index)

    def cancel(self, index):
        self.value[index] = 0
        self.moveEvent.cancel()
        self.stringify(index)

    def subtract(self, index):
        self.value[index] = -1
        self.moveEvent = Clock.schedule_interval(self.manualMove, 0.1)
        self.stringify(index)

    def stringify(self, index):
        self.showVal[index] = str(self.value[index])
        self.m1 = self.showVal[0]
        self.m2 = self.showVal[1]
        self.m3 = self.showVal[2]

    pass


class App(AppBase):
    def __init__(self, controller: Controller, selected_HAL: HAL_base, vision: ColorObjectIdentifier, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.selected_HAL = selected_HAL
        self.vision = vision

    def build(self):
        Builder.load_file("Modules/App/res/app.kv")
        return Test(self.selected_HAL, self.controller, self.vision)

    def start_app(self):
        print('lol')
        self.run()
        print("App Started")
        return True

    # return False

    def stop_app(self):
        return True
    # return False
