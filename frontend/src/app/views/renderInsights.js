import { dashboardActions } from '../store/actions';
import { loadApexCharts } from '../utils/loadApexCharts.js';
import {
    initInsightGraphics,
    renderInsightGraphics,
    updateInsightGraphic,
} from '../components/insightGraphics.js';

const PERIOD_LABELS = {
    today: { en: 'Today', es: 'Hoy' },
    weekly: { en: 'Last 7 days', es: 'Últimos 7 días' },
    monthly: { en: 'Last 30 days', es: 'Últimos 30 días' },
    yearly: { en: 'Last 365 days', es: 'Últimos 365 días' },
    annual: { en: 'This year', es: 'Este año' },
};

const PERIOD_OPTIONS = ['today', 'weekly', 'monthly', 'yearly', 'annual'];

let _gauges = [];
let _graphics = [];
let _lang = 'en';
let _data = {};
let _gaugeCharts = new Map();
let _graphicsCleanup = null;

function escape(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function escapeAttribute(value) {
    return escape(value).replace(/"/g, '&quot;');
}

function insightId(item, index, prefix) {
    return String(item?.id ?? `${prefix}_${index}`);
}

function findByDataAttribute(attribute, id) {
    return [...document.querySelectorAll(`[${attribute}]`)]
        .find((element) => element.getAttribute(attribute) === String(id));
}

function locale(lang) {
    return lang === 'es' ? 'es-MX' : 'en-US';
}

function getLocalized(value, lang) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        return value[lang] ?? value.en ?? value.es ?? '';
    }
    return value ?? '';
}

function getPeriodLabel(period, lang) {
    const label = PERIOD_LABELS[period]?.[lang];
    return label ?? period ?? '';
}

function renderPeriodSelect(period, lang) {
    const selected = PERIOD_OPTIONS.includes(period) ? period : 'today';

    return `
    <label class="insight-period-control">
        <span class="sr-only">${lang === 'es' ? 'Periodo' : 'Period'}</span>
        <select class="insight-period-select" data-insight-period>
            ${PERIOD_OPTIONS.map((option) => `
            <option value="${option}" ${option === selected ? 'selected' : ''}>
                ${escape(getPeriodLabel(option, lang))}
            </option>`).join('')}
        </select>
    </label>`;
}

function formatKpiValue(kpi, lang) {
    const value = Number(kpi.value);
    if (!Number.isFinite(value)) return escape(kpi.value ?? '');
    const unit = getLocalized(kpi.unit, lang);

    if (unit === 'MXN') {
        return escape(new Intl.NumberFormat(locale(lang), {
            style: 'currency',
            currency: 'MXN',
            maximumFractionDigits: 2,
        }).format(value));
    }

    if (unit === '%') {
        return `${escape(new Intl.NumberFormat(locale(lang), {
            maximumFractionDigits: 2,
        }).format(value))}%`;
    }

    return `${escape(new Intl.NumberFormat(locale(lang), {
        maximumFractionDigits: 2,
    }).format(value))}${unit ? ` ${escape(unit)}` : ''}`;
}

function formatNumber(value, lang) {
    return new Intl.NumberFormat(locale(lang), {
        maximumFractionDigits: 2,
    }).format(value);
}

function formatGaugeValue(gauge, lang) {
    const value = Number(gauge.value);
    if (!Number.isFinite(value)) return String(gauge.value ?? '');

    if (gauge.unit === '%') {
        return `${formatNumber(value, lang)}%`;
    }

    return `${formatNumber(value, lang)}${gauge.unit ? ` ${gauge.unit}` : ''}`;
}

function renderTrend(trend, lang) {
    if (!trend) return '';

    const normalized = String(trend).toLowerCase();
    const isDown = normalized === 'down';
    const label = lang === 'es'
        ? (isDown ? 'Baja' : 'Sube')
        : (isDown ? 'Down' : 'Up');

    return `
    <span class="insight-kpi-trend insight-kpi-trend--${isDown ? 'down' : 'up'}">
        <span aria-hidden="true">${isDown ? '↓' : '↑'}</span>
        ${escape(label)}
    </span>`;
}

function renderKpis(kpis = [], period, lang) {
    if (!Array.isArray(kpis) || kpis.length === 0) {
        return `
        <div class="insight-empty">
            ${lang === 'es' ? 'Sin KPIs' : 'No KPIs'}
        </div>`;
    }

    return `
    <section class="insight-section" aria-labelledby="insight-kpis-title">
        <h3 id="insight-kpis-title" class="sr-only">KPIs</h3>
        <div class="insight-kpi-grid">
            ${kpis.map((kpi, index) => renderKpiCard(kpi, lang, insightId(kpi, index, 'kpi'))).join('')}
        </div>
    </section>`;
}

function renderKpiCard(kpi, lang, id) {
    return `
            <article class="insight-kpi-card" data-insight-kpi-id="${escapeAttribute(id)}">
                <div class="insight-kpi-head">
                    <h4 class="insight-kpi-name">${escape(getLocalized(kpi.name, lang))}</h4>
                    ${renderTrend(kpi.trend, lang)}
                </div>
                <p class="insight-kpi-value">${formatKpiValue(kpi, lang)}</p>
            </article>`;
}

function renderGauges(gauges = [], lang) {
    if (!Array.isArray(gauges) || gauges.length === 0) return '';

    return `
    <section class="insight-section" aria-labelledby="insight-gauges-title">
        <h3 id="insight-gauges-title" class="sr-only">Gauges</h3>
        <div class="insight-gauge-grid">
            ${gauges.map((gauge, index) => {
                const id = insightId(gauge, index, 'gauge');
                return `
            <article class="insight-gauge-card" data-insight-gauge-id="${escapeAttribute(id)}">
                <div class="insight-gauge-head">
                    <h4 class="insight-gauge-name">${escape(getLocalized(gauge.name, lang))}</h4>
                    <span class="insight-gauge-value">${escape(formatGaugeValue(gauge, lang))}</span>
                </div>
                <div class="insight-gauge-visual" data-insight-gauge-visual="${escapeAttribute(id)}">
                    <div class="insight-gauge-needle" aria-hidden="true"></div>
                    <div class="insight-gauge-chart" data-insight-gauge="${escapeAttribute(id)}"></div>
                </div>
            </article>`;
            }).join('')}
        </div>
    </section>`;
}

export function renderInsights(data = {}, lang = 'en') {
    _data = data;
    const period = data?.period ?? '';
    _gauges = Array.isArray(data?.gauges) ? data.gauges : [];
    _graphics = Array.isArray(data?.graphics) ? data.graphics : [];
    _lang = lang;

    return `
    <main id="dashboard-content" class="dash-content" role="main" aria-label="Insights">
        <div class="insight-layout">
            <header class="insight-header">
                ${renderPeriodSelect(period, lang)}
            </header>
            ${renderKpis(data?.kpis, period, lang)}
            ${renderGauges(_gauges, lang)}
            ${renderInsightGraphics(_graphics, lang, data?.layout)}
        </div>
    </main>
    `;
}

function getCssVar(name, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
}

function gaugePercent(gauge) {
    const value = Number(gauge.value) || 0;
    const max = Number(gauge.max) || 100;
    return Math.max(0, Math.min(100, (value / max) * 100));
}

function thresholdPercent(gauge, key, fallback) {
    const max = Number(gauge.max) || 100;
    const value = Number(gauge.thresholds?.[key] ?? fallback);
    return Math.max(0, Math.min(100, (value / max) * 100));
}

function gaugeSegments(gauge) {
    const yellowStart = thresholdPercent(gauge, 'yellow', 60);
    const greenStart = thresholdPercent(gauge, 'green', 80);
    const red = Math.max(0, yellowStart);
    const yellow = Math.max(0, greenStart - yellowStart);
    const green = Math.max(0, 100 - greenStart);

    return [red, yellow, green];
}

function applyGaugeVisual(el, gauge) {
    const percent = gaugePercent(gauge);
    el.style.setProperty('--gauge-needle-rotation', `${-120 + (percent * 2.4)}deg`);
}

function buildGaugeOptions(gauge) {
    return {
        chart: {
            type: 'donut',
            height: 220,
            sparkline: { enabled: true },
            toolbar: { show: false },
            animations: { enabled: true },
        },
        series: gaugeSegments(gauge),
        colors: [
            getCssVar('--dash-danger', '#ef4444'),
            getCssVar('--dash-warning', '#f59e0b'),
            getCssVar('--dash-success', '#10b981'),
        ],
        plotOptions: {
            pie: {
                startAngle: -120,
                endAngle: 120,
                expandOnClick: false,
                donut: {
                    size: '76%',
                    background: 'transparent',
                    labels: { show: false },
                },
            },
        },
        dataLabels: { enabled: false },
        legend: { show: false },
        stroke: {
            width: 0,
        },
        tooltip: { enabled: false },
        states: {
            hover: { filter: { type: 'none' } },
            active: { filter: { type: 'none' } },
        },
        labels: ['Red', 'Yellow', 'Green'],
    };
}

async function createGaugeChart(el, gauge) {
    try {
        const ApexCharts = await loadApexCharts();
        const chart = new ApexCharts(el, buildGaugeOptions(gauge));
        chart.render()?.catch?.((error) => {
            console.error('[insights] Failed to render gauge:', error);
        });
        return chart;
    } catch (error) {
        console.error('[insights] Failed to render gauge:', error);
        return null;
    }
}

function destroyGaugeCharts() {
    const charts = [..._gaugeCharts.values()];
    _gaugeCharts = new Map();
    charts.forEach((chartOrPromise) => {
        Promise.resolve(chartOrPromise).then((chart) => chart?.destroy?.());
    });
}

export function initInsights(lang = 'en') {
    _lang = lang;
    destroyGaugeCharts();
    _graphicsCleanup?.();
    _graphicsCleanup = null;
    _graphicsCleanup = initInsightGraphics(_graphics, lang);

    const periodSelect = document.querySelector('[data-insight-period]');
    if (periodSelect) {
        periodSelect.addEventListener('change', (e) => {
            dashboardActions.setInsightPeriod(e.target.value);
        });
    }

    document.querySelectorAll('[data-insight-gauge]').forEach((el) => {
        const id = el.dataset.insightGauge;
        const gauge = _gauges.find((item, index) => insightId(item, index, 'gauge') === id);
        if (!gauge) return;

        const visual = el.closest('[data-insight-gauge-visual]');
        if (visual) applyGaugeVisual(visual, gauge);

        _gaugeCharts.set(id, createGaugeChart(el, gauge));
    });

    return () => {
        destroyGaugeCharts();
        _graphicsCleanup?.();
        _graphicsCleanup = null;
    };
}

function sameInsightShape(previous = [], next = [], prefix) {
    return previous.length === next.length && previous.every((item, index) =>
        insightId(item, index, prefix) === insightId(next[index], index, prefix)
    );
}

export function updateInsightKpi(kpi, lang = _lang) {
    const card = findByDataAttribute('data-insight-kpi-id', kpi.id);
    if (!card) return false;
    card.outerHTML = renderKpiCard(kpi, lang, kpi.id);
    return true;
}

export async function updateInsightGauge(gauge, lang = _lang) {
    const id = String(gauge.id);
    const card = findByDataAttribute('data-insight-gauge-id', id);
    const chart = await _gaugeCharts.get(id);
    if (!card || !chart) return false;

    card.querySelector('.insight-gauge-name').textContent = getLocalized(gauge.name, lang);
    card.querySelector('.insight-gauge-value').textContent = formatGaugeValue(gauge, lang);
    const visual = card.querySelector('[data-insight-gauge-visual]');
    if (visual) applyGaugeVisual(visual, gauge);
    chart.updateOptions(buildGaugeOptions(gauge), true, true);
    return true;
}

/**
 * Updates existing insight elements by id. Returns false when the dashboard
 * structure changed and the caller must render the complete insights view.
 */
export function patchInsights(previous = {}, next = {}, lang = _lang) {
    const previousKpis = previous.kpis ?? [];
    const nextKpis = next.kpis ?? [];
    const previousGauges = previous.gauges ?? [];
    const nextGauges = next.gauges ?? [];
    const previousGraphics = previous.graphics ?? [];
    const nextGraphics = next.graphics ?? [];

    const structureIsStable =
        sameInsightShape(previousKpis, nextKpis, 'kpi') &&
        sameInsightShape(previousGauges, nextGauges, 'gauge') &&
        sameInsightShape(previousGraphics, nextGraphics, 'graphic') &&
        previous.layout?.graphics === next.layout?.graphics;
    if (!structureIsStable) return false;

    const periodSelect = document.querySelector('[data-insight-period]');
    if (periodSelect && previous.period !== next.period) periodSelect.value = next.period;

    nextKpis.forEach((item, index) => {
        if (item !== previousKpis[index]) updateInsightKpi(item, lang);
    });
    nextGauges.forEach((item, index) => {
        if (item !== previousGauges[index]) updateInsightGauge(item, lang);
    });
    nextGraphics.forEach((item, index) => {
        if (item !== previousGraphics[index]) updateInsightGraphic(item, lang);
    });

    _data = next;
    _gauges = nextGauges;
    _graphics = nextGraphics;
    _lang = lang;
    return true;
}
