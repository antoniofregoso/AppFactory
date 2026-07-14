import { appSignal } from '../appStore';

export const contextActions = {

    setTheme(theme) {
        appSignal.value = {
            ...appSignal.value,
            context: {
                ...appSignal.value.context,
                theme,
            },
        };
    },

    setLang(lang) {
        appSignal.value = {
            ...appSignal.value,
            context: {
                ...appSignal.value.context,
                lang,
            },
        };
    },

    toggleSidebar() {
        appSignal.value = {
            ...appSignal.value,
            context: {
                ...appSignal.value.context,
                sidebar_expanded: !appSignal.value.context.sidebar_expanded,
            },
        };
    },

    setActiveArea(area) {
        appSignal.value = {
            ...appSignal.value,
            context: {
                ...appSignal.value.context,
                active_area: area,
            },
        };
    },
};
