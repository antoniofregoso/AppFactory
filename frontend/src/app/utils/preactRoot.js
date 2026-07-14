import { render } from 'preact';

/**
 * Takes clean ownership of a page-root DOM node shared between Preact pages
 * and pages still rendered as raw HTML strings (during the gradual Preact
 * migration). Unmounts any previous Preact tree — running its cleanup and
 * clearing Preact's internal vnode cache on the node — then removes any
 * leftover DOM so the next render (Preact or legacy) starts from empty.
 */
export function resetAppRoot(container) {
    render(null, container);
    container.replaceChildren();
}

/** Mounts a Preact page into `container`, regardless of what the previous page rendered. */
export function mountPreactPage(vnode, container) {
    resetAppRoot(container);
    render(vnode, container);
}
