import uuid as uuid_lib

from app.domains.users.repository.user_repository import UserRepository
from app.core.exceptions import AuthenticationException, ResourceNotFoundException
from app.domains.users.service.auth_service import AuthService


class UserService:

    @staticmethod
    async def get_all():
        return await UserRepository.get_all()

    @staticmethod
    async def get_user_by_uuid(user_uuid: uuid_lib.UUID):
        user = await UserRepository.get_user_by_uuid(user_uuid)
        if not user:
            raise ResourceNotFoundException(resource="User", resource_id=str(user_uuid))
        return user

    @staticmethod
    async def get_by_email(email: str):
        user = await UserRepository.get_by_email(email)
        if not user:
            raise ResourceNotFoundException(resource="User", resource_id=email)
        return user

    @staticmethod
    async def update(
        user_uuid: uuid_lib.UUID,
        user_data: dict,
        current_password: str | None = None,
    ):
        revoke_sessions = "password" in user_data or user_data.get("active") is False
        if revoke_sessions:
            existing_user = await UserService.get_user_by_uuid(user_uuid)
            if not current_password or not AuthService.verify_password(
                current_password,
                existing_user.password,
            ):
                raise AuthenticationException(
                    "Current password is required for critical operations"
                )
        if "password" in user_data:
            user_data = {
                **user_data,
                "password": AuthService.hash_password(user_data["password"]),
            }
        user = await UserRepository.update(user_uuid, user_data)
        if not user:
            raise ResourceNotFoundException(resource="User", resource_id=str(user_uuid))
        if revoke_sessions:
            await AuthService.revoke_user_sessions(user.id)
        return user

    @staticmethod
    async def delete(user_uuid: uuid_lib.UUID):
        deleted = await UserRepository.delete(user_uuid)
        if not deleted:
            raise ResourceNotFoundException(resource="User", resource_id=str(user_uuid))
        return True
