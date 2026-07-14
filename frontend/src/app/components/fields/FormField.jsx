import { FieldControl } from './FieldControl.jsx';
import { FieldHelp } from './FieldHelp.jsx';
import { One2manyKanbanField } from './One2manyKanbanField.jsx';
import { One2manyListField } from './One2manyListField.jsx';
import { fieldLabel, localizedConfig } from './fieldHelpers.js';

/**
 * Full field unit (label + required mark + help + control) built around a single `FieldControl`.
 * Only here — the form body/tabs — `form.view: "one2many_kanban"` overrides the type-based
 * control; List and Kanban cells render the same field through `FieldControl` directly and
 * must keep their own type-based rendering.
 */
export function FormField({ field, value, onChange, lang = 'en', readOnly = false, context = {}, class: className = '', hideLabel = false, error = '' }) {
    const help = localizedConfig(field, 'help', lang);
    const required = field?.form?.required === true;
    let control;
    if (field?.form?.view === 'one2many_kanban') {
        control = <One2manyKanbanField field={field} value={value} onChange={onChange} lang={lang} readOnly={readOnly} context={context} />;
    } else if (field?.form?.view === 'one2many_list') {
        control = <One2manyListField field={field} value={value} onChange={onChange} lang={lang} readOnly={readOnly} context={context} />;
    } else {
        control = <FieldControl field={field} value={value} onChange={onChange} lang={lang} readOnly={readOnly} context={context} />;
    }

    if (field.type === 'boolean' && !hideLabel) {
        return (
            <div class={`form-field ${className}`.trim()} data-form-field={field.name}>
                <div class="form-field-label-row">
                    <label class="form-boolean-label">
                        {control}
                        <span>{fieldLabel(field, lang)} {required && <span class="form-required-mark" aria-hidden="true">*</span>}</span>
                    </label>
                    <FieldHelp help={help} lang={lang} />
                </div>
            </div>
        );
    }

    return (
        <div class={`form-field ${className}`.trim()} data-form-field={field.name}>
            {!hideLabel && (
                <div class="form-field-label-row">
                    <label class="form-field-label">{fieldLabel(field, lang)} {required && <span class="form-required-mark" aria-hidden="true">*</span>}</label>
                    <FieldHelp help={help} lang={lang} />
                </div>
            )}
            <div class="form-field-control">{control}</div>
            {error && <span role="alert" data-field-error={field.name} class="mt-1 block text-xs text-[var(--dash-danger)]">{error}</span>}
        </div>
    );
}
