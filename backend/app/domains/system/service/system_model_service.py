import uuid as uuid_lib
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import inspect

from app.core.exceptions import (
    AuthorizationException,
    DuplicateEntryException,
    ResourceNotFoundException,
    ValidationException,
)
from app.domains.users.repository.user_repository import UserRepository
from app.domains.users.service.auth_service import AuthService
from app.domains.users.service.user_activity_graphics_service import (
    PERIODS as USER_ACTIVITY_PERIODS,
    UserActivityGraphicsService,
)
from app.domains.system.service.system_message_service import SystemMessageService
from app.domains.system.models.system_model import (
    SystemModel,
    SystemModelField,
    SystemModelSchema,
    SystemModelSchemaUse,
)
from app.domains.system.repository.system_model_repository import (
    MODEL_CLASS_BY_NAME,
    SystemModelRepository,
)
from app.domains.system.search.authorization import (
    RECORD_AUTHORIZATION_POLICIES,
    authorization_policy_for,
)
from app.domains.talent.models import TalentAgent, TalentArea, TalentPosition, TalentSystem
from app.domains.talent.service import TalentService

MODEL_NAME_BY_CLASS = {cls: name for name, cls in MODEL_CLASS_BY_NAME.items()}
MODEL_NAME_BY_TABLE = {
    cls.__tablename__: name for name, cls in MODEL_CLASS_BY_NAME.items()
}
RELATION_FIELD_TYPES = {"many2one", "many2one_avatar"}
FOLLOWERS_FIELD_NAME = "followers"


def _with_locale_aliases(value):
    if isinstance(value, list):
        return [_with_locale_aliases(item) for item in value]
    if not isinstance(value, dict):
        return value

    result = {key: _with_locale_aliases(item) for key, item in value.items()}
    if "es_MX" in result and "es" not in result:
        result["es"] = result["es_MX"]
    if "en_US" in result and "en" not in result:
        result["en"] = result["en_US"]
    return result


def _schema_payload(schema) -> list[dict]:
    payload = getattr(schema, "schema", None)
    if callable(payload):
        payload = None
    if payload is None:
        payload = getattr(schema, "view", None)
    if isinstance(payload, dict) and set(payload) == {"schema"}:
        payload = payload["schema"]
    return payload or []


def _schema_field_names(schema: list[dict]) -> list[str]:
    field_names: list[str] = []
    for field in schema:
        name = field.get("name")
        if name and name not in field_names:
            field_names.append(name)
    return field_names


def _infer_relation_model(model: str, field_name: str) -> str | None:
    model_class = MODEL_CLASS_BY_NAME.get(model)
    if model_class is None:
        return None

    relationship = inspect(model_class).relationships.get(field_name)
    if relationship is not None:
        return MODEL_NAME_BY_CLASS.get(relationship.mapper.class_)

    column = inspect(model_class).columns.get(field_name)
    if column is None:
        return None

    for foreign_key in column.foreign_keys:
        return MODEL_NAME_BY_TABLE.get(foreign_key.column.table.name)
    return None


def _schema_with_relation_models(model: str, schema: list[dict]) -> list[dict]:
    fields: list[dict] = []
    for field in schema:
        field_type = field.get("type", "")
        if (
            field_type not in RELATION_FIELD_TYPES
            and not field_type.startswith("one2many")
        ) or field.get("model"):
            fields.append(field)
            continue

        related_model = _infer_relation_model(model, field.get("name", ""))
        fields.append({**field, "model": related_model} if related_model else field)
    return fields


def _schema_with_default_followers_field(
    schema: list[dict], options: list[dict]
) -> list[dict]:
    if any(field.get("type") == "one2many_followers" for field in schema):
        return [
            (
                {**field, "options": options}
                if field.get("type") == "one2many_followers"
                else field
            )
            for field in schema
        ]
    return [
        *schema,
        {
            "name": FOLLOWERS_FIELD_NAME,
            "type": "one2many_followers",
            "label": {"es_MX": "Seguidores", "en_US": "Followers"},
            "form": {"footer": "left"},
            "options": options,
        },
    ]


def _schema_with_user_options(schema: list[dict], options: list[dict]) -> list[dict]:
    return [
        (
            {**field, "model": "user.user", "options": options}
            if field.get("name") == "to_users"
            and field.get("type") in {"many2many", "many2many_pills"}
            else field
        )
        for field in schema
    ]


def _relation_model_map(
    schema: list[dict], relation_map: dict[str, str]
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field in schema:
        field_name = field.get("name", "")
        related_model = field.get("model")
        if (
            field.get("type") in RELATION_FIELD_TYPES
            and field_name.endswith("_id")
            and related_model
            and field_name not in relation_map
        ):
            mapping[field_name] = related_model
    return mapping


def _relation_map(model: str, schema: list[dict]) -> dict[str, str]:
    """Map FK columns (e.g. "company_id") to their relationship attribute
    (e.g. "company") for many2one/many2one_avatar schema fields, so records
    can embed the related {uuid, name, model} instead of the raw id."""
    model_class = MODEL_CLASS_BY_NAME.get(model)
    if model_class is None:
        return {}

    relationships = {relation.key for relation in inspect(model_class).relationships}
    mapping: dict[str, str] = {}
    for field in schema:
        field_name = field.get("name", "")
        if field.get("type") not in RELATION_FIELD_TYPES:
            continue
        if not field_name.endswith("_id"):
            continue
        attr_name = field_name[:-3]
        if attr_name in relationships:
            mapping[field_name] = attr_name
    return mapping


def _serialize_value(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if hasattr(value, "__mapper__"):
        return _serialize_related_record(value)
    return value


def _serialize_related_record(record) -> dict:
    payload = {}
    for column in record.__mapper__.column_attrs:
        if column.key == "id":
            continue
        key = (
            "schema"
            if isinstance(record, SystemModelSchema) and column.key == "view"
            else column.key
        )
        payload[key] = _serialize_value(getattr(record, column.key, None))
    payload["display_name"] = _display_name(record)
    payload["model"] = MODEL_NAME_BY_CLASS.get(type(record))
    return payload


def _localized_dict_value(value: dict) -> str:
    for key in ("es", "es_MX", "en", "en_US"):
        if value.get(key):
            return value[key]
    return next((item for item in value.values() if item), "")


def _display_name(related):
    for method_name in ("get_label", "get_name"):
        method = getattr(related, method_name, None)
        if callable(method):
            try:
                value = method("es_MX", "en_US")
            except TypeError:
                value = method()
            if value:
                return value
    name = getattr(related, "name", None)
    if isinstance(name, dict):
        return _localized_dict_value(name)
    if name:
        return name
    for attr_name in ("label", "title", "code", "email"):
        value = getattr(related, attr_name, None)
        if isinstance(value, dict):
            value = _localized_dict_value(value)
        if value:
            return value
    return str(getattr(related, "uuid", ""))


def _serialize_many2one(related) -> dict:
    display_name = _display_name(related)
    payload = {
        "uuid": _serialize_value(getattr(related, "uuid", None)),
        "name": display_name,
        "display_name": display_name,
        "model": MODEL_NAME_BY_CLASS.get(type(related)),
    }
    avatar = getattr(related, "avatar_url", None)
    if avatar:
        payload["avatar"] = avatar
    currency = getattr(related, "currency", None)
    if currency:
        payload["currency"] = {
            "code": currency.code,
            "symbol": currency.symbol,
            "position": _serialize_value(currency.position),
        }
    return payload


def _serialize_follower(user) -> dict:
    return {
        "uuid": _serialize_value(getattr(user, "uuid", None)),
        "name": _display_name(user),
        "display_name": _display_name(user),
        "email": str(getattr(user, "email", "")) or None,
        "avatar": getattr(user, "avatar_url", None),
        "user_type": _serialize_value(getattr(user, "user_type", None)),
        "model": "user.user",
    }


USER_SCOPED_MODELS = frozenset(RECORD_AUTHORIZATION_POLICIES)
TALENT_MODEL_CLASS_BY_NAME = {
    "talent.agent": TalentAgent,
    "talent.area": TalentArea,
    "talent.position": TalentPosition,
    "talent.system": TalentSystem,
}
COMPANY_SCOPED_MODELS = {"parties.party", *TALENT_MODEL_CLASS_BY_NAME}
READ_ONLY_MODELS = {"user.log"}
WRITABLE_MANY2MANY_RELATIONS = {
    "access.role": {"permissions"},
    "system.country": {"timezones"},
}
ACCESS_CONTROLLED_MODELS = {
    "access.permission",
    "access.role",
    "access.user.role",
    "parties.party",
    "system.country",
    "system.country.state",
    "system.lang",
    *TALENT_MODEL_CLASS_BY_NAME,
}
INSIGHT_GENERATORS = {
    ("system.insight", "userLogs"): UserActivityGraphicsService.get,
}


def _hydrate_insight_collection(
    configured: list, generated: list[dict], collection: str
) -> list[dict]:
    generated_by_id = {item.get("id"): item for item in generated}
    hydrated: list[dict] = []
    for configured_item in configured:
        item_id = (
            configured_item
            if isinstance(configured_item, str)
            else configured_item.get("id")
        )
        item = generated_by_id.get(item_id)
        if item is None:
            raise ValidationException(
                f"Insight {collection} item '{item_id}' has no registered output"
            )
        hydrated.append(item)
    return hydrated


async def _build_insight_view(
    system_model,
    schema,
    current_user,
    requested_period: str | None,
    requested_timezone: str | None,
) -> dict:
    if current_user is None:
        raise AuthorizationException("Authentication is required")
    from app.domains.access.service import AccessService
    await AccessService.require(current_user, "system.insight.read", company_id=current_user.company_id)

    generator = INSIGHT_GENERATORS.get((system_model.name, schema.name))
    if generator is None:
        raise ResourceNotFoundException(
            resource="InsightGenerator",
            resource_id=f"{system_model.name}/{schema.name}",
        )

    configured = dict(schema.view or {})
    period = requested_period or configured.get("period") or "today"
    if period not in USER_ACTIVITY_PERIODS:
        raise ValidationException(f"Unsupported insight period: {period}")
    generated = await generator(
        period,
        current_user.company_id,
        timezone_name=requested_timezone,
    )
    insight = {
        **configured,
        "period": period,
        "kpis": _hydrate_insight_collection(
            configured.get("kpis", []), generated.get("kpis", []), "kpis"
        ),
        "gauges": _hydrate_insight_collection(
            configured.get("gauges", []), generated.get("gauges", []), "gauges"
        ),
        "graphics": _hydrate_insight_collection(
            configured.get("graphics", []),
            generated.get("graphics", []),
            "graphics",
        ),
    }
    return {
        "model": {
            "name": system_model.name,
            "label": _with_locale_aliases(system_model.label),
            "readonly": True,
            "schema": insight,
        },
        "records": [],
    }


async def _schema_with_relation_options(schema: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for field in schema:
        if (
            field.get("type") != "many2many_pills"
            or not field.get("model")
            or field.get("options")
        ):
            enriched.append(field)
            continue
        related = await SystemModelRepository.get_records(
            field["model"],
            ["uuid", "name", "code"],
        )
        enriched.append(
            {
                **field,
                "options": [_serialize_related_record(record) for record in related],
            }
        )
    return enriched


async def _schema_with_selection_options(schema: list[dict]) -> list[dict]:
    """Populate a selection from another registered system model.

    ``selection_model`` is intentionally separate from ``model`` because the
    stored field remains a scalar value rather than a database relationship.
    """
    enriched: list[dict] = []
    for field in schema:
        source_model = field.get("selection_model")
        if (
            field.get("type") != "selection"
            or not source_model
            or field.get("selection_values")
        ):
            enriched.append(field)
            continue
        records = await SystemModelRepository.get_records(
            source_model,
            ["name", "label"],
        )
        options = []
        for record in records:
            value = str(getattr(record, "name", ""))
            label = getattr(record, "label", {})
            option = {"value": value, "color": "zinc"}
            if isinstance(label, dict):
                option.update(label)
            if not option.get("es_MX"):
                option["es_MX"] = value
            if not option.get("en_US"):
                option["en_US"] = value
            options.append(option)
        enriched.append({**field, "selection_values": options})
    return enriched


def _require_writable_model(model: str) -> None:
    if model in READ_ONLY_MODELS:
        raise AuthorizationException(f"Model '{model}' is read-only")


async def _require_model_permission(
    model: str,
    action: str,
    *,
    current_user_id: int | None = None,
    current_user=None,
) -> None:
    if model not in ACCESS_CONTROLLED_MODELS:
        return
    user = current_user
    if user is None and current_user_id is not None:
        user = await UserRepository.get_by_id(current_user_id)
    if user is None or getattr(user, "id", None) is None:
        return
    from app.domains.access.service import AccessService
    await AccessService.require(
        user,
        f"{model}.{action}",
        company_id=user.company_id,
    )


def _coerce_temporal_strings(model_class, values: dict) -> dict:
    """Parse ISO date/datetime strings into Python objects before they reach
    the DB driver. HTML `datetime-local`/`date` inputs submit plain strings,
    but asyncpg requires real `date`/`datetime` instances for those columns."""
    mapper_columns = inspect(model_class).columns
    for key, value in list(values.items()):
        if value is None or not isinstance(value, str):
            continue
        try:
            python_type = mapper_columns[key].type.python_type
        except (AttributeError, NotImplementedError, KeyError):
            continue
        if python_type is datetime:
            values[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif python_type is date:
            values[key] = date.fromisoformat(value)
    return values


def _belongs_to_user(model: str, record, current_user_id: int) -> bool:
    policy = authorization_policy_for(model)
    return policy is None or policy.allows_record(record, current_user_id)


async def _company_record(model: str, record_uuid, company_id: int):
    talent_model = TALENT_MODEL_CLASS_BY_NAME.get(model)
    if talent_model is not None:
        return await TalentService.get_by_uuid(talent_model, record_uuid, company_id)
    record = await SystemModelRepository.get_record_by_uuid(model, record_uuid)
    return record if record is not None and getattr(record, "company_id", None) == company_id else None


async def _validate_company_relations(model_class, values: dict, company_id: int) -> None:
    classes_by_table = {candidate.__tablename__: candidate for candidate in MODEL_CLASS_BY_NAME.values()}
    for field_name, value in values.items():
        if not isinstance(value, dict) or not value.get("uuid"):
            continue
        column = inspect(model_class).columns.get(field_name)
        if column is None or not column.foreign_keys:
            continue
        target_class = classes_by_table.get(next(iter(column.foreign_keys)).column.table.name)
        target_model = MODEL_NAME_BY_CLASS.get(target_class)
        if target_model is None:
            continue
        target = await SystemModelRepository.get_record_by_uuid(
            target_model, uuid_lib.UUID(str(value["uuid"]))
        )
        if target is None:
            raise ValidationException(f"Invalid {field_name}")
        if target_model in TALENT_MODEL_CLASS_BY_NAME:
            target = await _company_record(target_model, value["uuid"], company_id)
        elif "company_id" in inspect(target_class).columns:
            target = target if getattr(target, "company_id", None) == company_id else None
        if target is None:
            raise ValidationException(f"Invalid {field_name}")


# Fields on user.user that grant privileges or bypass normal signup checks —
# only an admin may set them through the generic model create/update endpoints.
USER_ADMIN_ONLY_FIELDS = {"mcp_access", "active", "email"}


async def _require_admin_for_user_fields(
    values: dict, current_user_id: int | None, restricted_fields: set[str]
) -> None:
    touched = restricted_fields & set(values)
    if not touched:
        return
    caller = (
        await UserRepository.get_by_id(current_user_id)
        if current_user_id is not None
        else None
    )
    from app.domains.access.service import AccessService
    if not caller or not await AccessService.has_permission(caller, "system.user.manage", company_id=caller.company_id):
        raise AuthorizationException(
            f"Only an admin can set: {', '.join(sorted(touched))}"
        )


def _serialize_record(
    record,
    field_names: list[str],
    relation_map: dict[str, str] | None = None,
    relation_model_map: dict[str, str] | None = None,
    related_lookup: dict[tuple[str, int], object] | None = None,
    followers_lookup: dict[str, list[dict]] | None = None,
) -> dict:
    relation_map = relation_map or {}
    relation_model_map = relation_model_map or {}
    related_lookup = related_lookup or {}
    followers_lookup = followers_lookup or {}
    result = {}
    for field_name in field_names:
        if field_name == FOLLOWERS_FIELD_NAME:
            result[field_name] = followers_lookup.get(
                str(getattr(record, "uuid", "")), []
            )
            continue
        relation_attr = relation_map.get(field_name)
        if relation_attr:
            related = getattr(record, relation_attr, None)
            result[field_name] = (
                _serialize_many2one(related) if related is not None else None
            )
        elif field_name in relation_model_map:
            related_id = getattr(record, field_name, None)
            related = related_lookup.get((relation_model_map[field_name], related_id))
            result[field_name] = (
                _serialize_many2one(related) if related is not None else None
            )
        else:
            result[field_name] = _serialize_value(getattr(record, field_name, None))
    return result


class SystemModelService:
    @staticmethod
    async def create_record(
        model: str,
        values: dict,
        current_user_id: int | None = None,
    ) -> dict:
        _require_writable_model(model)
        await _require_model_permission(
            model, "create", current_user_id=current_user_id
        )
        if model == "system.message":
            sender = (
                await UserRepository.get_by_id(current_user_id)
                if current_user_id is not None
                else None
            )
            if sender is None:
                raise ValidationException("Message sender is required")
            recipient_values = values.get("to_users") or []
            recipient_uuids = [
                item.get("uuid") if isinstance(item, dict) else item
                for item in recipient_values
                if (isinstance(item, dict) and item.get("uuid"))
                or isinstance(item, str)
            ]
            if not recipient_uuids:
                raise ValidationException("At least one message recipient is required")
            message = await SystemMessageService.create(
                {
                    "subject": values.get("subject") or {},
                    "message": values.get("message") or {},
                    "from_user_uuid": sender.uuid,
                    "to_user_uuids": recipient_uuids,
                }
            )
            return {
                "uuid": str(message.uuid),
                "status": _serialize_value(message.status),
                "date": _serialize_value(message.date),
                "subject": message.subject,
                "message": message.message,
                "from_user_id": _serialize_follower(message.from_user),
                "to_users": [_serialize_follower(user) for user in message.to_users],
                "created_at": _serialize_value(message.created_at),
                "followers": [_serialize_follower(sender)],
            }
        model_class = MODEL_CLASS_BY_NAME.get(model)
        if model_class is None:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=model)
        protected = {
            "id",
            "uuid",
            "created_at",
            "create_by",
            "updated_at",
            "updated_by",
        }
        columns = {column.key for column in inspect(model_class).columns} - protected
        writable_relations = WRITABLE_MANY2MANY_RELATIONS.get(model, set())
        invalid = set(values) - columns - writable_relations
        if invalid:
            raise ValidationException(
                f"Fields cannot be created: {', '.join(sorted(invalid))}"
            )
        prepared = {
            key: value for key, value in values.items() if value not in (None, "", [])
        }
        if model in COMPANY_SCOPED_MODELS:
            caller = (
                await UserRepository.get_by_id(current_user_id)
                if current_user_id is not None
                else None
            )
            if caller is None or caller.company_id is None:
                raise AuthorizationException("User has no company")
            if "company_id" in columns:
                prepared["company_id"] = caller.company_id
            await _validate_company_relations(model_class, prepared, caller.company_id)
        if model == "user.user":
            await _require_admin_for_user_fields(
                prepared, current_user_id, {"mcp_access"}
            )
            name = str(prepared.get("name", "")).strip()
            email = AuthService.normalize_email(str(prepared.get("email", "")))
            password = str(prepared.get("password", ""))
            user_type = str(prepared.get("user_type", ""))
            if not 2 <= len(name) <= 100:
                raise ValidationException(
                    "Name must contain between 2 and 100 characters"
                )
            if len(password) < 8:
                raise ValidationException("Password must contain at least 8 characters")
            if user_type not in {"HUMAN", "SYSTEM", "AIAGENT"}:
                raise ValidationException("User type is required")
            if await UserRepository.get_by_email(email):
                raise DuplicateEntryException(field="email", value=email)
            prepared.update(
                name=name,
                email=email,
                password=AuthService.hash_password(password),
                user_type=user_type,
            )
        if current_user_id is not None:
            prepared["create_by"] = current_user_id
        prepared = _coerce_temporal_strings(model_class, prepared)
        record = await SystemModelRepository.create_record(model, prepared)
        if record is None:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=model)
        result = {
            column.key: _serialize_value(getattr(record, column.key))
            for column in inspect(model_class).columns
            if column.key not in {"id", "password"}
        }
        creator = (
            await UserRepository.get_by_id(current_user_id)
            if current_user_id is not None
            else None
        )
        result[FOLLOWERS_FIELD_NAME] = (
            [_serialize_follower(creator)]
            if creator and creator.user_type != "SYSTEM"
            else []
        )
        return result

    @staticmethod
    async def delete_record(
        model: str,
        record_uuid: uuid_lib.UUID,
        current_user_id: int | None = None,
    ) -> bool:
        _require_writable_model(model)
        await _require_model_permission(
            model, "delete", current_user_id=current_user_id
        )
        if model in COMPANY_SCOPED_MODELS:
            caller = (
                await UserRepository.get_by_id(current_user_id)
                if current_user_id is not None
                else None
            )
            record = (
                await _company_record(model, record_uuid, caller.company_id)
                if caller is not None and caller.company_id is not None
                else None
            )
            if record is None:
                raise ResourceNotFoundException(
                    resource=model, resource_id=str(record_uuid)
                )
        else:
            record = await SystemModelRepository.get_record_by_uuid(model, record_uuid)
        if record is None or (
            model in USER_SCOPED_MODELS
            and current_user_id is not None
            and not _belongs_to_user(model, record, current_user_id)
        ):
            raise ResourceNotFoundException(
                resource=model, resource_id=str(record_uuid)
            )
        return await SystemModelRepository.delete_record(model, record_uuid)

    @staticmethod
    async def update_record(
        model: str,
        record_uuid: uuid_lib.UUID,
        values: dict,
        current_user_id: int | None = None,
    ) -> dict:
        _require_writable_model(model)
        await _require_model_permission(
            model, "update", current_user_id=current_user_id
        )
        values = dict(values)
        follower_values = values.pop(FOLLOWERS_FIELD_NAME, None)
        model_class = MODEL_CLASS_BY_NAME.get(model)
        if model_class is None:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=model)
        protected = {
            "id",
            "uuid",
            "created_at",
            "create_by",
            "updated_at",
            "updated_by",
        }
        columns = {column.key for column in inspect(model_class).columns} - protected
        writable_relations = WRITABLE_MANY2MANY_RELATIONS.get(model, set())
        invalid = set(values) - columns - writable_relations
        if invalid:
            raise ValidationException(
                f"Fields cannot be updated: {', '.join(sorted(invalid))}"
            )
        if model == "user.user":
            if "password" in values:
                raise ValidationException(
                    "Password cannot be changed through this endpoint"
                )
            await _require_admin_for_user_fields(
                values, current_user_id, USER_ADMIN_ONLY_FIELDS
            )
        values = _coerce_temporal_strings(model_class, values)
        if model in COMPANY_SCOPED_MODELS:
            caller = (
                await UserRepository.get_by_id(current_user_id)
                if current_user_id is not None
                else None
            )
            existing = (
                await _company_record(model, record_uuid, caller.company_id)
                if caller is not None and caller.company_id is not None
                else None
            )
            if existing is None:
                raise ResourceNotFoundException(
                    resource=model, resource_id=str(record_uuid)
                )
            await _validate_company_relations(model_class, values, caller.company_id)
            values.pop("company_id", None)
        else:
            existing = await SystemModelRepository.get_record_by_uuid(model, record_uuid)
        if existing is None or (
            model in USER_SCOPED_MODELS
            and current_user_id is not None
            and not _belongs_to_user(model, existing, current_user_id)
        ):
            raise ResourceNotFoundException(
                resource=model, resource_id=str(record_uuid)
            )
        record = await SystemModelRepository.update_record(model, record_uuid, values)
        if record is None:
            raise ResourceNotFoundException(
                resource=model, resource_id=str(record_uuid)
            )
        result = {key: _serialize_value(getattr(record, key)) for key in values}
        if follower_values is not None:
            system_model = await SystemModelRepository.get_by_name(model)
            follower_uuids = [
                uuid_lib.UUID(str(item["uuid"]))
                for item in follower_values
                if isinstance(item, dict) and item.get("uuid")
            ]
            followers = await SystemModelRepository.set_followers_for_record(
                system_model.id,
                record_uuid,
                follower_uuids,
                current_user_id,
            )
            result[FOLLOWERS_FIELD_NAME] = [
                _serialize_follower(user) for user in followers
            ]
        return result

    @staticmethod
    async def create(model_data: dict):
        fields_data = model_data.pop("fields", [])
        schemas_data = model_data.pop("schemas", [])
        system_model = SystemModel(**model_data)
        system_model.fields = [
            SystemModelField(**field_data) for field_data in fields_data
        ]
        system_model.schemas = [
            SystemModelSchema(**schema_data) for schema_data in schemas_data
        ]
        return await SystemModelRepository.create(system_model)

    @staticmethod
    async def get_all():
        return await SystemModelRepository.get_all()

    @staticmethod
    async def get_by_uuid(model_uuid: uuid_lib.UUID):
        system_model = await SystemModelRepository.get_by_uuid(model_uuid)
        if not system_model:
            raise ResourceNotFoundException(
                resource="SystemModel", resource_id=str(model_uuid)
            )
        return system_model

    @staticmethod
    async def get_by_name(name: str):
        system_model = await SystemModelRepository.get_by_name(name)
        if not system_model:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=name)
        return system_model

    @staticmethod
    async def get_view(
        model: str,
        use: SystemModelSchemaUse,
        name: str,
        current_user_id: int | None = None,
        current_user=None,
        period: str | None = None,
        timezone_name: str | None = None,
    ):
        await _require_model_permission(
            model,
            "read",
            current_user_id=current_user_id,
            current_user=current_user,
        )
        system_model, schema = await SystemModelRepository.get_view_definition(
            model, use, name
        )
        if not system_model:
            raise ResourceNotFoundException(resource="SystemModel", resource_id=model)
        if not schema:
            raise ResourceNotFoundException(
                resource="SystemModelSchema",
                resource_id=f"{model}/{use.value}/{name}",
            )

        if use == SystemModelSchemaUse.insight:
            return await _build_insight_view(
                system_model,
                schema,
                current_user,
                period,
                timezone_name,
            )

        followable_users = await SystemModelRepository.get_followable_users()
        followable_by_id = {user.id: user for user in followable_users}
        follower_options = [_serialize_follower(user) for user in followable_users]
        schema_fields = _schema_with_default_followers_field(
            _schema_with_user_options(
                _schema_with_relation_models(model, _schema_payload(schema)),
                follower_options,
            ),
            follower_options,
        )
        schema_fields = await _schema_with_relation_options(schema_fields)
        schema_fields = await _schema_with_selection_options(schema_fields)
        field_names = _schema_field_names(schema_fields)
        model_class = MODEL_CLASS_BY_NAME.get(model)
        if (
            model_class is not None
            and "sequence" in inspect(model_class).columns
            and "sequence" not in field_names
        ):
            field_names.append("sequence")
        if system_model.group_by and system_model.group_by not in field_names:
            field_names.append(system_model.group_by)

        relation_map = _relation_map(model, schema_fields)
        records = await SystemModelRepository.get_records(
            model, field_names, list(relation_map.values())
        )
        if model in USER_SCOPED_MODELS and current_user_id is not None:
            records = [
                record
                for record in records
                if _belongs_to_user(model, record, current_user_id)
            ]
        if model in COMPANY_SCOPED_MODELS:
            if current_user is None or current_user.company_id is None:
                raise AuthorizationException("User has no company")
            if model in TALENT_MODEL_CLASS_BY_NAME:
                allowed = {
                    str(record.uuid)
                    for record in await TalentService.get_all(
                        TALENT_MODEL_CLASS_BY_NAME[model], current_user.company_id
                    )
                }
                records = [record for record in records if str(record.uuid) in allowed]
            else:
                records = [
                    record
                    for record in records
                    if getattr(record, "company_id", None) == current_user.company_id
                ]
        relation_model_map = _relation_model_map(schema_fields, relation_map)
        ids_by_model: dict[str, set[int]] = {}
        for record in records:
            for field_name, related_model in relation_model_map.items():
                related_id = getattr(record, field_name, None)
                if related_id is not None:
                    ids_by_model.setdefault(related_model, set()).add(related_id)

        related_lookup = {}
        for related_model, record_ids in ids_by_model.items():
            related_records = await SystemModelRepository.get_records_by_ids(
                related_model, record_ids
            )
            related_lookup.update(
                ((related_model, record_id), related_record)
                for record_id, related_record in related_records.items()
            )
        record_uuids = {
            getattr(record, "uuid")
            for record in records
            if getattr(record, "uuid", None) is not None
        }
        model_id = getattr(system_model, "id", None)
        followers_by_record = (
            await SystemModelRepository.get_followers_by_record(model_id, record_uuids)
            if model_id is not None
            else {}
        )
        followers_lookup = {}
        for record in records:
            record_uuid = str(getattr(record, "uuid", ""))
            users_by_uuid = {
                str(user.uuid): user
                for user in followers_by_record.get(record_uuid, [])
            }
            creator = followable_by_id.get(getattr(record, "create_by", None))
            if creator is not None:
                users_by_uuid.setdefault(str(creator.uuid), creator)
            followers_lookup[record_uuid] = [
                _serialize_follower(user) for user in users_by_uuid.values()
            ]
        model_payload = {
            "name": system_model.name,
            "label": _with_locale_aliases(system_model.label),
            "readonly": bool(getattr(system_model, "readonly", False)),
            "groupBy": system_model.group_by,
        }
        if getattr(system_model, "uuid", None) is not None:
            model_payload["uuid"] = str(system_model.uuid)
        if system_model.group_by:
            model_payload[system_model.group_by] = _with_locale_aliases(
                system_model.group_by_values
            )
        model_payload["tags"] = _with_locale_aliases(system_model.tags)
        model_payload["schema"] = _with_locale_aliases(schema_fields)

        return {
            "model": model_payload,
            "records": [
                _serialize_record(
                    record,
                    field_names,
                    relation_map,
                    relation_model_map,
                    related_lookup,
                    followers_lookup,
                )
                for record in records
            ],
        }

    @staticmethod
    async def update(model_uuid: uuid_lib.UUID, model_data: dict):
        system_model = await SystemModelRepository.update(model_uuid, model_data)
        if not system_model:
            raise ResourceNotFoundException(
                resource="SystemModel", resource_id=str(model_uuid)
            )
        return system_model

    @staticmethod
    async def delete(model_uuid: uuid_lib.UUID):
        deleted = await SystemModelRepository.delete(model_uuid)
        if not deleted:
            raise ResourceNotFoundException(
                resource="SystemModel", resource_id=str(model_uuid)
            )
        return True
