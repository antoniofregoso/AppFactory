/**
 * Ejemplo de tests básicos con Vitest
 * Estos tests demuestran funcionalidades básicas de testing
 */

import { describe, it, expect, beforeEach } from "vitest";

describe("Operaciones matemáticas", () => {
  it("suma dos números correctamente", () => {
    expect(2 + 2).toBe(4);
  });

  it("resta dos números correctamente", () => {
    expect(5 - 3).toBe(2);
  });

  it("multiplica dos números correctamente", () => {
    expect(3 * 4).toBe(12);
  });

  it("divide dos números correctamente", () => {
    expect(10 / 2).toBe(5);
  });
});

describe("Strings", () => {
  it("concatena strings", () => {
    const greeting = "Hello" + " " + "World";
    expect(greeting).toBe("Hello World");
  });

  it("verifica longitud de string", () => {
    expect("test".length).toBe(4);
  });

  it("incluye substring", () => {
    expect("hello world".includes("world")).toBe(true);
  });
});

describe("Arrays", () => {
  it("crea array correctamente", () => {
    const arr = [1, 2, 3];
    expect(arr).toEqual([1, 2, 3]);
  });

  it("encuentra elemento en array", () => {
    const arr = ["a", "b", "c"];
    expect(arr).toContain("b");
  });

  it("filtra array correctamente", () => {
    const numbers = [1, 2, 3, 4, 5];
    const evens = numbers.filter((n) => n % 2 === 0);
    expect(evens).toEqual([2, 4]);
  });

  it("mapea array correctamente", () => {
    const numbers = [1, 2, 3];
    const doubled = numbers.map((n) => n * 2);
    expect(doubled).toEqual([2, 4, 6]);
  });
});

describe("Objetos", () => {
  it("crea objeto correctamente", () => {
    const user = { name: "John", age: 30 };
    expect(user.name).toBe("John");
    expect(user.age).toBe(30);
  });

  it("verifica propiedades de objeto", () => {
    const obj = { a: 1, b: 2 };
    expect(obj).toHaveProperty("a");
    expect(obj).not.toHaveProperty("c");
  });

  it("extiende objeto correctamente", () => {
    const user = { name: "John" };
    const extended = { ...user, age: 30 };
    expect(extended).toEqual({ name: "John", age: 30 });
  });
});

describe("Funciones", () => {
  it("ejecuta función correctamente", () => {
    const add = (a, b) => a + b;
    expect(add(2, 3)).toBe(5);
  });

  it("lanza error en función", () => {
    const divide = (a, b) => {
      if (b === 0) throw new Error("Cannot divide by zero");
      return a / b;
    };

    expect(() => divide(10, 0)).toThrow("Cannot divide by zero");
  });

  it("usa beforeEach para setup", () => {
    let state = { count: 0 };

    beforeEach(() => {
      state.count = 0;
    });

    const increment = () => {
      state.count++;
    };

    increment();
    expect(state.count).toBe(1);
  });
});

describe("Promesas y async", () => {
  it("resuelve promesa correctamente", async () => {
    const fetchData = () =>
      new Promise((resolve) => {
        setTimeout(() => resolve("data"), 100);
      });

    const result = await fetchData();
    expect(result).toBe("data");
  });

  it("rechaza promesa correctamente", async () => {
    const failPromise = () =>
      new Promise((_, reject) => {
        reject(new Error("Failed"));
      });

    try {
      await failPromise();
    } catch (error) {
      expect(error.message).toBe("Failed");
    }
  });
});
