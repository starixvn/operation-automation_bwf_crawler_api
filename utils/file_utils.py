"""File utilities for managing directories and files"""

import os
import shutil
from datetime import datetime, timedelta


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

def delete_file(file_path: str) -> None:
    """Delete a file"""
    if os.path.exists(file_path):
        os.remove(file_path)
    return

def cleanup_old_json_files(directory: str = "mode_max_round", days: int = 7):
    """
    Delete JSON files older than specified days from the directory
    
    Args:
        directory: Directory path containing JSON files
        days: Number of days to keep files (default: 7)
    """
    if not os.path.exists(directory):
        return
    
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Delete if older than cutoff time
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Deleted old file: {filename} (last modified: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")
    
    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old JSON file(s) from {directory}")

