"""Test configuration and fixtures."""

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

import main


class FakeSession:
    async def execute(self, _statement):
        return None


class FakeDatabase:
    @asynccontextmanager
    async def session(self):
        yield FakeSession()

    async def close(self):
        return None


@pytest.fixture(autouse=True)
def fake_database(monkeypatch):
    """Evita que las pruebas HTTP dependan de PostgreSQL."""
    monkeypatch.setattr(main, "db", FakeDatabase())


@pytest.fixture
async def client():
    """Crea un cliente de prueba para la aplicación."""
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
