/**
 * Tests para funciones utilitarias
 */

import { describe, it, expect } from "vitest";
import {
  isValidEmail,
  capitalize,
  formatCurrency,
  filterByProperty,
  arrayToObject,
  isValidPassword,
  daysBetween,
  objectToQueryString,
  debounce,
  isEmpty,
} from "../src/utils";

describe("Email validation", () => {
  it("valida email válido", () => {
    expect(isValidEmail("user@example.com")).toBe(true);
  });

  it("rechaza email sin @", () => {
    expect(isValidEmail("userexample.com")).toBe(false);
  });

  it("rechaza email sin dominio", () => {
    expect(isValidEmail("user@.com")).toBe(false);
  });

  it("rechaza email vacío", () => {
    expect(isValidEmail("")).toBe(false);
  });
});

describe("Capitalize", () => {
  it("capitaliza primera letra", () => {
    expect(capitalize("hello")).toBe("Hello");
  });

  it("maneja string vacío", () => {
    expect(capitalize("")).toBe("");
  });

  it("maneja una letra", () => {
    expect(capitalize("a")).toBe("A");
  });
});

describe("Format currency", () => {
  it("formatea USD correctamente", () => {
    const result = formatCurrency(1000);
    expect(result).toContain("1,000");
  });

  it("formatea con moneda diferente", () => {
    const result = formatCurrency(1000, "EUR");
    expect(result).toContain("1,000");
  });

  it("formatea con decimales", () => {
    const result = formatCurrency(99.99);
    expect(result).toContain("99.99");
  });
});

describe("Filter by property", () => {
  it("filtra array de objetos", () => {
    const users = [
      { name: "John", age: 30 },
      { name: "Jane", age: 25 },
      { name: "Bob", age: 30 },
    ];

    const result = filterByProperty(users, "age", 30);
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe("John");
  });

  it("retorna array vacío si no hay coincidencias", () => {
    const users = [{ name: "John", age: 30 }];
    const result = filterByProperty(users, "age", 25);
    expect(result).toEqual([]);
  });
});

describe("Array to object", () => {
  it("convierte array a objeto", () => {
    const users = [
      { id: 1, name: "John" },
      { id: 2, name: "Jane" },
    ];

    const result = arrayToObject(users, "id");
    expect(result[1].name).toBe("John");
    expect(result[2].name).toBe("Jane");
  });

  it("sobrescribe valores con misma clave", () => {
    const items = [
      { id: 1, value: "first" },
      { id: 1, value: "second" },
    ];

    const result = arrayToObject(items, "id");
    expect(result[1].value).toBe("second");
  });
});

describe("Password validation", () => {
  it("acepta contraseña válida", () => {
    expect(isValidPassword("MyPassword123")).toBe(true);
  });

  it("rechaza contraseña corta", () => {
    expect(isValidPassword("Short1")).toBe(false);
  });

  it("rechaza contraseña sin mayúscula", () => {
    expect(isValidPassword("mypassword123")).toBe(false);
  });

  it("rechaza contraseña sin número", () => {
    expect(isValidPassword("MyPassword")).toBe(false);
  });
});

describe("Days between", () => {
  it("calcula diferencia de días", () => {
    const date1 = new Date("2024-01-01");
    const date2 = new Date("2024-01-10");
    expect(daysBetween(date1, date2)).toBe(9);
  });

  it("maneja mismo día", () => {
    const date = new Date("2024-01-01");
    expect(daysBetween(date, date)).toBe(0);
  });
});

describe("Object to query string", () => {
  it("convierte objeto simple a query string", () => {
    const obj = { name: "John", age: 30 };
    const result = objectToQueryString(obj);
    expect(result).toContain("name=John");
    expect(result).toContain("age=30");
  });

  it("encoda caracteres especiales", () => {
    const obj = { search: "hello world" };
    const result = objectToQueryString(obj);
    expect(result).toContain("hello%20world");
  });

  it("maneja objeto vacío", () => {
    const result = objectToQueryString({});
    expect(result).toBe("");
  });
});

describe("Debounce", () => {
  it("ejecuta función después del delay", (done) => {
    let called = false;
    const func = () => {
      called = true;
    };

    const debouncedFunc = debounce(func, 50);
    debouncedFunc();

    setTimeout(() => {
      expect(called).toBe(true);
      done();
    }, 100);
  });

  it("solo ejecuta una vez si se llama múltiples veces", (done) => {
    let callCount = 0;
    const func = () => {
      callCount++;
    };

    const debouncedFunc = debounce(func, 50);
    debouncedFunc();
    debouncedFunc();
    debouncedFunc();

    setTimeout(() => {
      expect(callCount).toBe(1);
      done();
    }, 100);
  });
});

describe("Is empty", () => {
  it("retorna true para objeto vacío", () => {
    expect(isEmpty({})).toBe(true);
  });

  it("retorna false para objeto con propiedades", () => {
    expect(isEmpty({ a: 1 })).toBe(false);
  });

  it("retorna false para objeto con método", () => {
    const obj = {};
    obj.method = () => {};
    expect(isEmpty(obj)).toBe(false);
  });
});
