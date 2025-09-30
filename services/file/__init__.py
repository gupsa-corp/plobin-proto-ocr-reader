# File management domain
from .storage import save_result, load_result
from .metadata import generate_filename
from .directories import create_directories

__all__ = ['save_result', 'load_result', 'generate_filename', 'create_directories']