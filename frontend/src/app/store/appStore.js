import { signal, effect, computed } from '@preact/signals';
import initialStateJson from './state.json';

const EMPTY_INSIGHTS = {
    period: 'today',
    kpis: [],
    gauges: [],
    graphics: [],
    layout: {},
};

const INITIAL_STATE = {
    ...initialStateJson,
    insights: EMPTY_INSIGHTS,
};
const STORAGE_KEY = 'dashboard_state';

function persistState(storage, state) {
    const persistedState = { ...state };
    delete persistedState.insights;
    // The declarative model view is fetched fresh over GraphQL each session
    // (see dashboard.js), so it should never be read back from a stale cache.
    delete persistedState.model;
    storage?.setItem(STORAGE_KEY, JSON.stringify(persistedState));
}

function loadInitialState() {
    const storage = globalThis.localStorage;
    const localData = storage?.getItem(STORAGE_KEY);

    // CASE 1: First visit
    if (!localData) {
        const newState = JSON.parse(JSON.stringify(INITIAL_STATE));
        newState.meta.start = Date.now();
        persistState(storage, newState);
        return newState;
    }

    const savedState = JSON.parse(localData);
    // Dashboard configuration and seed data are loaded fresh on every startup.
    // Runtime refreshes update indicator data in memory through dashboardActions.
    savedState.insights = JSON.parse(JSON.stringify(EMPTY_INSIGHTS));
    const sessionStarted = savedState.meta?.start > 0;

    // CASE 2: Return after 24 h — reset session but keep preferences
    if (sessionStarted) {
        const EXPIRATION_LIMIT = 24 * 60 * 60 * 1000;
        if (Date.now() - savedState.meta.start > EXPIRATION_LIMIT) {
            const newState = JSON.parse(JSON.stringify(INITIAL_STATE));
            // Preserve user preferences (theme, lang, sidebar)
            newState.context.theme            = savedState.context?.theme            ?? INITIAL_STATE.context.theme;
            newState.context.lang             = savedState.context?.lang             ?? INITIAL_STATE.context.lang;
            newState.context.sidebar_expanded = savedState.context?.sidebar_expanded ?? INITIAL_STATE.context.sidebar_expanded;
            newState.meta.start = Date.now();
            return newState;
        }
    }

    // CASE 3: Return before 24 h — restore full state
    return savedState;
}

// ── Signal ────────────────────────────────────────────────────────────────────
export const appSignal = signal(loadInitialState());

// ── Auto-persist to localStorage ──────────────────────────────────────────────
effect(() => {
    persistState(globalThis.localStorage, appSignal.value);
});

// ── Computed selectors ────────────────────────────────────────────────────────
export const currentTheme       = computed(() => appSignal.value.context.theme);
export const currentLang        = computed(() => appSignal.value.context.lang);
export const isSidebarExpanded  = computed(() => appSignal.value.context.sidebar_expanded);
export const activeArea         = computed(() => appSignal.value.context.active_area);
