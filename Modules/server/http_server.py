import threading
from typing import Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uvicorn import Config, Server
import cv2
import base64
import numpy as np

from Controllers.Controller import Controller
from HALs.HAL_base import HAL_base
from Modules.server.ServerBase import ServerBase
from Vision.ColorObjectIdentifier import ColorObjectIdentifier
from Config.ArmRuntime import ArmRuntime

class HTTPServer(ServerBase):

    class JointRequest(BaseModel):
        joint_index: int
        joint_angle: float

    def __init__(self, runtime: ArmRuntime, host_port: int):
        super().__init__()
        self.controller: Controller = runtime.selected_controller
        self.selected_HAL: HAL_base = runtime.selected_HAL
        self.objectIdentifier: ColorObjectIdentifier = runtime.selected_object_identifier
        self.runtime: ArmRuntime = runtime
        self.host_port = host_port
        self.server_thread = None
        self.keep_running = False
        
        self.app = FastAPI()
        self.templates = Jinja2Templates(directory="Modules/server/templates")
        self.setup_routes()
        
    def setup_routes(self):
        self.app.get("/", response_class=HTMLResponse)(self.home_page)
        self.app.post("/set_joint")(self.set_joint)
        self.app.get("/get_joint")(self.get_joint)
        self.app.get("/joint_count")(self.joint_count)
        self.app.get("/get_arm_cam_img_rgb")(self.get_arm_cam_img_rgb)
        self.app.get("/get_arm_cam_stream")(self.get_arm_cam_stream)
        self.app.get("/get_camera_focal_length")(self.get_camera_focal_length)
        self.app.post("/gripper_open")(self.gripper_open)
        self.app.post("/gripper_close")(self.gripper_close)
        self.app.get("/status_string")(self.get_status_string)
    
    def home_page(self, request: Request):
        return self.templates.TemplateResponse("index.html", {"request": request})
    
    def set_joint(self, request: JointRequest):
        success = self.selected_HAL.set_joint(request.joint_index, request.joint_angle)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid joint index")
        return {"success": True}
    
    def get_joint(self, joint_index: int):
        angle = self.selected_HAL.get_joint(joint_index)
        if angle is None:
            raise HTTPException(status_code=400, detail="Invalid joint index")
        return {"joint_angle": angle}
    
    def joint_count(self):
        return {"joint_count": self.selected_HAL.joint_count()}
    
    def get_camera_image(self):
        # img = np.zeros((480, 640, 3), dtype=np.uint8)
        # img = cv2.putText(img, 'Camera Feed', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        rgb_image = self.selected_HAL.get_arm_cam_img_rgb()
        
        # Convert the HSV image to BGR for JPEG encoding
        bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)

        # Encode the BGR image to JPEG format
        ret, jpeg_image = cv2.imencode('.jpg', bgr_image)
        return base64.b64encode(jpeg_image).decode('utf-8')
    
    def get_arm_cam_img_rgb(self):
        img_base64 = self.get_camera_image()
        return {"image": img_base64}
    
    def generate_mjpeg(self):
        while self.keep_running:
            # img = np.zeros((480, 640, 3), dtype=np.uint8)
            # img = cv2.putText(img, 'Camera Stream', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            rgb_image = self.selected_HAL.get_arm_cam_img_rgb()
        
            # Convert the HSV image to BGR for JPEG encoding
            bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)

            # Encode the BGR image to JPEG format
            ret, jpeg_image = cv2.imencode('.jpg', bgr_image)
            
            frame = jpeg_image.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    def get_arm_cam_stream(self):
        return StreamingResponse(self.generate_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")
    
    def get_camera_focal_length(self):
        return {"focal_length": self.selected_HAL.get_camera_focal_length()}
    
    def gripper_open(self):
        return {"success": self.selected_HAL.gripper_open()}
    
    def gripper_close(self):
        return {"success": self.selected_HAL.gripper_close()}
    
    def get_status_string(self):
        status_string = "status"
        if self.controller is not None:
            visible_objects = self.controller.get_visible_object_labels()            
            status_string = "Controler: " + self.controller.__class__.__name__ + " can see: " + str(visible_objects) + "\n"
            status_string += "Object Identifier: " + self.objectIdentifier.__class__.__name__ + "\n"
        return {"status_string": status_string}
    
    def start_server(self, print_local_ip_address: bool = True) -> bool:
        
        self.keep_running = True
        
        host: str = "127.0.0.1"
        port: int = self.host_port
        
        if print_local_ip_address:
            import socket
            host = socket.gethostbyname(socket.gethostname())
            print("local ip address: \"" + host + "\"")
        
        # the logger on this needs to have access to the normal stdout, so we need to disable our custom one if we are using it
        if self.runtime.selected_logger is not None:
            self.runtime.selected_logger.stop()
        
        config = Config(app=self.app, host=host, port=port, log_level="critical") # if you want to see http requests, log_level="info"
        self.server = Server(config)
        
        # and reenable it
        if self.runtime.selected_logger is not None:
            self.runtime.selected_logger.start()

        # Run the server in a separate thread
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()
        print("connect to: \"http://" + host + ":" + str(port) + "/\" to see the image feed")
        return True

    def stop_server(self) -> bool:
        #self.app.shutdown()
        did_shutdown = self.keep_running
        self.keep_running = False
        if self.server:
            self.server.should_exit = True
        if self.server_thread:
            self.server_thread.join()
        return did_shutdown
        