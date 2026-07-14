"""Excepciones compartidas por las capas de la aplicación."""

from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationException(AppException):
    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, 422, error_code, details)


class AuthenticationException(AppException):
    def __init__(
        self,
        message: str = "Invalid credentials",
        error_code: str = "AUTHENTICATION_ERROR",
    ):
        super().__init__(message, 401, error_code)


class AuthorizationException(AppException):
    def __init__(
        self,
        message: str = "Access denied",
        error_code: str = "AUTHORIZATION_ERROR",
    ):
        super().__init__(message, 403, error_code)


class ResourceNotFoundException(AppException):
    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Any | None = None,
        error_code: str = "NOT_FOUND",
    ):
        message = f"{resource} not found"
        if resource_id is not None:
            message += f" (ID: {resource_id})"
        super().__init__(message, 404, error_code)


class ConflictException(AppException):
    def __init__(
        self,
        message: str,
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, 409, error_code, details)


class DuplicateEntryException(ConflictException):
    def __init__(self, field: str, value: Any, error_code: str = "DUPLICATE_ENTRY"):
        super().__init__(
            f"A record with {field} '{value}' already exists",
            error_code,
            {field: value},
        )


class DatabaseException(AppException):
    def __init__(
        self,
        message: str = "Database error",
        error_code: str = "DATABASE_ERROR",
    ):
        super().__init__(message, 500, error_code)


class ExternalServiceException(AppException):
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
    ):
        super().__init__(f"{service}: {message}", 502, error_code)
