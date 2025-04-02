import threading
import sys
from typing import List
from typing import Callable
from enum import Enum

class Commands:
    
    COMMAND_START_CHAR = "/"
    
    class Trust(Enum):
        UNKNOWN = 0
        SUS = 1
        TRUSTED = 2
        SELF = 4
    
    def __init__(self) -> None:
        self.commands = {}
        self.looping = False
        self.loop_thread = None

    def add_command(self, name: str, func: Callable[[str], None], help_text: str="", required_trust: Trust = Trust.SUS, aliases: List[str]=None) -> None:
        # Add command and its aliases
        aliases = aliases or []
        all_names = [name] + aliases
        for cmd_name in all_names:
            if not cmd_name.startswith(self.COMMAND_START_CHAR):
                cmd_name = self.COMMAND_START_CHAR + cmd_name
            self.commands[cmd_name] = {"func": func, "help": help_text, "required_trust": required_trust}

    def run_command(self, command_str: str, caller_trust: Trust, caller: object) -> bool:
        
        #check if the command starts with the command start character
        if not command_str.startswith(self.COMMAND_START_CHAR):
            return False
        
        # Parse command and args
        parts = command_str.split()
        if not parts:
            return False
        cmd_name, args = parts[0], parts[1:]
        command = self.commands.get(cmd_name)
        if command:
            # Call the command's function with the argument string if it has enough trust
            required_trust = command["required_trust"]
            if caller_trust.value < required_trust.value:
                print(f"{caller.__name__} is unable to run command: {cmd_name} requires trust level {required_trust.name}")
                return False
            command["func"](" ".join(args))
        else:
            print(f"Unknown command: {cmd_name}")
            return False
        
        return True
    
    def user_input(self, input_str: str, trust: Trust, source: object) -> None:
        is_command: bool = self.run_command(input_str, trust, source)
        if not is_command:
            self.run_command("/llm " + input_str, trust, source)
