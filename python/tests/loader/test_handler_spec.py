"""Unit tests for HandlerSpec class."""

import pytest

from model_hosting_container_standards.common.handler.spec import HandlerSpec
from model_hosting_container_standards.exceptions import InvalidHandlerSpecError


class TestHandlerSpec:
    """Test HandlerSpec class."""

    def test_file_function_spec(self):
        """Test file-based function specification."""
        spec = HandlerSpec("model.py:predict_fn")
        assert spec.is_function
        assert spec.is_file_function
        assert not spec.is_module_function
        assert not spec.is_router_path
        assert spec.file_path == "model.py"
        assert spec.function_name == "predict_fn"

    def test_module_function_spec(self):
        """Test module-based function specification."""
        spec = HandlerSpec("mypackage:handler_fn")
        assert spec.is_function
        assert spec.is_module_function
        assert not spec.is_file_function
        assert not spec.is_router_path
        assert spec.module_name == "mypackage"
        assert spec.function_name == "handler_fn"

    def test_class_method_spec(self):
        """Test class method specification."""
        spec = HandlerSpec("handler.py:MyClass.process")
        assert spec.is_function
        assert spec.is_class_method
        assert spec.class_name == "MyClass"
        assert spec.method_name == "process"

    def test_router_spec(self):
        """Test router path specification."""
        spec = HandlerSpec("/health")
        assert spec.is_router_path
        assert not spec.is_function
        assert spec.router_path == "/health"

    def test_absolute_path_function_spec(self):
        """Test absolute path function specification."""
        spec = HandlerSpec("/opt/ml/model.py:predict_fn")
        assert spec.is_function
        assert spec.is_file_function
        assert not spec.is_router_path
        assert spec.file_path == "/opt/ml/model.py"
        assert spec.function_name == "predict_fn"

    def test_validation(self):
        """Test specification validation."""
        # Valid function specs
        assert HandlerSpec("model.py:func").is_valid_function_spec()
        assert HandlerSpec("module:func").is_valid_function_spec()

        # Router paths are NOT function specs
        assert not HandlerSpec("/health").is_valid_function_spec()

        # Invalid function specs
        assert not HandlerSpec("no_colon").is_valid_function_spec()
        assert not HandlerSpec(":empty_module").is_valid_function_spec()
        assert not HandlerSpec("empty_func:").is_valid_function_spec()

    def test_validate_function_spec(self):
        """Test function spec validation and parsing."""
        spec = HandlerSpec("model.py:predict_fn")
        module_path, func_name = spec.validate_function_spec()
        assert module_path == "model.py"
        assert func_name == "predict_fn"

    def test_validate_router_spec_raises_error(self):
        """Test that validating router spec raises error."""
        spec = HandlerSpec("/health")
        with pytest.raises(InvalidHandlerSpecError):
            spec.validate_function_spec()
