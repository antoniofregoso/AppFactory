import { render } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';

import {
    icon,
    faCircleInfo,
    faTriangleExclamation,
    faCircleExclamation,
    faXmark,
} from './icon.js';
import { newAlertsSignal } from '../store/notificationsStore.js';
import { currentLang } from '../store/appStore.js';
import { localizedValue } from '../utils/ux.js';
import { t } from '../../i18n/translations.js';

const PRIORITY_META = {
    info: { icon: faCircleInfo, class: 'alert-toast--info' },
    warning: { icon: faTriangleExclamation, class: 'alert-toast--warning' },
    danger: { icon: faCircleExclamation, class: 'alert-toast--danger' },
};

function priorityMeta(priority) {
    return PRIORITY_META[String(priority ?? '').toLowerCase()] ?? PRIORITY_META.info;
}

let toastIdCounter = 0;

/**
 * Persistent, globally-mounted stack of live alert toasts. New reminders
 * enter at the bottom-right and push earlier ones upward; nothing here
 * auto-dismisses — the user closes each toast explicitly. Missed reminders
 * (fired while offline) never reach this component — see notificationsStore.
 */
export function AlertStack() {
    const [toasts, setToasts] = useState([]);
    const mergedUuids = useRef(new Set());
    const lang = currentLang.value;

    useEffect(() => {
        const arrivals = newAlertsSignal.value.filter((notification) => !mergedUuids.current.has(notification.uuid));
        if (!arrivals.length) return;
        arrivals.forEach((notification) => mergedUuids.current.add(notification.uuid));
        setToasts((current) => [
            ...current,
            ...arrivals.map((notification) => ({ id: `${notification.uuid}-${toastIdCounter++}`, notification, closing: false })),
        ]);
    }, [newAlertsSignal.value]);

    const closeToast = (id) => {
        setToasts((current) => current.map((toast) => (toast.id === id ? { ...toast, closing: true } : toast)));
    };

    const removeToast = (id) => {
        setToasts((current) => current.filter((toast) => toast.id !== id));
    };

    if (!toasts.length) return null;

    return (
        <div class="alert-stack" role="region" aria-live="polite" aria-label={t('notifications.panel_title', lang)}>
            {toasts.map((toast) => {
                const meta = priorityMeta(toast.notification.priority);
                return (
                    <div
                        key={toast.id}
                        class={`alert-toast ${meta.class} ${toast.closing ? 'alert-toast--closing' : ''}`}
                        role="alert"
                        onAnimationEnd={() => { if (toast.closing) removeToast(toast.id); }}
                    >
                        <span class="alert-toast-icon" aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(meta.icon) }} />
                        <div class="alert-toast-body">
                            <strong class="alert-toast-title">{localizedValue(toast.notification.title, lang)}</strong>
                            <p class="alert-toast-message">{localizedValue(toast.notification.message, lang)}</p>
                        </div>
                        <button
                            type="button"
                            class="alert-toast-close"
                            aria-label={t('notifications.close', lang)}
                            onClick={() => closeToast(toast.id)}
                            dangerouslySetInnerHTML={{ __html: icon(faXmark) }}
                        />
                    </div>
                );
            })}
        </div>
    );
}

let mounted = false;

/** Mounts the alert stack once, outside #app, so it survives route re-renders. */
export function ensureAlertStackMounted() {
    if (mounted) return;
    mounted = true;
    const container = document.createElement('div');
    container.id = 'app-alert-stack-root';
    document.body.appendChild(container);
    render(<AlertStack />, container);
}
