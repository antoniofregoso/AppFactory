/**
 * Ejemplos de funciones utilitarias para testing
 */

/**
 * Valida formato de email
 * @param {string} email
 * @returns {boolean}
 */
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Capitaliza primera letra de string
 * @param {string} str
 * @returns {string}
 */
export const capitalize = (str) => {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Formatea número como moneda
 * @param {number} amount
 * @param {string} currency
 * @returns {string}
 */
export const formatCurrency = (amount, currency = "USD") => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
  }).format(amount);
};

/**
 * Filtra array de objetos por propiedad
 * @param {Array} items
 * @param {string} property
 * @param {*} value
 * @returns {Array}
 */
export const filterByProperty = (items, property, value) => {
  return items.filter((item) => item[property] === value);
};

/**
 * Convierte array a objeto con clave específica
 * @param {Array} items
 * @param {string} key
 * @returns {Object}
 */
export const arrayToObject = (items, key) => {
  return items.reduce((acc, item) => {
    acc[item[key]] = item;
    return acc;
  }, {});
};

/**
 * Valida contraseña (mínimo 8 caracteres, 1 mayúscula, 1 número)
 * @param {string} password
 * @returns {boolean}
 */
export const isValidPassword = (password) => {
  const hasLength = password.length >= 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  return hasLength && hasUpperCase && hasNumber;
};

/**
 * Calcula diferencia de días entre dos fechas
 * @param {Date} date1
 * @param {Date} date2
 * @returns {number}
 */
export const daysBetween = (date1, date2) => {
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  return Math.abs(
    Math.round((date1.getTime() - date2.getTime()) / millisecondsPerDay)
  );
};

/**
 * Convierte objeto a query string
 * @param {Object} obj
 * @returns {string}
 */
export const objectToQueryString = (obj) => {
  return Object.entries(obj)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
};

/**
 * Debounce una función
 * @param {Function} func
 * @param {number} delay
 * @returns {Function}
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Valida si objeto está vacío
 * @param {Object} obj
 * @returns {boolean}
 */
export const isEmpty = (obj) => {
  return Object.keys(obj).length === 0;
};
