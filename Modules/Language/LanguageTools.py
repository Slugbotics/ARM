from Modules.Language.LanguageInterpreter import LanguageInterpreter, tool
import requests

@tool("Returns a list of IDs of objects that are visible to the arm")
def get_visible_objects() -> list[str]:
    return ["blue_object", "red_object", "green_object"]

@tool("Makes an HTTP GET request to the specified URL, returning the full body of the response as a string",
      url="The URL to send the GET request to")
def http_get(url: str) -> str:
    res = requests.get(url=url)
    return res.text

def register_default_tools(interpreter: LanguageInterpreter):
    interpreter.add_tool(get_visible_objects)
    interpreter.add_tool(http_get)