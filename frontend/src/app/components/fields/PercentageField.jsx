import { fieldLabel, isFieldReadOnly } from './fieldHelpers.js';

function clampPercentage(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? Math.max(0, Math.min(100, numeric)) : 0;
}

export function PercentageField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const percentage = clampPercentage(value);

    if (isFieldReadOnly(field, readOnly)) {
        return (
            <div class="flex items-center gap-2" aria-label={`${percentage}%`}>
                <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--dash-border)]">
                    <div class="h-full rounded-full bg-[var(--dash-accent)]" style={{ width: `${percentage}%` }} />
                </div>
                <span class="tabular-nums text-[var(--dash-text-muted)]">{percentage}%</span>
            </div>
        );
    }

    return (
        <div class="form-percentage-editor flex">
            <input type="range" name={field.name} min="0" max="100" step="1" class="form-percentage-slider" value={percentage}
                style={{ '--form-percentage': `${percentage}%` }} aria-label={fieldLabel(field, lang)}
                aria-valuetext={`${percentage}%`}
                onInput={(event) => onChange(field.name, Number(event.currentTarget.value))} />
            <output class="form-percentage-output">{percentage}%</output>
        </div>
    );
}
