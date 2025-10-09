"""Unit tests for SageMaker loader functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from model_hosting_container_standards.sagemaker.loaders import (
    create_sagemaker_function_loader,
)


class TestSageMakerLoaders:
    """Test SageMaker-specific loader functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "model.py"

        # Create test Python file
        test_code = """
def predict_fn(input_data):
    return f"prediction for {input_data}"

def transform_fn(model, input_data, content_type, accept):
    return f"transformed {input_data}"

class ModelHandler:
    def __init__(self):
        self.model = "test_model"

    def predict(self, data):
        return f"handler prediction for {data}"
"""
        self.test_file.write_text(test_code)

        yield

        # Cleanup
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_create_loader_with_default_env_vars(self):
        """Test loader creation with default environment variables."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "model.py",
            },
            clear=False,
        ):
            loader = create_sagemaker_function_loader()

            # Test that the loader was created successfully
            assert loader is not None

            # Test that the module alias is set up correctly
            assert "model" in loader.module_aliases
            expected_path = os.path.join(str(self.temp_dir), "model.py")
            assert loader.module_aliases["model"] == expected_path

    def test_create_loader_uses_sagemaker_model_path(self):
        """Test loader creation uses SAGEMAKER_MODEL_PATH as search path."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "model.py",
            },
            clear=False,
        ):
            loader = create_sagemaker_function_loader()

            # Test that SAGEMAKER_MODEL_PATH is used as search path
            assert str(self.temp_dir) in loader.file_loader.search_paths

    def test_preloading_existing_file(self):
        """Test that existing model file is preloaded and cached."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "model.py",
            },
            clear=False,
        ):
            loader = create_sagemaker_function_loader()

            # The module should be preloaded and cached
            expected_cache_key = f"file:{self.test_file}"
            assert expected_cache_key in loader._module_cache

            # Test that we can load functions from the preloaded module
            func = loader.load_function("model:predict_fn")
            assert func is not None
            assert func("test_data") == "prediction for test_data"

    def test_preloading_nonexistent_file_no_error(self):
        """Test that nonexistent model file doesn't cause errors during loader creation."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "nonexistent.py",
            },
            clear=False,
        ):
            # This should not raise an exception
            loader = create_sagemaker_function_loader()
            assert loader is not None

            # The module alias should still be set up
            assert "model" in loader.module_aliases

    def test_preloading_file_with_syntax_error_raises_exception(self):
        """Test that syntax errors in model file are raised during loader creation."""
        # Create a file with syntax error
        bad_file = Path(self.temp_dir) / "bad_model.py"
        bad_file.write_text("def invalid_syntax(\n  # Missing closing parenthesis")

        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "bad_model.py",
            },
            clear=False,
        ):
            # This should raise an exception since we now raise errors for existing files
            with pytest.raises(
                Exception
            ):  # Could be SyntaxError or other compilation error
                create_sagemaker_function_loader()

    def test_load_function_with_model_alias(self):
        """Test loading functions using the 'model' alias."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "model.py",
            },
            clear=False,
        ):
            loader = create_sagemaker_function_loader()

            # Test loading different functions
            predict_fn = loader.load_function("model:predict_fn")
            assert predict_fn("input") == "prediction for input"

            transform_fn = loader.load_function("model:transform_fn")
            assert transform_fn(None, "data", "json", "json") == "transformed data"

            # Test loading class method
            handler_predict = loader.load_function("model:ModelHandler.predict")
            assert handler_predict is not None

    def test_environment_variable_defaults(self):
        """Test that default values are used when environment variables are not set."""
        # Clear relevant environment variables
        env_vars_to_clear = ["SAGEMAKER_MODEL_PATH", "CUSTOM_SCRIPT_FILENAME"]
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_clear:
                os.environ.pop(var, None)

            loader = create_sagemaker_function_loader()

            # Should use default values
            assert "model" in loader.module_aliases
            # Default path should be /opt/ml/model/model.py
            expected_default = "/opt/ml/model/model.py"
            assert loader.module_aliases["model"] == expected_default

    def test_caching_behavior(self):
        """Test that module caching works correctly."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "model.py",
            },
            clear=False,
        ):
            loader = create_sagemaker_function_loader()

            # Load the same function twice
            func1 = loader.load_function("model:predict_fn")
            func2 = loader.load_function("model:predict_fn")

            # Should be the same function object (from cached module)
            assert func1 is func2

            # Module should be in cache
            expected_cache_key = f"file:{self.test_file}"
            assert expected_cache_key in loader._module_cache

    def test_public_load_module_from_file_method(self):
        """Test the public load_module_from_file method works with SageMaker loader."""
        with patch.dict(
            os.environ,
            {
                "SAGEMAKER_MODEL_PATH": str(self.temp_dir),
                "CUSTOM_SCRIPT_FILENAME": "model.py",
            },
            clear=False,
        ):
            loader = create_sagemaker_function_loader()

            # Test loading module directly
            module = loader.load_module_from_file(str(self.test_file))
            assert module is not None
            assert hasattr(module, "predict_fn")
            assert hasattr(module, "ModelHandler")

            # Test that it's cached
            module2 = loader.load_module_from_file(str(self.test_file))
            assert module is module2
