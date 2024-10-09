import cv2

from Modules.Base.ImageDisplay import ImageDisplay

class ImageDisplay(ImageDisplay):
    
    window_name: str = "frame"
    
    def __init__(self, window_name: str) -> None:
        self.window_name = window_name

    # display a frame to the twitch chat
    def write_image(self, image: cv2.typing.MatLike) -> None:
        self.display_image(image)

    def display_image(self, img: cv2.typing.MatLike) -> None:
        cv2.imshow(self.window_name, img)