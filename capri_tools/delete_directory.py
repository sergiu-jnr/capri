import json
import os
import shutil
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for delete_directory tool
delete_directory_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "The relative path of the directory to delete in the Capri data directory."
        },
        "recursive": {
            "type": "boolean",
            "description": "If True, recursively remove directories and their contents.",
            "default": True
        }
    },
    "required": ["path"]
}

def delete_directory_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Delete a directory and optionally its contents from the Capri data directory"""
    try:
        input_data = json.loads(input_bytes)
        path = input_data.get("path", "")
        recursive = input_data.get("recursive", True)
        
        if not path:
            return "", Exception("No directory path provided")
        
        # Safety check: prevent deleting the root directory
        if path == "" or path == "/" or path == ".":
            return "", Exception("Cannot delete the root directory")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided directory path
        full_path = os.path.join(capri_dir, path)
        
        # Check if path exists
        if not os.path.exists(full_path):
            return "", Exception(f"Directory not found: {path}")
        
        # Check if it's actually a directory
        if not os.path.isdir(full_path):
            return "", Exception(f"The specified path is not a directory: {path}")
        
        # Delete the directory
        if recursive:
            shutil.rmtree(full_path)
        else:
            os.rmdir(full_path)  # Will only work if directory is empty
        
        return f"Directory deleted successfully: {path}", None
    except OSError as e:
        if not recursive and len(os.listdir(full_path)) > 0:
            return "", Exception(f"Directory not empty and recursive is False: {path}")
        return "", Exception(f"Error deleting directory: {str(e)}")
    except Exception as e:
        return "", e

# Create the tool definition
delete_directory_tool = ToolDefinition(
    name="delete_directory",
    description="Delete a directory from the Capri data directory, with option to recursively remove all contents.",
    input_schema=delete_directory_schema,
    function=delete_directory_function
)