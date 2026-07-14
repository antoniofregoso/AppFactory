import { AuthenticatedImage } from '../AuthenticatedImage.jsx';
import { buildRecordUrl, rememberRecordBreadcrumb } from '../../utils/routing.js';
import { localizedValue } from '../../utils/ux.js';
import { isFieldReadOnly } from './fieldHelpers.js';

function userLabel(user, lang) {
    return localizedValue(user?.display_name, lang)
        || localizedValue(user?.name, lang)
        || user?.email
        || '';
}

function userAvatar(user, label) {
    return user?.avatar
        ? <AuthenticatedImage src={user.avatar} alt="" class="h-7 w-7 rounded-full object-cover" />
        : (
            <span class="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--dash-bg)] text-[10px] font-semibold text-[var(--dash-text-muted)]">
                {label ? String(label).slice(0, 1).toUpperCase() : '—'}
            </span>
        );
}

function allowedUsers(field) {
    return (field?.options ?? []).filter((user) => user?.user_type !== 'SYSTEM');
}

export function One2manyFollowersField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const followers = Array.isArray(value) ? value : [];
    const options = allowedUsers(field);
    const selectedUuids = new Set(followers.map((user) => String(user?.uuid)));
    const disabled = isFieldReadOnly(field, readOnly);
    const label = lang === 'es' ? 'Seguidores' : 'Followers';
    const emptyLabel = lang === 'es' ? 'Sin seguidores' : 'No followers';
    const statusLabel = context.followerStatus === 'saving'
        ? (lang === 'es' ? 'Guardando…' : 'Saving…')
        : context.followerStatus === 'saved'
            ? (lang === 'es' ? 'Guardado' : 'Saved')
            : context.followerStatus === 'error'
                ? (lang === 'es' ? 'Error al guardar' : 'Save failed')
                : '';

    if (disabled) {
        return (
            <div class="flex items-center gap-2" aria-label={label}>
                <span class="text-xs font-semibold text-[var(--dash-text)]">{label}</span>
                {followers.length === 0 ? (
                    <span class="rounded-full border border-dashed border-[var(--dash-border)] bg-[var(--dash-bg)] px-2 py-0.5 text-xs text-[var(--dash-text-muted)]">{emptyLabel}</span>
                ) : (
                    <div class="flex items-center -space-x-2">
                        {followers.slice(0, 6).map((user) => {
                            const name = userLabel(user, lang);
                            const href = user?.uuid ? buildRecordUrl('user.user', user.uuid) : '';
                            const content = (
                                <span class="inline-flex h-7 w-7 rounded-full ring-2 ring-[var(--dash-surface)]" data-tooltip={name} title={name}>
                                    {userAvatar(user, name)}
                                </span>
                            );
                            return href
                                ? <a href={href} onClick={() => rememberRecordBreadcrumb(href, name)}
                                    class="relative hover:z-10" key={user.uuid}>{content}</a>
                                : <span class="relative hover:z-10" key={user.uuid ?? name}>{content}</span>;
                        })}
                        {followers.length > 6 && (
                            <span class="relative inline-flex h-7 min-w-7 items-center justify-center rounded-full bg-[var(--dash-surface-hover)] px-1.5 text-[10px] font-semibold text-[var(--dash-text-muted)] ring-2 ring-[var(--dash-surface)]">
                                +{followers.length - 6}
                            </span>
                        )}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div class="flex items-center gap-2" aria-label={label}>
            <span class="text-xs font-semibold text-[var(--dash-text)]">{label}</span>
            {statusLabel && <span role="status" data-follower-status class={`text-xs ${context.followerStatus === 'error' ? 'text-[var(--dash-danger)]' : 'text-[var(--dash-text-muted)]'}`}>{statusLabel}</span>}
            <div class="flex flex-wrap items-center gap-1.5" role="group" aria-label={lang === 'es' ? 'Seleccionar seguidores' : 'Select followers'}>
                {options.map((user) => {
                    const selected = selectedUuids.has(String(user.uuid));
                    const name = userLabel(user, lang);
                    return (
                        <button
                            type="button"
                            key={user.uuid}
                            class={`inline-flex h-8 w-8 items-center justify-center rounded-full border bg-[var(--dash-surface)] transition ${selected ? 'border-[var(--dash-accent)] ring-2 ring-[var(--dash-accent)] ring-offset-2 ring-offset-[var(--dash-surface)]' : 'border-[var(--dash-border)] opacity-75 hover:opacity-100'}`}
                            aria-pressed={String(selected)}
                            aria-label={name}
                            data-tooltip={name}
                            onClick={() => {
                                const next = selected
                                    ? followers.filter((item) => String(item.uuid) !== String(user.uuid))
                                    : [...followers, user];
                                onChange(field.name, next);
                            }}
                        >
                            {userAvatar(user, name)}
                        </button>
                    );
                })}
                {options.length === 0 && (
                    <span class="rounded-full border border-dashed border-[var(--dash-border)] px-2 py-0.5 text-xs text-[var(--dash-text-soft)]">
                        {lang === 'es' ? 'No hay usuarios disponibles' : 'No users available'}
                    </span>
                )}
            </div>
        </div>
    );
}
