function positiveInteger(value, fallback) {
    const number = Number(value);
    return Number.isInteger(number) && number > 0 ? number : fallback;
}

export function normalizePagination(pagination = {}, fallbackTotal = 0) {
    const perPage = positiveInteger(pagination.per_page ?? pagination.perPage, 20);
    const totalValue = Number(pagination.total);
    const total = Number.isInteger(totalValue) && totalValue >= 0
        ? totalValue
        : Math.max(0, Number(fallbackTotal) || 0);
    const totalPages = Math.max(1, Math.ceil(total / perPage));
    const page = Math.min(positiveInteger(pagination.page, 1), totalPages);

    return {
        page,
        perPage,
        total,
        totalPages,
        start: (page - 1) * perPage,
        end: Math.min(page * perPage, total),
    };
}

export function paginateData(data = {}, pagination = {}) {
    const records = data?.records ?? [];
    const normalized = normalizePagination(pagination, records.length);
    return {
        ...data,
        records: records.slice(normalized.start, normalized.end),
        pagination: normalized,
    };
}
