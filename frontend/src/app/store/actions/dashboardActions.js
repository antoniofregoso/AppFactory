import { appSignal } from '../appStore';

const INSIGHT_COLLECTIONS = new Set(['kpis', 'gauges', 'graphics']);
const REFRESH_FIELDS = {
    kpis: ['value', 'trend'],
    gauges: ['value'],
    graphics: ['data', 'series', 'categories', 'labels'],
};

function indicatorDataPatch(collection, update) {
    return REFRESH_FIELDS[collection].reduce((patch, field) => {
        if (Object.hasOwn(update, field)) patch[field] = update[field];
        return patch;
    }, {});
}

function refreshInsightCollection(collection, items, updates) {
    if (!Array.isArray(updates)) {
        throw new Error(`Insight refresh must provide an array: ${collection}`);
    }

    const updatesById = new Map(updates.map((update) => [update?.id, update]));
    updatesById.forEach((update, id) => {
        if (!id) throw new Error('An insight id is required');
        if (!items.some((item) => item.id === id)) {
            throw new Error(`Insight not found: ${collection}.${id}`);
        }
    });

    return items.map((item) => {
        const update = updatesById.get(item.id);
        return update ? { ...item, ...indicatorDataPatch(collection, update) } : item;
    });
}

function updateInsightCollection(collection, id, patch) {
    if (!INSIGHT_COLLECTIONS.has(collection)) {
        throw new Error(`Unknown insight collection: ${collection}`);
    }
    if (!id) throw new Error('An insight id is required');

    const state = appSignal.value;
    const insights = state.insights ?? {};
    const items = Array.isArray(insights[collection]) ? insights[collection] : [];
    let found = false;
    const nextItems = items.map((item) => {
        if (item.id !== id) return item;
        found = true;
        const changes = typeof patch === 'function' ? patch(item) : patch;
        return { ...item, ...changes, id };
    });

    if (!found) throw new Error(`Insight not found: ${collection}.${id}`);

    appSignal.value = {
        ...state,
        insights: { ...insights, [collection]: nextItems },
    };
}

export const dashboardActions = {

    setInsights(insights) {
        appSignal.value = { ...appSignal.value, insights };
    },

    setModelView(modelView) {
        const total = Math.max(0, Number(modelView?.records?.length) || 0);
        appSignal.value = {
            ...appSignal.value,
            model: modelView,
            dashboard: {
                ...appSignal.value.dashboard,
                total,
                page: 1,
            },
        };
    },

    setModelSchema(model) {
        dashboardActions.setModelView({ model, records: [] });
    },

    updateModelRecord(recordUuid, patch) {
        const model = appSignal.value.model;
        if (!model?.records) return;
        // This is an in-memory cache patch. Views already own their optimistic
        // state; emitting a new root signal here would remount them and reset
        // transient UI such as Calendar's active week/day mode.
        model.records = model.records.map((record) => String(record.uuid) === String(recordUuid)
            ? { ...record, ...patch }
            : record);
    },

    addModelRecord(record) {
        const model = appSignal.value.model;
        if (!model?.records || !record) return;
        model.records = [record, ...model.records];
        if (model.model?.name === 'user.user' && record.active !== false && record.user_type !== 'SYSTEM') {
            const followerField = model.model.schema?.find((field) => field.type === 'one2many_followers');
            if (followerField && !followerField.options?.some((user) => String(user.uuid) === String(record.uuid))) {
                followerField.options = [...(followerField.options ?? []), record];
            }
        }
        appSignal.value = {
            ...appSignal.value,
            dashboard: {
                ...appSignal.value.dashboard,
                total: model.records.length,
            },
        };
    },

    removeModelRecords(recordUuids) {
        const model = appSignal.value.model;
        if (!model?.records) return;
        const removed = new Set([...recordUuids].map(String));
        model.records = model.records.filter((record) => !removed.has(String(record.uuid)));
        appSignal.value = {
            ...appSignal.value,
            dashboard: {
                ...appSignal.value.dashboard,
                total: model.records.length,
            },
        };
    },

    setPendingCounts(counts = {}) {
        const messages = Math.max(0, Number(counts.messages) || 0);
        const notifications = Math.max(0, Number(counts.notifications) || 0);
        appSignal.value = {
            ...appSignal.value,
            pendingCounts: { messages, notifications },
        };
    },

    refreshInsights(data = {}) {
        const state = appSignal.value;
        const insights = state.insights ?? {};
        const refreshed = { ...insights };

        INSIGHT_COLLECTIONS.forEach((collection) => {
            if (!Object.hasOwn(data, collection)) return;
            const items = Array.isArray(insights[collection]) ? insights[collection] : [];
            refreshed[collection] = refreshInsightCollection(collection, items, data[collection]);
        });
        if (Object.hasOwn(data, 'period')) refreshed.period = data.period;

        appSignal.value = { ...state, insights: refreshed };
    },

    setInsightPeriod(period) {
        appSignal.value = {
            ...appSignal.value,
            insights: { ...appSignal.value.insights, period },
        };
    },

    updateInsight(collection, id, patch) {
        updateInsightCollection(collection, id, patch);
    },

    updateKpi(id, patch) {
        updateInsightCollection('kpis', id, patch);
    },

    updateGauge(id, patch) {
        updateInsightCollection('gauges', id, patch);
    },

    updateGraphic(id, patch) {
        updateInsightCollection('graphics', id, patch);
    },

    setView(view) {
        appSignal.value = {
            ...appSignal.value,
            dashboard: {
                ...appSignal.value.dashboard,
                view,
                page: 1,
            }
        };
    },

    setPage(page) {
        const dashboard = appSignal.value.dashboard ?? {};
        const perPage = Math.max(1, Number(dashboard.per_page) || 20);
        const total = Math.max(0, Number(dashboard.total) || 0);
        const totalPages = Math.max(1, Math.ceil(total / perPage));
        const nextPage = Math.min(Math.max(1, Number(page) || 1), totalPages);
        if (nextPage === dashboard.page) return;
        appSignal.value = {
            ...appSignal.value,
            dashboard: { ...dashboard, page: nextPage },
        };
    },

    previousPage() {
        dashboardActions.setPage((appSignal.value.dashboard?.page ?? 1) - 1);
    },

    nextPage() {
        dashboardActions.setPage((appSignal.value.dashboard?.page ?? 1) + 1);
    },

    setTotal(total) {
        const dashboard = appSignal.value.dashboard ?? {};
        const safeTotal = Math.max(0, Number(total) || 0);
        const perPage = Math.max(1, Number(dashboard.per_page) || 20);
        const totalPages = Math.max(1, Math.ceil(safeTotal / perPage));
        const page = Math.min(Math.max(1, Number(dashboard.page) || 1), totalPages);
        if (dashboard.total === safeTotal && dashboard.page === page) return;
        appSignal.value = {
            ...appSignal.value,
            dashboard: { ...dashboard, total: safeTotal, page },
        };
    },

}
