import json
import os
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for read_file tool
read_file_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "The relative path of a file in the Capri data directory."
        }
    },
    "required": ["path"]
}

def read_file_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Read the contents of a given file path from the Capri data directory"""
    try:
        input_data = json.loads(input_bytes)
        path = input_data.get("path", "")
        
        if not path:
            return "", Exception("No file path provided")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided file path
        full_path = os.path.join(capri_dir, path)
            
        with open(full_path, 'r') as file:
            content = file.read()
        
        return content, None
    except FileNotFoundError:
        return "", Exception(f"File not found: {path}")
    except Exception as e:
        return "", e

# Create the tool definition
read_file_tool = ToolDefinition(
    name="read_file",
    description="Read the contents of a file from the Capri data directory. Use this when you want to see what's inside a file.",
    input_schema=read_file_schema,
    function=read_file_function
)