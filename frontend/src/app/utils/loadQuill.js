let quillPromise;

/** Lazily loads Quill and its stylesheet on first use, then caches the module for reuse. */
export function loadQuill() {
    if (!quillPromise) {
        quillPromise = Promise.all([
            import('quill'),
            import('quill/dist/quill.snow.css'),
        ]).then(([quillModule]) => quillModule.default ?? quillModule);
    }
    return quillPromise;
}
