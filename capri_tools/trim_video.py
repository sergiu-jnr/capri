import json
import os
import subprocess
import re
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for trim_video tool
trim_video_schema = {
    "type": "object",
    "properties": {
        "input_file": {
            "type": "string",
            "description": "The input video file to trim"
        },
        "cut_from": {
            "type": "string",
            "description": "Start time in format HH:MM:SS"
        },
        "cut_to": {
            "type": "string",
            "description": "End time in format HH:MM:SS"
        },
        "output_file": {
            "type": "string",
            "description": "Optional output file name. If not provided, it will be generated automatically."
        }
    },
    "required": ["input_file", "cut_from", "cut_to"]
}

def generate_slug(text: str) -> str:
    """Generate a slug from text by removing special characters and replacing spaces with hyphens"""
    # Remove file extension if present
    text = os.path.splitext(text)[0]
    # Convert to lowercase and replace spaces with hyphens
    text = re.sub(r'[^\w\s-]', '', text.lower())
    return re.sub(r'[-\s]+', '-', text).strip('-')

def trim_video_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Trim a video file using ffmpeg with specified start and end times"""
    try:
        input_data = json.loads(input_bytes)
        input_file = input_data.get("input_file", "")
        cut_from = input_data.get("cut_from", "")
        cut_to = input_data.get("cut_to", "")
        output_file = input_data.get("output_file", "")
        
        if not input_file:
            return "", Exception("No input file provided")
        
        if not cut_from:
            return "", Exception("No cut from time provided")
            
        if not cut_to:
            return "", Exception("No cut to time provided")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided file path
        full_input_path = os.path.join(capri_dir, input_file)
        
        # Generate output file name if not provided
        if not output_file:
            # Extract base name without extension
            input_base = os.path.splitext(os.path.basename(input_file))[0]
            # Generate a slug from input name, cut from and cut to
            slug = f"{generate_slug(input_base)}-{generate_slug(cut_from)}-{generate_slug(cut_to)}"
            # Add extension
            extension = os.path.splitext(input_file)[1]
            output_file = f"{slug}{extension}"
        
        full_output_path = os.path.join(capri_dir, output_file)
        
        # Construct the ffmpeg command
        cmd = [
            "ffmpeg", 
            "-i", full_input_path, 
            "-ss", cut_from, 
            "-to", cut_to, 
            "-c", "copy", 
            full_output_path
        ]
        
        # Execute the command
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            return "", Exception(f"ffmpeg error: {process.stderr}")
        
        return f"Successfully trimmed video to {output_file}", None
    
    except FileNotFoundError:
        return "", Exception(f"File not found: {input_file}")
    except Exception as e:
        return "", e

# Create the tool definition
trim_video_tool = ToolDefinition(
    name="trim_video",
    description="Trim a video file using ffmpeg with specified start and end times. Optionally specify an output file name.",
    input_schema=trim_video_schema,
    function=trim_video_function
)