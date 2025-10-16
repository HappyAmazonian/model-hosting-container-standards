"""Middleware registry for managing middleware functions and formatters."""

from typing import Any, Callable, Dict, List, Optional, Union

# Allowed middleware names in execution order
ALLOWED_MIDDLEWARE_NAMES = ["throttle", "pre_post_process"]


class MiddlewareInfo:
    """Information about registered middleware."""

    def __init__(self, name: str, middleware: Union[Callable, type]):
        self.name = name
        self.middleware = middleware
        self.is_class = isinstance(middleware, type)


class MiddlewareRegistry:
    """Registry specifically for managing middlewares."""

    def __init__(self) -> None:
        self._middlewares: Dict[str, MiddlewareInfo] = {}
        # Only allow these specific middleware names
        self._allowed_middleware_names = set(ALLOWED_MIDDLEWARE_NAMES)
        # Store formatter functions
        self._input_formatter: Optional[Callable] = None
        self._output_formatter: Optional[Callable] = None

    def register_middleware(self, name: str, middleware: Union[Callable, type]) -> None:
        """
        Register a middleware by name.

        Args:
            name: Middleware name (must be one of: throttle, pre_post_process)
            middleware: Middleware function or class

        Raises:
            ValueError: If name is not allowed or already registered
        """
        # Check if name is allowed
        if name not in self._allowed_middleware_names:
            allowed_names = ", ".join(sorted(self._allowed_middleware_names))
            raise ValueError(
                f"Middleware name '{name}' is not allowed. Allowed names: {allowed_names}"
            )

        # Check if already registered
        if name in self._middlewares:
            existing_type = "class" if self._middlewares[name].is_class else "function"
            new_type = "class" if isinstance(middleware, type) else "function"
            raise ValueError(
                f"Middleware '{name}' is already registered as a {existing_type}. Cannot register as {new_type}."
            )

        # Register the middleware
        self._middlewares[name] = MiddlewareInfo(name, middleware)

    def get_middleware(self, name: str) -> Optional[MiddlewareInfo]:
        """Get middleware info by name."""
        return self._middlewares.get(name)

    def has_middleware(self, name: str) -> bool:
        """Check if a middleware is registered by name."""
        return name in self._middlewares

    def list_middlewares(self) -> List[str]:
        """List all registered middleware names."""
        return list(self._middlewares.keys())

    def get_allowed_middleware_names(self) -> List[str]:
        """Get list of allowed middleware names."""
        return list(self._allowed_middleware_names)

    def clear_middlewares(self) -> None:
        """Clear all registered middlewares."""
        self._middlewares.clear()

    # Formatter functions management
    def set_input_formatter(self, formatter: Callable) -> None:
        """Set the input formatter function."""
        if self._input_formatter is not None:
            raise ValueError(
                "Input formatter is already registered. Only one input formatter is allowed."
            )
        self._input_formatter = formatter

    def set_output_formatter(self, formatter: Callable) -> None:
        """Set the output formatter function."""
        if self._output_formatter is not None:
            raise ValueError(
                "Output formatter is already registered. Only one output formatter is allowed."
            )
        self._output_formatter = formatter

    def get_input_formatter(self) -> Optional[Callable]:
        """Get the input formatter function."""
        return self._input_formatter

    def get_output_formatter(self) -> Optional[Callable]:
        """Get the output formatter function."""
        return self._output_formatter

    def has_formatters(self) -> bool:
        """Check if any formatter functions are registered."""
        return self._input_formatter is not None or self._output_formatter is not None

    def generate_process_middleware(self) -> None:
        """Generate and register the process middleware if formatters exist."""
        if not self.has_formatters():
            return

        # Import here to avoid circular imports
        from ....logging_config import logger

        async def process_middleware(request: Any, call_next: Callable) -> Any:
            """Auto-generated process middleware that calls registered formatters."""
            try:
                # Apply input formatter if exists
                if self._input_formatter is not None:
                    logger.debug("[PROCESS] Applying input formatter")
                    request = await self._input_formatter(request) or request

                # Call the next middleware/handler
                response = await call_next(request)

                # Apply output formatter if exists
                if self._output_formatter is not None:
                    logger.debug("[PROCESS] Applying output formatter")
                    response = await self._output_formatter(response) or response

                return response

            except Exception as e:
                logger.error(f"[PROCESS] Error in process middleware: {e}")
                # Return 500 error as requested
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error in process middleware",
                        "message": str(e),
                    },
                )

        # Register the generated middleware
        if not self.has_middleware("pre_post_process"):
            self._middlewares["pre_post_process"] = MiddlewareInfo(
                "pre_post_process", process_middleware
            )
            logger.info(
                "[PROCESS] Auto-generated pre_post_process middleware registered"
            )

    def clear_formatters(self) -> None:
        """Clear all formatter functions."""
        self._input_formatter = None
        self._output_formatter = None


# Global registry instance
middleware_registry = MiddlewareRegistry()
