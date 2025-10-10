"""Mock vLLM server for integration testing.

This simulates exactly how a real vLLM server works:
- Defines endpoint functions decorated with @sagemaker_standards.register_*_handler
- The decorators resolve the final handler at startup time
- When endpoints are called, they directly call the resolved handler function
- No direct calls to get_ping_handler() or get_invoke_handler() needed
"""

from typing import Any, Dict

import model_hosting_container_standards.sagemaker as sagemaker_standards


class MockRequest:
    """Mock request object for testing."""

    def __init__(self, body: str = '{"prompt": "Hello world"}'):
        self._body = body.encode()

    async def body(self) -> bytes:
        return self._body


class MockVLLMServer:
    """Mock vLLM server with FastAPI-style endpoints."""

    def __init__(self):
        self.request_count = 0
        # Setup endpoint handlers exactly like real vLLM server
        self._setup_endpoints()

    def _setup_endpoints(self):
        """Setup FastAPI endpoint handlers with sagemaker_standards decorators."""

        # This is exactly how real vLLM server defines its ping endpoint
        @sagemaker_standards.register_ping_handler
        async def ping_endpoint():
            """vLLM ping endpoint - decorator returns the final handler."""
            return {
                "status": "healthy",
                "source": "vllm_default",
                "message": "Default ping from vLLM server",
            }

        # This is exactly how real vLLM server defines its invocations endpoint
        @sagemaker_standards.register_invocation_handler
        async def invocations_endpoint(request=None):
            """vLLM invocations endpoint - decorator returns the final handler."""
            return {"predictions": ["Default vLLM response"], "source": "vllm_default"}

        # Store the final handlers returned by decorators
        self._ping_handler = ping_endpoint
        self._invocations_handler = invocations_endpoint

    async def get(self, path: str) -> Dict[str, Any]:
        """Simulate FastAPI GET routing."""
        if path == "/ping":
            self.request_count += 1
            # Call the handler returned by the decorator directly
            return await self._ping_handler()
        return {"error": f"Endpoint {path} not found", "source": "error"}

    async def post(
        self, path: str, data: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Simulate FastAPI POST routing."""
        if path == "/invocations":
            self.request_count += 1
            # Call the handler returned by the decorator directly
            mock_request = MockRequest()
            return await self._invocations_handler(mock_request)
        return {"error": f"Endpoint {path} not found", "source": "error"}


# Global server instance
mock_server = MockVLLMServer()


async def call_ping_endpoint() -> Dict[str, Any]:
    """Simulate calling GET /ping endpoint."""
    return await mock_server.get("/ping")


async def call_invoke_endpoint() -> Dict[str, Any]:
    """Simulate calling POST /invocations endpoint."""
    return await mock_server.post("/invocations", {"prompt": "Hello world"})
