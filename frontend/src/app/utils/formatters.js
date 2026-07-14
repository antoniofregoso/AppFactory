/**
 * Formats a number as a currency string.
 * @param {number} value 
 * @param {string} locale 
 * @param {string} currency 
 * @returns 
 */
export const formatCurrency = (value, locale = 'es-MX', currency = 'MXN') => {
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
    }).format(value);
};

const parseDate = (dateString) => {
    return new Date(dateString.replace(' ', 'T'));
};

/**
 * Formats a date string into a more readable format.
 * @param {string} dateString 
 * @param {string} locale 
 * @returns 
 */
export const formatDate = (dateString, locale = 'es-MX') => {
    const date = parseDate(dateString);
    return new Intl.DateTimeFormat(locale, {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    }).format(date);
};

/**
 * Formats a date and time string into a more readable format.
 * @param {string} dateString 
 * @param {string} locale 
 * @returns 
 */
export const formatDateTime = (dateString, locale = 'es-MX') => {
    const date = parseDate(dateString);
    
    // Validar que la fecha sea correcta para evitar errores en el format
    if (isNaN(date.getTime())) return 'Fecha inválida';

    return new Intl.DateTimeFormat(locale, {
        day: 'numeric',
        month: 'short',   // Cambia a 'long' si quieres "enero" completo
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).format(date);
};