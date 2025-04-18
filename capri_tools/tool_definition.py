from typing import Callable, Dict, Any, Tuple, Optional

class ToolDefinition:
    """Definition for a tool that Claude can use"""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], 
                 function: Callable[[bytes], Tuple[str, Optional[Exception]]]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.function = function
