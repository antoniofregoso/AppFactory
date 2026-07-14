import { loadApexCharts } from '../utils/loadApexCharts.js';

const graphicInstances = new Map();

function escape(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function escapeAttribute(value) {
    return escape(value).replace(/"/g, '&quot;');
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

function graphicId(graphic, index = 0) {
    return String(graphic?.id ?? `graphic_${index}`);
}

function findGraphicElement(id) {
    return [...document.querySelectorAll('[data-insight-graphic-id]')]
        .find((element) => element.dataset.insightGraphicId === String(id));
}

function getNodeTitle(node, lang) {
    if (lang === 'en') return node.title_en ?? node.title ?? node.id;
    return node.title ?? node.title_en ?? node.id;
}

function formatValue(value, lang) {
    return new Intl.NumberFormat(locale(lang), {
        maximumFractionDigits: 2,
    }).format(Number(value) || 0);
}

function hexLighten(hex, amount) {
    const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
    if (!m) return hex;
    const ch = (i) => Math.round(parseInt(m[i], 16) + (255 - parseInt(m[i], 16)) * amount);
    return `#${ch(1).toString(16).padStart(2,'0')}${ch(2).toString(16).padStart(2,'0')}${ch(3).toString(16).padStart(2,'0')}`;
}

function getApexTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function getCssVar(name, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
}

function getCategories(graphic, lang) {
    const cats = graphic.categories;
    if (!cats) return [];
    return cats[lang] ?? cats.en ?? cats.es ?? [];
}

function getSeries(graphic, lang) {
    if (Array.isArray(graphic.series)) {
        return graphic.series.map((s) => ({
            name: getLocalized(s.name, lang),
            data: Array.isArray(s.data) ? s.data : [],
        }));
    }
    return [{
        name: getLocalized(graphic.title, lang),
        data: Array.isArray(graphic.data) ? graphic.data : [],
    }];
}

function buildBarOptions(graphic, lang) {
    const isHorizontal = graphic.mode === 'horizontal';
    const series = getSeries(graphic, lang);
    const stacked = series.length > 1;
    return {
        chart: {
            type: 'bar',
            height: 420,
            width: '100%',
            background: 'transparent',
            stacked,
            toolbar: { show: false },
            foreColor: getCssVar('--dash-text', '#374151'),
        },
        plotOptions: {
            bar: {
                horizontal: isHorizontal,
                borderRadius: stacked ? 0 : 4,
                columnWidth: '60%',
                barHeight: '60%',
            },
        },
        series,
        xaxis: {
            categories: getCategories(graphic, lang),
            axisBorder: { color: getCssVar('--dash-border', '#e5e7eb') },
            axisTicks: { color: getCssVar('--dash-border', '#e5e7eb') },
        },
        yaxis: isHorizontal ? { labels: { maxWidth: 160 } } : {},
        grid: { borderColor: getCssVar('--dash-border', '#e5e7eb') },
        dataLabels: { enabled: false },
        legend: { show: stacked },
        tooltip: { shared: stacked, intersect: false, theme: getApexTheme() },
    };
}

function buildLineOptions(graphic, lang) {
    const series = getSeries(graphic, lang);
    const multi = series.length > 1;
    return {
        chart: {
            type: 'line',
            height: 420,
            width: '100%',
            background: 'transparent',
            toolbar: { show: false },
            foreColor: getCssVar('--dash-text', '#374151'),
        },
        series,
        xaxis: {
            categories: getCategories(graphic, lang),
            axisBorder: { color: getCssVar('--dash-border', '#e5e7eb') },
            axisTicks: { color: getCssVar('--dash-border', '#e5e7eb') },
        },
        grid: { borderColor: getCssVar('--dash-border', '#e5e7eb') },
        stroke: { curve: 'smooth', width: 2 },
        markers: { size: 4 },
        dataLabels: { enabled: false },
        legend: { show: multi },
        tooltip: { shared: true, intersect: false, theme: getApexTheme() },
    };
}

async function renderHeatmap(el, graphic, lang) {
    const rawRows = Array.isArray(graphic.data) ? graphic.data : [];
    const dayNames = rawRows.map((row) => getLocalized(row.name, lang));
    const hourLabels = (rawRows[0]?.data ?? []).map((pt) => getLocalized(pt.x, lang));

    const series = hourLabels.map((hour, hi) => ({
        name: hour,
        data: rawRows.map((row, di) => ({ x: dayNames[di], y: row.data[hi]?.y ?? 0 })),
    }));

    const maxVal = Math.max(1, ...series.flatMap((s) => s.data.map((pt) => pt.y)));
    const midVal = Math.round(maxVal / 2);
    const accent = getCssVar('--dash-accent', '#10b981');
    const colorMid = hexLighten(accent, 0.5);

    el.innerHTML = `
        <div class="heatmap-wrapper">
            <div class="heatmap-chart-inner"></div>
            <div class="heatmap-scale" aria-hidden="true">
                <span class="heatmap-scale-value">${escape(String(maxVal))}</span>
                <div class="heatmap-scale-track">
                    <div class="heatmap-scale-bar"></div>
                    <div class="heatmap-scale-ticks">
                        <span class="heatmap-scale-tick"></span>
                        <span class="heatmap-scale-tick heatmap-scale-tick--mid">
                            <span class="heatmap-scale-tick-label">${escape(String(midVal))}</span>
                        </span>
                        <span class="heatmap-scale-tick"></span>
                    </div>
                </div>
                <span class="heatmap-scale-value heatmap-scale-value--min">0</span>
            </div>
        </div>`;

    el.querySelector('.heatmap-scale-bar').style.background =
        `linear-gradient(to bottom, ${accent}, ${colorMid}, #ffffff)`;

    const chartEl = el.querySelector('.heatmap-chart-inner');
    const height = el.clientHeight || 420;

    const ApexCharts = await loadApexCharts();
    const chart = new ApexCharts(chartEl, {
        chart: {
            type: 'heatmap',
            height,
            width: '100%',
            background: 'transparent',
            toolbar: { show: false },
            foreColor: getCssVar('--dash-text', '#374151'),
        },
        series,
        colors: [accent],
        dataLabels: { enabled: false },
        plotOptions: {
            heatmap: {
                shadeIntensity: 0.4,
                colorScale: { min: 0, max: maxVal },
            },
        },
        legend: { show: false },
        tooltip: { theme: getApexTheme() },
    });

    chart.render()?.catch?.((error) => console.error('[insights] Failed to render heatmap:', error));
    el._apexChart = chart;
    return chart;
}

function buildRadarOptions(graphic, lang) {
    const series = getSeries(graphic, lang);
    return {
        chart: {
            type: 'radar',
            height: 420,
            width: '100%',
            background: 'transparent',
            toolbar: { show: false },
            foreColor: getCssVar('--dash-text', '#374151'),
        },
        series,
        xaxis: { categories: getCategories(graphic, lang) },
        yaxis: { show: false },
        markers: { size: 4 },
        fill: { opacity: 0.2 },
        stroke: { width: 2 },
        legend: { show: series.length > 1, position: 'bottom' },
        tooltip: { theme: getApexTheme() },
    };
}

function buildTreemapOptions(graphic, lang) {
    const data = Array.isArray(graphic.data)
        ? graphic.data.map((item) => ({ x: getLocalized(item.x, lang), y: item.y }))
        : [];
    return {
        chart: {
            type: 'treemap',
            height: 420,
            width: '100%',
            background: 'transparent',
            toolbar: { show: false },
            foreColor: getCssVar('--dash-text', '#374151'),
        },
        series: [{ data }],
        dataLabels: { enabled: true, style: { fontSize: '13px' } },
        colors: [getCssVar('--dash-accent', '#10b981')],
        plotOptions: { treemap: { distributed: true, enableShades: true } },
        legend: { show: false },
        tooltip: { theme: getApexTheme() },
    };
}

function buildDonutOptions(graphic, lang) {
    const labels = graphic.labels;
    const localizedLabels = Array.isArray(labels)
        ? labels
        : (labels?.[lang] ?? labels?.en ?? labels?.es ?? []);
    return {
        chart: {
            type: 'donut',
            height: 420,
            width: '100%',
            background: 'transparent',
            toolbar: { show: false },
            foreColor: getCssVar('--dash-text', '#374151'),
        },
        series: Array.isArray(graphic.series) ? graphic.series : [],
        labels: localizedLabels,
        dataLabels: { enabled: true },
        legend: { show: true, position: 'bottom' },
        plotOptions: {
            pie: {
                donut: { size: '60%' },
                expandOnClick: false,
            },
        },
        tooltip: { theme: getApexTheme(), fillSeriesColor: false },
    };
}

async function renderApexChart(el, options) {
    el.innerHTML = '';
    const ApexCharts = await loadApexCharts();
    const chart = new ApexCharts(el, options);
    chart.render()?.catch?.((error) => {
        console.error('[insights] Failed to render chart:', error);
    });
    el._apexChart = chart;
    return chart;
}

export function renderInsightGraphics(graphics = [], lang = 'en', layout = {}) {
    if (!Array.isArray(graphics) || graphics.length === 0) return '';

    const cols = Math.max(1, parseInt(layout?.graphics) || 1);

    return `
    <section class="insight-section" aria-labelledby="insight-graphics-title">
        <h3 id="insight-graphics-title" class="sr-only">Graphics</h3>
        <div class="insight-graphic-grid" style="--graphic-cols:${cols}" data-graphic-cols="${cols}">
            ${graphics.map((graphic, index) => `
            <article class="insight-graphic-card" data-insight-graphic-card-id="${escapeAttribute(graphicId(graphic, index))}">
                <div class="insight-graphic-head">
                    <h4 class="insight-graphic-title">${escape(getLocalized(graphic.title, lang))}</h4>
                    <button
                        class="insight-graphic-expand"
                        type="button"
                        aria-label="${lang === 'es' ? 'Expandir a pantalla completa' : 'Expand to fullscreen'}"
                        data-label-expand="${lang === 'es' ? 'Expandir a pantalla completa' : 'Expand to fullscreen'}"
                        data-label-compress="${lang === 'es' ? 'Salir de pantalla completa' : 'Exit fullscreen'}"
                    >
                        <svg class="icon-expand" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <path d="M1 6V1h5M15 6V1h-5M1 10v5h5M15 10v5h-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <svg class="icon-compress" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <path d="M6 1v5H1M10 1v5h5M6 15v-5H1M10 15v-5h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
                <div
                    class="insight-graphic-chart"
                    data-insight-graphic="${index}"
                    data-insight-graphic-id="${escapeAttribute(graphicId(graphic, index))}"
                    data-insight-graphic-type="${escape(graphic.type ?? '')}"
                >${graphic.type === 'sankey' ? renderFallbackSankey(graphic, lang) : ''}</div>
            </article>`).join('')}
        </div>
    </section>`;
}

function getSankeyData(graphic, lang) {
    const data = graphic?.data ?? {};
    const nodes = (data.nodes ?? []).map((node) => ({
        ...node,
        title: getNodeTitle(node, lang),
    }));
    const edges = (data.edges ?? []).map((edge) => ({
        ...edge,
        type: edge.type ?? graphic.type ?? 'flow',
    }));

    return {
        nodes,
        edges,
        options: data.options ?? {},
    };
}

function getFallbackLayers(data) {
    const orderedLayers = data.options?.order;
    const nodeIds = new Set(data.nodes.map((node) => node.id));

    if (Array.isArray(orderedLayers) && orderedLayers.length > 0) {
        const layers = orderedLayers
            .map((layer) => layer.flat().filter((id) => nodeIds.has(id)))
            .filter((layer) => layer.length > 0);
        const orderedIds = new Set(layers.flat());
        const missingIds = data.nodes
            .map((node) => node.id)
            .filter((id) => !orderedIds.has(id));

        if (missingIds.length > 0) layers.push(missingIds);
        return layers;
    }

    const sourceIds = new Set(data.edges.map((edge) => edge.source));
    const targetIds = new Set(data.edges.map((edge) => edge.target));
    const sources = data.nodes.map((node) => node.id).filter((id) => !targetIds.has(id));
    const targets = data.nodes.map((node) => node.id).filter((id) => !sourceIds.has(id));
    const middle = data.nodes
        .map((node) => node.id)
        .filter((id) => !sources.includes(id) && !targets.includes(id));

    return [sources, middle, targets].filter((layer) => layer.length > 0);
}

function truncateText(text, maxChars) {
    if (!text || text.length <= maxChars) return text;
    return text.slice(0, Math.max(2, maxChars - 1)) + '…';
}

function renderFallbackSankey(graphic, lang) {
    const data = getSankeyData(graphic, lang);
    const width = 1180;
    const height = graphic.height ?? 460;
    const nodeWidth = 16;
    const nodeHeight = 34;
    const layers = getFallbackLayers(data);
    const maxValue = Math.max(...data.edges.map((edge) => Number(edge.value) || 0), 1);
    const positions = new Map();
    const nodeMap = new Map(data.nodes.map((node) => [node.id, node]));

    const layerXPositions = layers.map((_, i) =>
        layers.length === 1
            ? (width / 2) - (nodeWidth / 2)
            : 24 + ((width - 64) * i / (layers.length - 1))
    );

    const nodeLayerIndex = new Map();
    layers.forEach((layer, i) => layer.forEach((id) => nodeLayerIndex.set(id, i)));

    layers.forEach((layer, layerIndex) => {
        const x = layerXPositions[layerIndex];
        const gap = Math.max(18, (height - 60 - (layer.length * nodeHeight)) / Math.max(layer.length - 1, 1));

        layer.forEach((id, index) => {
            const totalHeight = (layer.length * nodeHeight) + ((layer.length - 1) * gap);
            const y = Math.max(24, ((height - totalHeight) / 2) + (index * (nodeHeight + gap)));
            positions.set(id, { x, y });
        });
    });

    const CHAR_WIDTH = 7;
    const LABEL_PADDING = 8;

    const layerMaxChars = layerXPositions.map((x, i) => {
        const isLeft = x < width / 2;
        let availableWidth;
        if (isLeft) {
            const nextX = i + 1 < layerXPositions.length ? layerXPositions[i + 1] : width - 4;
            availableWidth = nextX - (x + nodeWidth + LABEL_PADDING) - 4;
        } else {
            const prevX = i - 1 >= 0 ? layerXPositions[i - 1] + nodeWidth : 4;
            availableWidth = (x - LABEL_PADDING) - prevX - 4;
        }
        return Math.max(6, Math.floor(availableWidth / CHAR_WIDTH));
    });

    const edges = data.edges.map((edge, index) => {
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);
        const sourceNode = nodeMap.get(edge.source);
        const targetNode = nodeMap.get(edge.target);
        if (!source || !target) return '';

        const strokeWidth = Math.max(3, Math.min(28, ((Number(edge.value) || 0) / maxValue) * 28));
        const y1 = source.y + (nodeHeight / 2);
        const y2 = target.y + (nodeHeight / 2);
        const x1 = source.x + nodeWidth;
        const x2 = target.x;
        const curve = Math.max(80, (x2 - x1) * 0.45);

        return `
            <path
                class="insight-sankey-edge"
                tabindex="0"
                d="M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}"
                fill="none"
                stroke="var(--dash-accent)"
                stroke-width="${strokeWidth.toFixed(2)}"
                stroke-linecap="round"
                opacity="${0.16 + (index % 4) * 0.08}"
                data-source="${escapeAttribute(edge.source)}"
                data-target="${escapeAttribute(edge.target)}"
                data-source-title="${escapeAttribute(sourceNode?.title ?? edge.source)}"
                data-target-title="${escapeAttribute(targetNode?.title ?? edge.target)}"
                data-value="${escapeAttribute(formatValue(edge.value, lang))}"
            />`;
    }).join('');

    const nodes = data.nodes.map((node, index) => {
        const position = positions.get(node.id);
        if (!position) return '';
        const labelX = position.x < width / 2 ? position.x + nodeWidth + 8 : position.x - 8;
        const anchor = position.x < width / 2 ? 'start' : 'end';
        const fullTitle = nodeMap.get(node.id)?.title ?? node.id;
        const layerIdx = nodeLayerIndex.get(node.id) ?? 0;
        const displayTitle = truncateText(fullTitle, layerMaxChars[layerIdx]);

        return `
            <g
                class="insight-sankey-node"
                tabindex="0"
                data-node="${escapeAttribute(node.id)}"
                data-node-title="${escapeAttribute(fullTitle)}"
            >
                <rect
                    x="${position.x}"
                    y="${position.y}"
                    width="${nodeWidth}"
                    height="${nodeHeight}"
                    rx="4"
                    fill="${node.color ?? `hsl(${(index * 41) % 360} 65% 54%)`}"
                    stroke="var(--dash-border)"
                />
                <text
                    x="${labelX}"
                    y="${position.y + 21}"
                    text-anchor="${anchor}"
                    fill="var(--dash-text)"
                    font-size="12"
                    font-weight="650"
                >${escape(displayTitle)}</text>
            </g>`;
    }).join('');

    return `
        <svg class="insight-sankey-fallback" viewBox="0 0 ${width} ${height}" role="img">
            <g>${edges}</g>
            <g>${nodes}</g>
        </svg>`;
}

function renderSankey(el, graphic, lang) {
    el.innerHTML = renderFallbackSankey(graphic, lang);
    bindInteractiveSankey(el, lang);
    return null;
}

function getOrCreateTooltip() {
    let tooltip = document.querySelector('[data-insight-sankey-tooltip]');
    if (tooltip) return tooltip;

    tooltip = document.createElement('div');
    tooltip.className = 'insight-sankey-tooltip';
    tooltip.dataset.insightSankeyTooltip = '';
    tooltip.setAttribute('role', 'tooltip');
    document.body.appendChild(tooltip);
    return tooltip;
}

function moveTooltip(tooltip, event) {
    const offset = 14;
    const rect = event.currentTarget?.getBoundingClientRect?.();
    const clientX = Number.isFinite(event.clientX) ? event.clientX : (rect?.right ?? offset);
    const clientY = Number.isFinite(event.clientY) ? event.clientY : (rect?.top ?? offset);
    const x = Math.min(clientX + offset, window.innerWidth - tooltip.offsetWidth - offset);
    const y = Math.min(clientY + offset, window.innerHeight - tooltip.offsetHeight - offset);
    tooltip.style.left = `${Math.max(offset, x)}px`;
    tooltip.style.top = `${Math.max(offset, y)}px`;
}

function nodeTotals(svg, nodeId, lang) {
    let incoming = 0;
    let outgoing = 0;

    svg.querySelectorAll('.insight-sankey-edge').forEach((edge) => {
        const value = Number(String(edge.dataset.value ?? '').replace(/[^\d.-]/g, '')) || 0;
        if (edge.dataset.target === nodeId) incoming += value;
        if (edge.dataset.source === nodeId) outgoing += value;
    });

    return {
        incoming: formatValue(incoming, lang),
        outgoing: formatValue(outgoing, lang),
    };
}

function showTooltip(content, event) {
    const tooltip = getOrCreateTooltip();
    tooltip.innerHTML = content;
    tooltip.classList.add('insight-sankey-tooltip--visible');
    moveTooltip(tooltip, event);
}

function hideTooltip() {
    document
        .querySelector('[data-insight-sankey-tooltip]')
        ?.classList.remove('insight-sankey-tooltip--visible');
}

function setActiveNode(svg, nodeId) {
    svg.classList.add('insight-sankey-fallback--active');
    svg.querySelectorAll('.insight-sankey-node').forEach((node) => {
        node.classList.toggle('insight-sankey-node--active', node.dataset.node === nodeId);
    });
    svg.querySelectorAll('.insight-sankey-edge').forEach((edge) => {
        edge.classList.toggle(
            'insight-sankey-edge--active',
            edge.dataset.source === nodeId || edge.dataset.target === nodeId,
        );
    });
}

function setActiveEdge(svg, edge) {
    const sourceId = edge.dataset.source;
    const targetId = edge.dataset.target;
    svg.classList.add('insight-sankey-fallback--active');
    svg.querySelectorAll('.insight-sankey-edge').forEach((item) => {
        item.classList.toggle('insight-sankey-edge--active', item === edge);
    });
    svg.querySelectorAll('.insight-sankey-node').forEach((node) => {
        node.classList.toggle(
            'insight-sankey-node--active',
            node.dataset.node === sourceId || node.dataset.node === targetId,
        );
    });
}

function clearActive(svg) {
    svg.classList.remove('insight-sankey-fallback--active');
    svg.querySelectorAll('.insight-sankey-node--active, .insight-sankey-edge--active').forEach((el) => {
        el.classList.remove('insight-sankey-node--active', 'insight-sankey-edge--active');
    });
    hideTooltip();
}

function bindInteractiveSankey(el, lang) {
    const svg = el.querySelector('.insight-sankey-fallback');
    if (!svg || svg.dataset.interactive === 'true') return;
    svg.dataset.interactive = 'true';

    svg.querySelectorAll('.insight-sankey-edge').forEach((edge) => {
        const show = (event) => {
            setActiveEdge(svg, edge);
            showTooltip(`
                <strong>${escape(edge.dataset.sourceTitle ?? '')} &rarr; ${escape(edge.dataset.targetTitle ?? '')}</strong>
                <span>${escape(edge.dataset.value ?? '')}</span>
            `, event);
        };

        edge.addEventListener('mouseenter', show);
        edge.addEventListener('mousemove', (event) => moveTooltip(getOrCreateTooltip(), event));
        edge.addEventListener('mouseleave', () => clearActive(svg));
        edge.addEventListener('focus', show);
        edge.addEventListener('blur', () => clearActive(svg));
    });

    svg.querySelectorAll('.insight-sankey-node').forEach((node) => {
        const show = (event) => {
            const totals = nodeTotals(svg, node.dataset.node, lang);
            setActiveNode(svg, node.dataset.node);
            showTooltip(`
                <strong>${escape(node.dataset.nodeTitle ?? '')}</strong>
                <span>${lang === 'es' ? 'Entrada' : 'In'}: ${escape(totals.incoming)}</span>
                <span>${lang === 'es' ? 'Salida' : 'Out'}: ${escape(totals.outgoing)}</span>
            `, event);
        };

        node.addEventListener('mouseenter', show);
        node.addEventListener('mousemove', (event) => moveTooltip(getOrCreateTooltip(), event));
        node.addEventListener('mouseleave', () => clearActive(svg));
        node.addEventListener('focus', show);
        node.addEventListener('blur', () => clearActive(svg));
    });
}

function bindExpandButtons() {
    document.querySelectorAll('.insight-graphic-expand').forEach((btn) => {
        if (btn.dataset.expandBound) return;
        btn.dataset.expandBound = 'true';

        const card = btn.closest('.insight-graphic-card');
        if (!card || !document.fullscreenEnabled) {
            btn.hidden = true;
            return;
        }

        btn.addEventListener('click', () => {
            if (document.fullscreenElement === card) {
                document.exitFullscreen();
            } else {
                card.requestFullscreen();
            }
        });

        card.addEventListener('fullscreenchange', () => {
            const isFullscreen = document.fullscreenElement === card;
            btn.setAttribute('aria-label', isFullscreen
                ? (btn.dataset.labelCompress ?? 'Exit fullscreen')
                : (btn.dataset.labelExpand ?? 'Expand to fullscreen')
            );

            const tooltip = document.querySelector('[data-insight-sankey-tooltip]');
            if (tooltip) {
                if (isFullscreen) {
                    card.appendChild(tooltip);
                } else {
                    document.body.appendChild(tooltip);
                }
            }

            const chartEl = card.querySelector('[data-insight-graphic]');
            const apexChart = chartEl?._apexChart;
            if (apexChart) {
                requestAnimationFrame(() => {
                    const height = isFullscreen ? (chartEl.clientHeight || 420) : 420;
                    apexChart.updateOptions({ chart: { height } }, false, false);
                });
            }
        });
    });
}

export function initInsightGraphics(graphics = [], lang = 'en') {
    destroyInsightGraphics();

    bindExpandButtons();

    document.querySelectorAll('[data-insight-graphic]').forEach((el) => {
        const index = Number(el.dataset.insightGraphic);
        const graphic = graphics[index];
        if (!graphic) return;
        createGraphicInstance(el, graphic, lang, graphicId(graphic, index));
    });

    return destroyInsightGraphics;
}

async function destroyGraphicInstance(instanceOrPromise) {
    const instance = await instanceOrPromise;
    instance?.destroy?.();
    instance?.graph?.clear?.();
}

function destroyInsightGraphics() {
    const instances = [...graphicInstances.values()];
    graphicInstances.clear();
    instances.forEach(destroyGraphicInstance);
}

function createGraphicInstance(el, graphic, lang, id) {
    const instance = buildGraphicInstance(el, graphic, lang);
    graphicInstances.set(id, instance);
    return instance;
}

async function buildGraphicInstance(el, graphic, lang) {
    try {
        let instance = null;
        if (graphic.type === 'sankey') {
            instance = renderSankey(el, graphic, lang);
        } else if (graphic.type === 'bar') {
            instance = await renderApexChart(el, buildBarOptions(graphic, lang));
        } else if (graphic.type === 'line') {
            instance = await renderApexChart(el, buildLineOptions(graphic, lang));
        } else if (graphic.type === 'heatmap') {
            instance = await renderHeatmap(el, graphic, lang);
        } else if (graphic.type === 'radar') {
            instance = await renderApexChart(el, buildRadarOptions(graphic, lang));
        } else if (graphic.type === 'treemap') {
            instance = await renderApexChart(el, buildTreemapOptions(graphic, lang));
        } else if (graphic.type === 'donut') {
            instance = await renderApexChart(el, buildDonutOptions(graphic, lang));
        } else {
            el.innerHTML = `<div class="insight-empty">${escape(graphic.type ?? 'Unsupported chart')}</div>`;
        }
        return instance;
    } catch (error) {
        console.error('[insights] Failed to render graphic:', error);
        if (graphic.type === 'sankey') {
            el.innerHTML = renderFallbackSankey(graphic, lang);
        } else {
            el.innerHTML = `<div class="insight-empty">${escape(graphic.type ?? 'Chart')} error</div>`;
        }
        return null;
    }
}

/** Recreates only the chart identified by graphic.id. */
export function updateInsightGraphic(graphic, lang = 'en') {
    if (!graphic?.id) return false;
    const id = String(graphic.id);
    const el = findGraphicElement(id);
    if (!el) return false;

    const current = graphicInstances.get(id);
    graphicInstances.delete(id);
    if (current) destroyGraphicInstance(current);

    const card = el.closest('.insight-graphic-card');
    const title = card?.querySelector('.insight-graphic-title');
    if (title) title.textContent = getLocalized(graphic.title, lang);
    el.dataset.insightGraphicType = graphic.type ?? '';
    el.innerHTML = graphic.type === 'sankey' ? renderFallbackSankey(graphic, lang) : '';
    createGraphicInstance(el, graphic, lang, id);
    return true;
}
