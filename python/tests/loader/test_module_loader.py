"""Unit tests for ModuleLoader class."""

import os

import pytest

from model_hosting_container_standards.common.custom_code_ref_resolver import (
    ModuleLoader,
)
from model_hosting_container_standards.exceptions import (
    HandlerNotFoundError,
    ModuleLoadError,
)


class TestModuleLoader:
    """Test ModuleLoader class."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ModuleLoader()

    def test_load_builtin_function(self):
        """Test loading from built-in module."""
        func = self.loader.load_function("os.path", "join")
        assert func is not None
        assert func("a", "b") == os.path.join("a", "b")

    def test_load_nonexistent_module(self):
        """Test loading from nonexistent module."""
        with pytest.raises(ModuleLoadError):
            self.loader.load_function("nonexistent_module", "func")

    def test_load_nonexistent_attribute(self):
        """Test loading nonexistent attribute from valid module."""
        with pytest.raises(HandlerNotFoundError):
            self.loader.load_function("os", "nonexistent")
