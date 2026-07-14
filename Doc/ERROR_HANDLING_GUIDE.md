"""
Guía de uso de validación y manejo de errores estructurados.

Este archivo muestra ejemplos de cómo usar las excepciones personalizadas
en servicios y repositorios.
"""

# EJEMPLO 1: En Service/authentication.py
# ========================================

from exceptions import (
    AuthenticationException,
    DuplicateEntryException,
    ValidationException,
)

# Antes (HTTPException):
# raise HTTPException(status_code=401, detail="Email not found!")

# Después (AppException):
# raise AuthenticationException("Email not found")

# Más específico:
# raise AuthenticationException("Email not found", error_code="EMAIL_NOT_FOUND")


# EJEMPLO 2: Validación de entrada
# =================================

def register(user):
    if not user.email or "@" not in user.email:
        raise ValidationException(
            message="Invalid email format",
            error_code="INVALID_EMAIL",
            details={"field": "email", "value": user.email}
        )
    
    if len(user.password) < 8:
        raise ValidationException(
            message="Password must be at least 8 characters",
            error_code="WEAK_PASSWORD",
            details={"field": "password", "min_length": 8}
        )


# EJEMPLO 3: Recurso no encontrado
# ================================

from exceptions import ResourceNotFoundException

async def get_user(user_id: int):
    user = await UserRepository.get(user_id)
    
    if not user:
        raise ResourceNotFoundException(
            resource="User",
            resource_id=user_id,
            error_code="USER_NOT_FOUND"
        )
    return user


# EJEMPLO 4: Entrada duplicada
# ============================

from exceptions import DuplicateEntryException

async def register_user(email: str):
    existing_user = await UserRepository.get_by_email(email)
    
    if existing_user:
        raise DuplicateEntryException(
            field="email",
            value=email,
            error_code="EMAIL_ALREADY_EXISTS"
        )


# EJEMPLO 5: Respuestas HTTP estructuradas esperadas
# ===================================================

# Error de validación (422):
# {
#     "status_code": 422,
#     "error_code": "VALIDATION_ERROR",
#     "message": "Request validation failed",
#     "details": {
#         "errors": [
#             {
#                 "field": "email",
#                 "message": "value is not a valid email address",
#                 "type": "value_error.email"
#             }
#         ]
#     },
#     "timestamp": "2024-06-03T10:30:45.123456"
# }

# Error de autenticación (401):
# {
#     "status_code": 401,
#     "error_code": "AUTHENTICATION_ERROR",
#     "message": "Invalid credentials",
#     "details": {},
#     "timestamp": "2024-06-03T10:30:45.123456"
# }

# Error de recurso no encontrado (404):
# {
#     "status_code": 404,
#     "error_code": "NOT_FOUND",
#     "message": "User not found (ID: 123)",
#     "details": {},
#     "timestamp": "2024-06-03T10:30:45.123456"
# }

# Error de entrada duplicada (409):
# {
#     "status_code": 409,
#     "error_code": "DUPLICATE_ENTRY",
#     "message": "A record with email 'user@example.com' already exists",
#     "details": {
#         "email": "user@example.com"
#     },
#     "timestamp": "2024-06-03T10:30:45.123456"
# }
