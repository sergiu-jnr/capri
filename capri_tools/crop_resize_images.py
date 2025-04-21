import json
import os
import subprocess
from typing import Tuple, Optional, List, Union
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for crop_resize_images tool
crop_resize_images_schema = {
    "type": "object",
    "properties": {
        "input_path": {
            "type": "string",
            "description": "Path to either a single image or a directory of images to process."
        },
        "output_dir": {
            "type": "string",
            "description": "Directory to save processed images. If not provided, a 'cropped' subdirectory will be used.",
            "default": ""
        },
        "target_width": {
            "type": "integer",
            "description": "Target width for the output images.",
            "default": 900
        },
        "target_height": {
            "type": "integer",
            "description": "Target height for the output images.",
            "default": 600
        },
        "quality": {
            "type": "integer",
            "description": "JPEG quality (1-31, lower is better quality, 2 is high quality).",
            "default": 2
        },
        "output_format": {
            "type": "string",
            "description": "Format for output images (jpg, png, etc.).",
            "default": "jpg"
        }
    },
    "required": ["input_path"]
}

def get_image_dimensions(path: str) -> Tuple[int, int]:
    """Get the width and height of an image using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    width = info['streams'][0]['width']
    height = info['streams'][0]['height']
    return width, height

def process_image(input_path: str, output_path: str, target_width: int, target_height: int, quality: int) -> bool:
    """Process a single image, resize and crop as needed."""
    try:
        width, height = get_image_dimensions(input_path)
        
        # If image is smaller than target size, scale it directly
        if width < target_width or height < target_height:
            vf = f"scale={target_width}:{target_height}"
        else:
            # Step 1: Scale while preserving aspect ratio so that it fully covers target size
            # Step 2: Crop the center portion to the target size
            vf = (
                f"scale='if(gt(a,{target_width}/{target_height}),"
                f"{int(target_height)}*iw/ih,{target_width})':'if(gt(a,{target_width}/{target_height}),"
                f"{target_height},{int(target_width)}*ih/iw)',"
                f"crop={target_width}:{target_height}"
            )
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", vf,
            "-q:v", str(quality),
            "-y",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        return False

def crop_resize_images_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """
    Crop and resize images to the target dimensions.
    
    This function can process either a single image or a directory of images.
    It scales and crops images to fit the specified dimensions.
    """
    try:
        input_data = json.loads(input_bytes)
        input_path = input_data.get("input_path", "")
        
        if not input_path:
            return "", Exception("No input path provided")
        
        # Get parameters with defaults
        output_dir = input_data.get("output_dir", "")
        target_width = input_data.get("target_width", 900)
        target_height = input_data.get("target_height", 600)
        quality = input_data.get("quality", 2)
        output_format = input_data.get("output_format", "jpg").lower()
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Build full input path
        full_input_path = os.path.join(capri_dir, input_path)
        
        # If output_dir not specified, create 'cropped' directory in the same location as input
        if not output_dir:
            if os.path.isdir(full_input_path):
                output_dir = os.path.join(input_path, "cropped")
            else:
                output_dir = os.path.join(os.path.dirname(input_path), "cropped")
        
        # Create full output directory path
        full_output_dir = os.path.join(capri_dir, output_dir)
        
        # Create output directory if it doesn't exist
        os.makedirs(full_output_dir, exist_ok=True)
        
        processed_files = []
        failed_files = []
        
        # Determine if input is a directory or a single file
        if os.path.isdir(full_input_path):
            # Process all images in the directory
            for filename in os.listdir(full_input_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                    file_input_path = os.path.join(full_input_path, filename)
                    basename = os.path.splitext(filename)[0]
                    file_output_path = os.path.join(full_output_dir, f"{basename}.{output_format}")
                    
                    if process_image(file_input_path, file_output_path, target_width, target_height, quality):
                        processed_files.append(filename)
                    else:
                        failed_files.append(filename)
        else:
            # Process a single file
            if os.path.isfile(full_input_path):
                filename = os.path.basename(full_input_path)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                    basename = os.path.splitext(filename)[0]
                    file_output_path = os.path.join(full_output_dir, f"{basename}.{output_format}")
                    
                    if process_image(full_input_path, file_output_path, target_width, target_height, quality):
                        processed_files.append(filename)
                    else:
                        failed_files.append(filename)
                else:
                    return "", Exception(f"File is not a supported image format: {filename}")
            else:
                return "", Exception(f"Input path does not exist: {input_path}")
        
        # Generate result message
        result = f"Processed {len(processed_files)} images to {target_width}x{target_height}."
        result += f"\nOutput saved to: {output_dir}"
        
        if processed_files:
            result += f"\nProcessed files: {', '.join(processed_files[:5])}"
            if len(processed_files) > 5:
                result += f" and {len(processed_files) - 5} more"
        
        if failed_files:
            result += f"\nFailed to process: {', '.join(failed_files)}"
        
        return result, None
    except Exception as e:
        return "", e

# Create the tool definition
crop_resize_images_tool = ToolDefinition(
    name="crop_resize_images",
    description="Resize and crop images to fit specified dimensions while maintaining aspect ratio.",
    input_schema=crop_resize_images_schema,
    function=crop_resize_images_function
)