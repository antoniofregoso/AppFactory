import { useEffect, useId, useRef, useState } from 'preact/hooks';

import { icon, faCircleQuestion } from '../icon.js';
import { announceHelpOpen, subscribeHelpBus } from './fieldHelpers.js';

/** Help affordance shared by every field type: a "?" trigger with a single-open-at-a-time popover. */
export function FieldHelp({ help, lang = 'en' }) {
    const id = useId();
    const [open, setOpen] = useState(false);
    const rootRef = useRef(null);
    const triggerRef = useRef(null);

    useEffect(() => subscribeHelpBus(id, () => setOpen(false)), [id]);

    useEffect(() => {
        if (!open) return undefined;
        const onPointerDown = (event) => {
            if (!rootRef.current?.contains(event.target)) setOpen(false);
        };
        const onKeyDown = (event) => {
            if (event.key !== 'Escape') return;
            setOpen(false);
            triggerRef.current?.focus();
        };
        document.addEventListener('pointerdown', onPointerDown);
        document.addEventListener('keydown', onKeyDown);
        return () => {
            document.removeEventListener('pointerdown', onPointerDown);
            document.removeEventListener('keydown', onKeyDown);
        };
    }, [open]);

    if (!help) return null;

    const openLabel = lang === 'es' ? 'Mostrar ayuda' : 'Show help';
    const toggle = () => {
        const next = !open;
        if (next) announceHelpOpen(id);
        setOpen(next);
    };

    return (
        <span class="form-help" data-form-help ref={rootRef}>
            <button type="button" ref={triggerRef} class="form-help-trigger"
                aria-label={`${openLabel}: ${help}`} aria-expanded={String(open)} onClick={toggle}
                dangerouslySetInnerHTML={{ __html: icon(faCircleQuestion, 'form-help-icon') }} />
            <span class="form-help-popover" role="tooltip" hidden={!open}>{help}</span>
        </span>
    );
}
