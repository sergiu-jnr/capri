import json
import os
from typing import Tuple, Optional, Dict, Any, Union
from capri_tools.tool_definition import ToolDefinition
from capri_tools.get_capri_dir import get_capri_dir
from llama_cpp import Llama

# Schema for call_local_ai tool
call_local_ai_schema = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "The prompt to send to the local AI model."
        },
        "prompt_template": {
            "type": "string",
            "description": "Optional. Path to a file containing a prompt template. The template should contain %PROMPT% which will be replaced with the prompt argument."
        },
        "system_prompt": {
            "type": "string",
            "description": "Optional. The system prompt to use.",
            "default": "You are a helpful assistant."
        },
        "n_ctx": {
            "type": "integer",
            "description": "Optional. The context size to use for the model.",
            "default": 2048
        },
        "max_tokens": {
            "type": "integer",
            "description": "Optional. The maximum number of tokens to generate.",
            "default": 2048
        },
        "temperature": {
            "type": "number",
            "description": "Optional. The temperature to use for sampling.",
            "default": 0.7
        },
        "response_format": {
            "type": "object",
            "description": "Optional. The JSON schema for the expected response format.",
            "example": {
                "type": "json_object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "place_title": {
                            "type": "string",
                            "description": "The title of the place"
                        },
                        "place_subtitle": {
                            "type": "string",
                            "description": "The subtitle of the place"
                        },
                        "date": {
                            "type": "string",
                            "description": "The date of the review in 'Month Year' format"
                        },
                        "review": {
                            "type": "string",
                            "description": "The review text"
                        }
                    },
                    "required": ["place_title", "place_subtitle", "date", "review"]
                }
            }
        }
    },
    "required": ["prompt"]
}

def call_local_ai_function(input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
    """Call a local AI model with the given parameters"""
    try:
        input_data = json.loads(input_bytes)
        
        # Extract parameters with defaults
        prompt = input_data.get("prompt", "")
        prompt_template_path = input_data.get("prompt_template", "")
        system_prompt = input_data.get("system_prompt", "You are a helpful assistant.")
        n_ctx = input_data.get("n_ctx", 2048)
        max_tokens = input_data.get("max_tokens", 2048)
        temperature = input_data.get("temperature", 0.7)
        response_format = input_data.get("response_format", None)
        
        if not prompt:
            return "", Exception("No prompt provided")
        
        # Handle prompt template if provided
        if prompt_template_path:
            try:
                # Get the Capri data directory
                capri_dir = get_capri_dir()
                
                # Join the Capri directory with the provided template path
                full_template_path = os.path.join(capri_dir, prompt_template_path)
                
                # Read the template and replace %PROMPT% with the actual prompt
                with open(full_template_path, 'r') as file:
                    template_content = file.read()
                
                # Replace the placeholder with the actual prompt
                prompt = template_content.replace("%PROMPT%", prompt)
                
            except FileNotFoundError:
                return "", Exception(f"Prompt template file not found: {prompt_template_path}")
            except Exception as e:
                return "", Exception(f"Error processing prompt template: {str(e)}")
        
        # Initialize the Llama model
        llm = Llama(
            model_path="/home/sergiuf/.cache/huggingface/hub/models--bartowski--NousResearch_DeepHermes-3-Llama-3-3B-Preview-GGUF/snapshots/ff767d7602d37096a8593ce7e31d7a19cc9a7182/./NousResearch_DeepHermes-3-Llama-3-3B-Preview-Q8_0.gguf",
            chat_format="chatml",
            n_ctx=n_ctx,
            verbose=False,
        )
        
        # Prepare the messages for the chat completion
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Prepare arguments for the create_chat_completion call
        completion_args: Dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add response_format if provided
        if response_format:
            completion_args["response_format"] = response_format
        
        # Call the model
        response = llm.create_chat_completion(**completion_args)
        
        # Return the response as a string
        if response and "choices" in response and len(response["choices"]) > 0:
            result = response["choices"][0]["message"]["content"]
            return result, None
        else:
            return "", Exception("No response received from model")
        
    except Exception as e:
        return "", e

# Create the tool definition
call_local_ai_tool = ToolDefinition(
    name="call_local_ai",
    description="Call a local AI model with the given parameters. Use this when you want to query a local LLM.",
    input_schema=call_local_ai_schema,
    function=call_local_ai_function
)
