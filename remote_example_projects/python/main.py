# main.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QSlider, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import cv2

from remote_arm_interface import RemoteArmInterface


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robotic Arm Control")
        self.arm = RemoteArmInterface()
        self.init_ui()
        self.arm.stream_camera(self.update_camera_view)
        self.status_label.setText(self.arm.get_status_string())

    def init_ui(self):
        layout = QVBoxLayout()

        self.image_label = QLabel("Loading camera...")
        self.image_label.setFixedSize(640, 480)
        layout.addWidget(self.image_label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 20)
        self.slider.setValue(10)
        layout.addWidget(self.slider)

        self.response_label = QLabel("Waiting for command...")
        layout.addWidget(self.response_label)

        self.status_label = QLabel("Waiting for arm status...")
        layout.addWidget(self.status_label)

        directions = QHBoxLayout()
        directions.addWidget(self.make_button("⬅ Left", lambda: self.move_arm("left")))
        directions.addWidget(self.make_button("⬆ Up", lambda: self.move_arm("up")))
        directions.addWidget(self.make_button("⬇ Down", lambda: self.move_arm("down")))
        directions.addWidget(self.make_button("➡ Right", lambda: self.move_arm("right")))
        layout.addLayout(directions)

        gripper = QHBoxLayout()
        gripper.addWidget(self.make_button("Open Gripper", self.open_gripper))
        gripper.addWidget(self.make_button("Close Gripper", self.close_gripper))
        layout.addLayout(gripper)

        self.setLayout(layout)

    def make_button(self, label, func):
        btn = QPushButton(label)
        btn.clicked.connect(func)
        return btn

    def get_slider_value(self):
        return self.slider.value()

    def move_arm(self, direction):
        move = self.get_slider_value()
        if direction in ["left", "right"]:
            index = 0
            angle = self.arm.get_joint(index)
            self.arm.set_joint(index, angle + move if direction == "right" else angle - move)
        elif direction in ["up", "down"]:
            delta = move / 2
            idxs = [1, 2]
            for idx in idxs:
                angle = self.arm.get_joint(idx)
                self.arm.set_joint(idx, angle + delta if direction == "up" else angle - delta)
        self.response_label.setText(f"Moved {direction} by {move}")

    def open_gripper(self):
        success = self.arm.gripper_open()
        self.response_label.setText("Gripper opened" if success else "Failed to open gripper")

    def close_gripper(self):
        success = self.arm.gripper_close()
        self.response_label.setText("Gripper closed" if success else "Failed to close gripper")

    def update_camera_view(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qt_img)
        self.image_label.setPixmap(pix)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
