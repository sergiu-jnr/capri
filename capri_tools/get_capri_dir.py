import os
import platform

def get_capri_dir() -> str:
    """Get the appropriate Capri data directory based on the operating system"""
    system = platform.system()
    
    if system == "Windows":
        # Windows: %USERPROFILE%\Capri
        base_dir = os.path.join(os.path.expanduser("~"), "Capri")
    elif system == "Darwin":  # macOS
        # macOS: ~/Capri
        base_dir = os.path.expanduser("~/Capri")
    else:
        # Linux/Unix: ~/Capri (modified as requested)
        base_dir = os.path.expanduser("~/Capri")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    return base_dir