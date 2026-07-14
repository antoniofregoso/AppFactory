"""Casos de uso de autenticación del dominio de usuarios."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from passlib.context import CryptContext
from pydantic import EmailStr, TypeAdapter, ValidationError as PydanticValidationError

from app.core.config.settings import settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    DuplicateEntryException,
    ValidationException,
)
from app.core.security.jwt_manager import JWTManager
from app.domains.users.models.user_session import UserSession
from app.domains.users.models.user_user import UserUser
from app.domains.users.repository.user_repository import UserRepository
from app.domains.users.repository.user_session_repository import UserSessionRepository
from app.domains.users.service.user_log_service import UserLogService


@dataclass(frozen=True)
class LoginResult:
    email: str
    token: str
    access_token: str
    refresh_token: str


class AuthService:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    email_adapter = TypeAdapter(EmailStr)

    @classmethod
    def normalize_email(cls, email: str) -> str:
        try:
            return str(cls.email_adapter.validate_python(email))
        except PydanticValidationError as exc:
            raise ValidationException("Invalid email address") from exc

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return AuthService.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return AuthService.pwd_context.hash(password)

    @staticmethod
    def hash_refresh_token(refresh_token: str) -> str:
        return hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            refresh_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _refresh_token_expires_at() -> datetime:
        return datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    @staticmethod
    def _session_absolute_expires_at() -> datetime:
        return datetime.now(timezone.utc) + timedelta(
            days=settings.SESSION_ABSOLUTE_EXPIRE_DAYS
        )

    @classmethod
    async def _build_login_result(
        cls,
        user: UserUser,
        absolute_expires_at: datetime | None = None,
    ) -> LoginResult:
        email = user.email
        token_data = {"sub": email}
        access_token = JWTManager.generate_access_token(token_data)
        refresh_token = JWTManager.generate_refresh_token(token_data)
        if absolute_expires_at is None:
            absolute_expires_at = cls._session_absolute_expires_at()
        await UserSessionRepository.create(
            UserSession(
                user_id=user.id,
                refresh_token_hash=cls.hash_refresh_token(refresh_token),
                expires_at=cls._refresh_token_expires_at(),
                absolute_expires_at=absolute_expires_at,
            )
        )
        return LoginResult(
            email=email,
            token=access_token,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @classmethod
    async def login(cls, email: str, password: str) -> LoginResult:
        normalized_email = cls.normalize_email(email)
        existing_user = await UserRepository.get_by_email(normalized_email)

        if not existing_user or not cls.verify_password(
            password, existing_user.password
        ):
            raise AuthenticationException("Invalid email or password")
        if not existing_user.active:
            raise AuthorizationException("User account is disabled")

        return await cls._build_login_result(existing_user)

    @classmethod
    async def refresh_session(cls, refresh_token: str) -> LoginResult:
        try:
            payload = JWTManager.verify_token(
                refresh_token, expected_token_type="refresh"
            )
        except ValueError as exc:
            raise AuthenticationException("Invalid or expired refresh token") from exc

        email = payload.get("sub")
        if not isinstance(email, str):
            raise AuthenticationException("Invalid refresh token")

        refresh_token_hash = cls.hash_refresh_token(refresh_token)
        session = await UserSessionRepository.get_active_by_refresh_token_hash(
            refresh_token_hash
        )
        if not session:
            reused_session = await UserSessionRepository.get_by_refresh_token_hash(
                refresh_token_hash
            )
            if reused_session and reused_session.revoked_at is not None:
                await UserSessionRepository.revoke_all_by_user_id(
                    reused_session.user_id
                )
                raise AuthenticationException("Refresh token reuse detected")
            raise AuthenticationException("Invalid refresh token")

        existing_user = await UserRepository.get_by_email(email)
        if not existing_user:
            raise AuthenticationException("Invalid refresh token")
        if session.user_id != existing_user.id:
            raise AuthenticationException("Invalid refresh token")
        if not existing_user.active:
            raise AuthorizationException("User account is disabled")

        await UserSessionRepository.revoke(session)
        return await cls._build_login_result(
            existing_user,
            absolute_expires_at=session.absolute_expires_at,
        )

    @classmethod
    async def logout(cls, refresh_token: str) -> bool:
        if not refresh_token:
            return True
        refresh_token_hash = cls.hash_refresh_token(refresh_token)
        session = await UserSessionRepository.get_by_refresh_token_hash(
            refresh_token_hash
        )
        if session is not None:
            await UserLogService.close_open_for_user(session.user_id)
        await UserSessionRepository.revoke_by_refresh_token_hash(refresh_token_hash)
        return True

    @classmethod
    async def revoke_user_sessions(cls, user_id: int) -> int:
        return await UserSessionRepository.revoke_all_by_user_id(user_id)

    @classmethod
    async def register(cls, name: str, email: str, password: str) -> str:
        normalized_name = name.strip()
        normalized_email = cls.normalize_email(email)

        if not 2 <= len(normalized_name) <= 100:
            raise ValidationException("Name must contain between 2 and 100 characters")
        if len(password) < 8:
            raise ValidationException("Password must contain at least 8 characters")

        if await UserRepository.get_by_email(normalized_email):
            raise DuplicateEntryException(field="email", value=normalized_email)

        new_user = UserUser(
            name=normalized_name,
            email=normalized_email,
            password=cls.hash_password(password),
        )
        await UserRepository.create(new_user)
        return "User registered successfully"
