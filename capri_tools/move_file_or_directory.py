import json
import os
import shutil
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for move_file_or_directory tool
move_file_or_directory_schema = {
    "type": "object",
    "properties": {
        "source_path": {
            "type": "string",
            "description": "The relative source path of a file or directory in the Capri data directory."
        },
        "destination_path": {
            "type": "string",
            "description": "The relative destination path in the Capri data directory."
        }
    },
    "required": ["source_path", "destination_path"]
}

def move_file_or_directory_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Move a file or directory from source path to destination path within the Capri data directory"""
    try:
        input_data = json.loads(input_bytes)
        source_path = input_data.get("source_path", "")
        destination_path = input_data.get("destination_path", "")
        
        if not source_path:
            return "", Exception("No source path provided")
        
        if not destination_path:
            return "", Exception("No destination path provided")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided paths
        full_source_path = os.path.join(capri_dir, source_path)
        full_destination_path = os.path.join(capri_dir, destination_path)
        
        # Check if source exists
        if not os.path.exists(full_source_path):
            return "", Exception(f"Source not found: {source_path}")
        
        # Move the file or directory
        shutil.move(full_source_path, full_destination_path)
        
        # Determine what was moved
        source_type = "directory" if os.path.isdir(full_destination_path) else "file"
        
        return f"Successfully moved {source_type} from {source_path} to {destination_path}", None
    except Exception as e:
        return "", e

# Create the tool definition
move_file_or_directory_tool = ToolDefinition(
    name="move_file_or_directory",
    description="Move a file or directory from one location to another within the Capri data directory. Automatically detects whether the source is a file or directory.",
    input_schema=move_file_or_directory_schema,
    function=move_file_or_directory_function
)