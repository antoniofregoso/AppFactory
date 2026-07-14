import { currentLang } from '../store';
import { t } from '../../i18n';
import { mountPreactPage } from '../utils';

const BUTTON_BASE = 'inline-flex min-h-11 items-center justify-center rounded-xl border px-4 py-2.5 text-sm font-bold transition hover:-translate-y-px disabled:cursor-not-allowed disabled:opacity-50';
const BUTTON_PRIMARY = `${BUTTON_BASE} border-transparent bg-[var(--app-accent)] text-white shadow-[0_12px_30px_rgba(16,185,129,.24)] hover:bg-[var(--app-accent-hover)]`;
const SKELETON_LINE = 'block rounded-full bg-slate-200';
const BAR_HEIGHTS = [45, 68, 52, 82, 63, 92, 74];
const FEATURES = [
    ['01', 'organize'],
    ['02', 'collaborate'],
    ['03', 'grow'],
];

function PreviewKpi({ iconColor }) {
    return (
        <article class="min-w-0 rounded-xl border border-slate-200 bg-white p-4">
            <span class={`block h-6 w-6 rounded-full ${iconColor}`}></span>
            <strong class="mt-3 block h-3 w-3/5 rounded-full bg-slate-500"></strong>
            <small class="mt-2 block h-1.5 w-4/5 rounded-full bg-slate-200"></small>
        </article>
    );
}

function Home({ lang, onLogin }) {
    return (
        <div class="app-shell app-home flex min-h-svh flex-col overflow-hidden">
            <header class="relative z-10 px-5 py-5 sm:px-8 lg:px-16">
                <nav class="mx-auto flex min-h-14 w-full max-w-[1180px] items-center justify-between gap-8"
                    aria-label={t('home.nav.aria', lang)}>
                    <a class="home-brand inline-flex items-center gap-3 text-[var(--app-text)] no-underline" href="/" aria-label="WebApp">
                        <img class="home-brand-logo h-9 w-9 rounded-[.65rem] shadow-[0_8px_24px_rgba(16,185,129,.2)]" src="/logo.png" alt="" />
                        <span class="hidden text-base font-bold tracking-tight sm:inline">WebApp</span>
                    </a>
                    <div class="flex items-center gap-3">
                        <button class={`${BUTTON_BASE} border-[var(--app-border)] bg-white/70 text-[var(--app-text)] hover:bg-white`}
                            type="button" data-home-login onClick={onLogin}>{t('home.login', lang)}</button>
                        <button class={BUTTON_PRIMARY} type="button" disabled aria-disabled="true"
                            title={t('home.signup.soon', lang)}>{t('home.signup', lang)}</button>
                    </div>
                </nav>
            </header>

            <main class="flex-1">
                <section class="home-hero mx-auto grid min-h-[620px] w-[calc(100%_-_2.5rem)] max-w-[1180px] items-center gap-12 py-14 text-center lg:grid-cols-[minmax(0,.9fr)_minmax(460px,1.1fr)] lg:gap-20 lg:py-24 lg:text-left"
                    aria-labelledby="home-title">
                    <div class="relative z-[2]">
                        <span class="mb-4 inline-block text-xs font-extrabold uppercase tracking-[.12em] text-[var(--app-accent)]">
                            {t('home.eyebrow', lang)}
                        </span>
                        <h1 class="m-0 max-w-[700px] text-[clamp(2.7rem,5.8vw,5.25rem)] font-[780] leading-[.98] tracking-[-.06em] text-[var(--app-text)]"
                            id="home-title">{t('home.title', lang)}</h1>
                        <p class="mx-auto mt-7 max-w-[600px] text-[clamp(1rem,1.5vw,1.15rem)] leading-7 text-[var(--app-text-muted)] lg:mx-0">
                            {t('home.subtitle', lang)}
                        </p>
                        <div class="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start">
                            <button class={`${BUTTON_PRIMARY} min-h-13 w-full px-6 sm:w-auto`} type="button" data-home-login onClick={onLogin}>
                                {t('home.cta', lang)}
                            </button>
                            <a class="px-2 py-3 text-sm font-bold text-[var(--app-text)] underline-offset-4 hover:text-[var(--app-accent)]"
                                href="#features">{t('home.learn_more', lang)}</a>
                        </div>
                        <div class="mt-9 flex flex-wrap justify-center gap-x-5 gap-y-3 text-xs font-semibold text-[var(--app-text-muted)] lg:justify-start"
                            aria-label={t('home.trust.aria', lang)}>
                            <span><i class="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-emerald-500"></i>{t('home.trust.secure', lang)}</span>
                            <span><i class="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-emerald-500"></i>{t('home.trust.flexible', lang)}</span>
                            <span><i class="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-emerald-500"></i>{t('home.trust.simple', lang)}</span>
                        </div>
                    </div>

                    <div class="home-preview relative mx-auto mt-4 w-full max-w-[620px] [perspective:1200px]" aria-hidden="true">
                        <div class="absolute inset-[10%] -z-10 rounded-full bg-emerald-500/20 blur-[70px]"></div>
                        <div class="overflow-hidden rounded-2xl border border-white/80 bg-white/90 shadow-[0_35px_90px_rgba(15,23,42,.2)] backdrop-blur-xl lg:[transform:rotateY(-5deg)_rotateX(2deg)]">
                            <div class="flex h-11 items-center gap-1.5 border-b border-slate-200 px-4">
                                <span class="h-2 w-2 rounded-full bg-red-300"></span><span class="h-2 w-2 rounded-full bg-amber-300"></span><span class="h-2 w-2 rounded-full bg-green-300"></span>
                            </div>
                            <div class="grid min-h-[330px] grid-cols-[20%_1fr] sm:grid-cols-[25%_1fr]">
                                <aside class="bg-slate-900 px-3 py-6 sm:px-5">
                                    <div class="mb-8 h-8 w-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600"></div>
                                    <div class="my-5 h-2 w-full rounded-full bg-emerald-400"></div>
                                    <div class="my-5 h-2 w-4/5 rounded-full bg-slate-700"></div>
                                    <div class="my-5 h-2 w-4/5 rounded-full bg-slate-700"></div>
                                    <div class="my-5 h-2 w-1/2 rounded-full bg-slate-700"></div>
                                </aside>
                                <div class="bg-slate-50 p-4 sm:p-6">
                                    <div class="flex items-center justify-between">
                                        <div class="grid gap-2"><small class={`${SKELETON_LINE} h-1.5 w-14`}></small><strong class="block h-3 w-32 rounded-full bg-slate-400"></strong></div>
                                        <span class="h-7 w-16 rounded-lg bg-emerald-600"></span>
                                    </div>
                                    <div class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
                                        <PreviewKpi iconColor="bg-emerald-100" />
                                        <PreviewKpi iconColor="bg-emerald-100" />
                                        <div class="hidden sm:block"><PreviewKpi iconColor="bg-amber-100" /></div>
                                    </div>
                                    <div class="mt-4 h-36 rounded-xl border border-slate-200 bg-white p-4">
                                        <div class="flex h-full items-end justify-around gap-2">
                                            {BAR_HEIGHTS.map((height, index) => (
                                                <i key={index} class="w-[9%] rounded-t bg-gradient-to-b from-emerald-400 to-emerald-600" style={{ height: `${height}%` }}></i>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="border-t border-[var(--app-border)] bg-white/60 px-5 py-16 sm:px-8 lg:px-16 lg:py-24"
                    id="features" aria-labelledby="features-title">
                    <div class="mx-auto w-full max-w-[1180px]">
                        <span class="mb-4 inline-block text-xs font-extrabold uppercase tracking-[.12em] text-[var(--app-accent)]">
                            {t('home.features.eyebrow', lang)}
                        </span>
                        <h2 class="m-0 max-w-[620px] text-[clamp(2rem,4vw,3.4rem)] leading-[1.05] tracking-[-.045em]"
                            id="features-title">{t('home.features.title', lang)}</h2>
                    </div>
                    <div class="home-feature-grid mx-auto mt-12 grid w-full max-w-[1180px] gap-4 md:grid-cols-3">
                        {FEATURES.map(([number, key]) => (
                            <article key={key} class="rounded-2xl border border-[var(--app-border)] bg-white/80 p-6 transition hover:-translate-y-1 hover:shadow-[0_20px_50px_rgba(15,23,42,.09)] lg:p-9">
                                <span class="text-xs font-extrabold tracking-[.08em] text-[var(--app-accent)]">{number}</span>
                                <h3 class="mb-3 mt-8 text-lg font-bold">{t(`home.feature.${key}.title`, lang)}</h3>
                                <p class="m-0 text-sm leading-6 text-[var(--app-text-muted)]">{t(`home.feature.${key}.text`, lang)}</p>
                            </article>
                        ))}
                    </div>
                </section>
            </main>

            <footer class="home-footer border-t border-[var(--app-border)] bg-white px-5 py-8 sm:px-8 lg:px-16">
                <div class="mx-auto grid w-full max-w-[1180px] items-center gap-5 text-center text-xs text-[var(--app-text-muted)] sm:grid-cols-[1fr_auto_1fr]">
                    <a class="home-brand mx-auto inline-flex items-center gap-3 text-[var(--app-text)] no-underline sm:mx-0 sm:justify-self-start" href="/">
                        <img class="home-brand-logo h-9 w-9 rounded-[.65rem]" src="/logo.png" alt="" /><span class="font-bold">WebApp</span>
                    </a>
                    <p class="m-0">{t('home.footer.copy', lang)}</p>
                    <span class="sm:justify-self-end">© {new Date().getFullYear()} WebApp</span>
                </div>
            </footer>
        </div>
    );
}

export function home(_req, router) {
    const lang = currentLang.value;
    const appEl = document.getElementById('app');
    mountPreactPage(<Home lang={lang} onLogin={() => router.goTo('login')} />, appEl);
}
