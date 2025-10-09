"""File utilities for managing directories and files"""

import os
import shutil


def clear_directory(directory: str) -> None:
    """Clear all contents of a directory without deleting the directory itself"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    else:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

