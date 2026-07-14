export function fieldLabel(field, lang) {
    return field?.label?.[lang] ?? field?.label?.en ?? field?.name ?? '';
}

export function localizedConfig(field, key, lang) {
    const value = field?.form?.[key];
    if (value == null) return '';
    if (typeof value !== 'object') return String(value);
    return String(value[lang] ?? value.en ?? Object.values(value)[0] ?? '');
}

export function plainText(value) {
    return String(value ?? '').replace(/<[^>]*>/g, '').trim();
}

export function isFieldReadOnly(field, readOnly) {
    return readOnly || field?.form?.readonly === true;
}

export function hasValue(value) {
    return value !== '' && value !== null && value !== undefined;
}

export function toDateInputValue(value) {
    if (!value) return '';
    return String(value).slice(0, 10);
}

export function toDateTimeInputValue(value) {
    if (!value) return '';
    return String(value).replace(' ', 'T').slice(0, 16);
}

const helpBus = new EventTarget();

/** Tells every other open FieldHelp popover to close, so only one is open at a time. */
export function announceHelpOpen(id) {
    helpBus.dispatchEvent(new CustomEvent('open', { detail: id }));
}

export function subscribeHelpBus(id, onOtherOpen) {
    const handler = (event) => {
        if (event.detail !== id) onOtherOpen();
    };
    helpBus.addEventListener('open', handler);
    return () => helpBus.removeEventListener('open', handler);
}
