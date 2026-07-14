/**
 * Resolve effective theme considering 'system' preference.
 * @param {string} theme — 'light' | 'dark' | 'system'
 * @returns {'light'|'dark'}
 */
function resolveTheme(theme) {
    if (theme === 'system') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme;
}

/**
 * Apply the resolved theme to <html data-theme="...">
 * @param {string} theme
 */
export function applyTheme(theme) {
    const resolved = resolveTheme(theme);
    document.documentElement.setAttribute('data-theme', resolved);
}
