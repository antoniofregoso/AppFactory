# Guía de Calidad de Código, Testing y Rate Limiting

## 🧪 Testing con pytest

### Ejecutar tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests de un archivo específico
pytest tests/test_api.py

# Ejecutar un test específico
pytest tests/test_api.py::TestHealth::test_health_check_returns_ok

# Ejecutar con salida detallada
pytest -v

# Ejecutar con cobertura
pytest --cov=.

# Ejecutar tests en paralelo
pytest -n auto
```

### Estructura de tests

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

class TestMyFeature:
    def test_success_case(self, client):
        response = client.get("/endpoint")
        assert response.status_code == 200
    
    def test_error_case(self, client):
        response = client.post("/endpoint", json={"invalid": "data"})
        assert response.status_code == 422
```

### Tests Async

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

---

## 🔐 Rate Limiting

El rate limiting está configurado con `slowapi`. Por defecto, está disponible pero no aplicado.

### Aplicar rate limiting a un endpoint

```python
from main import limiter

@app.get("/api/endpoint")
@limiter.limit("5/minute")
async def limited_endpoint(request: Request):
    return {"message": "OK"}
```

### Ejemplos de límites

- `"1/minute"` - 1 request por minuto
- `"10/hour"` - 10 requests por hora
- `"100/day"` - 100 requests por día
- `"5/10 seconds"` - 5 requests cada 10 segundos

### Respuesta de rate limit

```json
{
  "status_code": 429,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "details": {},
  "timestamp": "2024-06-03T10:30:45.123456"
}
```

---

## 📝 Logging Estructurado

El logging ahora usa JSON estructurado para mejor análisis.

### Ejemplos de uso

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Log simple
logger.info("User logged in")

# Log con datos adicionales
logger.info(
    "User action",
    extra={
        "user_id": 123,
        "action": "login",
        "ip": "192.168.1.1"
    }
)

# Log de error
logger.error("Database connection failed", exc_info=True)

# Log de warning
logger.warning("Deprecated endpoint accessed")
```

### Niveles de log

- `DEBUG` - Información detallada para debugging
- `INFO` - Eventos normales
- `WARNING` - Advertencias, algo inesperado
- `ERROR` - Errores, algo falló
- `CRITICAL` - Errores críticos, el programa puede no continuar

### Cambiar nivel de log

En `.env`:
```
LOG_LEVEL=DEBUG  # Más detallado
LOG_LEVEL=INFO   # Normal (default)
LOG_LEVEL=WARNING # Solo warnings y errores
```

---

## 🎨 Code Quality con Black, Flake8 y Pylint

### Black (Formateador de código)

```bash
# Formatear un archivo
black main.py

# Formatear todos los archivos Python
black .

# Ver cambios sin aplicar
black --check --diff .

# Configuración en pyproject.toml
```

### Flake8 (Linter)

```bash
# Verificar errores de estilo
flake8

# Verificar un archivo específico
flake8 main.py

# Ver estadísticas
flake8 --statistics

# Configuración en .flake8
```

### Pylint (Análisis de código)

```bash
# Analizar un archivo
pylint main.py

# Analizar varios archivos
pylint Service/ Repository/

# Con configuración
pylint --rcfile=pyproject.toml main.py
```

### Pre-commit hook (Opcional)

Crea `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Formatear con black
black .
# Verificar con flake8
flake8 .
# Si flake8 falla, abortar el commit
if [ $? -ne 0 ]; then
    exit 1
fi
```

---

## 📦 Comandos útiles

```bash
# Ejecutar tests y verificar calidad
pytest && black . && flake8 .

# Ejecutar tests con cobertura
pytest --cov=. --cov-report=html

# Formatear y hacer linting
black . && flake8 . && pylint Service/ Repository/

# Verificar errores de sintaxis
python -m py_compile *.py

# Actualizar requirements
pip freeze > requirements.txt
```

---

## ⚙️ Configuración actual

- **pytest**: Configurado en `pyproject.toml`
- **black**: Línea máxima de 88 caracteres, Python 3.12
- **flake8**: Configurado en `.flake8`
- **rate limiting**: Importar desde `main.py`
- **logging**: JSON estructurado en la salida estándar

---

## 📊 Ejemplo completo

```python
# Service/user_service.py
from app.core.logging import get_logger
from exceptions import DuplicateEntryException, ResourceNotFoundException
from main import limiter

logger = get_logger(__name__)

class UserService:
    async def create_user(self, email: str, name: str):
        logger.info(
            "Creating user",
            extra={"email": email}
        )
        
        existing = await UserRepository.get_by_email(email)
        if existing:
            raise DuplicateEntryException("email", email)
        
        user = User(email=email, name=name)
        await UserRepository.create(user)
        
        logger.info(
            "User created successfully",
            extra={"user_id": user.id, "email": email}
        )
        return user

# tests/test_user_service.py
import pytest
from Service.user_service import UserService
from exceptions import DuplicateEntryException

@pytest.mark.asyncio
async def test_create_user_raises_on_duplicate():
    service = UserService()
    
    # Crear usuario
    user1 = await service.create_user("test@example.com", "Test User")
    assert user1.email == "test@example.com"
    
    # Intentar crear usuario duplicado
    with pytest.raises(DuplicateEntryException):
        await service.create_user("test@example.com", "Another User")
```
