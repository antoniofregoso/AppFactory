from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
import jwt
import logging

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class JWTManager:
    """Gestiona la generación y verificación de tokens JWT."""

    @staticmethod
    def generate_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
        token_type: str = "access",
    ) -> str:
        """Genera un token JWT firmado con los datos proporcionados."""
        issued_at = datetime.now(timezone.utc)
        to_encode = data.copy()
        if expires_delta:
            expire = issued_at + expires_delta
        else:
            expire = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update(
            {
                "exp": expire,
                "iat": issued_at,
                "iss": settings.JWT_ISSUER,
                "aud": settings.JWT_AUDIENCE,
                "jti": str(uuid4()),
                "token_type": token_type,
            }
        )
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def generate_access_token(data: dict) -> str:
        """Genera un access token usando la duración configurada."""
        return JWTManager.generate_token(
            data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access"
        )

    @staticmethod
    def generate_refresh_token(data: dict) -> str:
        """Genera un refresh token usando la duración configurada."""
        return JWTManager.generate_token(
            data, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh"
        )

    @staticmethod
    def generate_mcp_token(data: dict) -> str:
        """Genera un token de larga duración para clientes MCP (solo lectura)."""
        return JWTManager.generate_token(
            data, timedelta(days=settings.MCP_TOKEN_EXPIRE_DAYS), "mcp"
        )

    @staticmethod
    def verify_token(token: str, expected_token_type: str | None = None) -> dict:
        """Verifica y decodifica un token JWT. Lanza ValueError si es inválido."""
        try:
            decoded = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
            )
            if (
                expected_token_type is not None
                and decoded.get("token_type") != expected_token_type
            ):
                raise ValueError("Invalid token type")
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("Intento de uso de token expirado")
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Intento de uso de token inválido: {e}")
            raise ValueError("Invalid token")
