from Modules.Base.TextIn import TextIn
from Modules.Base.TextOut import TextOut

class Console(TextIn, TextOut):
    def read_line(self, prompt: str = "") -> str:
        return input(prompt)
    
    def write_line(self, item: str) -> None:
        print(item)