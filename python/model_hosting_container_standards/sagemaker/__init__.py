"""SageMaker integration decorators."""

from typing import List

from fastapi import FastAPI

# Import routing utilities (generic)
from ..common.fastapi.routing import RouteConfig
from ..common.handler.decorators import (
    create_override_decorator,
    create_register_decorator,
)
from ..common.handler.registry import handler_registry
from ..logging_config import logger

# Import the real resolver functions
from .handler_resolver import get_invoke_handler, get_ping_handler

# Import LoRA Handler factory and handler types
from .lora import (
    LoRAHandlerType,
    SageMakerLoRAApiHeader,
    create_lora_transform_decorator,
)
from .sagemaker_loader import SageMakerFunctionLoader
from .sagemaker_router import create_sagemaker_router

# Use resolver functions for decorators
_get_ping_handler = get_ping_handler
_get_invocation_handler = get_invoke_handler


# SageMaker decorator instances - created using utility functions

# Override decorators - immediately register customer handlers
ping = create_override_decorator("ping", handler_registry)
invoke = create_override_decorator("invoke", handler_registry)

# Register decorators - created using create_register_decorator
register_ping_handler = create_register_decorator(
    "ping", _get_ping_handler, handler_registry
)
register_invocation_handler = create_register_decorator(
    "invoke", _get_invocation_handler, handler_registry
)


# Transform decorators - for LoRA handling
def register_load_adapter_handler(request_shape: dict, response_shape: dict = {}):
    # TODO: validate and preprocess request shape
    # TODO: validate and preprocess response shape
    return create_lora_transform_decorator(LoRAHandlerType.REGISTER_ADAPTER)(
        request_shape, response_shape
    )


def register_unload_adapter_handler(request_shape: dict, response_shape: dict = {}):
    # TODO: validate and preprocess request shape
    # TODO: validate and preprocess response shape
    return create_lora_transform_decorator(LoRAHandlerType.UNREGISTER_ADAPTER)(
        request_shape, response_shape
    )


def inject_adapter_id(adapter_path: str):
    """Create a decorator that injects adapter ID from SageMaker headers into request body.

    This decorator extracts the adapter identifier from the SageMaker LoRA API header
    (X-Amzn-SageMaker-Adapter-Identifier) and injects it into the specified path
    within the request body using JMESPath syntax.

    Args:
        adapter_path: The JSON path where the adapter ID should be injected in the
                     request body (e.g., "model", "body.model.lora_name", etc.).
                     Supports both simple keys and nested paths using dot notation.

    Returns:
        A decorator function that can be applied to FastAPI route handlers to
        automatically inject adapter IDs from headers into the request body.

    Note:
        This is a transform-only decorator that does not create its own route.
        It must be applied to existing route handlers.
    """
    # validate and preprocess
    if not adapter_path:
        logger.exception("adapter_path cannot be empty")
        raise ValueError("adapter_path cannot be empty")
    if not isinstance(adapter_path, str):
        logger.exception("adapter_path must be a string")
        raise ValueError("adapter_path must be a string")
    # create request_shape
    request_shape = {}
    request_shape[adapter_path] = (
        f'headers."{SageMakerLoRAApiHeader.ADAPTER_IDENTIFIER}"'
    )
    return create_lora_transform_decorator(LoRAHandlerType.INJECT_ADAPTER_ID)(
        request_shape=request_shape, response_shape={}
    )


def bootstrap(app: FastAPI) -> FastAPI:
    """Configure a FastAPI application with SageMaker functionality.

    This function sets up all necessary SageMaker integrations on the provided
    FastAPI application, including middlewares and LoRA router paths.

    Args:
        app: The FastAPI application instance to configure

    Returns:
        The configured FastAPI app

    Note:
        All handlers must be registered before calling this function. Handlers
        registered after this call will not be automatically mounted.
    """
    from ..common.fastapi.middleware.core import (
        load_middlewares as core_load_middlewares,
    )

    logger.info("Starting SageMaker bootstrap process")
    logger.debug(f"Bootstrapping FastAPI app: {app.title or 'unnamed'}")

    # Load container standards middlewares with SageMaker function loader
    sagemaker_function_loader = SageMakerFunctionLoader.get_function_loader()
    core_load_middlewares(app, sagemaker_function_loader)

    # Mount the SageMaker router with registered handlers
    sagemaker_router = create_sagemaker_router()
    app.include_router(sagemaker_router)

    logger.info("SageMaker bootstrap completed successfully")
    return app


__all__: List[str] = [
    "ping",
    "invoke",
    "register_ping_handler",
    "register_invocation_handler",
    "get_ping_handler",
    "get_invoke_handler",
    "register_load_adapter_handler",
    "register_unload_adapter_handler",
    "inject_adapter_id",
    "load_middlewares",
    "bootstrap",
    "RouteConfig",
]

# Initialize custom script loading after all decorators are available
SageMakerFunctionLoader.get_function_loader()  # Load custom script now that decorators are ready
