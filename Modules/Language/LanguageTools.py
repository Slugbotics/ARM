from Controllers.Controller import Controller
from Modules.Language.LanguageInterpreter import LanguageInterpreter, tool
import requests
from typing import Callable

controller_getter: Callable[[None], Controller] = None

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
    return controller_getter().set_target_label(label)

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