import { render } from 'preact';

import { CalendarView, FormView, KanbanView, ListView } from '../../src/app/views/index.js';

function mount(Component, props) {
    const host = document.createElement('div');
    document.body.appendChild(host);
    render(<Component {...props} />, host);
    return { host, cleanup: () => render(null, host) };
}

export const mountForm = (data, lang = 'en', options = {}) => mount(FormView, { data, lang, options });
export const mountKanban = (data, lang = 'en') => mount(KanbanView, { data, lang });
export const mountList = (data, lang = 'en') => mount(ListView, { data, lang });
export const mountCalendar = (data, lang = 'en') => mount(CalendarView, { data, lang });
