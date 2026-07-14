import { renderPasswordReset } from '../components';
import { currentLang } from '../store';
import { resetAppRoot } from '../utils';

export function passwordReset(req, router){

    const appEl = document.getElementById('app');

    // Home/Login render with Preact — unmount any previous Preact tree
    // before taking over #app with a raw HTML string.
    resetAppRoot(appEl);
    appEl.innerHTML = renderPasswordReset(currentLang.value);
}
