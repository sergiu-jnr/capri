from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread

import anthropic
import os
import sys
import json

from tools import get_all_tools
from utils import apply_dark_theme, system_prompt
from dotenv import load_dotenv

load_dotenv()

class MessageEmitter(QObject):
    message_received = pyqtSignal(str)
    tool_executed = pyqtSignal(dict)

class ClaudeWorker(QThread):
    response_ready = pyqtSignal(dict)
    
    def __init__(self, client, conversation, tools):
        super().__init__()
        self.client = client
        self.conversation = conversation.copy()
        self.tools = tools
        
    def run(self):
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })

        try:
            model = os.environ.get("ANTHROPIC_MODEL")
            max_tokens = os.environ.get("MAX_TOKENS", 1024)

            response = self.client.messages.create(
                model=model,
                max_tokens=int(max_tokens),
                system=system_prompt(),
                messages=self.conversation,
                tools=anthropic_tools
            )
            self.response_ready.emit({"content": response.content})
        except Exception as e:
            self.response_ready.emit({"error": str(e)})

class ClaudeChat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TBC Chat")
        self.resize(800, 600)
        self.message_emitter = MessageEmitter()
        self.message_emitter.message_received.connect(self.display_message)
        self.message_emitter.tool_executed.connect(self.display_tool_execution)
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Initialize conversation and tools
        self.conversation = []
        self.tools = get_all_tools()

        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #0b202d;")
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.chat_history.setStyleSheet("""
            QTextEdit {
                color: #d4d4d4;
                border: none;
                font-family: Consolas, monospace;
                font-size: 14px;
            }
            QScrollBar:vertical {
                width: 0px;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)
        main_layout.addWidget(self.chat_history)

        # Input area
        input_widget = QWidget()
        input_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setFixedHeight(60)
        self.message_input.setStyleSheet("""
            QTextEdit {
                color: #fff;
                background-color: #030e15;
                font-family: Consolas, monospace;
                font-size: 14px;
                border: none;
                padding: 6px;
                border-radius: 4px;
            }
        """)
        self.message_input.keyPressEvent = self.input_key_press

        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(80, 60)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #911a53;
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                text-transform: uppercase;
                border-radius: 4px;
                font-weight: bold;
                font-family: Consolas, monospace;
            }
            QPushButton:hover {
                background-color: #7f194b;
            }
            QPushButton:pressed {
                background-color: #7f194b;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        main_layout.addWidget(input_widget)

        # Add welcome message
        tool_names = ", ".join(tool.name for tool in self.tools)
        self.chat_history.append(
            f"Welcome to TBC Chat!\nI'm here to help you with your questions and tasks. You have access to these tools: {tool_names}"
        )

    def input_key_press(self, event):
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.send_message()
        else:
            QTextEdit.keyPressEvent(self.message_input, event)
            
    def send_message(self):
        user_input = self.message_input.toPlainText().strip()
        if not user_input:
            return
        
        # Display user message
        self.chat_history.append(f"\nYou: {user_input}")
        
        # Clear input and disable send button
        self.message_input.clear()
        self.send_button.setEnabled(False)
        
        # Add to conversation and update title
        user_message = {"role": "user", "content": [{"type": "text", "text": user_input}]}
        self.conversation.append(user_message)
        
        # Start worker thread
        self.claude_worker = ClaudeWorker(self.client, self.conversation, self.tools)
        self.claude_worker.response_ready.connect(self.on_claude_response)
        self.claude_worker.start()
    
    def on_claude_response(self, message):
        if "error" in message:
            self.chat_history.append(f"\nError: {message['error']}")
            self.send_button.setEnabled(True)
            return
        
        # Add Claude's response to conversation
        self.conversation.append({"role": "assistant", "content": message["content"]})
        
        # Process response
        tool_results = []
        for content in message.get("content", []):
            if content.type == "text":
                self.message_emitter.message_received.emit(content.text)
            elif content.type == "tool_use":
                result = self.execute_tool(content.id, content.name, content.input)
                tool_results.append(result)
        
        # Handle tool results
        if tool_results:
            tool_results_message = {"role": "user", "content": tool_results}
            self.conversation.append(tool_results_message)
            self.claude_worker = ClaudeWorker(self.client, self.conversation, self.tools)
            self.claude_worker.response_ready.connect(self.on_claude_response)
            self.claude_worker.start()
        else:
            self.send_button.setEnabled(True)
            
    def display_message(self, message):
        self.chat_history.append(f"\nTBC Chat: {message}")
        
    def format_json_to_string(self, json_input):
        data = json.loads(json_input) if isinstance(json_input, str) else json_input
        return ", ".join(f"{k}: {v}" for k, v in data.items())

    def display_tool_execution(self, tool_data):
        if "name" in tool_data:
            print(tool_data['input'])
            print(type(tool_data['input']))
            self.chat_history.append(f"\nTool: Using {tool_data['name']} with input: {self.format_json_to_string(tool_data['input'])}")
        elif "result" in tool_data:
            self.chat_history.append(tool_data['result'])
        
    def execute_tool(self, id, name, input_data):
        tool_def = next((tool for tool in self.tools if tool.name == name), None)
        if not tool_def:
            return {"type": "tool_result", "tool_use_id": id, "content": "tool not found"}
        
        self.message_emitter.tool_executed.emit({"name": name, "input": json.dumps(input_data)})
        input_bytes = json.dumps(input_data).encode()
        
        try:
            response, error = tool_def.function(input_bytes)
            if error:
                self.message_emitter.tool_executed.emit({"result": str(error), "error": True})
                return {"type": "tool_result", "tool_use_id": id, "content": str(error)}
                
            lines = response.split('\n')
            total_lines = len(lines)

            max_lines = int(os.environ.get("MAX_LINES_PER_RESPONSE", 50))
            
            if total_lines > max_lines:
                truncated_response = '\n'.join(lines[:max_lines])
                truncated_response += f"\n\n(Response contains {total_lines} lines total, showing only the first {max_lines} lines due to chat display limitations)"
                self.message_emitter.tool_executed.emit({"result": truncated_response})
            else:
                self.message_emitter.tool_executed.emit({"result": response})
                
            return {"type": "tool_result", "tool_use_id": id, "content": response}
        except Exception as e:
            return {"type": "tool_result", "tool_use_id": id, "content": str(e)}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    window = ClaudeChat()
    window.show()
    sys.exit(app.exec())
