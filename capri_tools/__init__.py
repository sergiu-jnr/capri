# Import all tools
from capri_tools.read_file import read_file_tool
from capri_tools.edit_file import edit_file_tool

def get_all_tools():
    """Return a list of all available tools"""
    return [
        read_file_tool,
        edit_file_tool
    ]
