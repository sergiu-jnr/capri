import json
import os
import subprocess
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for rescale_video tool
rescale_video_schema = {
    "type": "object",
    "properties": {
        "input_path": {
            "type": "string",
            "description": "The relative path of the input video file in the Capri data directory."
        },
        "width": {
            "type": "integer",
            "description": "The target width for the video in pixels.",
            "default": 1920
        },
        "height": {
            "type": "integer",
            "description": "The target height for the video in pixels.",
            "default": 1080
        },
        "output_path": {
            "type": "string",
            "description": "The relative path for the output video file in the Capri data directory. If not provided, one will be generated automatically.",
            "default": ""
        }
    },
    "required": ["input_path"]
}

def rescale_video_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """
    Rescale a video to the specified dimensions while maintaining aspect ratio.
    
    The function uses FFmpeg to scale the video to fit within the specified dimensions,
    then crops any excess to ensure the exact dimensions are achieved.
    """
    try:
        input_data = json.loads(input_bytes)
        input_path = input_data.get("input_path", "")
        
        if not input_path:
            return "", Exception("No input file path provided")
        
        # Get optional parameters with defaults
        width = input_data.get("width", 1920)
        height = input_data.get("height", 1080)
        output_path = input_data.get("output_path", "")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided input file path
        full_input_path = os.path.join(capri_dir, input_path)
        
        # Generate output path if not provided
        if not output_path:
            # Extract input filename without extension
            input_filename = os.path.basename(input_path)
            input_name, input_ext = os.path.splitext(input_filename)
            
            # Create a new filename with resolution info
            output_filename = f"{input_name}_{width}x{height}{input_ext}"
            output_path = os.path.join(os.path.dirname(input_path), output_filename)
        
        # Create the full output path
        full_output_path = os.path.join(capri_dir, output_path)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
        
        # Build the FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", full_input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
            "-y",  # Overwrite output file if it exists
            full_output_path
        ]
        
        # Execute the FFmpeg command
        process = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )
        
        # Check for errors
        if process.returncode != 0:
            return "", Exception(f"FFmpeg error: {process.stderr}")
        
        return f"Video successfully rescaled to {width}x{height} and saved to {output_path}", None
    
    except FileNotFoundError:
        return "", Exception(f"Input file not found: {input_path}")
    except Exception as e:
        return "", e

# Create the tool definition
rescale_video_tool = ToolDefinition(
    name="rescale_video",
    description="Rescale a video to specified dimensions while maintaining aspect ratio through cropping.",
    input_schema=rescale_video_schema,
    function=rescale_video_function
)