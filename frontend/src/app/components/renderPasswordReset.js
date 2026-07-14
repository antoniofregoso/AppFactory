
import { t } from '../../i18n/translations.js';

export function renderPasswordReset(lang = 'en') {
    return `
    <main class="app-shell login-page">
        <section class="login-panel" aria-label="${t('auth.reset.aria', lang)}">
            <a class="login-brand" href="/" aria-label="WebApp home">
                <img class="login-logo" src="/logo.png" alt="WebApp logo" />
                <span class="login-brand-name">WebApp</span>
            </a>

            <div class="login-copy">
                <p class="login-eyebrow">${t('auth.reset.eyebrow', lang)}</p>
                <h1 class="login-title">${t('auth.reset.title', lang)}</h1>
                <p class="login-subtitle">${t('auth.reset.subtitle', lang)}</p>
            </div>

            <form class="login-form" action="#">
                <label class="login-field">
                    <span>${t('auth.email', lang)}</span>
                    <input type="email" name="email" placeholder="${t('auth.email.placeholder', lang)}" autocomplete="email" />
                </label>

                <button class="login-submit" type="button">${t('auth.reset.submit', lang)}</button>

                <div class="login-row">
                    <a href="/login" class="login-link">${t('auth.back_to_login', lang)}</a>
                </div>
            </form>
        </section>
    </main>
    `;
}
