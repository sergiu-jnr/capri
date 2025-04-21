import json
import os
import shutil
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for copy_file_or_directory tool
copy_file_or_directory_schema = {
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

def copy_file_or_directory_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Copy a file or directory from source path to destination path within the Capri data directory"""
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
        
        # Determine if source is a file or directory and copy accordingly
        if os.path.isfile(full_source_path):
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
            shutil.copy2(full_source_path, full_destination_path)
            result_message = f"Successfully copied file from {source_path} to {destination_path}"
        elif os.path.isdir(full_source_path):
            # Copy directory and all its contents
            if os.path.exists(full_destination_path):
                return "", Exception(f"Destination already exists: {destination_path}")
            shutil.copytree(full_source_path, full_destination_path)
            result_message = f"Successfully copied directory from {source_path} to {destination_path}"
        else:
            return "", Exception(f"Source is neither a file nor a directory: {source_path}")
        
        return result_message, None
    except Exception as e:
        return "", e

# Create the tool definition
copy_file_or_directory_tool = ToolDefinition(
    name="copy_file_or_directory",
    description="Copy a file or directory from one location to another within the Capri data directory. Automatically detects whether the source is a file or directory and performs the appropriate copy operation.",
    input_schema=copy_file_or_directory_schema,
    function=copy_file_or_directory_function
)