from Modules.Language.LanguageInterpreter import LanguageInterpreter
import requests

def set_tracking_color(r: int, g: int, b: int):
    "Sets the color that the arm will track to the specified red (r), green (g), and blue (b) color. This function does not return anything."
    pass

def http_get(url: str):
    "Makes an HTTP GET request to the specified URL, returning the full body of the response as a string."
    res = requests.get(url=url)
    return res.text

def register_default_tools(interpreter: LanguageInterpreter):
    interpreter.add_tool(set_tracking_color)
    interpreter.add_tool(http_get)