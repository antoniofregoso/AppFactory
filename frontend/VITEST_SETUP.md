# 🧪 Frontend Testing Setup - Vitest

## ✅ Instalado y configurado

### Paquetes
- `vitest` ^4.1.8 - Testing framework
- `@vitest/ui` ^4.1.8 - UI visual para tests
- `happy-dom` ^20.10.1 - DOM virtual

### Archivos de configuración
- `vitest.config.js` - Configuración de Vitest
- `package.json` - Scripts de test

### Archivos de tests
- `tests/basic.test.js` - 19 tests básicos
- `tests/utils.test.js` - 28 tests de funciones utilitarias
- `src/utils.js` - Funciones utilitarias implementadas

---

## 📊 Estadísticas

✅ **47/47 tests pasando**

```
 ✓ tests/basic.test.js (19 tests) 139ms
 ✓ tests/utils.test.js (28 tests) 126ms
```

---

## 🚀 Comandos disponibles

```bash
# Ejecutar tests una vez
npm test

# Ejecutar tests en modo watch
npm test -- --watch

# Ver UI visual de tests
npm test:ui

# Generar reporte de cobertura
npm test:coverage
```

---

## 📁 Estructura

```
frontend/
├── tests/
│   ├── basic.test.js      # Tests básicos (19 tests)
│   └── utils.test.js      # Tests de utilidades (28 tests)
├── src/
│   └── utils.js           # Funciones utilitarias
├── vitest.config.js       # Configuración de Vitest
├── package.json           # Scripts de test
└── TESTING_GUIDE.md       # Guía completa de testing
```

---

## 🧪 Tests incluidos

### basic.test.js (19 tests)
- Operaciones matemáticas (4 tests)
- Strings (3 tests)
- Arrays (4 tests)
- Objetos (3 tests)
- Funciones (2 tests)
- Promesas y async (2 tests)

### utils.test.js (28 tests)

**Email validation (4 tests)**
- Email válido
- Email sin @
- Email sin dominio
- Email vacío

**Capitalize (3 tests)**
- Capitaliza primera letra
- Maneja string vacío
- Maneja una letra

**Format currency (3 tests)**
- Formatea USD
- Formatea con moneda diferente
- Formatea con decimales

**Array filtering (2 tests)**
- Filtra array de objetos
- Retorna array vacío sin coincidencias

**Array to object (2 tests)**
- Convierte array a objeto
- Sobrescribe valores duplicados

**Password validation (4 tests)**
- Acepta contraseña válida
- Rechaza contraseña corta
- Rechaza sin mayúscula
- Rechaza sin número

**Days between (2 tests)**
- Calcula diferencia de días
- Maneja mismo día

**Query string (3 tests)**
- Convierte objeto simple
- Encoda caracteres especiales
- Maneja objeto vacío

**Debounce (2 tests)**
- Ejecuta después del delay
- Solo ejecuta una vez si se llama múltiples veces

**Is empty (3 tests)**
- Retorna true para objeto vacío
- Retorna false con propiedades
- Retorna false con métodos

---

## 💡 Funciones utilitarias implementadas

```javascript
// Validación
isValidEmail(email)          // Valida formato de email
isValidPassword(password)    // Valida contraseña

// String manipulation
capitalize(str)              // Capitaliza primera letra

// Formateo
formatCurrency(amount, currency) // Formatea como moneda

// Array operations
filterByProperty(items, property, value)  // Filtra por propiedad
arrayToObject(items, key)    // Convierte array a objeto

// Utilidades
daysBetween(date1, date2)    // Diferencia de días
objectToQueryString(obj)     // Convierte objeto a query string
debounce(func, delay)        // Debounce una función
isEmpty(obj)                 // Verifica si objeto está vacío
```

---

## 🔧 Configuración de Vitest

```javascript
// vitest.config.js
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,           // describe, it, expect sin importar
    environment: "happy-dom", // DOM virtual para testing
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
    },
  },
});
```

---

## 📝 Scripts en package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

---

## 🎯 Próximos pasos

1. **Agregar tests para componentes** (si usas framework UI)
2. **Integración con GraphQL** - Tests de queries y mutations
3. **Testing de API** - Mock de fetch/axios
4. **E2E tests** - Usar Playwright o Cypress
5. **CI/CD** - GitHub Actions ejecutando tests automáticamente

---

## 📚 Recursos

- [Testing Guide](./TESTING_GUIDE.md) - Guía completa
- [Vitest Docs](https://vitest.dev)
- [Vite Docs](https://vitejs.dev)

---

## 🎓 Ejemplo: Agregar nuevo test

```javascript
// tests/my-feature.test.js
import { describe, it, expect } from "vitest";

describe("My feature", () => {
  it("should work correctly", () => {
    expect(true).toBe(true);
  });

  it("should validate input", () => {
    expect(isValidInput("test")).toBe(true);
  });
});
```

Luego ejecuta: `npm test`

---

## ✨ Features

- ✅ 47 tests pasando
- ✅ Globals configurados (no importar describe, it, expect)
- ✅ Environment happy-dom para DOM virtual
- ✅ Coverage reporting
- ✅ Watch mode disponible
- ✅ UI visual con `npm test:ui`
- ✅ Funciones utilitarias implementadas y testeadas

