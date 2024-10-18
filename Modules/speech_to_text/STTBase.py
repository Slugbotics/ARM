from Modules.Base.TextIn import TextIn

class STTBase(TextIn):
        
    # load the speech recognition engine
    def start(self) -> bool: ...
    
    # unload the speech recognition engine
    def stop(self) -> bool: ...

    # if this speech recognition model is currently listening
    def is_active(self) -> bool: ...

    # start listening
    def activate(self) -> bool: ...

    # stop listening
    def deactivate(self) -> bool: ...
    
    # read the oldest line of text that this has recived.
    # Will return None if no lines are in the queue
    def get_last_sentence(self) -> str: ...

    # read the newst line of text that this has recived.
    # Will return None if no lines are in the queue
    def get_newst_sentence(self) -> str: ...

    # wrapper around get_last_sentence
    def read_line(self) -> str: ...