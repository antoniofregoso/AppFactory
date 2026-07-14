import { render } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';
import { icon, faChartLine, faUsers, faFolder, faCloud, faGear, faBars, faChevronLeft, faChevronRight } from './icon.js';
import { contextActions } from '../store/actions/index.js';
import { t } from '../../i18n/translations.js';
import data from '../data/sidebar.json' with { type: 'json' };

const iconMap = { faChartLine, faUsers, faFolder, faCloud, faGear };

export const MENU_ITEMS = data.map((item) => ({
    ...item,
    icon: iconMap[item.icon],
}));

function getLabel(item, lang) {
    return lang === 'es' ? item.labelEs : item.labelEn;
}

function SubmenuCard({ item, lang, isOpen, cardRef, onLinkClick }) {
    if (!item.items?.length) return null;
    const label = getLabel(item, lang);

    return (
        <div
            ref={cardRef}
            class={`sidebar-submenu-card ${isOpen ? 'sidebar-submenu-card--open' : ''}`}
            id={`sidebar-submenu-${item.key}`}
            role="menu"
            aria-label={label}
        >
            <div class="sidebar-submenu-title">{label}</div>
            <div class="sidebar-submenu-list">
                {item.items.map((subitem) => (
                    <a key={subitem.key} class="sidebar-submenu-link" href={subitem.url} data-submenu-link onClick={onLinkClick}>
                        <span class="sidebar-submenu-link-label">{getLabel(subitem, lang)}</span>
                    </a>
                ))}
            </div>
        </div>
    );
}

/**
 * Sidebar navigation. Fully self-contained: submenu open/close, floating
 * tooltip and their document/window listeners are all wired via hooks, so
 * Preact attaches and tears them down automatically on every re-render and
 * on unmount — no manual init/cleanup calls are needed from the page.
 */
export function Sidebar({ lang, expanded, activeArea, isAdmin }) {
    const [openKey, setOpenKey] = useState(null);
    const triggerRefs = useRef(new Map());
    const cardRefs = useRef(new Map());
    const tooltipRef = useRef(null);

    // Single floating tooltip node, appended to <body> so `.sidebar`'s
    // `overflow: hidden` / `will-change: width` can never clip it.
    useEffect(() => {
        const el = document.createElement('div');
        el.id = 'sidebar-floating-tooltip';
        el.className = 'sidebar-floating-tooltip';
        document.body.appendChild(el);
        tooltipRef.current = el;
        return () => {
            el.remove();
            tooltipRef.current = null;
        };
    }, []);

    const hideTooltip = () => {
        tooltipRef.current?.classList.remove('sidebar-floating-tooltip--visible');
    };

    const showTooltip = (event, label) => {
        if (expanded || !label) return;
        const tip = tooltipRef.current;
        if (!tip) return;
        const rect = event.currentTarget.getBoundingClientRect();
        tip.textContent = label;
        tip.style.top = `${rect.top + rect.height / 2}px`;
        tip.style.left = `${rect.right + 12}px`;
        tip.classList.add('sidebar-floating-tooltip--visible');
    };

    const closeSubmenu = () => setOpenKey(null);

    const positionCard = (key) => {
        const trigger = triggerRefs.current.get(key);
        const card = cardRefs.current.get(key);
        if (!trigger || !card) return;
        const rect = trigger.getBoundingClientRect();
        const cardWidth = card.offsetWidth || 236;
        const cardHeight = card.offsetHeight || 180;
        const gap = 12;
        const viewportPadding = 12;
        const left = Math.min(rect.right + gap, window.innerWidth - cardWidth - viewportPadding);
        const top = Math.min(Math.max(rect.top - 8, viewportPadding), window.innerHeight - cardHeight - viewportPadding);
        card.style.left = `${left}px`;
        card.style.top = `${top}px`;
    };

    // While a submenu is open: position it, close the tooltip, and listen
    // for outside clicks / Escape / resize / scroll. Preact re-runs this
    // (and its cleanup) whenever `openKey` changes, and always on unmount.
    useEffect(() => {
        if (!openKey) return undefined;
        positionCard(openKey);
        hideTooltip();

        const onOutsideClick = (event) => {
            const card = cardRefs.current.get(openKey);
            const trigger = triggerRefs.current.get(openKey);
            if (!card?.contains(event.target) && !trigger?.contains(event.target)) {
                closeSubmenu();
            }
        };
        const onEscape = (event) => {
            if (event.key === 'Escape') closeSubmenu();
        };
        const reposition = () => positionCard(openKey);

        document.addEventListener('click', onOutsideClick);
        document.addEventListener('keydown', onEscape);
        window.addEventListener('resize', reposition);
        window.addEventListener('scroll', reposition, true);

        return () => {
            document.removeEventListener('click', onOutsideClick);
            document.removeEventListener('keydown', onEscape);
            window.removeEventListener('resize', reposition);
            window.removeEventListener('scroll', reposition, true);
        };
    }, [openKey]);

    const toggleSubmenu = (event, key) => {
        event.preventDefault();
        event.stopPropagation();
        setOpenKey((current) => (current === key ? null : key));
    };

    const appName = t('sidebar.app_name', lang);

    return (
        <aside id="dashboard-sidebar" class={`sidebar ${expanded ? 'sidebar--expanded' : 'sidebar--collapsed'}`} aria-label="Sidebar navigation">
            <div class="sidebar-header">
                <a href="/dashboard" class="sidebar-logo" aria-label={appName}>
                    <img src="/logo.png" alt="App logo" class="sidebar-logo-img" style={{ width: '24px', height: '24px', borderRadius: '4px' }} />
                    <span class="sidebar-app-name">{appName}</span>
                </a>
                <button
                    id="sidebar-toggle"
                    class="sidebar-toggle-btn"
                    aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
                    aria-expanded={String(expanded)}
                    aria-controls="dashboard-sidebar"
                    title={expanded ? 'Collapse' : 'Expand'}
                    onClick={() => contextActions.toggleSidebar()}
                    dangerouslySetInnerHTML={{ __html: icon(expanded ? faChevronLeft : faBars, 'sidebar-toggle-icon') }}
                />
            </div>

            <nav class="sidebar-nav" aria-label="Main navigation">
                <ul class="sidebar-menu" role="list">
                    {MENU_ITEMS.filter((item) => !item.hidden && (!item.adminOnly || isAdmin)).map((item) => {
                        const label = getLabel(item, lang);
                        const isActive = item.key === activeArea;
                        const hasSubmenu = Boolean(item.items?.length);
                        const linkContent = (
                            <>
                                <span class="sidebar-icon" aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon(item.icon, 'sidebar-svg-icon') }} />
                                <span class={`sidebar-label ${expanded ? '' : 'sidebar-label--hidden'}`}>{label}</span>
                                {hasSubmenu && (
                                    <span
                                        class={`sidebar-submenu-chevron ${expanded ? '' : 'sidebar-submenu-chevron--hidden'}`}
                                        aria-hidden="true"
                                        dangerouslySetInnerHTML={{ __html: icon(faChevronRight, 'sidebar-submenu-chevron-icon') }}
                                    />
                                )}
                            </>
                        );

                        return (
                            <li key={item.key} class={`sidebar-item ${isActive ? 'sidebar-item--active' : ''}`} data-tooltip={label}>
                                {hasSubmenu ? (
                                    <button
                                        type="button"
                                        ref={(el) => triggerRefs.current.set(item.key, el)}
                                        class="sidebar-link sidebar-link--submenu"
                                        data-area={item.key}
                                        data-submenu-trigger={item.key}
                                        aria-label={label}
                                        aria-expanded={String(openKey === item.key)}
                                        aria-controls={`sidebar-submenu-${item.key}`}
                                        onClick={(event) => toggleSubmenu(event, item.key)}
                                        onMouseEnter={(event) => showTooltip(event, label)}
                                        onMouseLeave={hideTooltip}
                                    >
                                        {linkContent}
                                    </button>
                                ) : (
                                    <a
                                        href={item.url}
                                        class="sidebar-link"
                                        data-area={item.key}
                                        aria-label={label}
                                        aria-current={isActive ? 'page' : 'false'}
                                        onMouseEnter={(event) => showTooltip(event, label)}
                                        onMouseLeave={hideTooltip}
                                    >
                                        {linkContent}
                                    </a>
                                )}
                                {hasSubmenu && (
                                    <SubmenuCard
                                        item={item}
                                        lang={lang}
                                        isOpen={openKey === item.key}
                                        cardRef={(el) => cardRefs.current.set(item.key, el)}
                                        onLinkClick={closeSubmenu}
                                    />
                                )}
                            </li>
                        );
                    })}
                </ul>
            </nav>
            <a href="/dashboard" class="sidebar-collapsed-logo" aria-label={appName} title={appName}>
                <img src="/logo.png" alt="App logo" class="sidebar-logo-img" style={{ width: '24px', height: '24px', borderRadius: '4px' }} />
            </a>
        </aside>
    );
}

/** Mounts (or updates) the sidebar into `container`. Safe to call repeatedly. */
export function mountSidebar(container, props) {
    if (!container) return;
    render(<Sidebar {...props} />, container);
}
