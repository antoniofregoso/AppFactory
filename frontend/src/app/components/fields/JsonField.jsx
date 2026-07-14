import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { createJSONEditor } from 'vanilla-jsoneditor';
import 'vanilla-jsoneditor/themes/jse-theme-dark.css';

import { fieldLabel, hasValue, isFieldReadOnly, localizedConfig, plainText } from './fieldHelpers.js';

function toJsonValue(value) {
    if (!hasValue(value)) return {};
    if (typeof value !== 'string') return value;
    try {
        return JSON.parse(value);
    } catch {
        return value;
    }
}

function formatJsonValue(value) {
    if (!hasValue(value)) return '—';
    const jsonValue = toJsonValue(value);
    try {
        return JSON.stringify(jsonValue, null, 2);
    } catch {
        return String(jsonValue);
    }
}

function readEditorContent(content) {
    if (content && Object.hasOwn(content, 'json')) return content.json;
    if (content?.text == null) return undefined;
    try {
        return JSON.parse(content.text);
    } catch {
        return undefined;
    }
}

export function JsonField({ field, value, onChange, lang = 'en', readOnly = false }) {
    const disabled = isFieldReadOnly(field, readOnly);
    const containerRef = useRef(null);
    const editorRef = useRef(null);
    const internalChangeRef = useRef(false);
    const [isDarkTheme, setIsDarkTheme] = useState(() => (
        typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme') === 'dark'
    ));
    const placeholder = plainText(localizedConfig(field, 'placeholder', lang));

    useEffect(() => {
        if (typeof MutationObserver === 'undefined') return undefined;

        const updateTheme = () => {
            setIsDarkTheme(document.documentElement.getAttribute('data-theme') === 'dark');
        };
        updateTheme();

        const observer = new MutationObserver(updateTheme);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
        return () => observer.disconnect();
    }, []);

    useLayoutEffect(() => {
        if (disabled || !containerRef.current) return undefined;

        const editor = createJSONEditor({
            target: containerRef.current,
            props: {
                content: { json: toJsonValue(value) },
                mode: 'tree',
                mainMenuBar: true,
                navigationBar: false,
                statusBar: true,
                onChange: (content) => {
                    const nextValue = readEditorContent(content);
                    if (nextValue === undefined) return;
                    internalChangeRef.current = true;
                    onChange(field.name, nextValue);
                    queueMicrotask(() => {
                        internalChangeRef.current = false;
                    });
                },
            },
        });

        editorRef.current = editor;

        return () => {
            editor.destroy();
            editorRef.current = null;
        };
    }, [disabled, field.name]);

    useLayoutEffect(() => {
        if (disabled || !editorRef.current || internalChangeRef.current) return;
        editorRef.current.updateProps({
            content: { json: toJsonValue(value) },
        });
    }, [disabled, value]);

    if (disabled) {
        return (
            <pre class="form-json-display" aria-label={fieldLabel(field, lang)}>
                {formatJsonValue(value)}
            </pre>
        );
    }

    return (
        <div class="form-json-editor-shell">
            <div
                class={`form-json-editor${isDarkTheme ? ' jse-theme-dark' : ''}`}
                aria-label={fieldLabel(field, lang)}
                data-placeholder={placeholder}
                ref={containerRef}
            />
        </div>
    );
}
