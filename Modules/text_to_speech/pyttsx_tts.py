import pyttsx3
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from Modules.text_to_speech.TTSBase import TTSBase

class pyttsx_tts(TTSBase):
    def __init__(self, rate=150, volume=1.0, voice_index=1):
        # Initialize the pyttsx3 engine
        self.engine = pyttsx3.init()

        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index        

        self.init_engine()

        # For async execution
        self.executor = ThreadPoolExecutor()
        
        self.say_lock = threading.Lock()

    def init_engine(self):
        """Initialize the pyttsx3 engine."""
        engine = pyttsx3.init()
        
        # Set initial speech properties
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)

        # Set the voice (0 = male, 1 = female, typically)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[self.voice_index].id)
        
        return engine

    def say_sync(self, text):
        """Synchronous TTS function."""
        with self.say_lock:
            self.engine = self.init_engine()
            self.engine.say(text)
            self.engine.runAndWait()  # Block until speaking is done
            
            self.engine = None  # VERY IMPORTENT
                    
    def run_say_async(self, text):
        """Run the say_sync function in a new thread."""
        self.say_sync(text)        

    def say_async(self, text):
        """Asynchronous TTS function using threads."""
        if self.engine is not None:
            self.engine.stop()
            self.engine = None
        say_thread = threading.Thread(target=self.run_say_async, args=(text,))
        say_thread.start()

    def set_rate(self, rate):
        """Set the rate of speech."""
        self.rate = rate

    def set_volume(self, volume):
        """Set the volume of speech."""
        self.volume = volume

    def set_voice(self, voice_index):
        """Set the voice (by index)."""
        self.voice_index = voice_index
        
    def stop(self):
        """Stop any ongoing speech."""
        with self.say_lock:
            self.engine.stop()
        
    def say(self, text: str) -> None:
        self.say_async(text)    
    
    def write_line(self, text: str) -> None: 
        print("Arm Says: " + text)
        self.say_async(text)
        
        