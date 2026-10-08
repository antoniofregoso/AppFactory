import importlib

migration = importlib.import_module(
    "migrations.versions.20261004_1200_e7b2c3d4e5f6_add_task_recurrence"
)


class FakeConnection:
    def execute(self, *args, **kwargs):
        return None


def test_upgrade_skips_existing_recurrence_column(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    monkeypatch.setattr(migration, "_has_recurrence_column", lambda bind: True)

    def unexpected_add_column(*args, **kwargs):
        raise AssertionError("recurrence must not be added twice")

    monkeypatch.setattr(migration.op, "add_column", unexpected_add_column)

    migration.upgrade()


def test_upgrade_adds_missing_recurrence_column(monkeypatch):
    connection = FakeConnection()
    added_columns = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    monkeypatch.setattr(migration, "_has_recurrence_column", lambda bind: False)
    monkeypatch.setattr(
        migration.op,
        "add_column",
        lambda table, column: added_columns.append((table, column.name)),
    )

    migration.upgrade()

    assert added_columns == [("system_tasks", "recurrence")]
