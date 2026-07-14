"""Tests para endpoints de la API."""


class TestHealth:
    """Tests para el endpoint de salud."""

    async def test_health_check_returns_ok(self, client):
        """Verifica que el endpoint /health retorna estado ok."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_health_check_has_database_status(self, client):
        """Verifica que la respuesta incluye estado de BD."""
        response = await client.get("/health")
        data = response.json()
        assert "database" in data


class TestRoot:
    """Tests para el endpoint raíz."""

    async def test_root_endpoint_returns_message(self, client):
        """Verifica que el endpoint / retorna un mensaje."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()


class TestErrorHandling:
    """Tests para manejo de errores."""

    async def test_not_found_endpoint_returns_404(self, client):
        """Verifica que endpoint no existente retorna 404."""
        response = await client.get("/nonexistent")
        assert response.status_code == 404
