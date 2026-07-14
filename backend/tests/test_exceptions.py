"""Tests para las excepciones personalizadas."""

from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    ResourceNotFoundException,
    DuplicateEntryException,
    DatabaseException,
)


class TestValidationException:
    """Tests para ValidationException."""

    def test_validation_exception_has_correct_status_code(self):
        """Verifica que el status code es 422."""
        exc = ValidationException("Invalid email")
        assert exc.status_code == 422

    def test_validation_exception_has_error_code(self):
        """Verifica que tiene un error_code."""
        exc = ValidationException("Invalid email", error_code="INVALID_EMAIL")
        assert exc.error_code == "INVALID_EMAIL"

    def test_validation_exception_can_have_details(self):
        """Verifica que puede almacenar detalles."""
        exc = ValidationException(
            "Invalid email",
            details={"field": "email", "value": "invalid"},
        )
        assert exc.details["field"] == "email"


class TestAuthenticationException:
    """Tests para AuthenticationException."""

    def test_auth_exception_has_401_status(self):
        """Verifica que el status code es 401."""
        exc = AuthenticationException("Invalid credentials")
        assert exc.status_code == 401

    def test_auth_exception_has_correct_error_code(self):
        """Verifica que tiene el error_code correcto."""
        exc = AuthenticationException()
        assert exc.error_code == "AUTHENTICATION_ERROR"


class TestResourceNotFoundException:
    """Tests para ResourceNotFoundException."""

    def test_not_found_exception_has_404_status(self):
        """Verifica que el status code es 404."""
        exc = ResourceNotFoundException("User", resource_id=1)
        assert exc.status_code == 404

    def test_not_found_exception_includes_resource_name(self):
        """Verifica que el mensaje incluye el nombre del recurso."""
        exc = ResourceNotFoundException("User", resource_id=123)
        assert "User not found" in exc.message
        assert "123" in exc.message


class TestDuplicateEntryException:
    """Tests para DuplicateEntryException."""

    def test_duplicate_exception_has_409_status(self):
        """Verifica que el status code es 409."""
        exc = DuplicateEntryException("email", "user@example.com")
        assert exc.status_code == 409

    def test_duplicate_exception_includes_field_and_value(self):
        """Verifica que el mensaje incluye campo y valor."""
        exc = DuplicateEntryException("email", "user@example.com")
        assert "email" in exc.message
        assert "user@example.com" in exc.message


class TestDatabaseException:
    """Tests para DatabaseException."""

    def test_database_exception_has_500_status(self):
        """Verifica que el status code es 500."""
        exc = DatabaseException("Connection failed")
        assert exc.status_code == 500

    def test_database_exception_has_correct_error_code(self):
        """Verifica que tiene el error_code correcto."""
        exc = DatabaseException()
        assert exc.error_code == "DATABASE_ERROR"
