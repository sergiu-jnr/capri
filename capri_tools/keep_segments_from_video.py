import json
import os
import subprocess
from typing import Tuple, Optional, List
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for keep_segments_from_video tool
keep_segments_from_video_schema = {
    "type": "object",
    "properties": {
        "input_path": {
            "type": "string",
            "description": "The relative path of the input video file in the Capri data directory."
        },
        "output_path": {
            "type": "string",
            "description": "Optional. The relative path for the output video in the Capri data directory. If not provided, will use input filename with '_edited' suffix."
        },
        "segments_to_keep": {
            "type": "array",
            "description": "List of time segments to keep in the output video. Each segment is a tuple of [start_time, end_time] in seconds.",
            "items": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": {
                    "type": "number",
                    "description": "Time in seconds."
                }
            }
        }
    },
    "required": ["input_path", "segments_to_keep"]
}

def keep_segments_from_video_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Keep specified segments from a video and concatenate them using ffmpeg"""
    try:
        input_data = json.loads(input_bytes)
        input_path = input_data.get("input_path", "")
        output_path = input_data.get("output_path", "")
        segments_to_keep = input_data.get("segments_to_keep", [])
        
        if not input_path:
            return "", Exception("No input file path provided")
        
        if not segments_to_keep:
            return "", Exception("No segments to keep specified")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Join the Capri directory with the provided file paths
        full_input_path = os.path.join(capri_dir, input_path)
        
        # Check if the file exists
        if not os.path.exists(full_input_path):
            return "", Exception(f"Input file not found: {input_path}")
        
        # Generate default output path if not provided
        if not output_path:
            input_file_name = os.path.splitext(os.path.basename(input_path))[0]
            output_extension = os.path.splitext(os.path.basename(input_path))[1] or ".mp4"
            output_path = f"{input_file_name}_edited{output_extension}"
        
        # Preserve original extension if output_path is provided without extension
        if '.' not in os.path.basename(output_path):
            output_extension = os.path.splitext(os.path.basename(input_path))[1] or ".mp4"
            output_path += output_extension
            
        full_output_path = os.path.join(capri_dir, output_path)
        
        # First, check if the input file has audio
        probe_cmd = [
            "ffprobe", 
            "-v", "error", 
            "-select_streams", "a", 
            "-show_entries", "stream=codec_type", 
            "-of", "json", 
            full_input_path
        ]
        
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        has_audio = '"codec_type": "audio"' in probe_result.stdout
        
        # Build ffmpeg filter complex command
        filter_parts = []
        video_parts = []
        audio_parts = []
        
        for i, (start_time, end_time) in enumerate(segments_to_keep):
            # Create trim filter for video
            filter_parts.append(
                f"[0:v]trim=start={start_time}:end={end_time},setpts=PTS-STARTPTS[v{i}]"
            )
            video_parts.append(f"[v{i}]")
            
            # Create trim filter for audio if it exists
            if has_audio:
                filter_parts.append(
                    f"[0:a]atrim=start={start_time}:end={end_time},asetpts=PTS-STARTPTS[a{i}]"
                )
                audio_parts.append(f"[a{i}]")
        
        # Add concat filter - properly format the input streams
        if has_audio:
            # Create the string of inputs for concat filter
            concat_inputs = "".join(video_parts) + "".join(audio_parts)
            filter_parts.append(
                f"{concat_inputs}concat=n={len(segments_to_keep)}:v=1:a=1[outv][outa]"
            )
            mapping = ["-map", "[outv]", "-map", "[outa]"]
        else:
            # Create the string of inputs for concat filter
            concat_inputs = "".join(video_parts)
            filter_parts.append(
                f"{concat_inputs}concat=n={len(segments_to_keep)}:v=1:a=0[outv]"
            )
            mapping = ["-map", "[outv]"]
        
        # Combine all filter parts
        filter_complex = "; ".join(filter_parts)
        
        # Build ffmpeg command
        cmd = ["ffmpeg", "-i", full_input_path, "-filter_complex", filter_complex] + mapping + [full_output_path]
        
        # For debugging, print the command
        cmd_str = " ".join(cmd)
        print(f"Executing command: {cmd_str}")
        
        # Run ffmpeg command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return "", Exception(f"FFmpeg error: {result.stderr}")
        
        return f"Successfully created edited video at {output_path}", None
    except Exception as e:
        return "", e

# Create the tool definition
keep_segments_from_video_tool = ToolDefinition(
    name="keep_segments_from_video",
    description="Keep specified segments from a video and concatenate them together. Provide the input video path and a list of time segments to keep.",
    input_schema=keep_segments_from_video_schema,
    function=keep_segments_from_video_function
)