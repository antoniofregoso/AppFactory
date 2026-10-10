import importlib
from pathlib import Path

schema_migration = importlib.import_module(
    "migrations.versions.20261010_1000_f8c3d4e5a6b7_add_task_recurrence_series_state"
)
data_migration = importlib.import_module(
    "migrations.versions.20261010_1010_a9d4e5f6b7c8_sync_task_recurrence_series_metadata"
)


class FakeConnection:
    def execute(self, *args, **kwargs):
        return None


def test_schema_upgrade_adds_missing_series_state_columns(monkeypatch):
    added_columns = []
    monkeypatch.setattr(schema_migration.op, "get_bind", FakeConnection)
    monkeypatch.setattr(schema_migration, "_has_column", lambda bind, name: False)
    monkeypatch.setattr(
        schema_migration.op,
        "add_column",
        lambda table, column: added_columns.append((table, column.name)),
    )

    schema_migration.upgrade()

    assert added_columns == [
        ("system_tasks", "recurrence_until"),
        ("system_tasks", "recurrence_exceptions"),
    ]


def test_schema_upgrade_is_safe_after_create_all(monkeypatch):
    monkeypatch.setattr(schema_migration.op, "get_bind", FakeConnection)
    monkeypatch.setattr(schema_migration, "_has_column", lambda bind, name: True)
    monkeypatch.setattr(
        schema_migration.op,
        "add_column",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("existing columns must not be added twice")
        ),
    )

    schema_migration.upgrade()


def test_fresh_setup_stamps_schema_revision_before_data_revision():
    setup_source = (Path(__file__).parents[1] / "scripts" / "setup_database.py").read_text()
    assert '_POST_SCHEMA_MIGRATIONS_BASE_REVISION = "f8c3d4e5a6b7"' in setup_source
    assert data_migration.down_revision == schema_migration.revision
