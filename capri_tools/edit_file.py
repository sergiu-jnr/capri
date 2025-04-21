import json
import os
import platform
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for edit_file tool
edit_file_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "The path to the file (relative to Capri data directory unless absolute path is provided)"
        },
        "old_str": {
            "type": "string",
            "description": "Text to search for - must match exactly"
        },
        "new_str": {
            "type": "string",
            "description": "Text to replace old_str with"
        }
    },
    "required": ["path", "old_str", "new_str"]
}

def edit_file_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Make edits to a text file or create a new one"""
    try:
        input_data = json.loads(input_bytes)
        path = input_data.get("path", "")
        old_str = input_data.get("old_str", "").strip()
        new_str = input_data.get("new_str", "").strip()
        
        if not path:
            return "", Exception("No file path provided")
        
        if old_str == new_str:
            return "", Exception("old_str and new_str must be different")
        
        # Resolve path to be within Capri data directory if not absolute
        if not os.path.isabs(path):
            capri_dir = get_capri_dir()
            path = os.path.join(capri_dir, path)
        
        # Create new file
        if old_str == "":
            return create_new_file(path, new_str)
        
        # Edit existing file
        try:
            # Ensure the directory exists for the file
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Replace content
                new_content = content.replace(old_str, new_str)
                
                # Check if anything was replaced
                if new_content == content:
                    return "", Exception(f"Text '{old_str}' not found in file")
                
                # Write the modified content
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                return f"File updated successfully: {path}", None
            else:
                return "", Exception(f"File not found: {path}")
        
        except FileNotFoundError:
            return "", Exception(f"File not found: {path}")
        except Exception as e:
            return "", Exception(f"Error editing file: {str(e)}")
    except Exception as e:
        return "", Exception(f"Input error: {str(e)}")

def create_new_file(file_path: str, content: str) -> Tuple[str, Optional[Exception]]:
    """Create a new file with the given content"""
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return f"Created new file: {file_path}", None
    except Exception as e:
        return "", Exception(f"Failed to create file: {str(e)}")

# Create the tool definition
edit_file_tool = ToolDefinition(
    name="edit_file",
    description="Make edits to a text file or create a new one. Use empty old_str to create a new file. Files use platform-specific Capri data directory by default.",
    input_schema=edit_file_schema,
    function=edit_file_function
)