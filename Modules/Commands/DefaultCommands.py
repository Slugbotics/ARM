from Controllers.Base.Controller import Controller
from typing import Callable

import Modules.Commands.Commands as Commands

def register_default_commands(commands_instance: Commands) -> None:
    def help_command(args: str) -> None:
        print("Available commands:")
        for cmd_name, cmd_info in commands_instance.commands.items():
            print(f"{cmd_name}: {cmd_info['help']}")

    def run_file_command(args: str) -> None:
        try:
            with open(args.strip(), 'r') as file:
                for line in file:
                    commands_instance.run_command(line.strip())
        except FileNotFoundError:
            print(f"File not found: {args}")
        except Exception as e:
            print(f"Error running file commands: {e}")

    # Register default commands
    commands_instance.add_command("help", help_command, "Displays this help text", aliases=["?"])
    commands_instance.add_command("run", run_file_command, "Runs commands from a file")
    
def register_controler_commands(commands_instance: Commands, new_controller_getter: Callable[[None], Controller]) -> None:    
    def get_visible_objects(args: str) -> None:
        currently_visible_objects: list[str] = new_controller_getter().get_visible_object_labels()
        print(f"Visible objects: {currently_visible_objects}")

    def get_visible_objects_detailed(args: str) -> None:
        currently_visible_objects: list[str] = new_controller_getter().get_visible_object_labels_detailed()
        print(f"Visible objects detailed: {currently_visible_objects}")

    def set_look_at_target_label(args: str) -> None:
        if new_controller_getter().set_target_label(args):
            print(f"Set target label to: {args}")
        else:
            print(f"Failed to set target label to: {args}")

    # Register controller commands
    commands_instance.add_command("get_visible_objects", get_visible_objects, "Returns a list of IDs of objects that are visible to the arm")
    commands_instance.add_command("get_visible_objects_detailed", get_visible_objects_detailed, "Returns a list of IDs of objects that are visible to the arm, along with extra information")
    commands_instance.add_command("set_look_at_target_label", set_look_at_target_label, "Makes the arm look at the largest object with the specified label, will return false if the arm cannot perceive any objects with that label")
