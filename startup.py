# put in ~.bashrc
# this will open on terminal open

import os
import socket
from tkinter import Tk, filedialog, StringVar, IntVar, BooleanVar
from tkinter.ttk import Button, LabelFrame, Label, Entry, Frame, Checkbutton
from tkinter.messagebox import showerror
import subprocess
import sys

is_demo = True

class ArmStartupGUI:

    def get_wlan0_ip_ifconfig(self):
        try:
            output = subprocess.check_output(["ifconfig", "wlan0"], text=True)
            lines = output.splitlines()
            for line in lines:
                if "inet " in line:
                    ip_address = line.split("inet ")[1].split(" ")[0]
                    return ip_address
        except subprocess.CalledProcessError:
            return "<failed to find IP>"  # Return None if ifconfig fails

    def __submit(self):
        print("opening app")

        # Open another Python program
        subprocess.Popen(['python', 'ArmTeam/main.py'])  # Replace 'other_program.py' with the actual file name

        # Close the current Python program
        sys.exit()

    def __quit(self):
        sys.exit()

    def __init__(self):
        self.root = Tk()
        self.root.title("Arm Team Startup Popup")

        # Frame for file selection
        self.frame = LabelFrame(self.root, text="Arm Team PI")
        self.frame.pack(padx=200, pady=100)
        # Python Program to Get IP Address
        hostname = socket.gethostname()
        IPAddr = self.get_wlan0_ip_ifconfig()
        text = "To debug: ssh " + hostname + "@" + IPAddr
        self.label = Label(self.frame , text=text)
        self.label.pack(side="left", fill="y")

        # Submit button
        self.submit_button = Button(self.root, text="Run App", command=self.__submit)
        self.submit_button.pack(padx=10, pady=10)
        
        if not is_demo:
            self.quit_button = Button(self.root, text="Quit", command=self.__quit)
            self.quit_button.pack(padx=10, pady=10)

        self.root.mainloop()

# Run the GUI
gui = ArmStartupGUI()
