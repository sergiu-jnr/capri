import json
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition

# Schema for read_file tool
read_file_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "The relative path of a file in the working directory."
        }
    },
    "required": ["path"]
}

def read_file_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Read the contents of a given file path"""
    try:
        input_data = json.loads(input_bytes)
        path = input_data.get("path", "")
        
        if not path:
            return "", Exception("No file path provided")
            
        with open(path, 'r') as file:
            content = file.read()
        
        return content, None
    except FileNotFoundError:
        return "", Exception(f"File not found: {path}")
    except Exception as e:
        return "", e

# Create the tool definition
read_file_tool = ToolDefinition(
    name="read_file",
    description="Read the contents of a given relative file path. Use this when you want to see what's inside a file.",
    input_schema=read_file_schema,
    function=read_file_function
)
