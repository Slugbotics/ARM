import ollama
import ollama._types
from inspect import signature, Parameter
from typing import Callable

class LanguageInterpreter:
    model_name: str
    messages: list[str]
    tools: list[ollama._types.Tool]
    tool_callbacks: dict[str, Callable]
    tool_param_names: dict[str, list[str]]

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.messages = [{ "role": "system", "content": "You have the ability to control a robotic arm using tool calling." }]
        self.tools = []
        self.tool_callbacks = {}
        self.tool_param_names = {}
        if model_name not in ollama.list()["models"]:
            print(f"Downloading Ollama model '{model_name}'...")
            ollama.pull(model_name)

    def add_tool(self, fn: Callable):
        fn_sig = signature(fn)
        params: dict[str, ollama._types.Property] = {}
        required_params: list[str] = []
        for param_name in fn_sig.parameters.keys():
            fn_sig.parameters[param_name].default
            annotation = fn_sig.parameters[param_name].annotation.__name__
            description = f"The {param_name} parameter"
            param_type = "any"
            if annotation != Parameter.empty:
                param_type = annotation
            if fn_sig.parameters[param_name].default == Parameter.empty:
                required_params.append(param_name)
            params[param_name] = {
                "type": param_type,
                "description": description
            }
        tool: ollama._types.Tool = { 
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": fn.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": params,
                    "required": required_params
                }
            }
        }
        self.tools.append(tool)
        self.tool_callbacks[fn.__name__] = fn

    def run(self, command: str) -> str:
        self.messages.append({ "role": "user", "content": command })
        done = False
        content = ""
        while not done:
            response = ollama.chat(model=self.model_name,
                        messages=self.messages, 
                        tools=self.tools,
                        options={ "temperature": 0 })
            message = response["message"]
            content += message["content"]
            self.messages.append(message)
            if "tool_calls" in message:
                tool_calls = message["tool_calls"]
                if len(tool_calls) == 0:
                    done = True
                for tool_call in tool_calls:
                    fn = tool_call["function"]
                    name: str = fn["name"]
                    args: dict[str, any] = fn["arguments"]
                    print(f"[{name} {args}]")
                    tool_response = ""
                    if name in self.tool_callbacks:
                        try:
                            tool_response = "Completed with no errors. Result: " + repr(self.tool_callbacks[name](**args))
                        except Exception as ex:
                            tool_response = "Error: " + repr(ex)
                    else:
                        tool_response = f"Error: {name} is not a tool."
                    self.messages.append({ "role": "tool", "content": tool_response })
            else:
                done = True
        return content