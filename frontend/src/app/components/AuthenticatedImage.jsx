import { useEffect, useState } from 'preact/hooks';

import { fetchAttachmentContent } from '../api/attachments.js';

function isAttachmentUrl(src) {
    if (!src) return false;
    if (String(src).startsWith('attachment:')) return true;
    try {
        const url = new URL(src, globalThis.location?.origin ?? 'http://localhost');
        return url.pathname.startsWith('/api/system/attachments/');
    } catch {
        return false;
    }
}

export function AuthenticatedImage({ src, alt = '', class: className = '' }) {
    const [resolvedSrc, setResolvedSrc] = useState(src ?? '');

    useEffect(() => {
        if (!isAttachmentUrl(src)) {
            setResolvedSrc(src ?? '');
            return undefined;
        }

        let cancelled = false;
        let objectUrl = '';
        fetchAttachmentContent(src)
            .then((blob) => {
                if (cancelled) return;
                objectUrl = URL.createObjectURL(blob);
                setResolvedSrc(objectUrl);
            })
            .catch((error) => {
                if (!cancelled) {
                    setResolvedSrc('');
                    console.error('Unable to load authenticated image.', error);
                }
            });

        return () => {
            cancelled = true;
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [src]);

    if (!resolvedSrc) return null;
    return <img src={resolvedSrc} alt={alt} class={className} />;
}
