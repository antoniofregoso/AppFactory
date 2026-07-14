# 🧪 Frontend Testing Guide - Vitest

## Instalación

Vitest ya está instalado. Dependencias:
- `vitest` - Testing framework
- `@vitest/ui` - UI visual para tests
- `happy-dom` - DOM virtual para testing

---

## Comandos

```bash
# Ejecutar tests
npm test

# Ejecutar tests en modo watch
npm test -- --watch

# Ver UI de tests
npm test:ui

# Generar cobertura
npm test:coverage

# Ejecutar test específico
npm test -- basic.test.js

# Ejecutar test con patrón
npm test -- --grep "email"
```

---

## Estructura de tests

```javascript
import { describe, it, expect } from "vitest";

describe("Nombre del grupo", () => {
  it("debe hacer algo específico", () => {
    expect(2 + 2).toBe(4);
  });

  it("debe validar algo", () => {
    expect(true).toBe(true);
  });
});
```

---

## Ejemplos de assertions

```javascript
// Igualdad
expect(actual).toBe(expected);              // Igualdad estricta (===)
expect(actual).toEqual(expected);           // Igualdad profunda

// Tipos
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();
expect(value).toBeTruthy();
expect(value).toBeFalsy();

// Números
expect(value).toBeGreaterThan(2);
expect(value).toBeGreaterThanOrEqual(2);
expect(value).toBeLessThan(5);
expect(value).toBeCloseTo(0.3, 5);         // Para números flotantes

// Strings
expect(str).toMatch(/pattern/);
expect(str).toContain("substring");
expect(str).toHaveLength(5);

// Arrays
expect(array).toContain(item);
expect(array).toEqual([1, 2, 3]);
expect(array).toHaveLength(3);
expect(array).toStrictEqual([1, 2, 3]);

// Objetos
expect(obj).toHaveProperty("key");
expect(obj).toEqual({ a: 1 });
expect(obj).toMatchObject({ a: 1 });

// Funciones
expect(func).toThrow();
expect(func).toThrow(Error);
expect(func).toThrow("mensaje");

// Negación
expect(value).not.toBe(5);
expect(array).not.toContain(10);
```

---

## Testing de funciones

```javascript
describe("Validación de email", () => {
  it("valida email correcto", () => {
    const result = isValidEmail("user@example.com");
    expect(result).toBe(true);
  });

  it("rechaza email inválido", () => {
    expect(isValidEmail("invalid")).toBe(false);
  });

  it("maneja casos extremos", () => {
    expect(isValidEmail("")).toBe(false);
    expect(isValidEmail(null)).toBe(false);
  });
});
```

---

## Testing asincrónico

```javascript
describe("Funciones async", () => {
  it("resuelve promesa", async () => {
    const result = await fetchData();
    expect(result).toBeDefined();
  });

  it("rechaza promesa", async () => {
    try {
      await failingFunction();
    } catch (error) {
      expect(error).toBeDefined();
    }
  });

  // O con rejectsWith
  it("rechaza con rejectsWith", async () => {
    await expect(failingFunction()).rejects.toThrow();
  });
});
```

---

## Setup y Teardown

```javascript
import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from "vitest";

describe("Lifecycle hooks", () => {
  beforeAll(() => {
    // Ejecuta una vez antes de todos los tests
    console.log("Before all tests");
  });

  beforeEach(() => {
    // Ejecuta antes de cada test
    console.log("Before each test");
  });

  afterEach(() => {
    // Ejecuta después de cada test
    console.log("After each test");
  });

  afterAll(() => {
    // Ejecuta una vez después de todos los tests
    console.log("After all tests");
  });

  it("test 1", () => {
    expect(true).toBe(true);
  });

  it("test 2", () => {
    expect(true).toBe(true);
  });
});
```

---

## Testing con fixtures

```javascript
describe("User management", () => {
  let user;

  beforeEach(() => {
    user = {
      id: 1,
      name: "John",
      email: "john@example.com",
    };
  });

  it("crea usuario", () => {
    expect(user.name).toBe("John");
  });

  it("actualiza usuario", () => {
    user.name = "Jane";
    expect(user.name).toBe("Jane");
  });
});
```

---

## Mocking (básico)

```javascript
import { describe, it, expect, vi } from "vitest";

describe("Funciones con mocks", () => {
  it("mockea función", () => {
    const mockFunc = vi.fn();
    mockFunc("arg1", "arg2");

    expect(mockFunc).toHaveBeenCalled();
    expect(mockFunc).toHaveBeenCalledWith("arg1", "arg2");
    expect(mockFunc).toHaveBeenCalledTimes(1);
  });

  it("mockea valor de retorno", () => {
    const mockFunc = vi.fn(() => 42);
    const result = mockFunc();

    expect(result).toBe(42);
  });
});
```

---

## Testing de APIs (GraphQL)

```javascript
import { describe, it, expect, vi } from "vitest";

describe("GraphQL queries", () => {
  it("ejecuta query", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            data: {
              user: { id: 1, name: "John" },
            },
          }),
      })
    );

    global.fetch = mockFetch;

    // Ejecutar query...
    expect(mockFetch).toHaveBeenCalled();
  });
});
```

---

## Cobertura de código

```bash
# Generar reporte de cobertura
npm test:coverage

# Ver reporte HTML
open coverage/index.html
```

El reporte muestra:
- **Statements**: Líneas ejecutadas
- **Branches**: Caminos condicionales
- **Functions**: Funciones llamadas
- **Lines**: Líneas cubiertas

---

## Mejores prácticas

### ✅ Haz esto

```javascript
// Tests descriptivos y específicos
it("should validate email format correctly", () => {
  expect(isValidEmail("test@example.com")).toBe(true);
});

// Tests independientes (no dependen de otros)
describe("Independent tests", () => {
  it("test A", () => {
    expect(1).toBe(1);
  });

  it("test B", () => {
    expect(2).toBe(2);
  });
});

// Agrupa tests relacionados
describe("Email validation", () => {
  it("accepts valid emails", () => {});
  it("rejects invalid emails", () => {});
  it("handles edge cases", () => {});
});
```

### ❌ No hagas esto

```javascript
// Tests ambiguos
it("works", () => {
  expect(true).toBe(true);
});

// Tests que dependen de otros
let result;
it("sets up data", () => {
  result = getData();
});

it("uses previous result", () => {
  // ¡No hagas esto! Test debe ser independiente
  expect(result).toBeDefined();
});

// Múltiples asserts sin claridad
it("does everything", () => {
  expect(a).toBe(1);
  expect(b).toBe(2);
  expect(c).toBe(3);
  // ¿Cuál falla si hay error?
});
```

---

## Patrones comunes

### Testing de funciones puras

```javascript
describe("Pure functions", () => {
  it("adds numbers", () => {
    expect(add(2, 3)).toBe(5);
  });

  it("handles edge cases", () => {
    expect(add(0, 0)).toBe(0);
    expect(add(-1, 1)).toBe(0);
  });
});
```

### Testing de estado

```javascript
describe("State management", () => {
  let state;

  beforeEach(() => {
    state = { count: 0 };
  });

  it("increments count", () => {
    state.count++;
    expect(state.count).toBe(1);
  });

  it("resets state", () => {
    state.count = 5;
    state.count = 0;
    expect(state.count).toBe(0);
  });
});
```

### Testing de errores

```javascript
describe("Error handling", () => {
  it("throws on invalid input", () => {
    expect(() => divideByZero(10)).toThrow();
  });

  it("catches specific error", () => {
    expect(() => divideByZero(10)).toThrow("Cannot divide by zero");
  });
});
```

---

## CI/CD Integration

Para ejecutar tests en CI/CD (GitHub Actions, etc):

```bash
npm test -- --run           # Ejecuta una vez
npm test:coverage -- --run  # Con cobertura
```

---

## Archivos de ejemplo

En el proyecto ya existen:
- `tests/basic.test.js` - Tests básicos de Vitest
- `tests/utils.test.js` - Tests de funciones utilitarias
- `src/utils.js` - Funciones utilitarias

---

## Configuración de Vitest

Archivo: `vitest.config.js`

```javascript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,           // Usa describe, it, expect sin importar
    environment: "happy-dom", // DOM virtual para testing
    coverage: {
      provider: "v8",        // Provider de cobertura
      reporter: ["text", "json", "html"],
    },
  },
});
```

---

## Recursos

- [Documentación de Vitest](https://vitest.dev)
- [Documentación de Vite](https://vitejs.dev)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
