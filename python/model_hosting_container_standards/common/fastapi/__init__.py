"""FastAPI-specific configuration and utilities."""

from .middleware import (
    MiddlewareInfo,
    MiddlewareRegistry,
    create_middleware_object,
    input_formatter,
    load_middlewares,
    middleware_registry,
    output_formatter,
    register_middleware,
)

__all__ = [
    "register_middleware",
    "input_formatter",
    "output_formatter",
    "create_middleware_object",
    "load_middlewares",
    "MiddlewareInfo",
    "MiddlewareRegistry",
    "middleware_registry",
    "EnvVars",
    "ENV_CONFIG",
]


# FastAPI environment variables
class EnvVars:
    """FastAPI environment variable names."""

    CUSTOM_FASTAPI_PING_HANDLER = "CUSTOM_FASTAPI_PING_HANDLER"
    CUSTOM_FASTAPI_INVOCATION_HANDLER = "CUSTOM_FASTAPI_INVOCATION_HANDLER"


# FastAPI environment variable configuration mapping
ENV_CONFIG = {
    # FastAPI handler configuration
    EnvVars.CUSTOM_FASTAPI_PING_HANDLER: {
        "default": None,
        "description": "Custom ping handler specification (function spec or router URL)",
    },
    EnvVars.CUSTOM_FASTAPI_INVOCATION_HANDLER: {
        "default": None,
        "description": "Custom invocation handler specification (function spec or router URL)",
    },
}
