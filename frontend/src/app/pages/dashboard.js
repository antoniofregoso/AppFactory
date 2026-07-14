import { h, render } from 'preact';
import { effect } from '@preact/signals';
import { appSignal, authSignal, isAuthenticated } from '../store';
import { contextActions, dashboardActions } from '../store/actions';
import { mountSidebar, mountTopbar, ensureAlertStackMounted, MENU_ITEMS } from '../components';
import { CalendarView, FormView, KanbanView, ListView, renderInsights, initInsights, patchInsights } from '../views';
import { applyTheme, getAreaTitle, normalizePagination, paginateData, resetAppRoot } from '../utils';
import { getRecordBreadcrumbs, setRecordBreadcrumbs } from '../utils/routing.js';
import { startActivityHeartbeat } from '../api/activity.js';
import { startPendingCountsPolling } from '../api/pendingCounts.js';
import { startNotificationsPolling } from '../store/notificationsStore.js';
import { registerServiceWorker } from '../api/webPush.js';
import { fetchSystemModelView } from '../api/systemModel.js';

const EMPTY_DASHBOARD_DATA = {
    model: {
        name: '',
        label: {},
        groupBy: null,
        tags: [],
        schema: [],
    },
    records: [],
};

let _modelViewRequestKey = null;
let _insightViewRequestKey = null;
let _currentInsightView = null;

const INSIGHT_VIEWS = Object.freeze({
    userLogs: Object.freeze({
        model: 'system.insight',
        use: 'insight',
        name: 'userLogs',
    }),
});

function getDashboardData(state = appSignal.value) {
    return state.model ?? EMPTY_DASHBOARD_DATA;
}

function getRouteSearchParams() {
    return new URLSearchParams(globalThis.location?.search ?? '');
}

function getModelViewOptions() {
    const params = getRouteSearchParams();
    return {
        name: params.get('view_name') || params.get('name') || 'default',
        use: (params.get('mode') || params.get('use') || 'view').toLowerCase(),
    };
}

export function getInsightViewOptions(name = getRouteSearchParams().get('v')) {
    return name ? INSIGHT_VIEWS[name] ?? null : null;
}

function ensureInsightViewLoaded(options, period) {
    if (!options) {
        _insightViewRequestKey = null;
        return;
    }
    const requestKey = `${options.model}:${options.use}:${options.name}:${period}`;
    if (_insightViewRequestKey === requestKey) return;
    _insightViewRequestKey = requestKey;

    fetchSystemModelView({ ...options, period })
        .then((modelView) => {
            if (_insightViewRequestKey !== requestKey) return;
            const insight = modelView?.model?.schema;
            if (!insight || Array.isArray(insight)) {
                throw new Error(`Insight "${options.name}" returned an invalid schema`);
            }
            dashboardActions.setInsights(insight);
        })
        .catch((error) => {
            if (_insightViewRequestKey !== requestKey) return;
            console.error(`Unable to load insight "${options.name}".`, error);
        });
}

function ensureModelViewLoaded(modelName, options) {
    if (!modelName) {
        if (appSignal.value.model) dashboardActions.setModelView(null);
        _modelViewRequestKey = null;
        return;
    }

    const requestKey = `${modelName}:${options.use}:${options.name}`;
    if (_modelViewRequestKey === requestKey) return;
    _modelViewRequestKey = requestKey;

    fetchSystemModelView({ model: modelName, use: options.use, name: options.name })
        .then((modelView) => {
            if (_modelViewRequestKey !== requestKey) return;
            dashboardActions.setModelView(modelView);
        })
        .catch((error) => {
            if (_modelViewRequestKey !== requestKey) return;
            console.error(`Unable to load dashboard view "${requestKey}".`, error);
            dashboardActions.setModelView(null);
        });
}

// ── Track last rendered values to avoid redundant re-renders ──────────────────
let _lastLang = null;
let _lastTheme = null;
let _lastExpanded = null;
let _lastArea = null;
let _lastView = null;
let _lastPage = null;
let _lastPerPage = null;
let _lastTotal = null;
let _lastRecordRoute = false;
let _lastRecordModel = null;
let _lastRecordUuid = null;
let _lastInsights = null;
let _lastModel = null;
let _lastPendingCounts = null;
let _lastUserUuid = null;
let _lastUserName = null;
let _lastUserEmail = null;
let _lastUserAvatarUrl = null;
let _lastUserIsAdmin = null;
let _effectCleanup = null;
let _currentSubarea = null;
let _currentRecordModel = null;
let _currentRecordUuid = null;

// ── View renderers (dock view-switch buttons) ─────────────────────────────────
const VIEW_COMPONENTS = {
    kanban: KanbanView,
    list: ListView,
    form: FormView,
    calendar: CalendarView,
};
const DEFAULT_VIEW = 'kanban';

// Views that need event wiring after their HTML is injected.
const VIEW_INITIALIZERS = { insights: initInsights };
let _viewCleanup = null;

function getView(state) {
    return state.dashboard?.view ?? DEFAULT_VIEW;
}

function getEffectiveView(view) {
    return _currentRecordModel && _currentRecordUuid != null ? 'form' : view;
}

function hasRecordRoute() {
    return _currentRecordModel && _currentRecordUuid != null;
}

function getPagination(state = appSignal.value) {
    return normalizePagination(state.dashboard, getDashboardData(state).records.length);
}

/** Render the content markup for the currently selected view. */
function getViewProps(view, area, lang, pagination, data = getDashboardData()) {
    const paginatedData = paginateData(data, pagination);
    if (view === 'form') {
        const commercialAreas = new Set(['crm', 'sales', 'sale', 'ventas']);
        return { data: hasRecordRoute() ? data : paginatedData, lang, options: {
            recordModel: _currentRecordModel, recordUuid: _currentRecordUuid, showWhatsapp: commercialAreas.has(area),
        } };
    }
    return { data: paginatedData, lang };
}

/**
 * Insights is the default content on the dashboard home (no area) and on any
 * insights subarea — regardless of the selected dock view.
 */
function isInsightsContext(area, subarea) {
    return !area || subarea === 'insights';
}

/** Pick the content markup for the current page (insights or the dock view). */
function mountContent(area, subarea, view, lang, pagination = getPagination(), insights = appSignal.value.insights) {
    const root = document.getElementById('dashboard-content-root');
    if (!root) return;
    if (_viewCleanup) { _viewCleanup(); _viewCleanup = null; }
    render(null, root);
    if (isInsightsContext(area, subarea)) {
        root.innerHTML = renderInsights(insights, lang);
        _viewCleanup = initInsights(lang) || null;
        return;
    }
    root.replaceChildren();
    const Component = VIEW_COMPONENTS[view] ?? VIEW_COMPONENTS[DEFAULT_VIEW];
    const props = getViewProps(view, area, lang, pagination);
    const recordKey = view === 'form' ? props.options?.recordUuid ?? props.data?.records?.[0]?.uuid ?? '' : '';
    render(h(Component, { ...props, key: `${view}:${recordKey}` }), root);
}

/**
 * Wire up the active view after its markup is in the DOM. Cleans up the
 * previously active view first (e.g. stops the calendar now-line timer).
 */
function initActiveView(view, lang) {
    if (_viewCleanup) { _viewCleanup(); _viewCleanup = null; }
    const initFn = VIEW_INITIALIZERS[view];
    if (initFn) _viewCleanup = initFn(lang) || null;
}

/** Dock view-switch callback passed into the topbar. */
function handleViewChange(view) {
    dashboardActions.setView(view);
}

function getLabel(item, lang) {
    return lang === 'es' ? item.labelEs : item.labelEn;
}

function getTopbarBreadcrumb(area, subarea, lang) {
    const areaItem = MENU_ITEMS.find((item) => item.key === area);
    const subareaItem = areaItem?.items?.find((item) => item.key === subarea
        || item.url?.split('/').filter(Boolean).at(-1) === subarea);
    if (!area) return [];
    const items = [{ label: areaItem ? getLabel(areaItem, lang) : area, url: areaItem?.url ?? `/dashboard/${area}` }];
    const modelLabel = getDashboardData()?.model?.label?.[lang];
    const subareaBreadcrumb = subarea ? {
        label: subareaItem ? getLabel(subareaItem, lang) : (modelLabel || subarea),
        url: `/dashboard/${area}/${subarea}`,
    } : null;
    if (hasRecordRoute()) {
        const recordItems = getRecordBreadcrumbs();
        items.push(...(recordItems.length ? recordItems : (subareaBreadcrumb ? [subareaBreadcrumb] : [])));
    } else if (subareaBreadcrumb) {
        items.push(subareaBreadcrumb);
        setRecordBreadcrumbs(window.location.pathname, [subareaBreadcrumb]);
    }
    return items;
}

function shouldShowTopbarTools(area, subarea) {
    return Boolean(area) && subarea !== 'insights';
}

/** Unmount a nested Preact root (sidebar/topbar) before its container is destroyed. */
function unmountRegion(id) {
    const el = document.getElementById(id);
    if (el) render(null, el);
}

/**
 * Sidebar and topbar are self-contained Preact components: mounting them
 * again with fresh props is enough for Preact to diff the DOM and keep
 * every listener wired — no separate init/cleanup calls needed here.
 */
function syncChrome(lang, theme, expanded, area, subarea, view, pagination) {
    const pageTitle = area ? getAreaTitle(area, lang, MENU_ITEMS) : '';
    const breadcrumb = getTopbarBreadcrumb(area, subarea, lang);
    const showTopbarTools = shouldShowTopbarTools(area, subarea);
    const { uuid: userUuid, name: userName, email: userEmail, avatarUrl: userAvatarUrl, isAdmin: userIsAdmin } = authSignal.value;
    const pendingCounts = appSignal.value.pendingCounts ?? {};
    const disabledViews = subarea === 'system.message' ? ['kanban'] : [];

    mountSidebar(document.getElementById('dashboard-sidebar-root'), {
        lang,
        expanded,
        activeArea: area,
        isAdmin: userIsAdmin,
    });
    mountTopbar(document.getElementById('dashboard-topbar-root'), {
        lang,
        theme,
        pageTitle,
        breadcrumb,
        showTools: showTopbarTools,
        pagination,
        currentView: view,
        router: _router,
        onViewChange: handleViewChange,
        user: { uuid: userUuid, name: userName, email: userEmail, avatarUrl: userAvatarUrl },
        pendingCounts,
        disabledViews,
    });
}

/**
 * Full dashboard render (sidebar + topbar + content).
 * Called on first load and whenever signal values change.
 */
function renderDashboard(lang, theme, expanded, area, subarea, view) {
    const pagination = getPagination();
    const appEl = document.getElementById('app');
    if (!appEl) return;

    // Home/Login render with Preact — unmount any previous Preact tree
    // before taking over #app with a raw HTML string. Also unmount the
    // nested sidebar/topbar Preact roots from a prior dashboard visit
    // before their containers are torn down below.
    unmountRegion('dashboard-sidebar-root');
    unmountRegion('dashboard-topbar-root');
    unmountRegion('dashboard-content-root');
    resetAppRoot(appEl);
    appEl.innerHTML = `
    <div class="dash-layout">
        <div id="dashboard-sidebar-root"></div>
        <div class="dash-main">
            <div id="dashboard-topbar-root"></div>
            <div id="dashboard-content-root"></div>
        </div>
    </div>
    `;

    syncChrome(lang, theme, expanded, area, subarea, view, pagination);
    mountContent(area, subarea, view, lang, pagination);

    applyTheme(theme);

    // Listen for system theme changes when 'system' is selected
    if (theme === 'system') {
        const mql = window.matchMedia('(prefers-color-scheme: dark)');
        mql.addEventListener('change', () => applyTheme('system'));
    }
}

/**
 * Patch only the components that changed (avoids full re-render flicker).
 */
function patchDashboard(lang, theme, expanded, area, view, prevLang, prevTheme, prevExpanded, prevArea, prevView) {
    const areaChanged = area !== prevArea;
    const langChanged = lang !== prevLang;
    const themeChanged = theme !== prevTheme;
    const expandedChanged = expanded !== prevExpanded;
    const viewChanged = view !== prevView;
    const pagination = getPagination();
    const paginationChanged = pagination.page !== _lastPage
        || pagination.perPage !== _lastPerPage
        || pagination.total !== _lastTotal;
    const recordRouteChanged =
        hasRecordRoute() !== _lastRecordRoute ||
        _currentRecordModel !== _lastRecordModel ||
        _currentRecordUuid !== _lastRecordUuid;
    const insights = appSignal.value.insights;
    const insightsChanged = insights !== _lastInsights;
    const model = appSignal.value.model;
    const modelChanged = model !== _lastModel;
    const pendingCounts = appSignal.value.pendingCounts;
    const pendingCountsChanged = pendingCounts !== _lastPendingCounts;
    const {
        uuid: userUuid,
        name: userName,
        email: userEmail,
        avatarUrl: userAvatarUrl,
        isAdmin: userIsAdmin,
    } = authSignal.value;
    const userChanged =
        userUuid !== _lastUserUuid ||
        userName !== _lastUserName ||
        userEmail !== _lastUserEmail ||
        userAvatarUrl !== _lastUserAvatarUrl ||
        userIsAdmin !== _lastUserIsAdmin;

    // Sidebar + topbar just get re-rendered with fresh props — Preact keeps
    // their DOM and event listeners in sync automatically.
    if (areaChanged || langChanged || themeChanged || expandedChanged || viewChanged || recordRouteChanged || paginationChanged || pendingCountsChanged || userChanged || modelChanged) {
        syncChrome(lang, theme, expanded, area, _currentSubarea, view, pagination);
    }

    // Patch content (area, lang, view, selected record, or live schema change)
    if (areaChanged || langChanged || viewChanged || recordRouteChanged || paginationChanged || modelChanged) {
        mountContent(area, _currentSubarea, view, lang, pagination);
    }

    // Insight data changes keep the existing layout and patch only changed ids.
    if (
        insightsChanged &&
        !areaChanged && !langChanged && !viewChanged && !recordRouteChanged && !paginationChanged && !modelChanged &&
        isInsightsContext(area, _currentSubarea)
    ) {
        const patched = patchInsights(_lastInsights, insights, lang);
        if (!patched) {
            mountContent(area, _currentSubarea, view, lang, pagination, insights);
        }
    }

    // Apply theme to <html>
    if (themeChanged) {
        applyTheme(theme);
        if (isInsightsContext(area, _currentSubarea)) {
            initActiveView('insights', lang);
        }
    }
}

// Store router reference for sidebar navigation
let _router = null;

/**
 * Dashboard page callback — called by CJ Router.
 * @param {object} req    — router request object
 * @param {object} router — CJ Router instance
 */
export function dashboard(req, router) {
    if (!isAuthenticated.value) {
        _effectCleanup?.();
        _effectCleanup = null;
        _viewCleanup?.();
        _viewCleanup = null;
        router.goTo('login');
        return;
    }

    startActivityHeartbeat();
    startPendingCountsPolling();
    startNotificationsPolling();
    ensureAlertStackMounted();
    void registerServiceWorker().catch((error) => console.error('Unable to register the service worker.', error));
    _router = router;
    const areaFromUrl = req.params?.area;
    const prevSubarea = _currentSubarea;
    const hadRecordRoute = _currentRecordModel && _currentRecordUuid != null;
    _currentRecordUuid = req.params?.uuid ?? null;
    _currentSubarea = req.params?.model ?? null;
    _currentRecordModel = _currentSubarea === 'insights'
        ? null
        : req.params?.model ?? null;
    const isRecordRoute = hasRecordRoute();
    if (!MENU_ITEMS.some(item => item.key === areaFromUrl)) {
        if (areaFromUrl!=undefined) {return router.trigger404(req.pathname);}
    }
    const areaChanged = areaFromUrl !== appSignal.value.context.active_area;
    const subareaChanged = _currentSubarea !== prevSubarea;
    const modelViewOptions = getModelViewOptions();
    if (_currentSubarea === 'insights') {
        _currentInsightView = getInsightViewOptions();
        if (!_currentInsightView) return router.trigger404(req.pathname);
        ensureModelViewLoaded(null, modelViewOptions);
        ensureInsightViewLoaded(
            _currentInsightView,
            appSignal.value.insights?.period ?? 'today',
        );
    } else {
        _currentInsightView = null;
        ensureInsightViewLoaded(null, 'today');
        ensureModelViewLoaded(_currentRecordModel, modelViewOptions);
    }
    if (areaFromUrl && areaChanged) {
        contextActions.setActiveArea(areaFromUrl);
    }
    if (!areaFromUrl && appSignal.value.context.active_area) {
        contextActions.setActiveArea(null);
    }
    // Open record URLs directly in form view; otherwise reset when leaving a page.
    if (isRecordRoute) {
        dashboardActions.setView('form');
    } else if (areaChanged || subareaChanged) {
        dashboardActions.setView(_currentSubarea === 'system.message' ? 'list' : DEFAULT_VIEW);
    } else if (hadRecordRoute && getView(appSignal.value) === 'form') {
        // Leaving a record route via browser back — reset to default view.
        // If the user clicked a view button, the signal is already set to the target
        // view (not 'form'), so this branch is skipped and their choice is respected.
        dashboardActions.setView(DEFAULT_VIEW);
    }

    const state = appSignal.value;
    const lang = state.context.lang;
    const theme = state.context.theme;
    const expanded = state.context.sidebar_expanded;
    const area = state.context.active_area;
    const view = getEffectiveView(getView(state));

    // ── Initial full render ───────────────────────────────────────────────────
    renderDashboard(lang, theme, expanded, area, _currentSubarea, view);

    // Track rendered values
    _lastLang = lang;
    _lastTheme = theme;
    _lastExpanded = expanded;
    _lastArea = area;
    _lastView = view;
    const pagination = getPagination(state);
    _lastPage = pagination.page;
    _lastPerPage = pagination.perPage;
    _lastTotal = pagination.total;
    _lastRecordRoute = isRecordRoute;
    _lastRecordModel = _currentRecordModel;
    _lastRecordUuid = _currentRecordUuid;
    _lastInsights = state.insights;
    _lastModel = state.model;
    _lastPendingCounts = state.pendingCounts;
    _lastUserUuid = authSignal.value.uuid;
    _lastUserName = authSignal.value.name;
    _lastUserEmail = authSignal.value.email;
    _lastUserAvatarUrl = authSignal.value.avatarUrl;
    _lastUserIsAdmin = authSignal.value.isAdmin;

    // ── Cleanup previous effect if navigating back to this page ──────────────
    if (_effectCleanup) {
        _effectCleanup();
        _effectCleanup = null;
    }

    // ── Reactive effect: re-patch on any signal change ────────────────────────
    _effectCleanup = effect(() => {
        const s = appSignal.value;
        const newLang = s.context.lang;
        const newTheme = s.context.theme;
        const newExpanded = s.context.sidebar_expanded;
        const newArea = s.context.active_area;
        const newView = getEffectiveView(getView(s));
        const newPagination = getPagination(s);
        const newInsights = s.insights;
        const newModel = s.model;
        const newPendingCounts = s.pendingCounts;
        const auth = authSignal.value;

        if (
            _currentInsightView &&
            newInsights?.period !== _lastInsights?.period
        ) {
            ensureInsightViewLoaded(
                _currentInsightView,
                newInsights?.period ?? 'today',
            );
        }

        const changed =
            newLang !== _lastLang ||
            newTheme !== _lastTheme ||
            newExpanded !== _lastExpanded ||
            newArea !== _lastArea ||
            newView !== _lastView ||
            newPagination.page !== _lastPage ||
            newPagination.perPage !== _lastPerPage ||
            newPagination.total !== _lastTotal ||
            newInsights !== _lastInsights ||
            newModel !== _lastModel ||
            newPendingCounts !== _lastPendingCounts ||
            auth.uuid !== _lastUserUuid ||
            auth.name !== _lastUserName ||
            auth.email !== _lastUserEmail ||
            auth.avatarUrl !== _lastUserAvatarUrl ||
            auth.isAdmin !== _lastUserIsAdmin ||
            hasRecordRoute() !== _lastRecordRoute ||
            _currentRecordModel !== _lastRecordModel ||
            _currentRecordUuid !== _lastRecordUuid;

        if (!changed) return;

        patchDashboard(
            newLang, newTheme, newExpanded, newArea, newView,
            _lastLang, _lastTheme, _lastExpanded, _lastArea, _lastView
        );

        _lastLang = newLang;
        _lastTheme = newTheme;
        _lastExpanded = newExpanded;
        _lastArea = newArea;
        _lastView = newView;
        _lastPage = newPagination.page;
        _lastPerPage = newPagination.perPage;
        _lastTotal = newPagination.total;
        _lastRecordRoute = hasRecordRoute();
        _lastRecordModel = _currentRecordModel;
        _lastRecordUuid = _currentRecordUuid;
        _lastInsights = newInsights;
        _lastModel = newModel;
        _lastPendingCounts = newPendingCounts;
        _lastUserUuid = auth.uuid;
        _lastUserName = auth.name;
        _lastUserEmail = auth.email;
        _lastUserAvatarUrl = auth.avatarUrl;
        _lastUserIsAdmin = auth.isAdmin;
    });
}
