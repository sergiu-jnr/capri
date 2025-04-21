import json
import subprocess
import os
import platform
import time
from datetime import datetime
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for download_from_youtube tool
download_from_youtube_schema = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "The YouTube video URL to download"
        },
        "resolution": {
            "type": "string",
            "description": "Video resolution: '480', '720', or '1080'. Default is '720'",
            "enum": ["480", "720", "1080"]
        },
        "format": {
            "type": "string",
            "description": "Output format: 'video' for mp4 or 'audio' for mp3. Default is 'video'",
            "enum": ["video", "audio"]
        }
    },
    "required": ["url"]
}

def download_from_youtube_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Download a YouTube video in the specified resolution and format"""
    try:
        input_data = json.loads(input_bytes)
        url = input_data.get("url", "")
        resolution = input_data.get("resolution", "720")
        output_format = input_data.get("format", "video")
        
        if not url:
            return "", Exception("No YouTube URL provided")
        
        # Get Capri data directory for saving downloads
        output_dir = get_capri_dir()
        
        # Change to the Capri directory
        os.chdir(output_dir)
        
        # Generate timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "audio":
            # Set output filename with timestamp
            output_filename = f"{timestamp}.mp3"
            
            # Command for audio/mp3 download
            command = [
                "yt-dlp",
                "-f", "bestaudio",
                "--extract-audio",
                "--audio-format", "mp3",
                "-o", output_filename,
                url
            ]
        else:
            # Set output filename with timestamp
            output_filename = f"{timestamp}.mp4"
            
            # Command for video download with specified resolution
            height_param = f"height<={resolution}"
            format_string = f"bestvideo[{height_param}][ext=mp4]+bestaudio[ext=m4a]/best[{height_param}][ext=mp4]"
            
            command = [
                "yt-dlp",
                "-f", format_string,
                "-o", output_filename,
                url,
                "--merge-output-format", "mp4"
            ]
        
        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            return "", Exception(f"Download failed: {result.stderr}")
        
        # Full path to the downloaded file
        file_path = os.path.join(output_dir, output_filename)
        
        return f"Successfully downloaded {'audio' if output_format == 'audio' else 'video'} from {url} to {file_path}", None
    
    except Exception as e:
        return "", e

# Create the tool definition
download_from_youtube_tool = ToolDefinition(
    name="download_from_youtube",
    description="Download video or audio from YouTube. Can specify resolution for videos or download just the audio as mp3. Files are saved to the Capri data directory with timestamp filenames.",
    input_schema=download_from_youtube_schema,
    function=download_from_youtube_function
)