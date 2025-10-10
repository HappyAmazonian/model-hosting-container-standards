"""SageMaker integration decorators."""

from typing import Any, Callable, List

from ..registry import handler_registry
from ..utils import create_override_decorator, create_register_decorator

# Import the real resolver functions
from .handler_resolver import get_invoke_handler, get_ping_handler
from .sagemaker_loader import SageMakerFunctionLoader

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

__all__: List[str] = [
    "ping",
    "invoke",
    "register_ping_handler",
    "register_invocation_handler",
    "get_ping_handler",
    "get_invoke_handler",
]
