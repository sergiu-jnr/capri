from capri_tools.read_file import read_file_tool
from capri_tools.edit_file import edit_file_tool

def get_all_tools():
    """Return a list of all available tools. Add new items for Claude to use."""
    return [
        read_file_tool,
        edit_file_tool
    ]
