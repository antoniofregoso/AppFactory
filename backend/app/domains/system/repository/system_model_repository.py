import uuid as uuid_lib

from sqlalchemy import delete, inspect, select
from sqlalchemy.orm import selectinload

from app.core.database.session import db
from app.domains.system.models import (
    SystemApp,
    SystemAppSettings,
    SystemCompany,
    SystemCountry,
    SystemCountryState,
    SystemCurrency,
    SystemLang,
    SystemMessage,
    SystemNotification,
    SystemTask,
    SystemTimezone,
    SystemWhatsApp,
    SystemWhatsAppMessage,
    SystemWhatsAppTemplate,
)
from app.domains.system.models.system_model_followers import SystemModelFollowers
from app.domains.system.models.system_model import (
    SystemModel,
    SystemModelField,
    SystemModelSchema,
    SystemModelSchemaUse,
)
from app.domains.users.models import UserLog, UserUser
from app.domains.users.models.user_user import UserType

MODEL_CLASS_BY_NAME = {
    "system.app": SystemApp,
    "system.app.settings": SystemAppSettings,
    "system.company": SystemCompany,
    "system.country": SystemCountry,
    "system.country.state": SystemCountryState,
    "system.currency": SystemCurrency,
    "system.lang": SystemLang,
    "system.message": SystemMessage,
    "system.model": SystemModel,
    "system.notification": SystemNotification,
    "system.task": SystemTask,
    "system.timezone": SystemTimezone,
    "system.whatsapp": SystemWhatsApp,
    "system.whatsapp.message": SystemWhatsAppMessage,
    "system.whatsapp.template": SystemWhatsAppTemplate,
    "user.log": UserLog,
    "user.user": UserUser,
}


class SystemModelRepository:
    @staticmethod
    async def create(system_model: SystemModel):
        async with db.session() as session:
            session.add(system_model)
            await session.commit()
            await session.refresh(system_model)
            return await SystemModelRepository.get_by_uuid(system_model.uuid)

    @staticmethod
    async def get_all():
        async with db.session() as session:
            query = (
                select(SystemModel)
                .options(
                    selectinload(SystemModel.fields),
                    selectinload(SystemModel.schemas),
                )
                .order_by(SystemModel.name)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_all_with_fields():
        # Skips `schemas` (unused here, and the heaviest relation on SystemModel).
        async with db.session() as session:
            query = (
                select(SystemModel)
                .options(selectinload(SystemModel.fields))
                .order_by(SystemModel.name)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(model_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemModel)
                .where(SystemModel.uuid == model_uuid)
                .options(
                    selectinload(SystemModel.fields),
                    selectinload(SystemModel.schemas),
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(name: str):
        async with db.session() as session:
            query = (
                select(SystemModel)
                .where(SystemModel.name == name)
                .options(
                    selectinload(SystemModel.fields),
                    selectinload(SystemModel.schemas),
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_view_definition(
        model_name: str,
        use: SystemModelSchemaUse | str,
        schema_name: str,
    ):
        schema_use = use.value if isinstance(use, SystemModelSchemaUse) else use
        async with db.session() as session:
            query = (
                select(SystemModel)
                .where(SystemModel.name == model_name)
                .options(
                    selectinload(SystemModel.fields),
                    selectinload(SystemModel.schemas),
                )
            )
            result = await session.execute(query)
            system_model = result.scalar_one_or_none()
            if not system_model:
                return None, None

            schema = next(
                (
                    item
                    for item in system_model.schemas
                    if item.name == schema_name
                    and (
                        item.use.value
                        if isinstance(item.use, SystemModelSchemaUse)
                        else item.use
                    )
                    == schema_use
                ),
                None,
            )
            return system_model, schema

    @staticmethod
    async def get_records(
        model_name: str,
        field_names: list[str],
        relation_names: list[str] | None = None,
    ) -> list:
        model_class = MODEL_CLASS_BY_NAME.get(model_name)
        if model_class is None:
            return []

        mapper = inspect(model_class)
        relationships = {relationship.key for relationship in mapper.relationships}
        load_names = set(field_names) | set(relation_names or [])
        options = []
        for name in load_names:
            if name not in relationships:
                continue
            attribute = getattr(model_class, name)
            loader = selectinload(attribute)
            related_class = inspect(model_class).relationships[name].mapper.class_
            if "currency" in {relation.key for relation in inspect(related_class).relationships}:
                loader = loader.selectinload(getattr(related_class, "currency"))
            options.append(loader)

        async with db.session() as session:
            query = select(model_class).options(*options)
            if hasattr(model_class, "id"):
                query = query.order_by(model_class.id)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_records_by_ids(model_name: str, record_ids: set[int]) -> dict[int, object]:
        model_class = MODEL_CLASS_BY_NAME.get(model_name)
        if model_class is None or not record_ids:
            return {}

        async with db.session() as session:
            query = select(model_class).where(model_class.id.in_(record_ids))
            result = await session.execute(query)
            return {record.id: record for record in result.scalars().all()}

    @staticmethod
    async def update_record(model_name: str, record_uuid: uuid_lib.UUID, values: dict):
        model_class = MODEL_CLASS_BY_NAME.get(model_name)
        if model_class is None:
            return None
        async with db.session() as session:
            query = select(model_class).where(model_class.uuid == record_uuid)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record is None:
                return None
            for key, value in values.items():
                setattr(record, key, value)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def create_record(model_name: str, values: dict):
        model_class = MODEL_CLASS_BY_NAME.get(model_name)
        if model_class is None:
            return None
        async with db.session() as session:
            mapper = inspect(model_class)
            prepared = dict(values)
            classes_by_table = {candidate.__tablename__: candidate for candidate in MODEL_CLASS_BY_NAME.values()}
            for name, value in list(prepared.items()):
                column = mapper.columns.get(name)
                if column is None or not column.foreign_keys or not isinstance(value, dict):
                    continue
                related_uuid = value.get("uuid")
                target_class = classes_by_table.get(next(iter(column.foreign_keys)).column.table.name)
                if not related_uuid or target_class is None:
                    prepared[name] = None
                    continue
                related = await session.scalar(select(target_class).where(target_class.uuid == related_uuid))
                prepared[name] = related.id if related else None
            record = model_class(**prepared)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def get_record_by_uuid(model_name: str, record_uuid: uuid_lib.UUID):
        model_class = MODEL_CLASS_BY_NAME.get(model_name)
        if model_class is None:
            return None
        async with db.session() as session:
            query = select(model_class).where(model_class.uuid == record_uuid)
            if model_name == "system.message":
                query = query.options(selectinload(SystemMessage.to_users))
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def delete_record(model_name: str, record_uuid: uuid_lib.UUID) -> bool:
        model_class = MODEL_CLASS_BY_NAME.get(model_name)
        if model_class is None:
            return False
        async with db.session() as session:
            query = select(model_class).where(model_class.uuid == record_uuid)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record is None:
                return False
            await session.delete(record)
            await session.commit()
            return True

    @staticmethod
    async def get_followable_users() -> list[UserUser]:
        async with db.session() as session:
            query = (
                select(UserUser)
                .where(UserUser.active.is_(True))
                .where(UserUser.user_type != UserType.SYSTEM)
                .order_by(UserUser.name)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_followers_by_record(
        model_id: int,
        record_uuids: set[uuid_lib.UUID],
    ) -> dict[str, list[UserUser]]:
        if not record_uuids:
            return {}

        async with db.session() as session:
            query = (
                select(SystemModelFollowers)
                .where(SystemModelFollowers.model_id == model_id)
                .where(SystemModelFollowers.record_uuid.in_(record_uuids))
                .options(selectinload(SystemModelFollowers.user))
            )
            result = await session.execute(query)
            followers: dict[str, list[UserUser]] = {}
            for follower in result.scalars().all():
                if follower.user is None or follower.user.user_type == UserType.SYSTEM:
                    continue
                followers.setdefault(str(follower.record_uuid), []).append(follower.user)
            return followers

    @staticmethod
    async def set_followers_for_record(
        model_id: int,
        record_uuid: uuid_lib.UUID,
        user_uuids: list[uuid_lib.UUID],
        current_user_id: int | None = None,
    ) -> list[UserUser]:
        async with db.session() as session:
            users = list((await session.execute(
                select(UserUser)
                .where(UserUser.uuid.in_(user_uuids))
                .where(UserUser.active.is_(True))
                .where(UserUser.user_type != UserType.SYSTEM)
                .order_by(UserUser.name)
            )).scalars().all()) if user_uuids else []
            await session.execute(delete(SystemModelFollowers).where(
                SystemModelFollowers.model_id == model_id,
                SystemModelFollowers.record_uuid == record_uuid,
            ))
            for user in users:
                session.add(SystemModelFollowers(
                    model_id=model_id,
                    record_uuid=record_uuid,
                    user_id=user.id,
                    create_by=current_user_id,
                ))
            await session.commit()
            return users

    @staticmethod
    async def update(model_uuid: uuid_lib.UUID, model_data: dict):
        async with db.session() as session:
            query = (
                select(SystemModel)
                .where(SystemModel.uuid == model_uuid)
                .options(
                    selectinload(SystemModel.fields),
                    selectinload(SystemModel.schemas),
                )
            )
            result = await session.execute(query)
            system_model = result.scalar_one_or_none()
            if not system_model:
                return None

            fields_data = model_data.pop("fields", None)
            schemas_data = model_data.pop("schemas", None)

            for key, value in model_data.items():
                setattr(system_model, key, value)

            if fields_data is not None:
                system_model.fields = [
                    SystemModelField(**field_data) for field_data in fields_data
                ]

            if schemas_data is not None:
                system_model.schemas = [
                    SystemModelSchema(**schema_data) for schema_data in schemas_data
                ]

            session.add(system_model)
            await session.commit()
            await session.refresh(system_model)
            return await SystemModelRepository.get_by_uuid(system_model.uuid)

    @staticmethod
    async def delete(model_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemModel)
                .where(SystemModel.uuid == model_uuid)
                .options(
                    selectinload(SystemModel.fields),
                    selectinload(SystemModel.schemas),
                )
            )
            result = await session.execute(query)
            system_model = result.scalar_one_or_none()
            if not system_model:
                return False

            await session.delete(system_model)
            await session.commit()
            return True
