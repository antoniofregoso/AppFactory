"""Restaura PostgreSQL usando DATABASE_URL de backend/.env.

Ejecutar desde cualquier directorio:

    python backend/scripts/restore_database.py /ruta/respaldo.dump
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"


def _postgres_environment() -> tuple[dict[str, str], str]:
    database_url = dotenv_values(ENV_FILE).get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(f"DATABASE_URL no está definido en {ENV_FILE}.")

    url = make_url(database_url)
    if not url.drivername.startswith("postgresql") or not url.database:
        raise RuntimeError("DATABASE_URL debe apuntar a una base de datos PostgreSQL.")

    environment = os.environ.copy()
    values = {
        "PGHOST": url.host,
        "PGPORT": str(url.port) if url.port else None,
        "PGUSER": url.username,
        "PGPASSWORD": url.password,
        "PGDATABASE": url.database,
    }
    environment.update({key: value for key, value in values.items() if value})

    query_variables = {
        "sslmode": "PGSSLMODE",
        "sslcert": "PGSSLCERT",
        "sslkey": "PGSSLKEY",
        "sslrootcert": "PGSSLROOTCERT",
    }
    for query_key, environment_key in query_variables.items():
        value = url.query.get(query_key)
        if value:
            environment[environment_key] = str(value)

    return environment, url.database


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaura un backup custom y reemplaza los objetos existentes."
    )
    parser.add_argument("backup", type=Path, help="Archivo .dump creado con pg_dump.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Omite la confirmación interactiva.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    backup = arguments.backup.expanduser().resolve()
    if not backup.is_file():
        raise FileNotFoundError(f"No existe el backup: {backup}")
    if not shutil.which("pg_restore"):
        raise RuntimeError("No se encontró pg_restore en PATH.")

    environment, database = _postgres_environment()
    if not arguments.yes:
        answer = input(
            f"Se reemplazarán los objetos de la base '{database}'. ¿Continuar? [y/N]: "
        )
        if answer.strip().lower() not in {"y", "yes", "s", "si", "sí"}:
            print("Restauración cancelada; la base de datos no fue modificada.")
            return

    subprocess.run(
        [
            "pg_restore",
            f"--dbname={database}",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "--single-transaction",
            "--exit-on-error",
            str(backup),
        ],
        env=environment,
        check=True,
    )
    print(f"Base de datos '{database}' restaurada desde: {backup}")


if __name__ == "__main__":
    main()
