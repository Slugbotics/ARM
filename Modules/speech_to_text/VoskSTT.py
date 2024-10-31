import vosk
import pyaudio
import json
import threading
import os
from collections import deque

from Modules.speech_to_text.STTBase import STTBase

from Modules.speech_to_text.VoskModelDownloader import download_and_extract_vosk_model

class VoskSTT(STTBase):

    DEFAULT_MODEL_SMALL = "vosk-model-small-en-us-0.15" # small model
    DEFAULT_MODEL_LARGE = "vosk-model-en-us-0.22"       # big model

    DEFAULT_MODEL_DIRECTORY = "." + os.path.sep + "vosk_models"

    print_heard_text = True

    def __init__(self, selected_default_model = None, model_path=None):
        self.model_path = model_path
        self.selected_default_model = selected_default_model
        self.model = None
        self.recognizer = None
        self.p = None
        self.stream = None
        self.active = False
        self.listening_thread = None
        self.text_deque = deque()
        self.text_lock = threading.Lock()
        
        if self.selected_default_model is None:
            self.selected_default_model = VoskSTT.DEFAULT_MODEL_SMALL
        
    def get_default_model_path(self) -> str:
        return VoskSTT.DEFAULT_MODEL_DIRECTORY + os.path.sep + self.selected_default_model

    def get_default_model_download_url(self) -> str:
        return "https://alphacephei.com/vosk/models/" + self.selected_default_model + ".zip"
    
    def set_selected_default_model(self, selected_default_model: str) -> None:
        self.selected_default_model = selected_default_model

    def start(self) -> bool:
        """Load the Vosk model and initialize audio input, but don't start listening yet."""

        if self.model_path is None:
            print("VoskTTS.vosk model does not exist, downloading basic model from: " + self.get_default_model_download_url())
            print("If you want to select a different model, choose one from:")
            print("https://github.com/alphacep/vosk-space/blob/master/models.md")
            print("and pass the path to that model download location to the constructor of this VoaskTTS")
            self.model_path = self.get_default_model_path()
            if not os.path.exists(self.model_path):
                self.model_path = download_and_extract_vosk_model(self.get_default_model_download_url(), VoskSTT.DEFAULT_MODEL_DIRECTORY)

        try:
            self.model = vosk.Model(self.model_path)
            self.p = pyaudio.PyAudio()
            return True
        except Exception as e:
            print(f"Error starting TTS: {e}")
            return False

    def stop(self) -> bool:
        """Release any resources and clean up."""
        try:
            if self.stream:
                self.stream.close()
            if self.p:
                self.p.terminate()
            if self.listening_thread:
                self.listening_thread.join()  # Ensure the listening thread finishes before shutting down.
            self.model = None
            self.recognizer = None
            self.active = False
            return True
        except Exception as e:
            print(f"Error stopping TTS: {e}")
            return False

    def is_active(self) -> bool:
        """Check if the microphone is currently listening."""
        return self.active

    def activate(self) -> bool:
        """Start listening to the microphone on a new thread."""
        if not self.model or self.active:
            return False

        # Start the listening in a separate thread
        self.active = True
        self.listening_thread = threading.Thread(target=self.run_listen)
        self.listening_thread.start()
        return True

    def deactivate(self) -> bool:
        """Stop the microphone listening."""
        self.active = False
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join()  # Wait for the listening thread to finish
        return True

    def get_microphone_name(self):
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        for i in range(0, num_devices):
            device_info = self.p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                return device_info.get('name')
        return "No microphone found"

    def run_listen(self):
        """Internal method for handling the microphone listening in a separate thread."""
        try:
            # Initialize the recognizer and audio stream
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=16000,
                                      input=True,
                                      frames_per_buffer=4096)
            self.stream.start_stream()

            # Print the name of the microphone
            mic_name = self.get_microphone_name()
            print(f"VoskTTS - Speech to text Using microphone: {mic_name}")

            # Start listening to the microphone
            while self.active:
                data = self.stream.read(4096, exception_on_overflow=False)
                if len(data) == 0:
                    break

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    self.on_speech_detected(result.get('text', ''))
                else:
                    # You could handle partial results here if needed
                    pass

        except Exception as e:
            print(f"Error during listening: {e}")
        finally:
            self.active = False

    def on_speech_detected(self, text: str):
        """This method will handle speech detection output."""
        if text:
            if VoskSTT.print_heard_text:
                print(f"Detected speech: {text}")
            with self.text_lock:
                self.text_deque.appendleft(text)
    
    def get_last_sentence(self) -> str:
        with self.text_lock:
            if self.text_deque:
                return self.text_deque.pop()
            else:
                return None

    def get_newst_sentence(self) -> str:
        with self.text_lock:
            if self.text_deque:
                return self.text_deque.popleft()
            else:
                return None

    def read_line(self) -> str:
        return self.get_last_sentence()

if __name__ == "__main__":
    # Example Usage
    tts = VoskSTT(model_path="path_to_vosk_model")
    tts.start()  # Load the model

    # Activate the speech recognition in a non-blocking way
    tts.activate()  

    # Other code can continue executing while Vosk listens in the background...
    try:
        # You can keep the program running or do other tasks
        while True:
            pass
    except KeyboardInterrupt:
        tts.deactivate()  # Stop listening
        tts.stop()  # Cleanup resources