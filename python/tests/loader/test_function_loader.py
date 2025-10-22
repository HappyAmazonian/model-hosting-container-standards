"""Unit tests for FunctionLoader class."""

import os
import tempfile
from pathlib import Path

import pytest

from model_hosting_container_standards.common.custom_code_ref_resolver import (
    FunctionLoader,
)
from model_hosting_container_standards.exceptions import (
    HandlerFileNotFoundError,
    HandlerNotCallableError,
    HandlerNotFoundError,
    InvalidHandlerSpecError,
    ModuleLoadError,
)


class TestFunctionLoader:
    """Test FunctionLoader class."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_module.py"

        # Create test Python file
        test_code = """
def standalone_func():
    return "standalone"

class Handler:
    def process(self):
        return "processed"

    class NestedClass:
        def nested_method(self):
            return "nested"

# Non-callable attributes
NON_CALLABLE = "not_a_function"
NONE_ATTRIBUTE = None
"""
        self.test_file.write_text(test_code)

        self.loader = FunctionLoader(search_paths=[self.temp_dir])

        yield

        # Cleanup
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_load_file_function(self):
        """Test loading function from file."""
        func = self.loader.load_function("test_module.py:standalone_func")
        assert func is not None
        assert func() == "standalone"

    def test_load_file_class_method(self):
        """Test loading class method from file."""
        method = self.loader.load_function("test_module.py:Handler.process")
        assert method is not None
        # Note: This returns unbound method, would need instance to call

    def test_load_nested_class_method(self):
        """Test loading nested class method from file."""
        method = self.loader.load_function(
            "test_module.py:Handler.NestedClass.nested_method"
        )
        assert method is not None

    def test_load_module_function(self):
        """Test loading function from module."""
        func = self.loader.load_function("os.path:join")
        assert func is not None
        assert func("a", "b") == os.path.join("a", "b")

    def test_load_invalid_spec(self):
        """Test loading with invalid specification raises InvalidHandlerSpecError."""
        with pytest.raises(InvalidHandlerSpecError):
            self.loader.load_function("invalid_spec")

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises HandlerFileNotFoundError."""
        with pytest.raises(HandlerFileNotFoundError):
            self.loader.load_function("nonexistent.py:func")

    def test_load_nonexistent_module(self):
        """Test loading from nonexistent module raises ModuleLoadError."""
        with pytest.raises(ModuleLoadError):
            self.loader.load_function("nonexistent_module:func")

    def test_load_nonexistent_attribute(self):
        """Test loading nonexistent attribute from valid file raises HandlerNotFoundError."""
        with pytest.raises(HandlerNotFoundError):
            self.loader.load_function("test_module.py:nonexistent_func")

    def test_load_nonexistent_nested_attribute(self):
        """Test loading nonexistent nested attribute raises HandlerNotFoundError."""
        with pytest.raises(HandlerNotFoundError):
            self.loader.load_function("test_module.py:Handler.nonexistent_method")

    def test_load_non_callable_raises_error(self):
        """Test that loading non-callable attribute raises HandlerNotCallableError."""
        with pytest.raises(HandlerNotCallableError):
            self.loader.load_function("test_module.py:NON_CALLABLE")

    def test_load_none_attribute_raises_error(self):
        """Test that loading None attribute raises HandlerNotCallableError."""
        with pytest.raises(HandlerNotCallableError) as exc_info:
            self.loader.load_function("test_module.py:NONE_ATTRIBUTE")
        assert "NoneType" in str(exc_info.value)

    def test_load_router_path(self):
        """Test that router paths return None (not handled by function loader)."""
        result = self.loader.load_function("/health")
        assert result is None

        result = self.loader.load_function("/api/v1/status")
        assert result is None

    def test_empty_spec_parts(self):
        """Test specs with empty parts raise InvalidHandlerSpecError."""
        with pytest.raises(InvalidHandlerSpecError):
            self.loader.load_function(":empty_module")

        with pytest.raises(InvalidHandlerSpecError):
            self.loader.load_function("empty_func:")

    def test_load_module_from_file_public_method(self):
        """Test the public load_module_from_file method."""
        # Test successful loading
        module = self.loader.load_module_from_file(str(self.test_file))
        assert module is not None
        assert hasattr(module, "standalone_func")
        assert hasattr(module, "Handler")

        # Test that module is cached (loading again should return same object)
        module2 = self.loader.load_module_from_file(str(self.test_file))
        assert module is module2

        # Test loading nonexistent file raises error
        with pytest.raises(HandlerFileNotFoundError):
            self.loader.load_module_from_file("nonexistent.py")

    def test_load_function_with_absolute_path(self):
        """Test loading function using absolute file path."""
        # Use the absolute path to the test file
        absolute_path = str(self.test_file)

        # Test loading function with absolute path
        func = self.loader.load_function(f"{absolute_path}:standalone_func")
        assert func is not None
        assert func() == "standalone"

    def test_load_class_method_with_absolute_path(self):
        """Test loading class method using absolute file path."""
        absolute_path = str(self.test_file)

        # Test loading class method with absolute path
        method = self.loader.load_function(f"{absolute_path}:Handler.process")
        assert method is not None
        # Note: This returns unbound method, would need instance to call

    def test_load_nested_class_method_with_absolute_path(self):
        """Test loading nested class method using absolute file path."""
        absolute_path = str(self.test_file)

        # Test loading nested class method with absolute path
        method = self.loader.load_function(
            f"{absolute_path}:Handler.NestedClass.nested_method"
        )
        assert method is not None

    def test_load_function_with_nonexistent_absolute_path(self):
        """Test loading from nonexistent absolute path raises HandlerFileNotFoundError."""
        nonexistent_absolute_path = "/tmp/nonexistent_file_12345.py"

        with pytest.raises(HandlerFileNotFoundError):
            self.loader.load_function(f"{nonexistent_absolute_path}:some_func")

    def test_load_function_absolute_vs_relative_path(self):
        """Test that absolute and relative paths to same file load the same function."""
        # Load using relative path (current behavior)
        relative_func = self.loader.load_function("test_module.py:standalone_func")

        # Load using absolute path
        absolute_path = str(self.test_file)
        absolute_func = self.loader.load_function(f"{absolute_path}:standalone_func")

        # Both should work and return callable functions
        assert relative_func is not None
        assert absolute_func is not None
        assert callable(relative_func)
        assert callable(absolute_func)

        # Both should return the same result when called
        assert relative_func() == "standalone"
        assert absolute_func() == "standalone"

    def test_absolute_path_caching(self):
        """Test that modules loaded via absolute paths are properly cached."""
        absolute_path = str(self.test_file)

        # Load the same module twice using absolute path
        func1 = self.loader.load_function(f"{absolute_path}:standalone_func")
        func2 = self.loader.load_function(f"{absolute_path}:Handler.process")

        # Both should succeed
        assert func1 is not None
        assert func2 is not None

        # The underlying modules should be cached (same module object)
        # We can verify this by checking that loading the same file again uses cache
        # Note: Cache key uses resolved path to handle symlinks and relative paths consistently
        from pathlib import Path

        resolved_path = Path(absolute_path).resolve()
        cache_key = f"file:{resolved_path}"
        assert cache_key in self.loader._module_cache
