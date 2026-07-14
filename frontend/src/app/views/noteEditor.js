const TEXT_COLORS = [
    false,
    '#18181b',
    '#dc2626',
    '#ea580c',
    '#ca8a04',
    '#16a34a',
    '#2563eb',
    '#9333ea',
];

const BACKGROUND_COLORS = [
    false,
    '#fee2e2',
    '#ffedd5',
    '#fef3c7',
    '#dcfce7',
    '#dbeafe',
    '#f3e8ff',
    '#f4f4f5',
];

export const RICH_TEXT_TOOLBAR = [
    ['bold', 'italic', 'underline', 'strike'],
    [{ color: TEXT_COLORS }, { background: BACKGROUND_COLORS }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['blockquote'],
    ['link', 'image'],
];
