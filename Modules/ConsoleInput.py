from collections import deque
import threading
from typing import Callable

from Modules.Base.TextIn import TextIn
from Modules.Base.TextOut import TextOut

class ConsoleInput(TextIn, TextOut):
    
    def __init__(self, on_text_recived: Callable[[str], None] = None, input_prompt: str = None) -> None:
        self.input_prompt = input_prompt
        self.on_text_recived = on_text_recived
        self.message_queue = deque()
    
    def read_looping(self, prompt: str = "") -> str:
        return input(prompt)
    
    def run_input_looping(self):
        self.looping = True
        while self.looping:
            try:
                input_str = input(self.input_prompt)
                self.message_queue.append(input_str)
                self.on_text_recived(input_str)                
            except (KeyboardInterrupt, EOFError):
                self.looping = False
                print("\nExiting input loop.")
                raise KeyboardInterrupt


    def run_input_looping_async(self):
        self.loop_thread = threading.Thread(target=self.run_input_looping)
        self.loop_thread.start()
    
    def read_stored_message(self) -> str:
        if len(self.message_queue) == 0:
            return None
        return self.message_queue.popleft()
    
    def cleanup(self):
        self.looping = False
        
    def stop(self):
        self.cleanup()
    
    def read_line(self, prompt: str = "") -> str:
        return input(prompt)
    
    def write_line(self, item: str) -> None:
        print(item)