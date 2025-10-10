"""Handler registry for managing Custom handlers."""

from typing import Any, Callable, Dict, List, Optional


class HandlerRegistry:
    """General registry for managing handlers by name with proper priority."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def set_handler(self, name: str, handler: Callable[..., Any]) -> None:
        """Set a handler by name."""
        self._handlers[name] = handler

    def get_handler(self, name: str) -> Optional[Callable[..., Any]]:
        """Get a handler by name."""
        return self._handlers.get(name)

    def has_handler(self, name: str) -> bool:
        """Check if a handler is registered by name."""
        return name in self._handlers

    def remove_handler(self, name: str) -> None:
        """Remove a handler by name."""
        self._handlers.pop(name, None)

    def list_handlers(self) -> List[str]:
        """List all registered handler names."""
        return list(self._handlers.keys())

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()


# Global registry instance
handler_registry = HandlerRegistry()
