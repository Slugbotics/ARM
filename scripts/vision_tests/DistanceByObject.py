import cv2
import warnings
import os
import math
import time
warnings.filterwarnings("ignore")
import termcolor
from threading import Lock
from pathlib import Path
from camera_ports_list import open_camera

default_camera_port = 0

def cal_distance(ref_dist, ref_size, size):
    return (ref_size / size) * ref_dist 

def cal_focalLength(d, W, w):
    return (W * d) / w*2

class DistanceByObject:

    KNOWN_DISTANCE = 48
    PERSON_WIDTH = 15
    CUP_WIDTH = 3
    KEYBOARD_WIDTH = 4
    MOBILE_WIDTH = 3
    SCISSOR_WIDTH = 3

    FONTS = cv2.FONT_HERSHEY_TRIPLEX
    
    show_preview = True
    
    data_mutex = Lock()
    
    upstream_data = None
    
    # Define camera parameters
    screen_width = 1920  # Width of the screen in pixels
    screen_height = 1080  # Height of the screen in pixels
    field_of_view = math.radians(60)  # Field of view angle in radians (60 degrees in this case)
    
    def get_data(self):
        with self.data_mutex:
            return_data = self.upstream_data
            self.upstream_data = None
            return return_data
        
    def is_running(self):
        return self.keep_running
    
    # Warning: ChatGPT is great
    def screen_to_world_3d(self, screen_x, screen_y, distance_to_object):       

        # Calculate the aspect ratio
        aspect_ratio = self.screen_width / self.screen_height

        # Calculate the distances from the camera to the screen
        half_screen_width = distance_to_object * math.tan(self.field_of_view / 2)
        half_screen_height = half_screen_width / aspect_ratio

        # Convert screen coordinates to world coordinates
        world_x = (float)(screen_x / self.screen_width - 0.5) * 2 * half_screen_width
        world_y = (float)(0.5 - screen_y / self.screen_height) * 2 * half_screen_height
        world_z = (float)(-distance_to_object)

        return world_x, world_y, world_z

    def detect_object(self, object):
        classes, scores, boxes = self.model.detect(object,0.4,0.3)
        data_list = []
        for (classid, score, box) in zip(classes, scores, boxes):
            cv2.rectangle(object, box,(0,0,255), 2)
            cv2.putText(object,"{}:{}".format(self.class_names[classid],format(score,'.2f')), (box[0], box[1]-14), self.FONTS,0.6,(0,255,0), 3)

            if classid ==0: #person
                data_list.append([self.class_names[classid], box[2], (box[0], box[1]-2)])
            elif classid == 41: #cup
                data_list.append([self.class_names[classid], box[2], (box[0], box[1]-2)])
            elif classid ==66: #keyboard
                data_list.append([self.class_names[classid], box[2], (box[0], box[1]-2)])
            elif classid ==67: #cell phone
                data_list.append([self.class_names[classid], box[2], (box[0], box[1]-2)])
            elif classid ==76: #scissors
                data_list.append([self.class_names[classid], box[2], (box[0], box[1]-2)])            
                
        return data_list

    def get_filepath(self, filepath):
        if os.path.exists(filepath):
            return filepath
        else:
            absolute_file_path = os.path.join(os.path.dirname(__file__), filepath)
            return str(absolute_file_path)

    def detect_looping(self, _):
        
        self.class_names = []
        classes_path = self.get_filepath("src/classes.txt")
        with open(self.get_filepath("src/classes.txt"), "r") as objects_file:
            self.class_names = [e_g.strip() for e_g in objects_file.readlines()]
            
        yoloNet = cv2.dnn.readNet(self.get_filepath('src/yolov4-tiny.weights'), self.get_filepath('src/yolov4-tiny.cfg'))
        
        self.model = cv2.dnn_DetectionModel(yoloNet)
        self.model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

        person_image_path = os.path.join("src","person.jpg")
        cup_image_path = os.path.join("src","cup.jpg")
        kb_image_path = os.path.join("src","keyboard.jpg")
        moblie_image_path = os.path.join("src","mobile.jpg")
        scissors_image_path = os.path.join("src","scissors.jpg")


        person_data = self.detect_object(cv2.imread(self.get_filepath(person_image_path)))
        person_width_in_rf = person_data[0][1]

        """keyboard_data = self.detect_object(cv2.imread(kb_image_path))
        #print(keyboard_data)
        keyboard_width_in_rf = keyboard_data[1][1]"""

        mobile_data = self.detect_object(cv2.imread(self.get_filepath(moblie_image_path)))
        #print(mobile_data)
        mobile_width_in_rf = mobile_data[0][1]

        scissor_data = self.detect_object(cv2.imread(self.get_filepath(scissors_image_path)))
        #print(scissor_data)
        scissor_width_in_rf = scissor_data[0][1]

        cup_data = self.detect_object(cv2.imread(self.get_filepath(cup_image_path)))
        #print(cup_data)
        cup_width_in_rf = cup_data[1][1]


        focal_person = cal_focalLength(self.KNOWN_DISTANCE, self.PERSON_WIDTH, person_width_in_rf)
        focal_cup = cal_focalLength(self.KNOWN_DISTANCE, self.CUP_WIDTH, cup_width_in_rf)
        #focal_kb = cal_focalLength(self.KNOWN_DISTANCE, self.KEYBOARD_WIDTH, keyboard_width_in_rf)
        focal_mobile = cal_focalLength(self.KNOWN_DISTANCE, self.MOBILE_WIDTH, mobile_width_in_rf)
        focal_scissor = cal_focalLength(self.KNOWN_DISTANCE, self.SCISSOR_WIDTH, scissor_width_in_rf)

        try:
            capture = open_camera(default_camera_port)
            if capture is None:
                self.keep_running = False
            # capture = cv2.VideoCapture(default_camera_port,cv2.CAP_DSHOW)
            while True:
                _,frame = capture.read()

                cv2.imshow('frame',frame)
                
                new_upstream_data = []
                data = self.detect_object(frame) 
                for d in data:
                    print(d)
                    if d[0] =='person':
                        distance = cal_distance(20, 500, d[1])
                        x,y = d[2]
                    elif d[0] =='cup':
                        # distance = cal_distance(focal_cup, self.CUP_WIDTH, d[1])
                        x, y = d[2]  
                    elif d[0] =='cell phone':
                        # distance = cal_distance(focal_mobile, self.MOBILE_WIDTH, d[1])
                        x, y = d[2]
                    elif d[0] =='scissors':
                        # distance = cal_distance(focal_scissor, self.SCISSOR_WIDTH, d[1])
                        x, y = d[2]

                    if(self.show_preview):
                        cv2.rectangle(frame, (x,y-3), (x+150, y+23),(255,255,255),-1)
                        cv2.putText(frame,f"Distance:{format(distance,'.2f')}inchs", (x+5,y+13), self.FONTS, 0.45,(255,0,0), 2)
                        
                    world_x, world_y, world_z = self.screen_to_world_3d(d[2][0], d[2][1], distance)
                    
                    new_upstream_data.append((d[0], world_x, world_y, world_z, distance))
                    
                    with self.data_mutex:
                        self.upstream_data = new_upstream_data
                    
                    print("Distance of {} is {} inchs".format(d[1],distance))

                if(self.show_preview):
                    cv2.imshow('frame',frame)
                exit_key_press = cv2.waitKey(1)

                if (exit_key_press == ord('q')) or not self.keep_running:
                    self.keep_running = False
                    break

            capture.release()
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except cv2.error:
            termcolor.cprint("Select the WebCam or Camera index properly, in my case it is 2","red")
            
    def start_detect(self):
        # Start a separate thread to detect objects.
        self.keep_running = True
        import threading
        detect_thread = threading.Thread(target=self.detect_looping, args=(self,))
        detect_thread.daemon = True  # Set as a daemon thread to exit when the main program exits
        detect_thread.start()

    def stop(self):
        self.keep_running = False

if __name__ == "__main__":
    keep_running = True

    detection = DistanceByObject()

    detection.start_detect()

    while(keep_running):
        data = detection.get_data()
        print("Data: ")
        print(data)
        time.sleep(0.25)
        keep_running = detection.is_running()
        print("keep_running: " + str(keep_running))

