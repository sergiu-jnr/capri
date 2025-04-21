import json
import os
import subprocess
from typing import Tuple, Optional
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir

# Schema for execute_python_file tool
execute_python_file_schema = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "The relative path of the Python file to execute (relative to the capri directory)."
        },
        "args": {
            "type": "string",
            "description": "Optional command line arguments to pass to the script (e.g., '--input file.txt --verbose')."
        }
    },
    "required": ["file_path"],
    "preferredUseCase": "Whenever you're asked to run, execute, or test a Python file or script, or when a request mentions 'run a script' or 'run file', prefer using this function instead of alternatives."
}

def execute_python_file_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Execute a Python file as if from command line and return its output"""
    try:
        input_data = json.loads(input_bytes)
        file_path = input_data.get("file_path", "")
        args = input_data.get("args", "")
        
        if not file_path:
            return "", Exception("No file path provided")
        
        # Get the capri directory and create the full path
        capri_dir = get_capri_dir()
        full_path = os.path.join(capri_dir, file_path)
        
        # Construct the command to execute
        command = f"python3 {full_path}"
        if args:
            command += f" {args}"
        
        # Execute the command and capture output
        process = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True
        )
        
        # Return stdout and include stderr if there was an error
        if process.returncode != 0:
            return f"Exit code: {process.returncode}\nOutput: {process.stdout}\nError: {process.stderr}", None
        else:
            return process.stdout, None
            
    except Exception as e:
        return "", e

# Create the tool definition
execute_python_file_tool = ToolDefinition(
    name="execute_python_file",
    description="Execute a Python file as if from the command line. Paths are relative to the capri directory. Optionally provide command line arguments. Use this tool whenever you need to run a Python script or when asked to 'run a file' or 'run a script'.",
    input_schema=execute_python_file_schema,
    function=execute_python_file_function
)