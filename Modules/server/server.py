import os
import sys
import time
import socket
from random import random 
from flask import Flask, render_template, Response, request, jsonify, stream_with_context
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import numpy as np
import cv2
from flask_sock import Sock
import json

from Controllers.Controller import Controller
from HALs.HAL_base import HAL_base
from Modules.server.ServerBase import ServerBase
from Vision.ColorObjectIdentifier import ColorObjectIdentifier

class Server(ServerBase):

    def __init__(self, controller: Controller, selected_HAL: HAL_base, objectIdentifier: ColorObjectIdentifier = None):
        self.controller: Controller = controller
        self.selected_HAL: HAL_base = selected_HAL
        self.objectIdentifier: ColorObjectIdentifier = objectIdentifier
        
        self.app = Flask(__name__)
        self.sock = Sock(self.app)
        
        self.current_mode = 'Vision'
        self.clients = []
        
        self.nextMotor = 0
        
        self.rotate_move_amount = 30
        self.current_base_rotation = 0
        
        self.arm_bend_amount = 30
        self.current_arm_bend = 0
        self.max_arm_bend = 180
        
        # default 
        # self.color_lower_bound = np.array([100, 150, 50])
        # self.color_upper_bound = np.array([140, 255, 255])

    def move_joint_random(self):
        degree = random() * 360
        self.selected_HAL.set_joint(self.nextMotor, degree)            
        self.nextMotor = (self.nextMotor + 1) % self.selected_HAL.joint_count()
        if(self.nextMotor == 0):
            self.nextMotor = 1

    def get_camera_image(self):
        # Get the HSV image using the provided function
        hsv_image = self.selected_HAL.get_arm_cam_img_hsv()

        if hsv_image is None:
            print("get_camera_image - hsv_image is None!")
            return None
        
        # Convert the HSV image back to RGB color space
        rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_BGR2RGB)

        rgb_image = cv2.flip(rgb_image, 0)
        
        # Create a PIL image from the numpy array
        pil_image = Image.fromarray(rgb_image)
        buffer = BytesIO()
        
        # Save the image to the buffer in JPEG format
        pil_image.save(buffer, format='JPEG')
        
        # Now, buffer.getvalue() contains the encoded JPEG image data
        encoded_image_data = buffer.getvalue()
        
        return encoded_image_data

    def set_bend_verticle(self, new_bend):
        print("Moving verticle")
        self.selected_HAL.set_joint(1, new_bend / 2)
        self.selected_HAL.set_joint(2, new_bend / 2)

    def set_bend_horizontal(self, new_bend):
        print("Moving horizontal")
        self.selected_HAL.set_joint(0, new_bend)

    def move_up(self, amount):
        print("Moving up")
        new_arm_bend = (self.current_arm_bend + amount)
        if(abs(new_arm_bend) > self.max_arm_bend):
            return
        self.current_arm_bend = new_arm_bend

        print(f"current_arm_bend: {self.current_arm_bend}")
        self.set_bend_verticle(self.current_arm_bend)
        # move_joint_random()

    def move_down(self, amount):
        print("Moving down")
        new_arm_bend = (self.current_arm_bend - amount)
        if(abs(new_arm_bend) > self.max_arm_bend):
            return
        self.current_arm_bend = new_arm_bend    
        
        print(f"current_arm_bend: {self.current_arm_bend}")
        self.set_bend_verticle(self.current_arm_bend)
        # move_joint_random()

    def move_left(self, amount):
        print("Moving left")
        self.current_base_rotation = (self.current_base_rotation + amount) % 360

        print(f"current_base_rotation: {self.current_base_rotation}")
        self.set_bend_horizontal(self.current_base_rotation)
        # move_joint_random()

    def move_right(self, amount):
        print("Moving right")
        self.current_base_rotation = (self.current_base_rotation - amount)
        if(self.current_base_rotation < 0):
            self.current_base_rotation = 360 + self.current_base_rotation
        
        print(f"current_base_rotation: {self.current_base_rotation}")
        self.set_bend_horizontal(self.current_base_rotation)
        # move_joint_random()

    def grab(self):
        print("Grabbing")
        return self.selected_HAL.gripper_close()

    def release(self):
        print("Releasing")
        return self.selected_HAL.gripper_open()

    def set_color_bounds(self, color_lower_bound: np.array, color_upper_bound: np.array):
        if(self.objectIdentifier != None):
            self.objectIdentifier.set_color_lower_bound(color_lower_bound)
            self.objectIdentifier.set_color_upper_bound(color_upper_bound)
        else:
            print("self.objectIdentifier not found!")

    def vison_tar_red(self):
        print("Targeting red")
        color_lower_bound = np.array([0, 100, 100])
        color_upper_bound = np.array([10, 255, 255])
        self.set_color_bounds(color_lower_bound, color_upper_bound)

    def vison_tar_green(self):
        print("Targeting green")
        color_lower_bound = np.array([50, 100, 100])
        color_upper_bound = np.array([70, 255, 255])
        self.set_color_bounds(color_lower_bound, color_upper_bound)

    def vison_tar_blue(self):
        print("Targeting blue")
        # ChatGPT
        # color_lower_bound = np.array([110, 100, 100])
        # color_upper_bound = np.array([130, 255, 255])

        # Mr.Sam
        color_lower_bound = np.array([100, 150, 50])
        color_upper_bound = np.array([140, 255, 255])
        self.set_color_bounds(color_lower_bound, color_upper_bound)

    # Placeholder function to control the robotic arm
    def control_robotic_arm(self, command):
        if(len(command) < 100):
            print(f"Executing command: {command}")
        # Add your robotic arm control logic here
        time.sleep(1)  # Simulate some delay
        return_command = command

        if command == 'move_up':
            self.move_up(self.arm_bend_amount)
        elif command == 'move_down':
            self.move_down(self.arm_bend_amount)
        elif command == 'move_left':
            self.move_left(self.arm_bend_amount)
        elif command == 'move_right':
            self.move_right(self.arm_bend_amount)
        elif command == 'grab':
            result = self.grab()
            return_command += f" sucess({result})"
        elif command == 'release':
            result = self.release()
            return_command += f" sucess({result})"
        elif command == 'vison_tar_red':
            self.vison_tar_red()
        elif command == 'vison_tar_green':
            self.vison_tar_green()
        elif command == 'vison_tar_blue':
            self.vison_tar_blue()
        else:
            print("Unknown command")
            return_command = "Unknown command"

        return f"Command {return_command} executed"

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def setup_routes(self):
        self.app.route('/control', methods=['POST'])(self.control)
        self.app.route('/')(self.index)
        self.app.route('/video_feed')(self.video_feed)
        self.sock.route('/mode')(self.mode)

    def control(self):
        command = request.json.get('command')
        result = self.control_robotic_arm(command)
        return jsonify({'status': 'success', 'result': result})

    def index(self):
        local_ip = self.get_local_ip()
        return render_template('index.html', local_ip=local_ip, current_mode=self.current_mode)

    def generate(self):
        while True:
            hsv_image = self.selected_HAL.get_arm_cam_img_hsv()
            
            # Convert the HSV image to BGR for JPEG encoding
            bgr_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)

            # Encode the BGR image to JPEG format
            ret, jpeg_image = cv2.imencode('.jpg', bgr_image)

            if not ret:
                continue  # Skip the frame if encoding fails

            # Yield the JPEG image as a byte stream
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg_image.tobytes() + b'\r\n\r\n')

    def video_feed(self):
        return Response(self.generate(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def mode(self, ws):
        self.clients.append(ws)
        while True:
            data = ws.receive()
            if data:
                self.current_mode = json.loads(data).get('mode', self.current_mode)
                for client in self.clients:
                    if client != ws:
                        client.send(json.dumps({'mode': self.current_mode}))
                ws.send(json.dumps({'mode': self.current_mode}))

    def get_current_mode(self):
        return self.current_mode

    def start_server(self) -> bool:
        print("connect to: \"http://127.0.0.1:5000/video_feed\" to see the image feed")
        self.setup_routes()
        self.app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)          
        return True

    def stop_server(self) -> bool:
        #self.app.shutdown()
        return True


