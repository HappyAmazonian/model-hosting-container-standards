"""SageMaker-specific loader configuration."""

import os

from ..custom_code_ref_resolver import FunctionLoader
from .config import SageMakerDefaults, SageMakerEnvVars


def create_sagemaker_function_loader() -> FunctionLoader:
    """Create a FunctionLoader configured for SageMaker with customer script optimization."""
    # Get SageMaker model file path from environment using config
    script_filename = os.getenv(
        SageMakerEnvVars.CUSTOM_SCRIPT_FILENAME, SageMakerDefaults.SCRIPT_FILENAME
    )
    model_path = os.getenv(
        SageMakerEnvVars.SAGEMAKER_MODEL_PATH, SageMakerDefaults.SCRIPT_PATH
    )
    model_file_path = os.path.join(model_path, script_filename)

    # Create function loader with "model" alias pointing to the customer script
    loader = FunctionLoader(
        search_paths=[model_path], module_aliases={"model": model_file_path}
    )

    # Pre-load and cache the customer module if it exists
    if os.path.exists(model_file_path):
        # Pre-load the customer module using the loader's public interface
        # This will cache the module for future use
        # Since we've verified the file exists, any exception should be raised
        loader.load_module_from_file(model_file_path)

    return loader
