import { afterEach, describe, expect, it, vi } from 'vitest';
import { render } from 'preact';

vi.mock('../src/app/api/attachments.js', () => ({
    uploadAttachment: vi.fn().mockResolvedValue({
        content_url: '/api/system/attachments/avatar-1/content',
    }),
}));

vi.mock('../src/app/api/systemModel.js', () => ({
    fetchSystemModelByName: vi.fn().mockResolvedValue({ uuid: 'model-user-1', name: 'user.user' }),
    fetchSystemModelView: vi.fn().mockResolvedValue({
        records: [
            { code: 'en_US', url_code: 'en', flag: '🇺🇸', active: true },
            { code: 'es_MX', url_code: 'es', flag: '🇲🇽', active: true },
            { name: 'French / Français', code: 'fr_FR', url_code: 'fr', flag: '🇫🇷', active: true },
        ],
    }),
    searchSystemModels: vi.fn().mockResolvedValue({ status: 'OK', results: [] }),
    updateSystemModelRecord: vi.fn().mockResolvedValue({ avatar_url: '/api/system/attachments/avatar-1/content' }),
}));

import { Topbar } from '../src/app/components/topbar.jsx';
import { uploadAttachment } from '../src/app/api/attachments.js';
import { fetchSystemModelByName, fetchSystemModelView, searchSystemModels, updateSystemModelRecord } from '../src/app/api/systemModel.js';
import { authSignal } from '../src/app/store/authStore.js';

function mount(vnode) {
    const host = document.createElement('div');
    document.body.appendChild(host);
    render(vnode, host);
    return host;
}

afterEach(() => {
    uploadAttachment.mockClear();
    fetchSystemModelByName.mockClear();
    fetchSystemModelView.mockClear();
    updateSystemModelRecord.mockClear();
    searchSystemModels.mockClear();
    authSignal.value = { uuid: null, email: null, name: null, avatarUrl: null, isAuthenticated: false };
    document.body.innerHTML = '';
});

describe('Topbar user menu', () => {
    it('renders every active system.lang flag in the user card', async () => {
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" />);

        await vi.waitFor(() => {
            expect(host.querySelector('[data-lang="en"] .topbar-lang-flag').textContent)
                .toBe('🇺🇸');
            expect(host.querySelector('[data-lang="es"] .topbar-lang-flag').textContent)
                .toBe('🇲🇽');
            expect(host.querySelector('[data-lang="fr"] .topbar-lang-flag').textContent)
                .toBe('🇫🇷');
        });
        expect(host.querySelector('[data-lang="fr"]').getAttribute('aria-label'))
            .toBe('French / Français');
        expect(fetchSystemModelView).toHaveBeenCalledWith({
            model: 'system.lang',
            use: 'view',
            name: 'default',
        });
    });

    it('searches enabled system models and links the results', async () => {
        searchSystemModels.mockResolvedValueOnce({
            status: 'OK',
            results: [{ model: 'system.task', modelLabel: 'Tasks', uuid: 'task-1', title: 'Urgent report', subtitle: 'Urgent', url: '/dashboard/user/system.task/task-1' }],
        });
        const host = mount(<Topbar lang="en" theme="light" pageTitle="Tasks" showTools />);
        const input = host.querySelector('.topbar-search-input');
        input.value = 'urgent report';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise((resolve) => setTimeout(resolve, 0));
        host.querySelector('.topbar-search').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));

        await vi.waitFor(() => expect(searchSystemModels).toHaveBeenCalledWith({
            query: 'urgent report',
            lang: 'en',
            limit: 20,
            mode: 'AUTO',
            originalQuery: null,
            clarificationAnswer: null,
        }));
        await vi.waitFor(() => expect(host.querySelector('[data-search-results] a')).not.toBeNull());
        expect(host.querySelector('[data-search-results] a').getAttribute('href')).toBe('/dashboard/user/system.task/task-1');
        expect(host.querySelector('[data-search-results]').textContent).toContain('Urgent report');
    });

    it('resubmits clarification with the original question and new answer', async () => {
        searchSystemModels
            .mockResolvedValueOnce({
                status: 'NEEDS_CLARIFICATION',
                needsClarification: true,
                clarificationQuestion: 'Which priority?',
                results: [],
                errors: [],
            })
            .mockResolvedValueOnce({
                status: 'OK',
                needsClarification: false,
                results: [],
                errors: [],
            });
        const host = mount(<Topbar lang="en" theme="light" pageTitle="Tasks" showTools />);
        const form = host.querySelector('.topbar-search');
        const input = host.querySelector('.topbar-search-input');

        input.value = 'find my tasks';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise((resolve) => setTimeout(resolve, 0));
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        await vi.waitFor(() => expect(host.querySelector('[data-search-results]').textContent)
            .toContain('Which priority?'));

        input.value = 'urgent';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise((resolve) => setTimeout(resolve, 0));
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));

        await vi.waitFor(() => expect(searchSystemModels).toHaveBeenLastCalledWith({
            query: 'find my tasks\nurgent',
            lang: 'en',
            limit: 20,
            mode: 'AUTO',
            originalQuery: 'find my tasks',
            clarificationAnswer: 'urgent',
        }));
    });

    it('renders an ordered dynamic breadcrumb trail with smaller nested links', () => {
        const breadcrumb = [
            { label: 'Configuration', url: '/dashboard/configuration' },
            { label: 'Companies', url: '/dashboard/configuration/system.company' },
            { label: 'My Company', url: '/dashboard/configuration/system.company/company-1' },
        ];
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" breadcrumb={breadcrumb} />);
        const nav = host.querySelector('[aria-label="Breadcrumb"]');
        expect([...nav.querySelectorAll('a')].map((item) => item.textContent)).toEqual(['Configuration', 'Companies']);
        expect(nav.querySelector('[aria-current="page"]').textContent).toBe('My Company');
        expect(nav.textContent).toContain('Configuration/Companies/My Company');
    });

    it('renders a breadcrumb root with # as plain text', () => {
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" breadcrumb={[
            { label: 'Configuration', url: '#' },
            { label: 'App', url: '/dashboard/configuration/system.app' },
        ]} />);
        const nav = host.querySelector('[aria-label="Breadcrumb"]');
        expect(nav.querySelectorAll('a')).toHaveLength(0);
        expect(nav.querySelector('[aria-current="page"]').textContent).toBe('App');
        expect(nav.firstElementChild.textContent).toBe('Configuration');
    });

    it('keeps a fifth breadcrumb level visible instead of shrinking it away', () => {
        const breadcrumb = ['Configuration', 'App', 'My App', 'Company', 'Currency'].map((label, index) => ({
            label,
            url: index === 0 ? '#' : `/level/${index}`,
        }));
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" breadcrumb={breadcrumb} />);
        const nav = host.querySelector('[aria-label="Breadcrumb"]');
        expect(nav.querySelectorAll('a, [aria-current="page"]')).toHaveLength(4);
        expect(nav.querySelector('[aria-current="page"]').textContent).toBe('Currency');
        expect(nav.className).toContain('overflow-x-auto');
    });

    it('shows the user avatar and name above the theme selection when known', () => {
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" user={{ name: 'Ana Admin', email: 'ana@example.com', avatarUrl: '/avatar.jpg' }} />);
        expect(host.querySelector('.topbar-user-btn img').getAttribute('src')).toBe('/avatar.jpg');
        const profileCard = host.querySelector('.topbar-user-profile-card');
        expect(profileCard.querySelector('.topbar-user-menu-avatar').getAttribute('src')).toBe('/avatar.jpg');
        expect(profileCard.querySelector('.topbar-user-name').textContent).toBe('Ana Admin');
        expect(profileCard.nextElementSibling.querySelector('.topbar-menu-label').textContent).toBe('Theme');
    });

    it('omits the user name when the user has no name yet', () => {
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" user={{ email: 'ana@example.com' }} />);
        expect(host.querySelector('.topbar-user-profile-card')).not.toBeNull();
        expect(host.querySelector('.topbar-user-btn .topbar-user-icon')).not.toBeNull();
        expect(host.querySelector('.topbar-user-avatar-btn .topbar-user-icon')).not.toBeNull();
        expect(host.querySelector('.topbar-user-name')).toBeNull();
    });

    it('omits the profile card when no user is provided', () => {
        const host = mount(<Topbar lang="en" theme="light" pageTitle="" />);
        expect(host.querySelector('.topbar-user-profile-card')).toBeNull();
    });

    it('uploads a new avatar from the profile card', async () => {
        const host = mount(
            <Topbar
                lang="en"
                theme="light"
                pageTitle=""
                user={{ uuid: 'user-1', name: 'Ana Admin', email: 'ana@example.com' }}
            />,
        );
        const file = new File(['avatar'], 'ana.png', { type: 'image/png' });
        const upload = host.querySelector('.topbar-user-avatar-btn').click();
        const input = document.querySelector('input[type="file"]');
        Object.defineProperty(input, 'files', { value: [file], configurable: true });
        input.dispatchEvent(new Event('change', { bubbles: true }));
        await upload;
        await vi.waitFor(() => expect(updateSystemModelRecord).toHaveBeenCalled());

        expect(fetchSystemModelByName).toHaveBeenCalledWith('user.user');
        expect(uploadAttachment).toHaveBeenCalledWith({
            modelUuid: 'model-user-1',
            recordUuid: 'user-1',
            file,
        });
        expect(updateSystemModelRecord).toHaveBeenCalledWith({
            model: 'user.user',
            recordUuid: 'user-1',
            values: { avatar_url: '/api/system/attachments/avatar-1/content' },
        });
        expect(authSignal.value.avatarUrl).toBe('/api/system/attachments/avatar-1/content');
    });

    it('removes the avatar from the profile card and returns to the default icon', async () => {
        authSignal.value = {
            uuid: 'user-1',
            name: 'Ana Admin',
            email: 'ana@example.com',
            avatarUrl: '/avatar.jpg',
            isAuthenticated: true,
        };
        const host = mount(
            <Topbar
                lang="en"
                theme="light"
                pageTitle=""
                user={authSignal.value}
            />,
        );

        const removeButton = host.querySelector('.topbar-user-avatar-remove');
        expect(removeButton.textContent).toBe('Remove image');
        removeButton.click();
        await vi.waitFor(() => expect(updateSystemModelRecord).toHaveBeenCalled());

        expect(updateSystemModelRecord).toHaveBeenCalledWith({
            model: 'user.user',
            recordUuid: 'user-1',
            values: { avatar_url: null },
        });
        expect(authSignal.value.avatarUrl).toBeNull();
        render(
            <Topbar
                lang="en"
                theme="light"
                pageTitle=""
                user={authSignal.value}
            />,
            host,
        );
        expect(host.querySelector('.topbar-user-btn img')).toBeNull();
        expect(host.querySelector('.topbar-user-btn .topbar-user-icon')).not.toBeNull();
        expect(host.querySelector('.topbar-user-avatar-btn .topbar-user-icon')).not.toBeNull();
    });

    it('shows dynamic pending count badges only when counts are positive', () => {
        const host = mount(
            <Topbar
                lang="en"
                theme="light"
                pageTitle=""
                pendingCounts={{ messages: 4, notifications: 0 }}
            />,
        );

        expect(host.querySelector('.topbar-action-badge').textContent).toBe('4');
        expect(host.querySelector('[aria-label="Messages (4)"]')).not.toBeNull();
        expect(host.querySelector('[aria-label="Notifications"] .topbar-action-badge')).toBeNull();
    });

    it('caps large pending count badges', () => {
        const host = mount(
            <Topbar
                lang="en"
                theme="light"
                pageTitle=""
                pendingCounts={{ messages: 105, notifications: 12 }}
            />,
        );
        const badges = [...host.querySelectorAll('.topbar-action-badge')].map((badge) => badge.textContent);

        expect(badges).toEqual(['99+', '12']);
    });

    it('disables configured view buttons', () => {
        const host = mount(<Topbar lang="en" theme="light" pageTitle="Messages" showTools
            currentView="list" disabledViews={['kanban']} />);
        expect(host.querySelector('[data-view="kanban"]').disabled).toBe(true);
        expect(host.querySelector('[data-view="list"]').disabled).toBe(false);
    });
});
