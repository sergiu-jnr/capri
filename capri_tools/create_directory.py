import json
import os
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for create_directory tool
create_directory_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "The relative path of the directory to create in the Capri data directory."
        },
        "exist_ok": {
            "type": "boolean",
            "description": "If True, don't raise an error if the directory already exists.",
            "default": True
        }
    },
    "required": ["path"]
}

def create_directory_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Create a directory at the specified path in the Capri data directory"""
    try:
        input_data = json.loads(input_bytes)
        path = input_data.get("path", "")
        exist_ok = input_data.get("exist_ok", True)
        
        if not path:
            return "", Exception("No directory path provided")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided directory path
        full_path = os.path.join(capri_dir, path)
        
        # Create the directory and any parent directories that don't exist
        os.makedirs(full_path, exist_ok=exist_ok)
        
        return f"Directory created successfully: {path}", None
    except FileExistsError:
        return "", Exception(f"Directory already exists and exist_ok was set to False: {path}")
    except PermissionError:
        return "", Exception(f"Permission denied when creating directory: {path}")
    except Exception as e:
        return "", e

# Create the tool definition
create_directory_tool = ToolDefinition(
    name="create_directory",
    description="Create a directory and any necessary parent directories in the Capri data directory.",
    input_schema=create_directory_schema,
    function=create_directory_function
)