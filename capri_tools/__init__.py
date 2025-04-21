from capri_tools.read_file import read_file_tool
from capri_tools.edit_file import edit_file_tool
from capri_tools.list_files import list_files_tool
from capri_tools.download_from_youtube import download_from_youtube_tool
from capri_tools.trim_video import trim_video_tool
from capri_tools.copy_file_or_directory import copy_file_or_directory_tool
from capri_tools.move_file_or_directory import move_file_or_directory_tool
from capri_tools.rescale_video import rescale_video_tool
from capri_tools.create_directory import create_directory_tool
from capri_tools.delete_directory import delete_directory_tool
from capri_tools.crop_resize_images import crop_resize_images_tool
from capri_tools.execute_python_file import execute_python_file_tool

def get_all_tools():
    """Return a list of all available tools. Add new items for Claude to use."""
    return [
        list_files_tool,
        read_file_tool,
        edit_file_tool,
        download_from_youtube_tool,
        trim_video_tool,
        copy_file_or_directory_tool,
        move_file_or_directory_tool,
        rescale_video_tool,
        create_directory_tool,
        delete_directory_tool,
        crop_resize_images_tool,
        execute_python_file_tool
    ]
