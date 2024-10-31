import threading
import sys

class Commands:
    def __init__(self):
        self.commands = {}
        self.looping = False
        self.loop_thread = None

    def add_command(self, name, func, help_text="", aliases=None):
        # Add command and its aliases
        aliases = aliases or []
        all_names = [name] + aliases
        for cmd_name in all_names:
            self.commands[cmd_name] = {"func": func, "help": help_text}

    def run_command(self, command_str):
        # Parse command and args
        parts = command_str.split()
        if not parts:
            return
        cmd_name, args = parts[0], parts[1:]
        command = self.commands.get(cmd_name)
        if command:
            # Call the command's function with the argument string
            command["func"](" ".join(args))
        else:
            print(f"Unknown command: {cmd_name}")

    def run_commands_looping(self):
        self.looping = True
        # this is so the first prompt is empty and not prefixed with ">>"
        prompt: str = "" 
        while self.looping:
            try:
                command_str = input(prompt)
                self.run_command(command_str)
                
                prompt = ">> "
            except (KeyboardInterrupt, EOFError):
                self.looping = False
                print("\nExiting command loop.")

    def run_commands_looping_async(self):
        self.loop_thread = threading.Thread(target=self.run_commands_looping)
        self.loop_thread.start()

    def cleanup(self):
        self.looping = False
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join()
