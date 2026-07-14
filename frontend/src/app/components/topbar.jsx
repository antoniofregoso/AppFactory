import { render } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import {
    icon,
    faSun,
    faMoon,
    faDesktop,
    faCircleUser,
    faBell,
    faEnvelope,
    faListCheck,
    faMagnifyingGlass,
    faChevronLeft,
    faChevronRight,
    faTableColumns,
    faList,
    faRectangleList,
    faCalendarDays,
    faCircleInfo,
    faTriangleExclamation,
    faCircleExclamation,
    faBellSlash,
} from './icon.js';
import { uploadAttachment } from '../api/attachments.js';
import { contextActions, dashboardActions } from '../store/actions/index.js';
import { stopActivityHeartbeat } from '../api/activity.js';
import { logout } from '../api/auth.js';
import { refreshPendingCounts, stopPendingCountsPolling } from '../api/pendingCounts.js';
import { markNotificationRead } from '../api/notifications.js';
import { fetchSystemModelByName, fetchSystemModelView, searchSystemModels, updateSystemModelRecord } from '../api/systemModel.js';
import { clearAuthSession, setCurrentUser } from '../store/authStore.js';
import { markNotificationReadLocally, notificationsSignal, refreshNotificationsNow, stopNotificationsPolling } from '../store/notificationsStore.js';
import { disableWebPush, enableWebPush, getWebPushStatus } from '../api/webPush.js';
import { t } from '../../i18n/translations.js';
import { normalizePagination } from '../utils';
import { localizedValue } from '../utils/ux.js';
import { AuthenticatedImage } from './AuthenticatedImage.jsx';

const PRIORITY_META = {
    info: { icon: faCircleInfo, class: 'topbar-notification-icon--info' },
    warning: { icon: faTriangleExclamation, class: 'topbar-notification-icon--warning' },
    danger: { icon: faCircleExclamation, class: 'topbar-notification-icon--danger' },
};

function priorityMeta(priority) {
    return PRIORITY_META[String(priority ?? '').toLowerCase()] ?? PRIORITY_META.info;
}

function formatRelativeTime(value, lang) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    const diffMs = Date.now() - date.getTime();
    const minutes = Math.floor(diffMs / 60_000);
    if (minutes < 1) return t('notifications.just_now', lang);
    if (minutes < 60) return `${minutes} ${t('notifications.minutes_ago', lang)}`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} ${t('notifications.hours_ago', lang)}`;
    const days = Math.floor(hours / 24);
    return `${days} ${t('notifications.days_ago', lang)}`;
}

const THEMES = [
    { key: 'light', icon: faSun, labelEn: 'Light', labelEs: 'Claro' },
    { key: 'dark', icon: faMoon, labelEn: 'Dark', labelEs: 'Oscuro' },
    { key: 'system', icon: faDesktop, labelEn: 'System', labelEs: 'Sistema' },
];

const VIEW_BUTTONS = [
    { key: 'kanban', icon: faTableColumns },
    { key: 'list', icon: faList },
    { key: 'form', icon: faRectangleList },
    { key: 'calendar', icon: faCalendarDays },
];

const DEFAULT_LANGUAGE_OPTIONS = [
    { key: 'en', label: 'English', flag: 'EN' },
    { key: 'es', label: 'Español', flag: 'ES' },
];

let userModelUuidPromise = null;

function normalizeBadgeCount(value) {
    const count = Math.max(0, Number(value) || 0);
    return count > 99 ? '99+' : String(count);
}

function activeLanguageOptions(records = []) {
    const options = new Map();
    records.forEach((record) => {
        if (record?.active !== true) return;
        const key = String(record.url_code ?? record.iso_code ?? record.code ?? '').trim();
        if (!key || options.has(key)) return;
        options.set(key, {
            key,
            label: String(record.name ?? key),
            flag: String(record.flag || key.slice(0, 2).toUpperCase()),
        });
    });
    return [...options.values()];
}

function selectAvatarFile() {
    return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.className = 'hidden';
        input.addEventListener('change', () => {
            const file = input.files?.[0] ?? null;
            input.remove();
            resolve(file);
        }, { once: true });
        document.body.appendChild(input);
        input.click();
    });
}

async function getUserModelUuid() {
    if (!userModelUuidPromise) {
        userModelUuidPromise = fetchSystemModelByName('user.user').then((model) => model.uuid);
    }
    return userModelUuidPromise;
}

function UserAvatar({ user, class: className = '' }) {
    if (user?.avatarUrl) {
        return <AuthenticatedImage src={user.avatarUrl} alt={user?.name ?? ''} class={className} />;
    }
    return <span class={`topbar-user-avatar-fallback ${className}`} aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(faCircleUser, 'topbar-user-icon') }} />;
}

/**
 * Top navigation bar. The user menu's open/close state and its outside-click
 * / Escape listeners are wired via hooks — Preact attaches and tears them
 * down automatically on every re-render and on unmount, no manual init call
 * needed. View-switch clicks (`onViewChange`) and logout navigation
 * (`router`) stay owned by the dashboard page, since both carry routing
 * side effects beyond this component's concern.
 */
export function Topbar({ lang, theme, pageTitle, breadcrumb = [], showTools = true, pagination = {}, currentView, router, onViewChange, user = null, pendingCounts = {}, disabledViews = [] }) {
    const { page, totalPages } = normalizePagination(pagination);
    const pageStatus = lang === 'es' ? `Página ${page} de ${totalPages}` : `Page ${page} of ${totalPages}`;
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [avatarUploading, setAvatarUploading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searchOpen, setSearchOpen] = useState(false);
    const [searchLoading, setSearchLoading] = useState(false);
    const [searchError, setSearchError] = useState('');
    const [searchClarification, setSearchClarification] = useState(null);
    const [searchHelpOpen, setSearchHelpOpen] = useState(false);
    const [notificationsOpen, setNotificationsOpen] = useState(false);
    const [webPushStatus, setWebPushStatus] = useState('unsupported');
    const [webPushBusy, setWebPushBusy] = useState(false);
    const [languageOptions, setLanguageOptions] = useState(DEFAULT_LANGUAGE_OPTIONS);
    const userMenuWrapRef = useRef(null);
    const searchRef = useRef(null);
    const searchHelpWrapRef = useRef(null);
    const notificationsWrapRef = useRef(null);
    const searchRequestRef = useRef(0);
    const notifications = notificationsSignal.value;

    useEffect(() => {
        return () => { searchRequestRef.current += 1; };
    }, []);

    useEffect(() => {
        let cancelled = false;
        fetchSystemModelView({ model: 'system.lang', use: 'view', name: 'default' })
            .then((view) => {
                if (cancelled) return;
                const activeOptions = activeLanguageOptions(view?.records);
                setLanguageOptions(activeOptions.length ? activeOptions : DEFAULT_LANGUAGE_OPTIONS);
            })
            .catch(() => {
                if (!cancelled) setLanguageOptions(DEFAULT_LANGUAGE_OPTIONS);
            });
        return () => { cancelled = true; };
    }, []);

    useEffect(() => {
        let cancelled = false;
        getWebPushStatus().then((status) => { if (!cancelled) setWebPushStatus(status); });
        return () => { cancelled = true; };
    }, [notificationsOpen]);

    const toggleWebPush = async () => {
        if (webPushBusy) return;
        setWebPushBusy(true);
        try {
            if (webPushStatus === 'subscribed') {
                await disableWebPush();
                setWebPushStatus('not-subscribed');
            } else {
                await enableWebPush();
                setWebPushStatus('subscribed');
            }
        } catch (error) {
            console.error('Unable to toggle browser push notifications.', error);
            setWebPushStatus(await getWebPushStatus());
        } finally {
            setWebPushBusy(false);
        }
    };
    const messageCount = Math.max(0, Number(pendingCounts.messages) || 0);
    const notificationCount = Math.max(0, Number(pendingCounts.notifications) || 0);
    const messageLabel = messageCount
        ? `${t('topbar.messages', lang)} (${messageCount})`
        : t('topbar.messages', lang);
    const notificationLabel = notificationCount
        ? `${t('topbar.notifications', lang)} (${notificationCount})`
        : t('topbar.notifications', lang);

    useEffect(() => {
        if (!userMenuOpen) return undefined;

        const closeOnOutsideClick = (event) => {
            if (!userMenuWrapRef.current?.contains(event.target)) {
                setUserMenuOpen(false);
            }
        };
        const closeOnEscape = (event) => {
            if (event.key === 'Escape') setUserMenuOpen(false);
        };

        document.addEventListener('click', closeOnOutsideClick);
        document.addEventListener('keydown', closeOnEscape);
        return () => {
            document.removeEventListener('click', closeOnOutsideClick);
            document.removeEventListener('keydown', closeOnEscape);
        };
    }, [userMenuOpen]);

    useEffect(() => {
        if (!searchOpen) return undefined;
        const close = (event) => {
            if (event.key === 'Escape' || !searchRef.current?.contains(event.target)) setSearchOpen(false);
        };
        document.addEventListener('click', close);
        document.addEventListener('keydown', close);
        return () => {
            document.removeEventListener('click', close);
            document.removeEventListener('keydown', close);
        };
    }, [searchOpen]);

    useEffect(() => {
        if (!searchHelpOpen) return undefined;
        const closeOnOutsideClick = (event) => {
            if (!searchHelpWrapRef.current?.contains(event.target)) setSearchHelpOpen(false);
        };
        const closeOnEscape = (event) => {
            if (event.key === 'Escape') setSearchHelpOpen(false);
        };
        document.addEventListener('click', closeOnOutsideClick);
        document.addEventListener('keydown', closeOnEscape);
        return () => {
            document.removeEventListener('click', closeOnOutsideClick);
            document.removeEventListener('keydown', closeOnEscape);
        };
    }, [searchHelpOpen]);

    useEffect(() => {
        if (!notificationsOpen) return undefined;
        const closeOnOutsideClick = (event) => {
            if (!notificationsWrapRef.current?.contains(event.target)) {
                setNotificationsOpen(false);
            }
        };
        const closeOnEscape = (event) => {
            if (event.key === 'Escape') setNotificationsOpen(false);
        };
        document.addEventListener('click', closeOnOutsideClick);
        document.addEventListener('keydown', closeOnEscape);
        return () => {
            document.removeEventListener('click', closeOnOutsideClick);
            document.removeEventListener('keydown', closeOnEscape);
        };
    }, [notificationsOpen]);

    const toggleNotifications = (event) => {
        event.stopPropagation();
        setNotificationsOpen((open) => {
            const next = !open;
            if (next) void refreshNotificationsNow();
            return next;
        });
    };

    const handleNotificationClick = (notification) => {
        if (notification.read) return;
        markNotificationReadLocally(notification.uuid);
        markNotificationRead(notification.uuid)
            .then(() => refreshPendingCounts())
            .catch((error) => console.error('Unable to mark notification as read.', error));
    };

    const submitSearch = async (event) => {
        event.preventDefault();
        const query = searchQuery.trim();
        if (!query || searchLoading) return;
        setSearchLoading(true);
        setSearchError('');
        setSearchOpen(true);
        const requestId = ++searchRequestRef.current;
        const originalQuery = searchClarification?.originalQuery ?? null;
        const completeQuery = originalQuery ? `${originalQuery}\n${query}` : query;
        try {
            const response = await searchSystemModels({
                query: completeQuery,
                lang,
                limit: 20,
                mode: 'AUTO',
                originalQuery,
                clarificationAnswer: originalQuery ? query : null,
            });
            if (requestId !== searchRequestRef.current) return;
            setSearchResults(response.results ?? []);
            if (response.status === 'FAILED') {
                setSearchClarification(null);
                setSearchError(response.errors?.[0]?.message ?? (lang === 'es' ? 'No se pudo realizar la búsqueda.' : 'Unable to search.'));
            } else if (response.needsClarification) {
                setSearchClarification({
                    originalQuery: originalQuery ?? query,
                    question: response.clarificationQuestion ?? '',
                });
                setSearchQuery('');
                setSearchError(response.clarificationQuestion ?? '');
            } else if (response.status === 'PARTIAL' && response.errors?.length) {
                setSearchClarification(null);
                setSearchError(response.errors[0].message);
            } else {
                setSearchClarification(null);
            }
        } catch (error) {
            setSearchResults([]);
            setSearchError(lang === 'es' ? 'No se pudo realizar la búsqueda.' : 'Unable to search.');
            console.error('Unable to search system models.', error);
        } finally {
            if (requestId === searchRequestRef.current) setSearchLoading(false);
        }
    };

    const handleLogout = () => {
        stopActivityHeartbeat();
        stopPendingCountsPolling();
        stopNotificationsPolling();
        void logout();
        clearAuthSession();
        setUserMenuOpen(false);
        router?.goTo('login');
    };

    const handleAvatarUpload = async () => {
        if (!user?.uuid || avatarUploading) return;
        const file = await selectAvatarFile();
        if (!file) return;
        setAvatarUploading(true);
        try {
            const modelUuid = await getUserModelUuid();
            const attachment = await uploadAttachment({ modelUuid, recordUuid: user.uuid, file });
            await updateSystemModelRecord({
                model: 'user.user',
                recordUuid: user.uuid,
                values: { avatar_url: attachment.content_url },
            });
            setCurrentUser({ avatarUrl: attachment.content_url });
        } catch (error) {
            const message = error?.message ? `\n${error.message}` : '';
            window.alert(`${lang === 'es' ? 'No se pudo cambiar el avatar.' : 'Unable to change avatar.'}${message}`);
            console.error('Unable to update user avatar.', error);
        } finally {
            setAvatarUploading(false);
        }
    };

    const handleAvatarRemove = async () => {
        if (!user?.uuid || !user?.avatarUrl || avatarUploading) return;
        setAvatarUploading(true);
        try {
            await updateSystemModelRecord({
                model: 'user.user',
                recordUuid: user.uuid,
                values: { avatar_url: null },
            });
            setCurrentUser({ avatarUrl: null });
        } catch (error) {
            const message = error?.message ? `\n${error.message}` : '';
            window.alert(`${lang === 'es' ? 'No se pudo quitar el avatar.' : 'Unable to remove avatar.'}${message}`);
            console.error('Unable to remove user avatar.', error);
        } finally {
            setAvatarUploading(false);
        }
    };

    return (
        <div id="dashboard-topbar-shell" class="topbar-shell">
            <header id="dashboard-topbar" class="topbar" role="banner">
                <div class="topbar-title">
                    {breadcrumb.length ? (
                        <nav class="flex min-w-0 items-center gap-1.5 overflow-x-auto whitespace-nowrap text-[var(--dash-text)]" aria-label="Breadcrumb">
                            {breadcrumb.map((item, index) => {
                                const current = index === breadcrumb.length - 1;
                                const linked = !current && item.url && item.url !== '#';
                                return <span class="contents" key={`${item.url}:${index}`}>
                                    {index > 0 && <span class="shrink-0 text-xs text-[var(--dash-text-muted)]" aria-hidden="true">/</span>}
                                    {linked
                                        ? <a class={`${index === 0 ? 'text-[1.0625rem] font-semibold' : 'text-sm font-medium'} max-w-36 shrink-0 truncate text-[var(--dash-text-muted)] no-underline transition-colors hover:text-[var(--dash-accent)]`} href={item.url}>{item.label}</a>
                                        : <span class={`${index === 0 ? 'text-[1.0625rem] font-semibold' : 'text-sm font-medium'} max-w-36 shrink-0 truncate ${current ? 'text-[var(--dash-text)]' : 'text-[var(--dash-text-muted)]'}`} aria-current={current ? 'page' : undefined}>{item.label}</span>}
                                </span>;
                            })}
                        </nav>
                    ) : (
                        <h1 class="topbar-page-title">{pageTitle}</h1>
                    )}
                </div>

                <div class="topbar-controls" role="toolbar" aria-label="Toolbar controls">
                    <a
                        href="/dashboard/user/system.task"
                        class="topbar-action-btn"
                        aria-label={t('topbar.tasks', lang)}
                        data-tooltip={t('topbar.tasks', lang)}
                        dangerouslySetInnerHTML={{ __html: icon(faListCheck, 'topbar-action-icon') }}
                    />
                    <a href="/dashboard/user/system.message" class="topbar-action-btn" aria-label={messageLabel} data-tooltip={t('topbar.messages', lang)}>
                        <span dangerouslySetInnerHTML={{ __html: icon(faEnvelope, 'topbar-action-icon') }} />
                        {messageCount > 0 && <span class="topbar-action-badge" aria-hidden="true">{normalizeBadgeCount(messageCount)}</span>}
                    </a>
                    <div class="topbar-notifications-wrap" ref={notificationsWrapRef}>
                        <button
                            class="topbar-action-btn"
                            aria-label={notificationLabel}
                            aria-expanded={String(notificationsOpen)}
                            aria-controls="topbar-notifications-menu"
                            data-tooltip={t('topbar.notifications', lang)}
                            onClick={toggleNotifications}
                        >
                            <span dangerouslySetInnerHTML={{ __html: icon(faBell, 'topbar-action-icon') }} />
                            {notificationCount > 0 && <span class="topbar-action-badge" aria-hidden="true">{normalizeBadgeCount(notificationCount)}</span>}
                        </button>

                        <div class={`topbar-notifications-menu ${notificationsOpen ? 'topbar-notifications-menu--open' : ''}`} id="topbar-notifications-menu" role="region" aria-label={t('notifications.panel_title', lang)}>
                            <div class="topbar-notifications-header">
                                <span>{t('notifications.panel_title', lang)}</span>
                                {webPushStatus === 'default' || webPushStatus === 'not-subscribed' ? (
                                    <button type="button" class="topbar-notifications-push-btn" disabled={webPushBusy} onClick={toggleWebPush}>
                                        <span dangerouslySetInnerHTML={{ __html: icon(faBell) }} />
                                        {t('notifications.enable_push', lang)}
                                    </button>
                                ) : webPushStatus === 'subscribed' ? (
                                    <button type="button" class="topbar-notifications-push-btn" disabled={webPushBusy} onClick={toggleWebPush}>
                                        <span dangerouslySetInnerHTML={{ __html: icon(faBellSlash) }} />
                                        {t('notifications.disable_push', lang)}
                                    </button>
                                ) : webPushStatus === 'denied' ? (
                                    <span class="topbar-notifications-push-blocked">{t('notifications.push_blocked', lang)}</span>
                                ) : null}
                            </div>
                            {notifications.length === 0 ? (
                                <p class="topbar-notifications-empty">{t('notifications.empty', lang)}</p>
                            ) : (
                                <ul class="topbar-notifications-list">
                                    {notifications.map((notification) => {
                                        const meta = priorityMeta(notification.priority);
                                        return (
                                            <li key={notification.uuid}>
                                                <button
                                                    type="button"
                                                    class={`topbar-notification-item ${notification.read ? '' : 'topbar-notification-item--unread'}`}
                                                    onClick={() => handleNotificationClick(notification)}
                                                >
                                                    <span class={`topbar-notification-icon ${meta.class}`} aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(meta.icon) }} />
                                                    <span class="topbar-notification-body">
                                                        <strong class="topbar-notification-title">{localizedValue(notification.title, lang)}</strong>
                                                        <span class="topbar-notification-message">{localizedValue(notification.message, lang)}</span>
                                                        <time class="topbar-notification-time">{formatRelativeTime(notification.date, lang)}</time>
                                                    </span>
                                                </button>
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}
                        </div>
                    </div>

                    <div class="topbar-user-menu-wrap" ref={userMenuWrapRef}>
                        <button
                            class="topbar-user-btn"
                            aria-label="User profile"
                            aria-expanded={String(userMenuOpen)}
                            aria-controls="topbar-user-menu"
                            id="topbar-user"
                            onClick={(event) => {
                                event.stopPropagation();
                                setUserMenuOpen((open) => !open);
                            }}
                        >
                            <UserAvatar user={user} class="topbar-user-btn-avatar" />
                        </button>

                        <div class={`topbar-user-menu ${userMenuOpen ? 'topbar-user-menu--open' : ''}`} id="topbar-user-menu" role="menu" aria-labelledby="topbar-user">
                            {user && (
                                <div class="topbar-user-profile-card">
                                    <button
                                        type="button"
                                        class="topbar-user-avatar-btn"
                                        aria-label={lang === 'es' ? 'Cambiar avatar' : 'Change avatar'}
                                        onClick={handleAvatarUpload}
                                        disabled={!user?.uuid || avatarUploading}
                                    >
                                        <UserAvatar user={user} class="topbar-user-menu-avatar" />
                                        {avatarUploading && <span class="topbar-user-avatar-loading">{lang === 'es' ? 'Subiendo...' : 'Uploading...'}</span>}
                                    </button>
                                    {user?.avatarUrl && (
                                        <button
                                            type="button"
                                            class="topbar-user-avatar-remove"
                                            onClick={handleAvatarRemove}
                                            disabled={!user?.uuid || avatarUploading}
                                        >
                                            {lang === 'es' ? 'Quitar imagen' : 'Remove image'}
                                        </button>
                                    )}
                                    {user?.name && <span class="topbar-user-name">{user.name}</span>}
                                    {user?.email && <span class="topbar-user-email">{user.email}</span>}
                                </div>
                            )}

                            <div class="topbar-menu-section">
                                <span class="topbar-menu-label">{t('topbar.theme', lang)}</span>
                                <div class="topbar-theme-group" role="group" aria-label={t('topbar.theme', lang)}>
                                    {THEMES.map((th) => {
                                        const label = lang === 'es' ? th.labelEs : th.labelEn;
                                        return (
                                            <button
                                                key={th.key}
                                                class={`topbar-theme-btn ${theme === th.key ? 'topbar-theme-btn--active' : ''}`}
                                                data-theme={th.key}
                                                aria-label={label}
                                                aria-pressed={String(theme === th.key)}
                                                title={label}
                                                onClick={() => contextActions.setTheme(th.key)}
                                            >
                                                <span class="topbar-theme-icon" aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(th.icon) }} />
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            <div class="topbar-menu-section">
                                <span class="topbar-menu-label">{t('topbar.lang', lang)}</span>
                                <div class="topbar-lang-group" role="group" aria-label={t('topbar.lang', lang)}>
                                    {languageOptions.map((option) => (
                                        <button
                                            key={option.key}
                                            class={`topbar-lang-btn ${lang === option.key ? 'topbar-lang-btn--active' : ''}`}
                                            data-lang={option.key}
                                            aria-label={option.label}
                                            aria-pressed={String(lang === option.key)}
                                            onClick={() => contextActions.setLang(option.key)}
                                        >
                                            <span class="topbar-lang-flag" aria-hidden="true">
                                                {option.flag}
                                            </span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div class="topbar-menu-links">
                                <a class="topbar-menu-link" href="/dashboard/account" role="menuitem">{t('topbar.account', lang)}</a>
                                <a class="topbar-menu-link" href="/dashboard/settings" role="menuitem">{t('topbar.settings', lang)}</a>
                                <button class="topbar-menu-link topbar-menu-link--logout" type="button" role="menuitem" data-logout onClick={handleLogout}>
                                    {t('topbar.logout', lang)}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {showTools && (
                <div class="topbar-tools-dock">
                    <div class="topbar-floating-tools" aria-label={t('topbar.tools', lang)}>
                        <div class="topbar-view-group" role="group" aria-label={t('topbar.view_type', lang)}>
                            {VIEW_BUTTONS.map((v) => (
                                <button
                                    key={v.key}
                                    class={`topbar-tool-btn ${currentView === v.key ? 'topbar-tool-btn--active' : ''}`}
                                    data-view={v.key}
                                    aria-label={t(`topbar.view.${v.key}`, lang)}
                                    data-tooltip={t(`topbar.view.${v.key}`, lang)}
                                    disabled={disabledViews.includes(v.key)}
                                    onClick={() => onViewChange?.(v.key)}
                                    dangerouslySetInnerHTML={{ __html: icon(v.icon, 'topbar-tool-icon') }}
                                />
                            ))}
                        </div>

                        <div class="topbar-search-wrap" ref={searchHelpWrapRef}>
                            <form class="topbar-search" role="search" aria-label={t('topbar.search', lang)} onSubmit={submitSearch} ref={searchRef}>
                                <input
                                    class="topbar-search-input"
                                    type="search"
                                    value={searchQuery}
                                    placeholder={t('topbar.search_placeholder', lang)}
                                    aria-label={t('topbar.search', lang)}
                                    aria-expanded={String(searchOpen)}
                                    onInput={(event) => setSearchQuery(event.currentTarget.value)}
                                />
                                <button
                                    class="topbar-search-btn"
                                    type="submit"
                                    aria-label={t('topbar.search', lang)}
                                    data-tooltip={t('topbar.search', lang)}
                                    disabled={searchLoading}
                                    dangerouslySetInnerHTML={{ __html: icon(faMagnifyingGlass, 'topbar-tool-icon') }}
                                />
                                {searchOpen && <div class="topbar-search-results" data-search-results role="region" aria-live="polite">
                                    {searchLoading ? <p class="topbar-search-state">{lang === 'es' ? 'Buscando…' : 'Searching…'}</p>
                                        : searchError ? <p class="topbar-search-state topbar-search-state--error">{searchError}</p>
                                            : searchResults.length === 0 ? <p class="topbar-search-state">{lang === 'es' ? 'Sin resultados' : 'No results'}</p>
                                                : searchResults.map((result) => <a class="topbar-search-result" href={result.url} key={`${result.model}:${result.uuid}`}>
                                                    <span class="topbar-search-result-model">{result.modelLabel}</span>
                                                    <strong>{result.title}</strong>
                                                    {result.subtitle && <span>{result.subtitle}</span>}
                                                </a>)}
                                </div>}
                            </form>
                            <button
                                type="button"
                                class="topbar-search-help-btn"
                                aria-label={t('topbar.search_help', lang)}
                                aria-expanded={String(searchHelpOpen)}
                                aria-controls="topbar-search-help-panel"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    setSearchHelpOpen((open) => !open);
                                }}
                                dangerouslySetInnerHTML={{ __html: icon(faCircleInfo, 'topbar-tool-icon') }}
                            />
                            <div
                                class={`topbar-search-help-panel ${searchHelpOpen ? 'topbar-search-help-panel--open' : ''}`}
                                id="topbar-search-help-panel"
                                role="region"
                                aria-label={t('topbar.search_help', lang)}
                            >
                                <p class="topbar-search-help-title">{t('topbar.search_help_title', lang)}</p>
                                <p>{t('topbar.search_help_intro', lang)}</p>
                                <p class="topbar-search-help-examples-title">{t('topbar.search_help_examples_title', lang)}</p>
                                <ul class="topbar-search-help-examples">
                                    <li>{t('topbar.search_help_example_1', lang)}</li>
                                    <li>{t('topbar.search_help_example_2', lang)}</li>
                                    <li>{t('topbar.search_help_example_3', lang)}</li>
                                </ul>
                                <p class="topbar-search-help-note">{t('topbar.search_help_note', lang)}</p>
                            </div>
                        </div>

                        <div class="topbar-pagination" aria-label={t('topbar.pagination', lang)}>
                            <button
                                class="topbar-tool-btn"
                                data-page-previous
                                aria-label={t('topbar.page_prev', lang)}
                                data-tooltip={t('topbar.page_prev', lang)}
                                disabled={page <= 1}
                                onClick={() => dashboardActions.previousPage()}
                                dangerouslySetInnerHTML={{ __html: icon(faChevronLeft, 'topbar-tool-icon') }}
                            />
                            <span class="topbar-page-indicator" aria-label={pageStatus}>{page} / {totalPages}</span>
                            <button
                                class="topbar-tool-btn"
                                data-page-next
                                aria-label={t('topbar.page_next', lang)}
                                data-tooltip={t('topbar.page_next', lang)}
                                disabled={page >= totalPages}
                                onClick={() => dashboardActions.nextPage()}
                                dangerouslySetInnerHTML={{ __html: icon(faChevronRight, 'topbar-tool-icon') }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

/** Mounts (or updates) the topbar into `container`. Safe to call repeatedly. */
export function mountTopbar(container, props) {
    if (!container) return;
    render(<Topbar {...props} />, container);
}
