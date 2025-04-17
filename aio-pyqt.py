from typing import Callable, List, Dict, Any, Tuple, Optional
import json
import anthropic
import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QSplitter, QLabel, QScrollArea, QComboBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread

class ToolDefinition:
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], function: Callable[[bytes], Tuple[str, Optional[Exception]]]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.function = function

class MessageEmitter(QObject):
    message_received = pyqtSignal(dict)
    tool_executed = pyqtSignal(dict)

class ClaudeWorker(QThread):
    response_ready = pyqtSignal(dict)
    
    def __init__(self, client, conversation, tools, model, max_tokens):
        super().__init__()
        self.client = client
        self.conversation = conversation.copy()  # Make a copy to avoid race conditions
        self.tools = tools
        self.model = model
        self.max_tokens = max_tokens
        
    def run(self):
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })

        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=self.conversation,
                tools=anthropic_tools
            )
            
            print(response.usage.input_tokens, response.usage.output_tokens)

            # Emit the response
            self.response_ready.emit({
                "role": "assistant",
                "content": response.content
            })
        except Exception as e:
            # Handle errors
            self.response_ready.emit({
                "error": str(e)
            })

class ClaudeChat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat with Capri")
        self.resize(900, 700)
        
        # Set up the message emitter for thread safety
        self.message_emitter = MessageEmitter()
        self.message_emitter.message_received.connect(self.display_message)
        self.message_emitter.tool_executed.connect(self.display_tool_execution)
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic()
        
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = "claude-3-5-haiku-20241022"
        self.max_tokens = 1024

        # Setup UI
        self.setup_ui()
        
        # Initialize agent with tools
        self.conversation = []
        self.setup_tools()

        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except:
                self.client = None
        else:
            self.client = None
        
    def setup_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        
        # Settings area
        settings_widget = QWidget()
        settings_layout = QFormLayout(settings_widget)
        
        # API Key input
        self.api_key_input = QLineEdit(self.api_key)
        self.api_key_input.setPlaceholderText("Enter your Anthropic API key...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # Hide the API key
        self.api_key_input.textChanged.connect(self.update_api_key)
        settings_layout.addRow("API Key:", self.api_key_input)
        
        # Model selection
        self.model_input = QComboBox()
        self.model_input.addItems([
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229"
        ])
        self.model_input.setEditable(True)  # Allow custom model names
        self.model_input.setCurrentText(self.model)
        self.model_input.currentTextChanged.connect(self.update_model)
        settings_layout.addRow("Model:", self.model_input)
        
        # Max tokens input
        self.max_tokens_input = QLineEdit(str(self.max_tokens))
        self.max_tokens_input.setPlaceholderText("Max tokens for response...")
        self.max_tokens_input.textChanged.connect(self.update_max_tokens)
        settings_layout.addRow("Max Tokens:", self.max_tokens_input)
        
        # Add settings to main layout
        main_layout.addWidget(settings_widget)
        
        # Create splitter for chat and optional log area
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #333333;
                font-size: 14px;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        
        # Send button
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #5e72e4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #324cdd;
            }
        """)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        
        chat_layout.addLayout(input_layout)
        
        # Add chat widget to splitter
        splitter.addWidget(chat_widget)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Add welcome message
        self.chat_history.append('<div style="margin-left: 10px;">Hello! How can I assist you today?</div>')
    
    def update_api_key(self, key):
        self.api_key = key
        # Reinitialize client with new API key
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except Exception as e:
            self.chat_history.append(f'<div style="color: red;">Error initializing API: {str(e)}</div>')
            self.client = None
    
    def update_model(self, model):
        self.model = model
    
    def update_max_tokens(self, max_tokens_text):
        try:
            self.max_tokens = int(max_tokens_text)
        except ValueError:
            # If invalid input, revert to default
            self.max_tokens = 1024
            self.max_tokens_input.setText("1024")
   
        
    def send_message(self):
        user_input = self.message_input.text().strip()
        if not user_input:
            return
            
        # Display user message
        self.chat_history.append(f'<div style="color: #2dce89; font-weight: bold;">You:</div><div style="margin-left: 10px;">{user_input}</div>')
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
        
        # Clear input and disable it while waiting for response
        self.message_input.clear()
        self.message_input.setEnabled(False)
        
        # Create user message for the conversation
        user_message = {"role": "user", "content": [{"type": "text", "text": user_input}]}
        self.conversation.append(user_message)
        
        # Show a "Claude is thinking" message
        self.chat_history.append('<div style="margin-left: 10px; font-style: italic;">Thinking...</div>')
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
        
        # Start the Claude worker in a separate thread
        self.start_claude_worker()
    
    def start_claude_worker(self):
        # Create and start the worker thread
        self.claude_worker = ClaudeWorker(self.client, self.conversation, self.tools, self.model, self.max_tokens)
        self.claude_worker.response_ready.connect(self.on_claude_response)
        self.claude_worker.start()

    def on_claude_response(self, message):
        # Remove the "thinking" message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove the newline
        
        if "error" in message:
            # Display error message
            self.chat_history.append(f'<div style="color: #f5365c; font-weight: bold;">Error:</div><div style="margin-left: 10px;">{message["error"]}</div>')
            self.message_input.setEnabled(True)
            return
        
        # Add Claude's response to the conversation
        self.conversation.append(message)
        
        # Process Claude's response
        tool_results = []
        for content in message.get("content", []):
            if content.type == "text":
                # Send the text message to be displayed
                self.message_emitter.message_received.emit({"text": content.text})
            elif content.type == "tool_use":
                # Execute tool and get results
                result = self.execute_tool(
                    content.id,
                    content.name,
                    content.input
                )
                tool_results.append(result)
        
        # If tools were used, send results back to Claude
        if tool_results:
            tool_results_message = {"role": "user", "content": tool_results}
            self.conversation.append(tool_results_message)
            # Process Claude's response again with tool results
            self.start_claude_worker()
        else:
            # Re-enable input when we're done processing
            self.message_input.setEnabled(True)

            # clear self.confersation for next message
            # self.conversation = []
            
    # Replace your process_with_claude method with this version (it's no longer needed)
    def process_with_claude(self):
        # This is now handled by the worker thread
        pass
    
    def execute_tool(self, id: str, name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        tool_def = None
        for tool in self.tools:
            if tool.name == name:
                tool_def = tool
                break

        if not tool_def:
            return {
                "type": "tool_result",
                "tool_use_id": id,
                "content": "tool not found"
            }
        
        # Emit tool execution info for UI
        self.message_emitter.tool_executed.emit({
            "name": name,
            "input": json.dumps(input_data)
        })
        
        input_bytes = json.dumps(input_data).encode()
        
        try:
            # Execute the tool
            response, error = tool_def.function(input_bytes)
            if error:
                result = {
                    "type": "tool_result",
                    "tool_use_id": id,
                    "content": str(error)
                }
                # Display tool error
                self.message_emitter.tool_executed.emit({
                    "result": str(error),
                    "error": True
                })
                return result
                
            # Display successful tool result
            self.message_emitter.tool_executed.emit({
                "result": response[:100] + "..." if len(response) > 100 else response,
                "error": False
            })
            
            return {
                "type": "tool_result",
                "tool_use_id": id,
                "content": response
            }
        except Exception as e:
            self.message_emitter.tool_executed.emit({
                "result": str(e),
                "error": True
            })
            return {
                "type": "tool_result",
                "tool_use_id": id,
                "content": str(e)
            }

    def run_inference(self, conversation):
        # This is now handled in the worker thread
        pass
    
    def display_message(self, message_data):
        # Display Claude's text response
        self.chat_history.append(f'<div style="color: #5e72e4; font-weight: bold;">Capri:</div><div style="margin-left: 10px;">{message_data["text"]}</div>')
        # Scroll to bottom
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
    
    def display_tool_execution(self, tool_data):
        if "name" in tool_data:
            # Display tool execution
            self.chat_history.append(f'<div style="color: #11cdef; font-weight: bold;">Capri\'s toy:</div><div style="margin-left: 10px;">Using {tool_data["name"]} with input: {tool_data["input"]}</div>')
        elif "result" in tool_data:
            # Display tool result
            color = "#f5365c" if tool_data.get("error", False) else "#2dce89"
            result_text = tool_data["result"]
            self.chat_history.append(f'<div style="margin-left: 10px;">{result_text}</div>')
        
        # Scroll to bottom
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
        
    def setup_tools(self):
        read_file_definition = ToolDefinition(
            name="read_file",
            description="Read the contents of a given relative file path. Use this when you want to see what's inside a file. Do not use this with directory names.",
            input_schema=self.get_schema(ReadFileInput),
            function=self.read_file
        )

        list_files_definition = ToolDefinition(
            name="list_files",
            description="List files and directories at a given path. If no path is provided, lists files in the current directory.",
            input_schema=self.get_schema(ListFilesInput),
            function=self.list_files
        )

        edit_file_definition = ToolDefinition(
            name="edit_file",
            description="Make edits to a text file. Replaces 'old_str' with 'new_str' in the given file. 'old_str' and 'new_str' MUST be different from each other. If the file specified with path doesn't exist, it will be created.",
            input_schema=self.get_schema(EditFileInput),
            function=self.edit_file
        )

        self.tools = [read_file_definition, list_files_definition, edit_file_definition]
    
    # Tool schema and functions
    def get_schema(self, cls):
        """Simple schema generator - in a real implementation you'd want to use a proper JSON schema library"""
        props = {}
        
        if cls == ReadFileInput:
            props = {
                "path": {
                    "type": "string",
                    "description": "The relative path of a file in the working directory."
                }
            }
        elif cls == ListFilesInput:
            props = {
                "path": {
                    "type": "string",
                    "description": "Optional relative path to list files from. Defaults to current directory if not provided."
                }
            }
        elif cls == EditFileInput:
            props = {
                "path": {
                    "type": "string",
                    "description": "The path to the file"
                },
                "old_str": {
                    "type": "string",
                    "description": "Text to search for - must match exactly and must only have one match exactly"
                },
                "new_str": {
                    "type": "string", 
                    "description": "Text to replace old_str with"
                }
            }
        
        return {
            "type": "object",
            "properties": props
        }
    
    def read_file(self, input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
        try:
            input_data = json.loads(input_bytes)
            path = input_data.get("path", "")
            
            with open(path, 'r') as file:
                content = file.read()
            
            return content, None
        except Exception as e:
            return "", e
    
    def list_files(self, input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
        try:
            input_data = json.loads(input_bytes)
            path = input_data.get("path", ".")
            
            files = []
            for root, dirs, filenames in os.walk(path):
                rel_root = os.path.relpath(root, path)
                if rel_root == ".":
                    for d in dirs:
                        files.append(f"{d}/")
                    for f in filenames:
                        files.append(f)
                else:
                    for d in dirs:
                        files.append(f"{os.path.join(rel_root, d)}/")
                    for f in filenames:
                        files.append(os.path.join(rel_root, f))
            
            return json.dumps(files), None
        except Exception as e:
            return "", e
    
    def edit_file(self, input_bytes: bytes) -> Tuple[str, Optional[Exception]]:
        try:
            input_data = json.loads(input_bytes)
            path = input_data.get("path", "")
            old_str = input_data.get("old_str", "").strip()
            new_str = input_data.get("new_str", "").strip()
            
            if path == "" or old_str == new_str:
                return "", Exception("invalid input parameters")
            
            try:
                with open(path, 'r') as file:
                    old_content = file.read()
                
                new_content = old_content.replace(old_str, new_str)
                
                if old_content == new_content and old_str != "":
                    return "", Exception("old_str not found in file")
                
                with open(path, 'w') as file:
                    file.write(new_content)
                
                return "OK", None
            except FileNotFoundError:
                if old_str == "":
                    return self.create_new_file(path, new_str)
                else:
                    return "", Exception(f"File not found: {path}")
        except Exception as e:
            return "", e
    
    def create_new_file(self, file_path: str, content: str) -> Tuple[str, Optional[Exception]]:
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w') as file:
                file.write(content)
            
            return f"Successfully created file {file_path}", None
        except Exception as e:
            return "", Exception(f"failed to create file: {str(e)}")

# Tool input classes
class ReadFileInput:
    path: str

class ListFilesInput:
    path: str

class EditFileInput:
    path: str
    old_str: str
    new_str: str

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    window = ClaudeChat()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()