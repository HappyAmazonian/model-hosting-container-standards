"""Unit tests for sessions models module."""

import pytest
from pydantic import ValidationError

from model_hosting_container_standards.sagemaker.sessions.models import (
    SessionRequest,
    SessionRequestType,
)


class TestSessionRequestType:
    """Test SessionRequestType enum."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("NEW_SESSION", SessionRequestType.NEW_SESSION),
            ("CLOSE", SessionRequestType.CLOSE),
        ],
    )
    def test_enum_can_be_created_from_string(self, value, expected):
        """Test enum can be instantiated from string."""
        request_type = SessionRequestType(value)
        assert request_type == expected

    def test_enum_raises_error_for_invalid_value(self):
        """Test enum raises ValueError for invalid string."""
        with pytest.raises(ValueError):
            SessionRequestType("INVALID")


class TestSessionRequest:
    """Test SessionRequest pydantic model."""

    @pytest.mark.parametrize(
        "request_type,expected",
        [
            (SessionRequestType.NEW_SESSION, SessionRequestType.NEW_SESSION),
            (SessionRequestType.CLOSE, SessionRequestType.CLOSE),
        ],
    )
    def test_valid_request(self, request_type, expected):
        """Test creating valid session requests."""
        request = SessionRequest(requestType=request_type)
        assert request.requestType == expected

    @pytest.mark.parametrize(
        "invalid_value",
        ["INVALID_TYPE", None],
        ids=["invalid_string", "null_value"],
    )
    def test_rejects_invalid_request_type(self, invalid_value):
        """Test model rejects invalid or null requestType values."""
        with pytest.raises(ValidationError) as exc_info:
            SessionRequest(requestType=invalid_value)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_rejects_missing_request_type(self):
        """Test model rejects missing requestType field."""
        with pytest.raises(ValidationError) as exc_info:
            SessionRequest()

        errors = exc_info.value.errors()
        assert any(error["type"] == "missing" for error in errors)

    def test_rejects_extra_fields(self):
        """Test model rejects extra fields due to extra='forbid'."""
        with pytest.raises(ValidationError) as exc_info:
            SessionRequest(requestType="NEW_SESSION", extra_field="not_allowed")

        errors = exc_info.value.errors()
        assert any("extra_forbidden" in error["type"] for error in errors)
