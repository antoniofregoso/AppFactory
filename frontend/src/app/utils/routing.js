function encodePathSegment(segment) {
    try {
        return encodeURIComponent(decodeURIComponent(String(segment)));
    } catch {
        return encodeURIComponent(String(segment));
    }
}

function getDashboardBaseSegments() {
    const segments = window.location.pathname.split('/').filter(Boolean);
    const [root, area] = segments;

    if (root !== 'dashboard') return ['dashboard'];
    const base = ['dashboard'];
    if (area) base.push(area);

    return base;
}

export function buildRecordUrl(model, uuid) {
    const base = getDashboardBaseSegments().map(encodePathSegment).join('/');
    return `/${base}/${encodePathSegment(model)}/${encodePathSegment(uuid)}`;
}

const BREADCRUMB_PREFIX = 'dashboard:breadcrumbs:';

function pathKey(url) {
    return new URL(url, window.location.origin).pathname;
}

export function getRecordBreadcrumbs(pathname = window.location.pathname) {
    try {
        return JSON.parse(sessionStorage.getItem(`${BREADCRUMB_PREFIX}${pathname}`) ?? '[]');
    } catch {
        return [];
    }
}

export function setRecordBreadcrumbs(pathname, items) {
    sessionStorage.setItem(`${BREADCRUMB_PREFIX}${pathname}`, JSON.stringify(items));
}

export function rememberRecordBreadcrumb(url, label) {
    const current = getRecordBreadcrumbs();
    const targetPath = pathKey(url);
    const next = [...current, { label: String(label || targetPath), url: targetPath }];
    sessionStorage.setItem(`${BREADCRUMB_PREFIX}${targetPath}`, JSON.stringify(next));
}
