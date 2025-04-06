import ollama
import ollama._types
from inspect import signature, Parameter
from typing import Callable
import os.path
import httpcore
import httpx
from Modules.Language.OLLAMA_installer import install_ollama, prompt_user
from Modules.Language.LanguageInterpreterBase import LanguageInterpreterBase

DEFAULT_MODEL_FROM = "llama3.2:3b"

DEFAULT_MODEL_FILE = """FROM llama3.2:3b
PARAMETER temperature 0
SYSTEM \"""You have the ability to control a robotic arm using tool calling.
All information about physical objects must be obtained through tool calling, you must not generate any other information about objects.
You don't need to mention the fact that you are using tool calling, this is implied.
You may run multiple consecutive tool calls if necessary.\"""
"""

class LanguageInterpreter(LanguageInterpreterBase):
    messages: list[str]
    tools: list[ollama._types.Tool]
    tool_callbacks: dict[str, Callable]
    tool_param_names: dict[str, list[str]]

    def __init__(self, model_file_path: str) -> None:
        super().__init__(model_file_path)
        self.messages = []
        self.tools = []
        self.tool_callbacks = {}
        self.tool_param_names = {}
        if not os.path.isfile(model_file_path):
            print("Language model file does not exist, creating default...")
            with open(model_file_path, "w") as f:
                f.write(DEFAULT_MODEL_FILE)
        last_status_line = ""
        
        ollama_infos = None
        try:
            ollama_infos = ollama.create("arm_model", from_=DEFAULT_MODEL_FROM, files={"path": model_file_path}, stream=True)
        except httpcore.ConnectError as ex:
            print("Error loading arm language model: " + repr(ex))
            if prompt_user("Ollama is not installed. Would you like to install it?"):
                install_ollama()
                ollama_infos = ollama.create("arm_model", from_=DEFAULT_MODEL_FROM, files={"path": model_file_path}, stream=True)

        # this code may fail with an exception if ollama is not installed, so we need to check if it is installed and re-run this loop after installing it if needed 
        max_re_run_attempts = 3
        re_run_attempts = 0
        while re_run_attempts < max_re_run_attempts:
            try:
                re_run_attempts = re_run_attempts + 1
                for info in ollama_infos:
                    status_line = f"Loading arm language model from '{model_file_path}': " + info["status"]
                    if "total" in info and "completed" in info:
                        status_line += " (" + str(info["total"]) + " / " + str(info["completed"]) + ")"
                    print("\r" + " " * len(last_status_line) + "\r" + status_line, end="")
                    last_status_line = status_line
                print()
                break
            except (httpcore.ConnectError, httpx.ConnectError):
                if prompt_user("Ollama is not installed. Would you like to install it?"):
                    install_ollama()
                else:
                    print("Ollama is required to run the language interpreter.")
                    break

    def add_tool(self, fn: Callable):
        if fn.tool_name is None:
            raise Exception("The provided function does not have a tool decorator")
        params: dict[str, ollama._types.Property] = {}
        for param_name in fn.tool_param_types.keys():
            params[param_name] = {
                "type": fn.tool_param_types[param_name],
                "description": fn.tool_param_descriptions[param_name]
            }
        tool: ollama._types.Tool = { 
            "type": "function",
            "function": {
                "name": fn.tool_name,
                "description": fn.tool_description,
                "parameters": {
                    "type": "object",
                    "properties": params,
                    "required": fn.tool_required_params
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
            response = ollama.chat(model="arm_model",
                        messages=self.messages, 
                        tools=self.tools)
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
                    print(f"[LLM using tool: {name} {args}]")
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