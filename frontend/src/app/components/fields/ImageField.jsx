import { useRef, useState } from 'preact/hooks';

import { uploadAttachment } from '../../api/attachments.js';
import { AuthenticatedImage } from '../AuthenticatedImage.jsx';
import { fieldLabel, isFieldReadOnly } from './fieldHelpers.js';

function readAsDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

export function ImageField({ field, value, onChange, lang = 'en', readOnly = false, context = {} }) {
    const inputRef = useRef(null);
    const [uploading, setUploading] = useState(false);

    if (isFieldReadOnly(field, readOnly)) {
        if (context.view === 'list') {
            return value
                ? <AuthenticatedImage src={value} alt={fieldLabel(field, lang)} class="h-7 w-7 shrink-0 rounded-full object-cover ring-1 ring-[var(--dash-border)]" />
                : <span class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--dash-surface-hover)] text-[10px] text-[var(--dash-text-soft)] ring-1 ring-[var(--dash-border)]">—</span>;
        }
        return value
            ? <AuthenticatedImage src={value} alt={fieldLabel(field, lang)} class="h-20 w-20 rounded-xl object-cover ring-1 ring-[var(--dash-border)]" />
            : <span class="form-image-placeholder">{fieldLabel(field, lang)}</span>;
    }

    const onFileChange = async (event) => {
        const file = event.currentTarget.files?.[0];
        event.currentTarget.value = '';
        if (!file) return;
        const modelUuid = context.modelUuid ?? context.uuid;
        const recordUuid = context.record?.uuid;
        if (!modelUuid || !recordUuid) {
            onChange(field.name, await readAsDataUrl(file));
            return;
        }
        setUploading(true);
        try {
            const attachment = await uploadAttachment({ modelUuid, recordUuid, file });
            onChange(field.name, attachment.content_url);
        } catch (error) {
            const message = error?.message ? `\n${error.message}` : '';
            window.alert(`${lang === 'es' ? 'No se pudo subir la imagen.' : 'Unable to upload image.'}${message}`);
            console.error('Unable to upload image attachment.', error);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div class="inline-flex flex-col items-center gap-1.5">
            <button type="button" class="block" onClick={() => inputRef.current?.click()} aria-label={fieldLabel(field, lang)}>
                {value
                    ? <AuthenticatedImage src={value} alt="" class="h-20 w-20 rounded-xl object-cover ring-1 ring-[var(--dash-border)]" />
                    : <span class="form-image-placeholder">{uploading ? (lang === 'es' ? 'Subiendo...' : 'Uploading...') : (lang === 'es' ? 'Subir imagen' : 'Upload image')}</span>}
            </button>
            {value && (
                <button type="button" class="form-image-remove" data-image-remove
                    aria-label={lang === 'es' ? 'Quitar imagen' : 'Remove image'}
                    disabled={uploading} onClick={() => onChange(field.name, '')}>
                    {lang === 'es' ? 'Quitar imagen' : 'Remove image'}
                </button>
            )}
            <input ref={inputRef} type="file" name={field.name} accept="image/*" class="hidden" disabled={uploading} onChange={onFileChange} />
        </div>
    );
}
