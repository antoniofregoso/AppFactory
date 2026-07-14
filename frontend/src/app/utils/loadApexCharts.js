let apexChartsPromise;

/** Lazily loads ApexCharts on first use, then caches the module for reuse. */
export function loadApexCharts() {
    if (!apexChartsPromise) {
        apexChartsPromise = import('apexcharts').then((module) => module.default ?? module);
    }
    return apexChartsPromise;
}
