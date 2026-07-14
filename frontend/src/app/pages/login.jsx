import { useRef } from 'preact/hooks';
import { startActivityHeartbeat } from '../api/activity.js';
import { authenticate } from '../api/auth.js';
import { fetchCurrentUser } from '../api/user.js';
import { currentLang, setAuthSession, setCurrentUser } from '../store';
import { t } from '../../i18n/translations.js';
import { faEye, faEyeSlash, icon } from '../components/icon.js';
import { mountPreactPage } from '../utils';

const REMEMBERED_EMAIL_KEY = 'login_email';

function getRememberedEmail() {
    return globalThis.localStorage?.getItem(REMEMBERED_EMAIL_KEY) ?? '';
}

function updateRememberedEmail(email, remember) {
    if (remember) {
        globalThis.localStorage?.setItem(REMEMBERED_EMAIL_KEY, email);
        return;
    }
    globalThis.localStorage?.removeItem(REMEMBERED_EMAIL_KEY);
}

function Login({ lang, router }) {
    const formRef = useRef(null);
    const passwordInputRef = useRef(null);
    const passwordToggleRef = useRef(null);
    const showIconRef = useRef(null);
    const hideIconRef = useRef(null);
    const errorRef = useRef(null);
    const submitButtonRef = useRef(null);

    const submitLabel = t('auth.sign_in', lang);
    const rememberedEmail = getRememberedEmail();

    const togglePassword = () => {
        const passwordInput = passwordInputRef.current;
        const toggle = passwordToggleRef.current;
        const showPassword = passwordInput.type === 'password';
        passwordInput.type = showPassword ? 'text' : 'password';
        toggle.setAttribute('aria-pressed', String(showPassword));
        const label = t(showPassword ? 'auth.password.hide' : 'auth.password.show', lang);
        toggle.setAttribute('aria-label', label);
        toggle.title = label;
        showIconRef.current.hidden = showPassword;
        hideIconRef.current.hidden = !showPassword;
        passwordInput.focus();
    };

    const showError = (message) => {
        const errorElement = errorRef.current;
        errorElement.textContent = message;
        errorElement.hidden = false;
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        const form = formRef.current;
        if (!form.reportValidity()) return;

        const submitButton = submitButtonRef.current;
        errorRef.current.hidden = true;
        submitButton.disabled = true;
        submitButton.setAttribute('aria-busy', 'true');
        submitButton.textContent = t('auth.signing_in', lang);

        const email = form.elements.email.value.trim();
        try {
            const session = await authenticate(email, form.elements.password.value);
            setAuthSession(session);
            try {
                setCurrentUser(await fetchCurrentUser());
            } catch {
                // Non-critical: the topbar just won't show the user's name.
            }
            updateRememberedEmail(email, form.elements.remember.checked);
            startActivityHeartbeat();
            router.goTo('dash');
        } catch (error) {
            const messageKey = error?.code === 'AUTHENTICATION_FAILED'
                ? 'auth.login.error'
                : 'auth.login.unavailable';
            showError(t(messageKey, lang));
        } finally {
            submitButton.disabled = false;
            submitButton.removeAttribute('aria-busy');
            submitButton.textContent = submitLabel;
        }
    };

    return (
        <main class="app-shell login-page">
            <section class="login-panel" aria-label={t('auth.login.aria', lang)}>
                <a class="login-brand" href="/" aria-label="WebApp home">
                    <img class="login-logo" src="/logo.png" alt="WebApp logo" />
                    <span class="login-brand-name">WebApp</span>
                </a>

                <div class="login-copy">
                    <p class="login-eyebrow">{t('auth.login.eyebrow', lang)}</p>
                    <h1 class="login-title">{t('auth.login.title', lang)}</h1>
                    <p class="login-subtitle">{t('auth.login.subtitle', lang)}</p>
                </div>

                <form class="login-form" data-login-form ref={formRef} onSubmit={handleSubmit}>
                    <label class="login-field">
                        <span>{t('auth.email', lang)}</span>
                        <input type="email" name="email" placeholder={t('auth.email.placeholder', lang)}
                            autocomplete="email" required defaultValue={rememberedEmail} />
                    </label>

                    <div class="login-field">
                        <label for="login-password">{t('auth.password', lang)}</label>
                        <div class="login-password-control">
                            <input id="login-password" ref={passwordInputRef} type="password" name="password"
                                placeholder="••••••••" autocomplete="current-password"
                                required minlength="8" />
                            <button class="login-password-toggle" type="button" ref={passwordToggleRef}
                                data-password-toggle aria-controls="login-password"
                                aria-label={t('auth.password.show', lang)}
                                aria-pressed="false" title={t('auth.password.show', lang)}
                                onClick={togglePassword}>
                                <span ref={showIconRef} data-password-show-icon dangerouslySetInnerHTML={{ __html: icon(faEye) }} />
                                <span ref={hideIconRef} data-password-hide-icon hidden dangerouslySetInnerHTML={{ __html: icon(faEyeSlash) }} />
                            </button>
                        </div>
                    </div>

                    <div class="login-row">
                        <label class="login-check">
                            <input type="checkbox" name="remember" defaultChecked={Boolean(rememberedEmail)} />
                            <span>{t('auth.remember', lang)}</span>
                        </label>
                        <a href="/password_reset" class="login-link">{t('auth.forgot_password', lang)}</a>
                    </div>

                    <p class="login-error" data-login-error role="alert" hidden ref={errorRef}></p>

                    <button class="login-submit" type="submit" data-login-submit ref={submitButtonRef}>
                        {submitLabel}
                    </button>
                </form>
            </section>
        </main>
    );
}

export function login(_req, router) {
    const lang = currentLang.value;
    const appEl = document.getElementById('app');
    mountPreactPage(<Login lang={lang} router={router} />, appEl);
}
