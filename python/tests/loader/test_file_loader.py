"""Unit tests for FileLoader class."""

import tempfile
from pathlib import Path

import pytest

from model_hosting_container_standards.common.custom_code_ref_resolver import FileLoader
from model_hosting_container_standards.exceptions import (
    HandlerFileNotFoundError,
    ModuleLoadError,
)


class TestFileLoader:
    """Test FileLoader class."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_module.py"

        # Create test Python file
        test_code = """
def test_function():
    return "test_result"

class TestClass:
    def test_method(self):
        return "method_result"

    class NestedClass:
        def nested_method(self):
            return "nested_result"

# Non-callable attribute for testing
TEST_CONSTANT = "constant_value"
"""
        self.test_file.write_text(test_code)

        # Create subdirectory with another test file
        self.sub_dir = Path(self.temp_dir) / "subdir"
        self.sub_dir.mkdir()
        self.sub_file = self.sub_dir / "sub_module.py"
        sub_code = """
def sub_function():
    return "sub_result"
"""
        self.sub_file.write_text(sub_code)

        self.loader = FileLoader([self.temp_dir])

        yield

        # Cleanup
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_load_function(self):
        """Test loading a function from file."""
        func = self.loader.load_function("test_module.py", "test_function")
        assert func is not None
        assert func() == "test_result"

    def test_load_class(self):
        """Test loading a class from file."""
        cls = self.loader.load_function("test_module.py", "TestClass")
        assert cls is not None
        instance = cls()
        assert instance.test_method() == "method_result"

    def test_load_from_subdirectory(self):
        """Test loading from subdirectory."""
        func = self.loader.load_function("subdir/sub_module.py", "sub_function")
        assert func is not None
        assert func() == "sub_result"

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(HandlerFileNotFoundError):
            self.loader.load_function("nonexistent.py", "func")

    def test_load_nonexistent_attribute(self):
        """Test loading nonexistent attribute."""
        with pytest.raises(ModuleLoadError):
            self.loader.load_function("test_module.py", "nonexistent")

    def test_multiple_search_paths(self):
        """Test FileLoader with multiple search paths."""
        # Create another temp directory
        temp_dir2 = tempfile.mkdtemp()
        try:
            test_file2 = Path(temp_dir2) / "other_module.py"
            test_file2.write_text("def other_func(): return 'other'")

            loader = FileLoader([self.temp_dir, temp_dir2])

            # Should find file in first search path
            func1 = loader.load_function("test_module.py", "test_function")
            assert func1() == "test_result"

            # Should find file in second search path
            func2 = loader.load_function("other_module.py", "other_func")
            assert func2() == "other"
        finally:
            import shutil

            shutil.rmtree(temp_dir2)

    def test_absolute_path_loading(self):
        """Test loading with absolute file paths."""
        # Test with absolute path
        absolute_path = str(self.test_file)
        func = self.loader.load_function(absolute_path, "test_function")
        assert func is not None
        assert func() == "test_result"

    def test_absolute_path_nonexistent(self):
        """Test loading with nonexistent absolute path."""
        absolute_path = "/nonexistent/absolute/path/file.py"
        with pytest.raises(HandlerFileNotFoundError):
            self.loader.load_function(absolute_path, "func")

    def test_relative_path_with_parent_dirs(self):
        """Test loading with relative paths containing parent directory references."""
        # Create a nested structure
        nested_dir = Path(self.temp_dir) / "level1" / "level2"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "nested_module.py"
        nested_file.write_text("def nested_func(): return 'nested'")

        # Test loading with relative path from temp_dir
        func = self.loader.load_function(
            "level1/level2/nested_module.py", "nested_func"
        )
        assert func is not None
        assert func() == "nested"

    def test_relative_path_with_dot_notation(self):
        """Test loading with dot notation in relative paths."""
        # Create file in parent of a subdirectory
        parent_file = Path(self.temp_dir) / "parent_module.py"
        parent_file.write_text("def parent_func(): return 'parent'")

        # Create loader with subdirectory as search path
        subdir_loader = FileLoader([str(self.sub_dir)])

        # Test loading with parent directory reference
        func = subdir_loader.load_function("../parent_module.py", "parent_func")
        assert func is not None
        assert func() == "parent"

    def test_current_directory_default(self):
        """Test that current directory is used as default search path."""
        # Create loader with no search paths (should default to ".")
        default_loader = FileLoader()
        assert default_loader.search_paths == ["."]

    def test_search_path_priority(self):
        """Test that files in earlier search paths take priority."""
        # Create another temp directory with same filename
        temp_dir2 = tempfile.mkdtemp()
        try:
            # Create file with same name but different content
            duplicate_file = Path(temp_dir2) / "test_module.py"
            duplicate_file.write_text("def test_function(): return 'second_result'")

            # Create loader with first temp_dir having priority
            loader = FileLoader([self.temp_dir, temp_dir2])
            func = loader.load_function("test_module.py", "test_function")

            # Should get result from first search path
            assert func() == "test_result"  # Not "second_result"
        finally:
            import shutil

            shutil.rmtree(temp_dir2)

    def test_absolute_path_bypasses_search_paths(self):
        """Test that absolute paths bypass search path resolution."""
        # Create another temp directory with same filename but different content
        temp_dir2 = tempfile.mkdtemp()
        try:
            duplicate_file = Path(temp_dir2) / "test_module.py"
            duplicate_file.write_text("def test_function(): return 'absolute_result'")

            # Create loader with only first temp_dir in search paths
            loader = FileLoader([self.temp_dir])

            # Load using absolute path to second file (not in search paths)
            absolute_path = str(duplicate_file)
            func = loader.load_function(absolute_path, "test_function")

            # Should get result from absolute path, not search paths
            assert func() == "absolute_result"
        finally:
            import shutil

            shutil.rmtree(temp_dir2)

    def test_absolute_path_class_loading(self):
        """Test loading classes using absolute file paths."""
        absolute_path = str(self.test_file)
        cls = self.loader.load_function(absolute_path, "TestClass")
        assert cls is not None
        instance = cls()
        assert instance.test_method() == "method_result"

    def test_absolute_path_nested_class_loading(self):
        """Test loading nested classes using absolute file paths."""
        absolute_path = str(self.test_file)
        nested_cls = self.loader.load_function(absolute_path, "TestClass")
        assert nested_cls is not None

        # Access nested class
        nested_class = nested_cls.NestedClass
        instance = nested_class()
        assert instance.nested_method() == "nested_result"

    def test_absolute_path_constant_loading(self):
        """Test loading constants using absolute file paths."""
        absolute_path = str(self.test_file)
        constant = self.loader.load_function(absolute_path, "TEST_CONSTANT")
        assert constant == "constant_value"

    def test_absolute_path_subdirectory_file(self):
        """Test loading from subdirectory file using absolute path."""
        absolute_path = str(self.sub_file)
        func = self.loader.load_function(absolute_path, "sub_function")
        assert func is not None
        assert func() == "sub_result"

    def test_mixed_absolute_relative_paths(self):
        """Test that absolute and relative paths to same file work consistently."""
        # Load using relative path
        relative_func = self.loader.load_function("test_module.py", "test_function")

        # Load using absolute path
        absolute_path = str(self.test_file)
        absolute_func = self.loader.load_function(absolute_path, "test_function")

        # Both should work and return same result
        assert relative_func() == "test_result"
        assert absolute_func() == "test_result"

    def test_absolute_path_with_symlinks(self):
        """Test absolute path handling with symbolic links (if supported)."""
        import os

        # Create a symlink to the test file (skip if not supported)
        symlink_path = Path(self.temp_dir) / "symlink_module.py"
        try:
            os.symlink(str(self.test_file), str(symlink_path))

            # Load using absolute path to symlink
            absolute_symlink_path = str(symlink_path)
            func = self.loader.load_function(absolute_symlink_path, "test_function")
            assert func is not None
            assert func() == "test_result"

        except (OSError, NotImplementedError):
            # Skip test if symlinks not supported on this platform
            pytest.skip("Symlinks not supported on this platform")
