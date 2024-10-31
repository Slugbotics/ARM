import pyttsx3
import asyncio
from concurrent.futures import ThreadPoolExecutor

from Modules.text_to_speech.TTSBase import TTSBase

class pyttsx_tts(TTSBase):
    def __init__(self, rate=150, volume=1.0, voice_index=1):
        # Initialize the pyttsx3 engine
        self.engine = pyttsx3.init()

        # Set initial speech properties
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)

        # Set the voice (0 = male, 1 = female, typically)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[voice_index].id)

        # For async execution
        self.executor = ThreadPoolExecutor()

    def say_sync(self, text):
        """Synchronous TTS function."""
        self.engine.say(text)
        self.engine.runAndWait()  # Block until speaking is done

    async def say_async(self, text):
        """Asynchronous TTS function using asyncio."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.say_sync, text)

    def set_rate(self, rate):
        """Set the rate of speech."""
        self.engine.setProperty('rate', rate)

    def set_volume(self, volume):
        """Set the volume of speech."""
        self.engine.setProperty('volume', volume)

    def set_voice(self, voice_index):
        """Set the voice (by index)."""
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[voice_index].id)
        
    def say(self, text: str) -> None:
        self.say_sync(text)    
    
    def write_line(self, text: str) -> None: 
        self.say_sync(text)
        
        