"""Utility functions for the application"""

from .file_utils import clear_directory, delete_file
from .logger import setup_logger, get_logger

__all__ = ["clear_directory", "delete_file", "setup_logger", "get_logger"]

