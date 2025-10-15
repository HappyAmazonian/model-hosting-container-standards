"""Handler resolution logic for SageMaker container standards.

This module provides SageMaker-specific handler resolution using the generic
handler resolver framework.

## Handler Resolution Priority Order

### For Ping Handlers:
1. **Environment variable** specified function (CUSTOM_FASTAPI_PING_HANDLER)
2. **Registry** @ping decorated function
3. **Customer script** def ping function
4. **Default** handler (if any)

### For Invoke Handlers:
1. **Environment variable** specified function (CUSTOM_FASTAPI_INVOCATION_HANDLER)
2. **Registry** @invoke decorated function
3. **Customer script** def invoke function
4. **Default** handler (if any)

## Usage Examples

```python
from model_hosting_container_standards.sagemaker.handler_resolver import (
    get_ping_handler, get_invoke_handler
)

# Get resolved handlers
ping_handler = get_ping_handler()
invoke_handler = get_invoke_handler()

# Use in FastAPI or other frameworks
if ping_handler:
    result = await ping_handler()
```

## Error Handling

- Environment variable errors are raised immediately (configuration errors)
- Customer script errors are raised if script exists but can't be loaded
- Missing handlers return None (graceful degradation)
"""

import logging
from typing import Any, Callable, Optional, Union

from ..common.handler.resolver import GenericHandlerResolver, HandlerConfig
from ..exceptions import HandlerFileNotFoundError, HandlerNotFoundError
from .sagemaker_loader import SageMakerFunctionLoader

logger = logging.getLogger(__name__)


class SageMakerHandlerConfig(HandlerConfig):
    """SageMaker-specific handler configuration."""

    def get_env_handler(
        self, handler_type: str
    ) -> Union[Callable[..., Any], str, None]:
        """Get handler from SageMaker environment variables."""
        if handler_type == "ping":
            return SageMakerFunctionLoader.get_ping_handler_from_env()
        elif handler_type == "invoke":
            return SageMakerFunctionLoader.get_invocation_handler_from_env()
        else:
            return None

    def get_customer_script_handler(
        self, handler_type: str
    ) -> Optional[Callable[..., Any]]:
        """Get handler from SageMaker customer script."""
        try:
            return SageMakerFunctionLoader.load_function_from_spec(
                f"model:{handler_type}"
            )
        except (HandlerFileNotFoundError, HandlerNotFoundError) as e:
            # File doesn't exist or handler not found - continue to next priority
            logger.debug(
                f"No customer script {handler_type} function found: {type(e).__name__}"
            )
            return None
        except Exception:
            # File exists but has errors (syntax, import, etc.) - this is a real error
            logger.error(f"Customer script {handler_type} function failed to load")
            raise


class SageMakerHandlerResolver:
    """SageMaker-specific handler resolver using generic resolution logic."""

    def __init__(self) -> None:
        """Initialize the SageMaker handler resolver."""
        self._generic_resolver = GenericHandlerResolver(SageMakerHandlerConfig())

    def resolve_ping_handler(self) -> Optional[Callable]:
        """Resolve ping handler using generic resolution logic."""
        return self._generic_resolver.resolve_handler("ping")

    def resolve_invoke_handler(self) -> Optional[Callable]:
        """Resolve invoke handler using generic resolution logic."""
        return self._generic_resolver.resolve_handler("invoke")


# Global resolver instance
_resolver = SageMakerHandlerResolver()


def get_ping_handler() -> Optional[Callable]:
    """Get the resolved ping handler."""
    return _resolver.resolve_ping_handler()


def get_invoke_handler() -> Optional[Callable]:
    """Get the resolved invoke handler."""
    return _resolver.resolve_invoke_handler()
