"""Crea una base de datos limpia y carga los datos iniciales del sistema.

Ejecutar desde el directorio backend:

    python scripts/setup_database.py
"""

from __future__ import annotations

import asyncio
import json
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config.settings import settings
from app.domains.system.models import (  # noqa: F401
    SystemApp,
    SystemAppSettings,
    SystemCompany,
    SystemCountry,
    SystemCountryState,
    SystemCurrency,
    SystemLang,
    SystemModel,
    SystemModelField,
    SystemModelSchema,
    SystemTimezone,
)
from app.domains.parties.models import PartiesParty  # noqa: F401
from app.domains.talent import models as talent_models  # noqa: F401
from app.domains.users.service.auth_service import AuthService
from app.domains.users.models import UserType, UserUser  # noqa: F401
from app.domains.access.models import (  # noqa: F401
    AccessPermission, AccessRole, AccessRolePermission, AccessScopeType, AccessUserRole,
)
from app.domains.system.search.indexes import SEARCH_INDEXES, create_index_statement

DATA_DIR = BACKEND_DIR / "app" / "domains" / "system" / "data"
PARTIES_DATA_DIR = BACKEND_DIR / "app" / "domains" / "parties" / "data"
TALENT_DATA_DIR = BACKEND_DIR / "app" / "domains" / "talent" / "data"
ACCESS_DATA_DIR = BACKEND_DIR / "app" / "domains" / "access" / "data"
BOT_NAME = "App Bot"
MODEL_DATA_SOURCES = (
    (DATA_DIR, "system_models.json", "system_model_schemas.json"),
    (PARTIES_DATA_DIR, "system_models.json", "system_model_schemas.json"),
    (TALENT_DATA_DIR, "system_models.json", "system_model_schemas.json"),
    (ACCESS_DATA_DIR, "system_model.json", "system_model_schema.json"),
)

# Fresh databases get the current schema from SQLModel and current data from
# the JSON sources. This checkpoint only allows later data-only migrations to
# run. Search indexes are installed explicitly by create_schema(), because
# their historical migration revisions are before this checkpoint.
# Every migration after this revision must remain safe on a schema produced by
# create_all; move the checkpoint forward when adding schema migrations.
_POST_SCHEMA_MIGRATIONS_BASE_REVISION = "9fa0b1c2d3e4"


def _load_json(file_name: str, data_dir: Path | None = None) -> Any:
    base_dir = data_dir or DATA_DIR
    with (base_dir / file_name).open(encoding="utf-8") as file:
        return json.load(file)


def _access_control_sources() -> list[tuple[Path, dict[str, Any]]]:
    return [
        (path.parent, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(
            (BACKEND_DIR / "app" / "domains").glob("*/data/access_control.json")
        )
    ]


def _validate_seed_sources() -> None:
    countries = _load_json("system_country.json")
    country_codes = {record.get("code") for record in countries}
    timezones = _load_json("system_timezone.json")
    timezone_codes = [record.get("code") for record in timezones]
    if len(timezone_codes) != len(set(timezone_codes)):
        raise RuntimeError("system_timezone.json contains duplicate timezone codes")
    invalid_country_codes = {
        country_code
        for record in timezones
        for country_code in record.get("country_codes", [])
        if country_code not in country_codes
    }
    if invalid_country_codes:
        codes = ", ".join(sorted(invalid_country_codes))
        raise RuntimeError(
            f"system_timezone.json references unknown countries: {codes}"
        )

    all_model_names: set[str] = set()
    for data_dir, models_file, schemas_file in MODEL_DATA_SOURCES:
        models = _load_json(models_file, data_dir)
        schemas = _load_json(schemas_file, data_dir)
        model_names = {record.get("name") for record in models}
        duplicate_models = all_model_names & model_names
        if duplicate_models:
            names = ", ".join(sorted(duplicate_models))
            raise RuntimeError(f"Duplicate models across data sources: {names}")
        all_model_names.update(model_names)

        invalid_schemas = {
            record.get("model") for record in schemas
        } - model_names
        if invalid_schemas:
            names = ", ".join(sorted(str(name) for name in invalid_schemas))
            raise RuntimeError(
                f"Schemas in '{data_dir}' reference models from another source: "
                f"{names}"
            )

    permission_codes: set[str] = set()
    role_codes: set[str] = set()
    assignments: list[tuple[Path, dict[str, Any]]] = []
    for data_dir, source in _access_control_sources():
        permissions = source.get("permissions") or []
        roles = source.get("roles") or []
        local_permissions = [item.get("code") for item in permissions]
        local_roles = [item.get("code") for item in roles]
        duplicate_permissions = permission_codes & set(local_permissions)
        duplicate_roles = role_codes & set(local_roles)
        if len(local_permissions) != len(set(local_permissions)) or duplicate_permissions:
            raise RuntimeError(f"Duplicate permissions in '{data_dir / 'access_control.json'}'")
        if len(local_roles) != len(set(local_roles)) or duplicate_roles:
            raise RuntimeError(f"Duplicate roles in '{data_dir / 'access_control.json'}'")
        permission_codes.update(local_permissions)
        role_codes.update(local_roles)
        assignments.extend((data_dir, item) for item in source.get("assignments") or [])

    for data_dir, source in _access_control_sources():
        for role in source.get("roles") or []:
            missing = set(role.get("permissions") or []) - permission_codes
            if missing:
                raise RuntimeError(
                    f"Role '{role.get('code')}' in '{data_dir}' references unknown permissions: "
                    f"{', '.join(sorted(missing))}"
                )
    for data_dir, assignment in assignments:
        if assignment.get("role") not in role_codes:
            raise RuntimeError(
                f"Assignment in '{data_dir}' references unknown role: {assignment.get('role')}"
            )


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _database_url() -> tuple[Any, str]:
    url = make_url(settings.DATABASE_URL)
    database = url.database
    if not database:
        raise RuntimeError("DATABASE_URL must include a database name.")
    return url, database


async def _database_exists(admin_url: Any, database: str) -> bool:
    engine = create_async_engine(admin_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database"),
                {"database": database},
            )
            return result.scalar_one_or_none() == 1
    finally:
        await engine.dispose()


async def _drop_database(admin_url: Any, database: str) -> None:
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    quoted_database = _quote_identifier(database)
    try:
        async with engine.connect() as conn:
            await conn.execute(
                text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database
                      AND pid <> pg_backend_pid()
                    """),
                {"database": database},
            )
            await conn.execute(text(f"DROP DATABASE {quoted_database}"))
    finally:
        await engine.dispose()


async def _create_database(admin_url: Any, database: str) -> None:
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    quoted_database = _quote_identifier(database)
    try:
        async with engine.connect() as conn:
            await conn.execute(text(f"CREATE DATABASE {quoted_database}"))
    finally:
        await engine.dispose()


async def reset_database() -> None:
    url, database = _database_url()
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("This setup script currently supports PostgreSQL only.")

    admin_database = "postgres" if database != "postgres" else "template1"
    admin_url = url.set(database=admin_database)

    if await _database_exists(admin_url, database):
        answer = input(
            f"The database '{database}' already exists. "
            "Delete it and continue? [y/N]: "
        )
        if answer.strip().lower() not in {"y", "yes", "s", "si", "sí"}:
            print("Setup stopped. The existing database was not changed.")
            raise SystemExit(1)
        await _drop_database(admin_url, database)
        print(f"Deleted database '{database}'.")

    await _create_database(admin_url, database)
    print(f"Created database '{database}'.")


async def create_schema() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.run_sync(SQLModel.metadata.create_all)
            for index in SEARCH_INDEXES:
                await conn.execute(
                    text(create_index_statement(index, if_not_exists=True))
                )

            expected = {index.name for index in SEARCH_INDEXES}
            actual_rows = (
                await conn.execute(
                    text("""
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE schemaname = current_schema()
                          AND indexname::text = ANY(CAST(:index_names AS text[]))
                    """),
                    {"index_names": sorted(expected)},
                )
            ).all()
            actual = {name for name, _definition in actual_rows}
            missing = expected - actual
            non_gin = {
                name
                for name, definition in actual_rows
                if "USING gin" not in definition
            }
            if missing or non_gin:
                details = []
                if missing:
                    details.append(f"missing: {', '.join(sorted(missing))}")
                if non_gin:
                    details.append(f"not GIN: {', '.join(sorted(non_gin))}")
                raise RuntimeError(
                    "Search index verification failed (" + "; ".join(details) + ")"
                )
    finally:
        await engine.dispose()
    print(
        f"Created database tables, pg_trgm, and {len(SEARCH_INDEXES)} search GIN indexes."
    )


def apply_post_schema_migrations() -> None:
    alembic_bin = Path(sys.executable).parent / "alembic"
    subprocess.run(
        [str(alembic_bin), "stamp", _POST_SCHEMA_MIGRATIONS_BASE_REVISION],
        cwd=BACKEND_DIR,
        check=True,
    )
    subprocess.run([str(alembic_bin), "upgrade", "head"], cwd=BACKEND_DIR, check=True)
    print("Applied post-schema data migrations.")


def _audit_values(bot_id: int, now: datetime) -> dict[str, Any]:
    return {
        "created_at": now,
        "create_by": bot_id,
        "updated_at": now,
        "updated_by": bot_id,
    }


def _bool_or_default(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _hash_password(password: str | None) -> str:
    return AuthService.hash_password(password or "ChangeMe123!")


def _hash_internal_password() -> str:
    return AuthService.hash_password(secrets.token_urlsafe(64))


def _localized_dict(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"es_MX": str(value), "en_US": str(value)}


def _currency_payload(
    record: dict[str, Any], bot_id: int, now: datetime
) -> dict[str, Any]:
    currency_code = record.get("name")
    return {
        **_audit_values(bot_id, now),
        "name": currency_code,
        "code": currency_code,
        "iso_numeric": _int_or_none(record.get("code")) or 0,
        "symbol": record.get("symbol") or currency_code,
        "currency_unit_label": record.get("currency_unit_label"),
        "currency_subunit_label": record.get("currency_subunit_label"),
        "active": _bool_or_default(record.get("active"), True),
    }


async def _load_bot(session: AsyncSession, now: datetime) -> UserUser:
    users = _load_json("user_users.json")
    bot_record = next(
        (record for record in users if record.get("name") == BOT_NAME),
        users[0] if users else None,
    )
    if not bot_record:
        raise RuntimeError("user_users.json must include App Bot.")

    bot = UserUser(
        name=bot_record["name"],
        email=bot_record.get("email") or "app.bot@internal.local",
        password=_hash_internal_password(),
        user_type=UserType(bot_record.get("type") or UserType.SYSTEM.value),
        active=False,
        created_at=now,
        updated_at=now,
    )
    session.add(bot)
    await session.flush()

    bot.create_by = bot.id
    bot.updated_by = bot.id
    await session.flush()
    return bot


async def _load_langs(
    session: AsyncSession, bot_id: int, now: datetime
) -> dict[str, SystemLang]:
    records = _load_json("system_lang.json")
    langs: dict[str, SystemLang] = {}
    for record in records:
        lang = SystemLang(
            **_audit_values(bot_id, now),
            name=record["name"],
            search=_bool_or_default(record.get("search")),
            code=record["code"],
            iso_code=record["iso_code"],
            url_code=record["url_code"],
            date_format=record.get("date_format"),
            time_format=record.get("time_format"),
            week_start=_int_or_none(record.get("week_start")),
            flag=record.get("flag"),
            active=_bool_or_default(record.get("active")),
        )
        session.add(lang)
        langs[lang.code] = lang
    await session.flush()
    return langs


async def _load_remaining_users(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    langs: dict[str, SystemLang],
    companies: dict[str, SystemCompany],
    company_by_user_email: dict[str, SystemCompany],
) -> None:
    for record in _load_json("user_users.json"):
        if record.get("name") == BOT_NAME:
            continue
        lang = langs.get(record.get("lang"))
        email = (
            record.get("email")
            or f"{record['name'].lower().replace(' ', '.')}@app.local"
        )
        company = companies.get(record.get("company")) or company_by_user_email.get(
            email
        )
        session.add(
            UserUser(
                **_audit_values(bot_id, now),
                name=record["name"],
                email=email,
                password=_hash_password(record.get("password")),
                user_type=UserType(record.get("type") or UserType.HUMAN.value),
                active=_bool_or_default(record.get("active"), True),
                mcp_access=_bool_or_default(record.get("mcp_access")),
                lang_id=lang.id if lang else None,
                company_id=company.id if company else None,
            )
        )
    await session.flush()


async def _load_access_control(session: AsyncSession, bot_id: int, now: datetime) -> None:
    """Load modular RBAC declarations from each domain's access_control.json."""
    sources = _access_control_sources()
    permissions: dict[str, AccessPermission] = {}
    for _, source in sources:
        for record in source.get("permissions") or []:
            code = record["code"]
            parts = code.split(".")
            if code == "*":
                domain, resource, action = "*", "*", "*"
            elif code.endswith(".*"):
                domain, resource, action = parts[0], ".".join(parts[1:-1]) or "*", "*"
            else:
                domain, resource, action = parts[0], ".".join(parts[1:-1]), parts[-1]
            permission = AccessPermission(
                **_audit_values(bot_id, now),
                code=code,
                domain=domain,
                resource=resource,
                action=action,
                name=record.get("name") or {},
                description=record.get("description") or {},
                active=_bool_or_default(record.get("active"), True),
            )
            session.add(permission)
            permissions[code] = permission
    await session.flush()

    roles: dict[str, AccessRole] = {}
    role_records: list[tuple[AccessRole, dict[str, Any]]] = []
    for _, source in sources:
        for record in source.get("roles") or []:
            role = AccessRole(
                **_audit_values(bot_id, now),
                code=record["code"],
                name=record.get("name") or {},
                description=record.get("description") or {},
                active=_bool_or_default(record.get("active"), True),
                sequence=record.get("sequence", 10),
            )
            session.add(role)
            roles[role.code] = role
            role_records.append((role, record))
    await session.flush()

    for role, record in role_records:
        session.add_all([
            AccessRolePermission(
                role_id=role.id,
                permission_id=permissions[permission_code].id,
            )
            for permission_code in record.get("permissions") or []
        ])

    for _, source in sources:
        for record in source.get("assignments") or []:
            user = (
                await session.execute(
                    select(UserUser).where(UserUser.email == record["user_email"])
                )
            ).scalar_one_or_none()
            if user is None:
                raise RuntimeError(
                    f"Access-control user {record['user_email']} is missing"
                )
            role = roles[record["role"]]
            scope_type = AccessScopeType(record.get("scope_type", "COMPANY"))
            session.add(
                AccessUserRole(
                    **_audit_values(bot_id, now),
                    user_id=user.id,
                    role_id=role.id,
                    company_id=(
                        record.get("company_id", user.company_id)
                        if scope_type != AccessScopeType.GLOBAL
                        else None
                    ),
                    scope_type=scope_type,
                    scope_model=record.get("scope_model"),
                    scope_record_uuid=record.get("scope_record_uuid"),
                    active=_bool_or_default(record.get("active"), True),
                )
            )
    await session.flush()


async def _load_currencies(
    session: AsyncSession, bot_id: int, now: datetime
) -> dict[str, SystemCurrency]:
    currencies: dict[str, SystemCurrency] = {}
    for record in _load_json("system_currency.json"):
        currency = SystemCurrency(**_currency_payload(record, bot_id, now))
        session.add(currency)
        currencies[currency.code] = currency
    await session.flush()
    return currencies


async def _load_countries(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    currencies: dict[str, SystemCurrency],
) -> dict[str, SystemCountry]:
    countries: dict[str, SystemCountry] = {}
    for record in _load_json("system_country.json"):
        currency = currencies.get(record.get("currency_code"))
        country = SystemCountry(
            **_audit_values(bot_id, now),
            code=record["code"],
            name=record["name"],
            phone_code=str(record["phone_code"]) if record.get("phone_code") else None,
            currency_id=currency.id if currency else None,
        )
        session.add(country)
        await session.flush()
        countries[country.code] = country

        for state_record in record.get("states", []):
            session.add(
                SystemCountryState(
                    code=state_record["code"],
                    name=state_record["name"],
                    country_id=country.id,
                )
            )
    await session.flush()
    return countries


async def _load_timezones(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    countries: dict[str, SystemCountry],
) -> None:
    for record in _load_json("system_timezone.json"):
        timezone_record = SystemTimezone(
            **_audit_values(bot_id, now),
            name=record["name"],
            code=record["code"],
            offset=record.get("offset", 0),
            countries=[
                countries[country_code]
                for country_code in record.get("country_codes", [])
                if country_code in countries
            ],
        )
        session.add(timezone_record)
    await session.flush()


async def _load_companies(
    session: AsyncSession, bot_id: int, now: datetime
) -> tuple[dict[str, SystemCompany], dict[str, SystemCompany]]:
    companies: dict[str, SystemCompany] = {}
    company_by_user_email: dict[str, SystemCompany] = {}
    for record in _load_json("system_company.json"):
        company = SystemCompany(
            **_audit_values(bot_id, now),
            name=record["name"],
            active=_bool_or_default(record.get("active"), True),
            email=record.get("email"),
            phone=record.get("phone"),
            website=record.get("website"),
            vat=record.get("vat"),
        )
        session.add(company)
        await session.flush()
        companies[company.name] = company

        for user_record in record.get("users", []):
            email = user_record.get("email")
            if email:
                company_by_user_email[email] = company

    return companies, company_by_user_email


async def _load_apps(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    companies: dict[str, SystemCompany],
) -> None:
    for record in _load_json("system_app.json"):
        company = companies.get(record.get("company"))
        app = SystemApp(
            **_audit_values(bot_id, now),
            name=_localized_dict(record.get("name")),
            description=_localized_dict(record.get("description")),
            active=_bool_or_default(record.get("active"), True),
            public=_bool_or_default(record.get("public"), True),
            company_id=company.id if company else None,
            keys=record.get("keys"),
            schema_org=record.get("schema_org"),
        )
        session.add(app)
        await session.flush()

        for setting_record in record.get("settings_ids", []):
            session.add(
                SystemAppSettings(
                    **_audit_values(bot_id, now),
                    app_id=app.id,
                    name=setting_record["name"],
                    description=setting_record.get("description"),
                    value=setting_record.get("value"),
                )
            )
    await session.flush()


async def _load_system_models(
    session: AsyncSession, bot_id: int, now: datetime
) -> dict[str, SystemModel]:
    models: dict[str, SystemModel] = {}
    for record in _load_json("system_models.json"):
        model = SystemModel(
            **_audit_values(bot_id, now),
            name=record["name"],
            search=_bool_or_default(record.get("search")),
            label=record["label"],
            readonly=_bool_or_default(record.get("readonly")),
            group_by=record.get("group_by") or None,
            group_by_values=record.get("group_by_values") or [],
            tags=record.get("tags") or [],
        )
        session.add(model)
        await session.flush()
        models[model.name] = model

        for index, field_record in enumerate(record.get("fields", []), start=1):
            search_config = dict(field_record.get("search") or {})
            if field_record.get("selection_values"):
                search_config["selection_values"] = field_record["selection_values"]
            session.add(
                SystemModelField(
                    **_audit_values(bot_id, now),
                    name=field_record["name"],
                    sequence=field_record.get("sequence", index * 10),
                    type=field_record.get("type", "string"),
                    required=_bool_or_default(field_record.get("required")),
                    readonly=_bool_or_default(field_record.get("readonly")),
                    placeholder=field_record.get("placeholder") or {},
                    help=field_record.get("help") or {},
                    search_config=search_config,
                    model_id=model.id,
                )
            )
    await session.flush()
    return models


async def _load_model_schemas(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    models: dict[str, SystemModel],
) -> None:
    for record in _load_json("system_model_schemas.json"):
        model = models.get(record.get("model"))
        if not model:
            raise RuntimeError(
                f"Model '{record.get('model')}' is missing for schema '{record.get('name')}'."
            )
        view = record.get("view")
        if view is None:
            raise RuntimeError(
                f"Schema '{record.get('name')}' for model '{record.get('model')}' "
                "must define the 'view' field."
            )
        session.add(
            SystemModelSchema(
                **_audit_values(bot_id, now),
                name=record["name"],
                use=record["use"],
                view=view,
                model_id=model.id,
            )
        )
    await session.flush()


async def _load_domain_model_metadata(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    data_dir: Path,
    file_name: str = "system_models.json",
) -> dict[str, SystemModel]:
    models: dict[str, SystemModel] = {}
    for record in _load_json(file_name, data_dir):
        model = SystemModel(
            **_audit_values(bot_id, now),
            name=record["name"],
            search=_bool_or_default(record.get("search")),
            label=record["label"],
            readonly=_bool_or_default(record.get("readonly")),
            group_by=record.get("group_by") or None,
            group_by_values=record.get("group_by_values") or [],
            tags=record.get("tags") or [],
        )
        session.add(model)
        await session.flush()
        models[model.name] = model

        for index, field_record in enumerate(record.get("fields", []), start=1):
            search_config = dict(field_record.get("search") or {})
            if field_record.get("selection_values"):
                search_config["selection_values"] = field_record["selection_values"]
            session.add(
                SystemModelField(
                    **_audit_values(bot_id, now),
                    name=field_record["name"],
                    sequence=field_record.get("sequence", index * 10),
                    type=field_record.get("type", "string"),
                    required=_bool_or_default(field_record.get("required")),
                    readonly=_bool_or_default(field_record.get("readonly")),
                    placeholder=field_record.get("placeholder") or {},
                    help=field_record.get("help") or {},
                    search_config=search_config,
                    model_id=model.id,
                )
            )
    await session.flush()
    return models


async def _load_domain_model_schemas(
    session: AsyncSession,
    bot_id: int,
    now: datetime,
    models: dict[str, SystemModel],
    data_dir: Path,
    file_name: str = "system_model_schemas.json",
) -> None:
    for record in _load_json(file_name, data_dir):
        model = models.get(record.get("model"))
        if not model:
            raise RuntimeError(
                f"Model '{record.get('model')}' is missing for schema '{record.get('name')}'."
            )
        session.add(
            SystemModelSchema(
                **_audit_values(bot_id, now),
                name=record["name"],
                use=record["use"],
                view=record.get("view") or [],
                model_id=model.id,
            )
        )
    await session.flush()


async def seed_data() -> None:
    _validate_seed_sources()
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
    now = datetime.now(timezone.utc)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            bot = await _load_bot(session, now)
            bot_id = bot.id
            if bot_id is None:
                raise RuntimeError("App Bot was not persisted correctly.")

            currencies = await _load_currencies(session, bot_id, now)
            countries = await _load_countries(session, bot_id, now, currencies)
            await _load_timezones(session, bot_id, now, countries)
            langs = await _load_langs(session, bot_id, now)
            companies, company_by_user_email = await _load_companies(
                session, bot_id, now
            )
            await _load_remaining_users(
                session, bot_id, now, langs, companies, company_by_user_email
            )
            await _load_access_control(session, bot_id, now)
            await _load_apps(session, bot_id, now, companies)
            models = await _load_system_models(session, bot_id, now)
            await _load_model_schemas(session, bot_id, now, models)
            parties_models = await _load_domain_model_metadata(
                session, bot_id, now, PARTIES_DATA_DIR
            )
            await _load_domain_model_schemas(
                session, bot_id, now, parties_models, PARTIES_DATA_DIR
            )
            talent_models = await _load_domain_model_metadata(
                session, bot_id, now, TALENT_DATA_DIR
            )
            await _load_domain_model_schemas(
                session, bot_id, now, talent_models, TALENT_DATA_DIR
            )
            access_models = await _load_domain_model_metadata(
                session,
                bot_id,
                now,
                ACCESS_DATA_DIR,
                "system_model.json",
            )
            await _load_domain_model_schemas(
                session,
                bot_id,
                now,
                access_models,
                ACCESS_DATA_DIR,
                "system_model_schema.json",
            )

            await session.commit()
    finally:
        await engine.dispose()
    print("Loaded initial system data.")


async def main() -> None:
    # Validate every JSON source before reset_database can remove existing data.
    _validate_seed_sources()
    await reset_database()
    await create_schema()
    await seed_data()
    apply_post_schema_migrations()
    print("Setup complete.")


if __name__ == "__main__":
    asyncio.run(main())
