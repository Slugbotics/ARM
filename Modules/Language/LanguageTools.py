from Controllers.Controller import Controller
from Modules.Language.LanguageInterpreter import LanguageInterpreter, tool
import requests
from typing import Callable
from typing import List

controller_getter: Callable[[None], Controller] = None

#utility
def find_closest_matches(target: str, potential_targets: List[str]) -> List[str]:
    # Define characters to replace with a space
    replace_chars = {':', ',', '-', '_'}
    
    def normalize(s: str) -> str:
        for char in replace_chars:
            s = s.replace(char, ' ')
        return s.lower()
    
    # Exact matches
    exact_matches = [s for s in potential_targets if s == target]
    if exact_matches:
        return exact_matches
    
    # Normalized matches
    norm_target = normalize(target)
    norm_matches = [s for s in potential_targets if normalize(s) == norm_target]
    if norm_matches:
        return norm_matches
    
    # Substring matches
    substring_matches = [s for s in potential_targets if norm_target in normalize(s)]
    return substring_matches

@tool("Returns a list of IDs of objects that are visible to the arm")
def get_visible_objects() -> list[str]:
    currently_visible_objects: list[str] = controller_getter().get_visible_object_labels()
    return currently_visible_objects

@tool("Returns a list of IDs of objects that are visible to the arm, along with extra information")
def get_visible_objects_detailed() -> list[str]:
    currently_visible_objects: list[str] = controller_getter().get_visible_object_labels_detailed()
    return currently_visible_objects

@tool("Makes the arm look at the largest object with the specified label, you must only give a label as returned by get_visible_objects(), will return false if the arm cannot perceive any objects with that label", label="The label of the object to look at")
def set_look_at_target_label(label: str) -> bool:
    currently_visible_objects: list[str] = controller_getter().get_visible_object_labels()
    closest_matchess = find_closest_matches(label, currently_visible_objects)
    print(f"Found tag matches: {closest_matchess}")
    tag_target:str = closest_matchess[0] if len(closest_matchess) > 0 else label
    return controller_getter().set_target_label(tag_target)

@tool("Returns the label of the object that the arm is currently looking at")
def get_look_at_target_label() -> str:
    return controller_getter().get_target_label()

def register_controler_tools(interpreter: LanguageInterpreter, new_controller_getter: Callable[[None], Controller]):
    """Registers tools that require a controller to be set"""
    global controller_getter
    controller_getter = new_controller_getter
    interpreter.add_tool(get_visible_objects)
    interpreter.add_tool(get_visible_objects_detailed)
    interpreter.add_tool(set_look_at_target_label)
    interpreter.add_tool(get_look_at_target_label)

@tool("Makes an HTTP GET request to the specified URL, returning the full body of the response as a string",
      url="The URL to send the GET request to")
def http_get(url: str) -> str:
    res = requests.get(url=url)
    return res.text

def register_default_tools(interpreter: LanguageInterpreter):
    """Registers default tools the arm AI can use"""
    interpreter.add_tool(http_get)