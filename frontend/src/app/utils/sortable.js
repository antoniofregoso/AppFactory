import Sortable from 'sortablejs';

/**
 * Make a container's direct children drag-sortable.
 * Reusable across views (list rows, kanban cards, calendar items, …).
 *
 * @param {HTMLElement} el — the container whose children will be sortable.
 * @param {object}   [options]
 * @param {string}   [options.handle] — selector of the drag handle inside each
 *                   item; omit to allow dragging from anywhere on the item.
 * @param {(ids: string[], evt: object) => void} [options.onReorder] — called
 *                   after a drag ends, with the children's `data-uuid` values in
 *                   their new order.
 * @param {object}   [options.sortableOptions] — extra SortableJS options.
 * @returns {() => void} cleanup function that destroys the instance.
 */
export function makeSortable(el, { handle, onReorder, sortableOptions = {} } = {}) {
    if (!el) return () => {};

    const instance = Sortable.create(el, {
        animation: 150,
        ...(handle ? { handle } : {}),
        ...sortableOptions,
        onEnd: (evt) => {
            if (onReorder) {
                const ids = Array.from(el.children)
                    .map((child) => child.dataset.uuid)
                    .filter(Boolean);
                onReorder(ids, evt);
            }
            sortableOptions.onEnd?.(evt);
        },
    });

    return () => instance.destroy();
}
