from Modules.Language.LanguageInterpreter import LanguageInterpreter
import requests

def get_visible_objects() -> list[str]:
    "Returns a list of IDs of objects that are visible to the arm"
    return ["blue_object", "red_object", "green_object"]

def http_get(url: str) -> str:
    "Makes an HTTP GET request to the specified URL, returning the full body of the response as a string"
    res = requests.get(url=url)
    return res.text

def register_default_tools(interpreter: LanguageInterpreter):
    interpreter.add_tool(get_visible_objects)
    interpreter.add_tool(http_get)