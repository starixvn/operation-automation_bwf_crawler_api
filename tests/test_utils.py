"""Tests for utility functions"""

import pytest
import os
from utils.file_utils import clear_directory


class TestClearDirectory:
    """Tests for clear_directory function"""
    
    def test_clear_empty_directory(self, temp_dir):
        """Test clearing an empty directory"""
        test_dir = os.path.join(temp_dir, "test_empty")
        os.makedirs(test_dir)
        
        clear_directory(test_dir)
        
        assert os.path.exists(test_dir)
        assert len(os.listdir(test_dir)) == 0
    
    def test_clear_directory_with_files(self, temp_dir):
        """Test clearing a directory with files"""
        test_dir = os.path.join(temp_dir, "test_files")
        os.makedirs(test_dir)
        
        # Create test files
        for i in range(3):
            with open(os.path.join(test_dir, f"file_{i}.txt"), "w") as f:
                f.write(f"Content {i}")
        
        assert len(os.listdir(test_dir)) == 3
        
        clear_directory(test_dir)
        
        assert os.path.exists(test_dir)
        assert len(os.listdir(test_dir)) == 0
    
    def test_clear_directory_with_subdirectories(self, temp_dir):
        """Test clearing a directory with subdirectories"""
        test_dir = os.path.join(temp_dir, "test_subdirs")
        os.makedirs(test_dir)
        
        # Create subdirectories with files
        for i in range(2):
            subdir = os.path.join(test_dir, f"subdir_{i}")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "file.txt"), "w") as f:
                f.write(f"Content {i}")
        
        assert len(os.listdir(test_dir)) == 2
        
        clear_directory(test_dir)
        
        assert os.path.exists(test_dir)
        assert len(os.listdir(test_dir)) == 0
    
    def test_clear_nonexistent_directory(self, temp_dir):
        """Test clearing a directory that doesn't exist (should create it)"""
        test_dir = os.path.join(temp_dir, "test_nonexistent")
        
        assert not os.path.exists(test_dir)
        
        clear_directory(test_dir)
        
        assert os.path.exists(test_dir)
        assert len(os.listdir(test_dir)) == 0
    
    def test_clear_directory_with_mixed_content(self, temp_dir):
        """Test clearing a directory with mixed files and subdirectories"""
        test_dir = os.path.join(temp_dir, "test_mixed")
        os.makedirs(test_dir)
        
        # Create files
        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("File 1")
        with open(os.path.join(test_dir, "file2.html"), "w") as f:
            f.write("<html>File 2</html>")
        
        # Create subdirectory with files
        subdir = os.path.join(test_dir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "nested.json"), "w") as f:
            f.write('{"key": "value"}')
        
        assert len(os.listdir(test_dir)) == 3
        
        clear_directory(test_dir)
        
        assert os.path.exists(test_dir)
        assert len(os.listdir(test_dir)) == 0
    
    def test_clear_directory_preserves_directory(self, temp_dir):
        """Test that clear_directory preserves the directory itself"""
        test_dir = os.path.join(temp_dir, "test_preserve")
        os.makedirs(test_dir)
        
        # Add some content
        with open(os.path.join(test_dir, "file.txt"), "w") as f:
            f.write("Content")
        
        clear_directory(test_dir)
        
        # Directory should still exist
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)

