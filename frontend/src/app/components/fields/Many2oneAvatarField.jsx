import { AuthenticatedImage } from '../AuthenticatedImage.jsx';
import { buildRecordUrl, rememberRecordBreadcrumb } from '../../utils/routing.js';
import { Many2oneField } from './Many2oneField.jsx';
import { isFieldReadOnly } from './fieldHelpers.js';

export function Many2oneAvatarField(props) {
    const { field, value, readOnly } = props;
    if (!isFieldReadOnly(field, readOnly)) return <Many2oneField {...props} />;

    const name = value?.name ?? value ?? '';
    const href = value?.model && value?.uuid != null ? buildRecordUrl(value.model, value.uuid) : '';
    const avatar = value?.avatar
        ? <AuthenticatedImage src={value.avatar} alt="" class="h-6 w-6 shrink-0 rounded-full object-cover" />
        : (
            <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full
                bg-[var(--dash-bg)] text-[10px] font-semibold text-[var(--dash-text-muted)]">
                {name ? String(name).slice(0, 1).toUpperCase() : '—'}
            </span>
        );
    const content = (
        <span class="inline-flex items-center gap-2">
            {avatar}
            <span class={name ? 'font-medium text-[var(--dash-text)]' : 'text-[var(--dash-text-soft)]'}>{name || '—'}</span>
        </span>
    );
    return href ? <a href={href} class="hover:underline" onClick={() => rememberRecordBreadcrumb(href, name)}>{content}</a> : content;
}
