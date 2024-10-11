import pyttsx3

from Modules.Base.TextOut import TextOut

class TTSBase(TextOut):
        
    def say(self, text: str) -> None: ...
    
    def say_async(self, text: str) -> None: ...
    
    def write_line(self, text: str) -> None: ...