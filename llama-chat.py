#!/usr/bin/env python3
import json
import argparse
import readline
from typing import Dict, List, Optional, Any, Union, Tuple
from llama_cpp import Llama
from tools import get_all_tools

class TerminalChat:
    def __init__(self):
        # Initialize models for regular chat and function calling
        # self.model_regular = Llama(model_path=model_path, chat_format="chatml")
        # self.model_function = Llama(model_path=model_path, chat_format="chatml-function-calling")

        self.model_regular  = Llama.from_pretrained(
            repo_id="bartowski/NousResearch_DeepHermes-3-Llama-3-3B-Preview-GGUF",
            filename="NousResearch_DeepHermes-3-Llama-3-3B-Preview-Q8_0.gguf",
            chat_format="chatml"
        )
        self.model_function  = Llama.from_pretrained(
            repo_id="bartowski/NousResearch_DeepHermes-3-Llama-3-3B-Preview-GGUF",
            filename="NousResearch_DeepHermes-3-Llama-3-3B-Preview-Q8_0.gguf",
            chat_format="chatml-function-calling"
        )

        # Verbose mode for debugging
        self.verbose = False
        
        # Initialize messages history
        self.messages = [
            {
                "role": "system",
                "content": "A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions. The assistant calls functions with appropriate input when necessary."
            }
        ]
        
        # Load tools dynamically
        self.tool_objects = get_all_tools()
        self.tools = self._convert_tools_to_llama_format()
        
    def _convert_tools_to_llama_format(self) -> List[Dict[str, Any]]:
        """Convert ToolDefinition objects to llama.cpp format"""
        llama_tools = []
        for tool in self.tool_objects:
            llama_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        return llama_tools
    
    def handle_function_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the requested function and return the result."""
        function_name = tool_call["function"]["name"]
        
        # Try to parse arguments
        try:
            function_args = json.loads(tool_call["function"]["arguments"])
        except (KeyError, json.JSONDecodeError):
            function_args = {}
            
            # If arguments is not JSON but a raw string, use it as-is
            if tool_call.get("function", {}).get("arguments", "").strip():
                function_args = tool_call["function"]["arguments"].strip()
        
        # Find the appropriate tool object
        tool_obj = next((tool for tool in self.tool_objects if tool.name == function_name), None)
        
        if tool_obj:
            try:
                # Convert arguments to bytes as expected by tool functions
                args_bytes = json.dumps(function_args).encode()
                
                # Call the function
                result, error = tool_obj.function(args_bytes)
                
                if error:
                    return {
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": str(error)})
                    }
                else:
                    return {
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"result": result})
                    }
            except Exception as e:
                return {
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": f"Error executing function: {str(e)}"})
                }
        else:
            return {
                "role": "tool",
                "name": function_name,
                "content": json.dumps({"error": f"Unknown function: {function_name}"})
            }

    def identify_appropriate_tool(self, user_input: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Identify if there's an appropriate tool for the user input using structured JSON output.
        Returns both the tool name and arguments for calling the function.
        """
        if self.verbose:
            print("\n[System: Using intermediary prompt to identify appropriate tool...]")
        else:
            print("\n[System: Analyzing query for appropriate tool...]")
        
        # Create a schema that includes all our tools and their parameters
        tools_schema = {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The name of the tool to use, or 'none' if no tool is appropriate",
                    "enum": [tool.name for tool in self.tool_objects] + ["none"]
                },
                "arguments": {
                    "type": "object",
                    "description": "Arguments to pass to the selected tool (if any)"
                }
            },
            "required": ["tool_name"]
        }
        
        # Build comprehensive tool descriptions including parameter details
        tool_descriptions = []
        for tool in self.tool_objects:
            tool_name = tool.name
            tool_desc = tool.description
            
            # Format parameters for better display
            params = tool.input_schema.get("properties", {})
            required_params = tool.input_schema.get("required", [])
            
            param_details = []
            for name, param in params.items():
                required_mark = " (required)" if name in required_params else ""
                default_value = f", default: {param.get('default')}" if "default" in param else ""
                param_details.append(f"- {name}: {param.get('description', 'No description')}{required_mark}{default_value}")
            
            param_text = "\nParameters:\n" + "\n".join(param_details) if param_details else "\nNo parameters required."
            tool_descriptions.append(f"{tool_name}: {tool_desc}{param_text}")
        
        # Create the tool decision messages with detailed instructions
        tool_decision_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that decides which tool to use for a given query and " +
                           "extracts the necessary arguments from the query. You must output valid JSON with 'tool_name' " +
                           "and 'arguments' fields. If no tool is appropriate, set tool_name to 'none' and arguments to {}."
            },
            {
                "role": "user",
                "content": f"Here are the available tools:\n\n" +
                           "\n\n".join([f"Tool {i+1}. {desc}" for i, desc in enumerate(tool_descriptions)]) + 
                           f"\n\nUser query: {user_input}\n\n" +
                           "Which tool should be used and what arguments should be passed to it? Respond with structured JSON."
            }
        ]
        
        try:
            decision = self.model_regular.create_chat_completion(
                messages=tool_decision_messages,
                response_format={
                    "type": "json_object",
                    "schema": tools_schema
                },
                temperature=0.1
            )
            
            # Parse the JSON response
            tool_decision_json = json.loads(decision["choices"][0]["message"]["content"])
            
            if self.verbose:
                print(f"[System: Tool decision JSON: {json.dumps(tool_decision_json, indent=2)}]")
            
            tool_name = tool_decision_json.get("tool_name", "none")
            arguments = tool_decision_json.get("arguments", {})
            
            if tool_name.lower() == "none":
                print("[System: No appropriate tool identified]")
                return None, None
            else:
                # Verify that the tool exists
                for tool in self.tool_objects:
                    if tool.name == tool_name:
                        print(f"[System: Identified tool: {tool_name} with arguments: {json.dumps(arguments, indent=2)}]")
                        return tool_name, arguments
                
                print(f"[System: Unclear tool decision: '{tool_name}']")
                return None, None
                
        except json.JSONDecodeError:
            print("[System: Error parsing tool decision JSON response]")
        except Exception as e:
            print(f"[System: Error determining tool: {e}]")
        
        return None, None
    
    def chat(self, use_functions: bool = True):
        """Run the interactive chat loop."""
        print("\n=== Terminal Chat with LLama.cpp ===")
        print("Type 'exit', 'quit', or press Ctrl+C to end the conversation.")
        print("Type '/functions on' or '/functions off' to toggle function calling.")
        print("Type '/clear' to reset the conversation history.")
        print("Type '/help' for more commands.\n")
        
        try:
            while True:
                user_input = input("\nYou: ")
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit']:
                    break
                elif user_input.lower() == '/functions on':
                    use_functions = True
                    print("Function calling enabled")
                    continue
                elif user_input.lower() == '/functions off':
                    use_functions = False
                    print("Function calling disabled")
                    continue
                elif user_input.lower() == '/clear':
                    self.messages = [self.messages[0]]  # Keep only the system message
                    print("Conversation history cleared")
                    continue
                elif user_input.lower() == '/help':
                    print("\n=== Available Commands ===")
                    print("exit, quit - End the conversation")
                    print("/functions on - Enable function calling")
                    print("/functions off - Disable function calling")
                    print("/clear - Reset conversation history")
                    print("/tools - List available tools")
                    print("/help - Show this help message\n")
                    continue
                elif user_input.lower() == '/tools':
                    print("\n=== Available Tools ===")
                    for i, tool in enumerate(self.tool_objects):
                        print(f"{i+1}. {tool.name}: {tool.description}")
                    print("")
                    continue
                
                # Add user message to history
                self.messages.append({"role": "user", "content": user_input})
                
                # Check if there's an appropriate tool to use
                tool_name, tool_args = self.identify_appropriate_tool(user_input) if use_functions else (None, None)
                
                if use_functions and tool_name:
                    # Generate response with explicit tool choice and prepared arguments
                    if tool_args:
                        print(f"\n[System: Using tool: {tool_name} with extracted arguments]")
                        response = self.model_function.create_chat_completion(
                            messages=self.messages,
                            tools=self.tools,
                            tool_choice={
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args)
                                }
                            },
                            temperature=0.7
                        )
                    else:
                        print(f"\n[System: Using tool: {tool_name} without extracted arguments]")
                        response = self.model_function.create_chat_completion(
                            messages=self.messages,
                            tools=self.tools,
                            tool_choice={
                                "type": "function",
                                "function": {
                                    "name": tool_name
                                }
                            },
                            temperature=0.7
                        )
                elif use_functions:
                    # Generate response with tools available but no forced choice
                    response = self.model_function.create_chat_completion(
                        messages=self.messages,
                        tools=self.tools,
                        temperature=0.7
                    )
                else:
                    # Regular chat without tools
                    response = self.model_regular.create_chat_completion(
                        messages=self.messages,
                        temperature=0.7
                    )
                
                # Process the response
                if use_functions and "tool_calls" in response["choices"][0]["message"]:
                    # Handle function calls
                    tool_calls = response["choices"][0]["message"]["tool_calls"]
                    print(f"\nAssistant: [Calling functions: {', '.join(tc['function']['name'] for tc in tool_calls)}]")
                    
                    # Add assistant message with tool calls to history
                    self.messages.append({
                        "role": "assistant",
                        "content": response["choices"][0]["message"].get("content", ""),
                        "tool_calls": tool_calls
                    })
                    
                    # Process each tool call
                    for tool_call in tool_calls:
                        tool_response = self.handle_function_call(tool_call)
                        self.messages.append(tool_response)
                        print(f"Function {tool_call['function']['name']} result: {tool_response['content']}")
                    
                    # Get final response after function calls
                    final_response = self.model_function.create_chat_completion(
                        messages=self.messages,
                        tools=self.tools,
                        temperature=0.7
                    )
                    
                    assistant_message = final_response["choices"][0]["message"]["content"]
                    self.messages.append({"role": "assistant", "content": assistant_message})
                    print(f"\nAssistant: {assistant_message}")
                    
                else:
                    # Regular response without function calls
                    assistant_message = response["choices"][0]["message"]["content"]
                    self.messages.append({"role": "assistant", "content": assistant_message})
                    print(f"\nAssistant: {assistant_message}")
                
        except KeyboardInterrupt:
            print("\nExiting chat...")
        except Exception as e:
            print(f"\nAn error occurred: {e}")

def main():
    chat = TerminalChat()
    chat.chat()

if __name__ == "__main__":
    main()
