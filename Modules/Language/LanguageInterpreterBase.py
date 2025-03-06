from inspect import signature, Parameter
from typing import Callable

class LanguageInterpreterBase:
    
    def __init__(self, model_file_path: str) -> None: ...
    """Initialise the language model with the given file path"""
    
    def run(self, command: str) -> str: ...
    """Run this command in the language model and return the response"""    
    
    def add_tool(self, fn: Callable): ...
    """Add a tool to this language model"""
    
def tool(description: str, **parameter_descriptions):
    """Decorator for adding a tool to a language model"""
    def tool_decorator(func: Callable):
        func.tool_name = func.__name__
        func.tool_description = description
        func.tool_param_descriptions = parameter_descriptions
        func.tool_param_types = {}
        func.tool_required_params = []
        func_sig = signature(func)
        for param_name in func_sig.parameters.keys():
            if param_name not in parameter_descriptions:
                raise Exception(f"Missing parameter description for '{param_name}' on '{func.__name__}'")
            param = func_sig.parameters[param_name]
            if param.annotation == Parameter.empty:
                func.tool_param_types[param_name] = "any"
            else:
                func.tool_param_types[param_name] = param.annotation.__name__
            if param.default == Parameter.empty:
                func.tool_required_params.append(param_name)
        return func
    return tool_decorator