import cv2

class ImageProducer:
    def capture_image(self) -> cv2.typing.MatLike: ...
    """ Captures an image from the camera and returns it as a cv2 Mat in RGB format. """