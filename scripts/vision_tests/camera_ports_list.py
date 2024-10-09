import cv2
    
def open_camera(default_camera_port = 0):
    capture = cv2.VideoCapture(default_camera_port)
    capture_works = True
    if not capture.isOpened():
        capture_works = False
    else:
        is_reading, img = capture.read()
        if not is_reading:
            capture_works = False
    
    if capture_works:
        return capture
    
    print("camera port " + str(default_camera_port) + " is not working, attempting to find working port.")

    working_ports = get_working_ports()
    if len(working_ports) <= 0:
        print("no working camera ports have been identified, please attach a USB camera to continue.")
        return None
    
    print("Found " + str(len(working_ports)) + " working camera ports: [" + str(working_ports) + "] selecting port: " + working_ports[0])

    capture = cv2.VideoCapture(working_ports[0])
    return capture

def get_working_ports():
    available_ports,working_ports,non_working_ports = list_ports()
    return working_ports
    
def list_ports():
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    """
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 6: # if there are more than 5 non working ports stop the testing. 
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                working_ports.append(dev_port)
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports,non_working_ports

if __name__ == "__main__":
    available_ports,working_ports,non_working_ports = list_ports()
    print("Available ports: ", available_ports)
    print("Working ports: ", working_ports)
    print("Non working ports: ", non_working_ports)
    print("Total ports: ", len(available_ports)+len(working_ports)+len(non_working_ports))