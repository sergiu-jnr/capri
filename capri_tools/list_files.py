import json
import os
from typing import Tuple, Optional, Dict, List
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for list_files tool
list_files_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "The relative path of a directory in the Capri data directory. Leave empty to list files in the root Capri directory."
        }
    }
}

def list_files_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """List files and directories in the specified path within the Capri data directory"""
    try:
        input_data = json.loads(input_bytes)
        path = input_data.get("path", "")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided path (if any)
        target_dir = os.path.join(capri_dir, path) if path else capri_dir
        
        # Check if the directory exists
        if not os.path.isdir(target_dir):
            return "", Exception(f"Directory not found: {path}")
        
        # List files and directories
        items = os.listdir(target_dir)
        
        # Separate files and directories and add type information
        result = {
            "directories": [],
            "files": []
        }
        
        for item in items:
            item_path = os.path.join(target_dir, item)
            if os.path.isdir(item_path):
                result["directories"].append(item)
            else:
                result["files"].append(item)
        
        # Convert to JSON string for output
        return json.dumps(result, indent=2), None
    
    except Exception as e:
        return "", e

# Create the tool definition
list_files_tool = ToolDefinition(
    name="list_files",
    description="List all files and directories in a specified path within the Capri data directory. Returns separate lists of files and directories.",
    input_schema=list_files_schema,
    function=list_files_function
)