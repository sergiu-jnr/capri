import json
import os
import subprocess
import tempfile
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for text_to_speech tool
text_to_speech_schema = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "The text to convert to speech"
        },
        "output_filename": {
            "type": "string",
            "description": "The filename for the output audio file (should end with .wav or .mp3)"
        },
        "speed": {
            "type": "number",
            "description": "The speed of the speech (default: 0.9)",
            "default": 0.9
        },
        "lang": {
            "type": "string",
            "description": "The language code: 'en-us' for American English or 'en-gb' for British English (default: 'en-gb')",
            "enum": ["en-us", "en-gb"],
            "default": "en-gb"
        },
        "voice": {
            "type": "string",
            "description": "The voice to use: 'af_heart'/'am_michael' for American, 'bf_lily'/'bm_lewis' for British. By default, use: bm_lewis.",
            "enum": ["af_heart", "am_michael", "bf_lily", "bm_lewis"]
        },
        "format": {
            "type": "string",
            "description": "The output audio format",
            "enum": ["mp3", "wav"],
            "default": "mp3"
        }
    },
    "required": ["text", "output_filename"]
}

def text_to_speech_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Convert text to speech using kokoro-tts"""
    try:
        input_data = json.loads(input_bytes)
        text = input_data.get("text", "")
        output_filename = input_data.get("output_filename", "")
        speed = input_data.get("speed", 1)
        lang = input_data.get("lang", "en-gb")
        format_type = input_data.get("format", "mp3")
        
        # Set default voice based on language if not provided
        if "voice" not in input_data:
            voice = "bf_lily" if lang == "en-gb" else "af_heart"
        else:
            voice = input_data["voice"]
        
        if not text:
            return "", Exception("No text provided")
        
        if not output_filename:
            return "", Exception("No output filename provided")
        
        # Get the Capri data directory
        capri_dir = get_capri_dir()
        
        # Create a temporary input text file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_input_path = temp_file.name
            temp_file.write(text)
        
        try:
            # Join the Capri directory with the output filename
            full_output_path = os.path.join(capri_dir, output_filename)
            
            # Get the kokoro directory path
            kokoro_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "capri_tools", "kokoro")
            
            # Build the command (now with relative path since we'll change directory)
            command = [
                "./kokoro-tts",
                temp_input_path,
                full_output_path,
                "--speed", str(speed),
                "--lang", lang,
                "--voice", voice,
                "--format", format_type
            ]
            
            # Run the command from the kokoro directory
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=kokoro_dir  # Change working directory to kokoro folder
            )
            
            return f"Successfully created audio file: {output_filename}", None
        except subprocess.CalledProcessError as e:
            return "", Exception(f"Error executing TTS command: {e.stderr}")
        finally:
            # Clean up the temporary input file
            os.unlink(temp_input_path)
            
    except Exception as e:
        return "", e

# Create the tool definition
text_to_speech_tool = ToolDefinition(
    name="text_to_speech",
    description="Convert text to speech using kokoro-tts. Supports American and British English voices.",
    input_schema=text_to_speech_schema,
    function=text_to_speech_function
)