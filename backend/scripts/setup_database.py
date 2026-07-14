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

from sqlalchemy import text
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
)
from app.domains.users.service.auth_service import AuthService
from app.domains.users.models import UserType, UserUser  # noqa: F401

DATA_DIR = BACKEND_DIR / "app" / "domains" / "system" / "data"
BOT_NAME = "App Bot"

# Revision right before the tail of migrations that only run raw SQL (CREATE
# EXTENSION / CREATE INDEX for pg_trgm and full-text search) with no
# schema change, so nothing in `SQLModel.metadata.create_all` produces them.
# Stamping here and running `alembic upgrade head` makes Alembic actually
# execute those migrations for real instead of skipping them as already
# applied. Every migration between this revision and head must stay
# raw-SQL-only (no op.create_table/op.add_column) since create_schema()
# already created that schema; if a future migration adds columns/tables
# after this point, move this constant to the new boundary.
_SEARCH_INDEX_MIGRATIONS_BASE_REVISION = "f2a6c8d9b4e0"


def _load_json(file_name: str) -> Any:
    with (DATA_DIR / file_name).open(encoding="utf-8") as file:
        return json.load(file)


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
            await conn.run_sync(SQLModel.metadata.create_all)
    finally:
        await engine.dispose()
    print("Created database tables.")


def apply_search_index_migrations() -> None:
    alembic_bin = Path(sys.executable).parent / "alembic"
    subprocess.run(
        [str(alembic_bin), "stamp", _SEARCH_INDEX_MIGRATIONS_BASE_REVISION],
        cwd=BACKEND_DIR,
        check=True,
    )
    subprocess.run([str(alembic_bin), "upgrade", "head"], cwd=BACKEND_DIR, check=True)
    print("Applied search index migrations (pg_trgm, FTS GIN indexes).")


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
                is_admin=_bool_or_default(record.get("is_admin")),
                mcp_access=_bool_or_default(record.get("mcp_access")),
                lang_id=lang.id if lang else None,
                company_id=company.id if company else None,
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
) -> None:
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

        for state_record in record.get("states", []):
            session.add(
                SystemCountryState(
                    code=state_record["code"],
                    name=state_record["name"],
                    country_id=country.id,
                )
            )
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


async def seed_data() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
    now = datetime.now(timezone.utc)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            bot = await _load_bot(session, now)
            bot_id = bot.id
            if bot_id is None:
                raise RuntimeError("App Bot was not persisted correctly.")

            currencies = await _load_currencies(session, bot_id, now)
            await _load_countries(session, bot_id, now, currencies)
            langs = await _load_langs(session, bot_id, now)
            companies, company_by_user_email = await _load_companies(
                session, bot_id, now
            )
            await _load_remaining_users(
                session, bot_id, now, langs, companies, company_by_user_email
            )
            await _load_apps(session, bot_id, now, companies)
            models = await _load_system_models(session, bot_id, now)
            await _load_model_schemas(session, bot_id, now, models)

            await session.commit()
    finally:
        await engine.dispose()
    print("Loaded initial system data.")


async def main() -> None:
    await reset_database()
    await create_schema()
    await seed_data()
    apply_search_index_migrations()
    print("Setup complete.")


if __name__ == "__main__":
    asyncio.run(main())
