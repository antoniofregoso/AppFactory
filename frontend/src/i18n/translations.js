/**
 * Dashboard translations — EN / ES
 * To add a new language: add a new key to each translation object.
 */

const translations = {
    // ── Sidebar ──────────────────────────────────────────────────────────────
    'menu.area1':           { en: 'Area 1',       es: 'Área 1' },
    'menu.area2':           { en: 'Area 2',       es: 'Área 2' },
    'menu.area3':           { en: 'Area 3',       es: 'Área 3' },
    'menu.area4':           { en: 'Area 4',       es: 'Área 4' },
    'sidebar.app_name':     { en: 'Dashboard',    es: 'Dashboard' },

    // ── Topbar ───────────────────────────────────────────────────────────────
    'topbar.theme':         { en: 'Theme',         es: 'Tema' },
    'topbar.theme.light':   { en: 'Light',         es: 'Claro' },
    'topbar.theme.dark':    { en: 'Dark',          es: 'Oscuro' },
    'topbar.theme.system':  { en: 'System',        es: 'Sistema' },
    'topbar.lang':          { en: 'Language',      es: 'Idioma' },
    'topbar.account':       { en: 'Account',       es: 'Cuenta' },
    'topbar.settings':      { en: 'Settings',      es: 'Ajustes' },
    'topbar.logout':        { en: 'Log out',       es: 'Cerrar sesión' },
    'topbar.tasks':         { en: 'Tasks',         es: 'Tareas' },
    'topbar.messages':      { en: 'Messages',      es: 'Mensajes' },
    'topbar.notifications': { en: 'Notifications', es: 'Notificaciones' },
    'notifications.panel_title': { en: 'Notifications', es: 'Notificaciones' },
    'notifications.empty':  { en: 'No notifications yet', es: 'Sin notificaciones por ahora' },
    'notifications.close':  { en: 'Close', es: 'Cerrar' },
    'notifications.just_now': { en: 'Just now', es: 'Justo ahora' },
    'notifications.minutes_ago': { en: 'min ago', es: 'min' },
    'notifications.hours_ago': { en: 'h ago', es: 'h' },
    'notifications.days_ago': { en: 'd ago', es: 'd' },
    'notifications.enable_push': { en: 'Enable browser notifications', es: 'Activar notificaciones del navegador' },
    'notifications.disable_push': { en: 'Disable browser notifications', es: 'Desactivar notificaciones del navegador' },
    'notifications.push_blocked': { en: 'Browser notifications are blocked', es: 'Las notificaciones del navegador están bloqueadas' },
    'notifications.push_error': { en: 'Could not enable browser notifications', es: 'No se pudieron activar las notificaciones del navegador' },
    'topbar.tools':         { en: 'Dashboard tools', es: 'Herramientas del dashboard' },
    'topbar.view_type':     { en: 'View type',     es: 'Tipo de vista' },
    'topbar.view.kanban':   { en: 'Kanban',        es: 'Kanban' },
    'topbar.view.list':     { en: 'List',          es: 'Lista' },
    'topbar.view.form':     { en: 'Form',          es: 'Formulario' },
    'topbar.view.calendar': { en: 'Calendar',      es: 'Calendario' },
    'topbar.search':        { en: 'Search',        es: 'Buscar' },
    'topbar.search_placeholder': { en: 'Search...', es: 'Buscar...' },
    'topbar.search_help':   { en: 'How search works', es: 'Cómo funciona la búsqueda' },
    'topbar.search_help_title': { en: 'How search works', es: 'Cómo funciona la búsqueda' },
    'topbar.search_help_intro': {
        en: 'Search tasks and messages by keyword. When AI interpretation is available, it also understands natural-language questions about dates, statuses, and priorities.',
        es: 'Busca tareas y mensajes por palabra clave. Cuando la interpretación con IA está disponible, también entiende preguntas en lenguaje natural sobre fechas, estados y prioridades.'
    },
    'topbar.search_help_examples_title': { en: 'Try queries like:', es: 'Prueba con búsquedas como:' },
    'topbar.search_help_example_1': { en: 'urgent tasks this week', es: 'tareas urgentes de esta semana' },
    'topbar.search_help_example_2': { en: 'pending messages from Antonio', es: 'mensajes pendientes de Antonio' },
    'topbar.search_help_example_3': { en: 'budget meeting', es: 'reunión presupuesto' },
    'topbar.search_help_note': {
        en: "If search needs more information to understand your question, it will ask a follow-up — just type your answer and search again.",
        es: 'Si la búsqueda necesita más información para entender tu pregunta, te hará una pregunta de seguimiento — solo escribe tu respuesta y vuelve a buscar.'
    },
    'topbar.pagination':    { en: 'Pagination',    es: 'Paginación' },
    'topbar.page_prev':     { en: 'Previous page', es: 'Página anterior' },
    'topbar.page_next':     { en: 'Next page',     es: 'Página siguiente' },
    'topbar.page_status':   { en: 'Page 1 of 10',  es: 'Página 1 de 10' },

    // ── Authentication ──────────────────────────────────────────────────────
    'auth.login.aria':      { en: 'Login', es: 'Inicio de sesión' },
    'auth.login.eyebrow':   { en: 'Template workspace', es: 'Espacio de trabajo' },
    'auth.login.title':     { en: 'Sign in to your app', es: 'Inicia sesión en tu aplicación' },
    'auth.login.subtitle':  {
        en: 'A clean starting point to generate modern web applications.',
        es: 'Un punto de partida limpio para crear aplicaciones web modernas.'
    },
    'auth.email':           { en: 'Email', es: 'Correo electrónico' },
    'auth.email.placeholder': { en: 'name@company.com', es: 'nombre@empresa.com' },
    'auth.password':        { en: 'Password', es: 'Contraseña' },
    'auth.password.show':   { en: 'Show password', es: 'Mostrar contraseña' },
    'auth.password.hide':   { en: 'Hide password', es: 'Ocultar contraseña' },
    'auth.remember':        { en: 'Remember me', es: 'Recordarme' },
    'auth.forgot_password': { en: 'Forgot password?', es: '¿Olvidaste tu contraseña?' },
    'auth.sign_in':         { en: 'Sign in', es: 'Iniciar sesión' },
    'auth.signing_in':      { en: 'Signing in…', es: 'Iniciando sesión…' },
    'auth.login.error':     {
        en: 'The email or password is incorrect.',
        es: 'El correo electrónico o la contraseña son incorrectos.'
    },
    'auth.login.unavailable': {
        en: 'The authentication service is unavailable. Please try again shortly.',
        es: 'El servicio de autenticación no está disponible. Inténtalo de nuevo en unos momentos.'
    },
    'auth.reset.aria':      { en: 'Password reset', es: 'Restablecimiento de contraseña' },
    'auth.reset.eyebrow':   { en: 'Account recovery', es: 'Recuperación de cuenta' },
    'auth.reset.title':     { en: 'Reset your password', es: 'Restablece tu contraseña' },
    'auth.reset.subtitle':  {
        en: 'Enter your email address and we’ll send you instructions to reset your password.',
        es: 'Ingresa tu correo electrónico y te enviaremos instrucciones para restablecer tu contraseña.'
    },
    'auth.reset.submit':    { en: 'Send reset instructions', es: 'Enviar instrucciones' },
    'auth.back_to_login':   { en: 'Back to sign in', es: 'Volver al inicio de sesión' },

    // ── Calendar ─────────────────────────────────────────────────────────────
    'calendar.today':       { en: 'Today',        es: 'Hoy' },
    'calendar.month':       { en: 'Month',        es: 'Mes' },
    'calendar.week':        { en: 'Week',         es: 'Semana' },
    'calendar.day':         { en: 'Day',          es: 'Día' },
    'calendar.year':        { en: 'Year',         es: 'Año' },
    'calendar.prev':        { en: 'Previous',     es: 'Anterior' },
    'calendar.next':        { en: 'Next',         es: 'Siguiente' },
    'calendar.all_day':     { en: 'all-day',      es: 'todo el día' },

    // ── Content area ─────────────────────────────────────────────────────────
    'content.area1.title':  { en: 'Area 1',       es: 'Área 1' },
    'content.area2.title':  { en: 'Area 2',       es: 'Área 2' },
    'content.area3.title':  { en: 'Area 3',       es: 'Área 3' },
    'content.area4.title':  { en: 'Area 4',       es: 'Área 4' },
    'content.home.title':   { en: 'Home',         es: 'Inicio' },
    'content.welcome':      { en: 'Welcome to',   es: 'Bienvenido a' },
    'content.placeholder':  {
        en: 'This is a template. Replace this content with your own.',
        es: 'Esta es una plantilla. Reemplaza este contenido con el tuyo.'
    },

    // ── Public home ─────────────────────────────────────────────────────────
    'home.nav.aria':        { en: 'Main navigation', es: 'Navegación principal' },
    'home.login':           { en: 'Log in', es: 'Iniciar sesión' },
    'home.signup':          { en: 'Sign up', es: 'Crear cuenta' },
    'home.signup.soon':     { en: 'Available soon', es: 'Disponible próximamente' },
    'home.eyebrow':         { en: 'A better way to work', es: 'Una mejor forma de trabajar' },
    'home.title':           {
        en: 'Bring your work, team and ideas together.',
        es: 'Reúne tu trabajo, equipo e ideas en un solo lugar.'
    },
    'home.subtitle':        {
        en: 'A flexible workspace designed to help modern teams organize their day and move every project forward.',
        es: 'Un espacio flexible diseñado para organizar el día de equipos modernos e impulsar cada proyecto.'
    },
    'home.cta':             { en: 'Enter your workspace', es: 'Entrar al espacio' },
    'home.learn_more':      { en: 'Explore the experience', es: 'Explorar la experiencia' },
    'home.trust.aria':      { en: 'Product benefits', es: 'Beneficios del producto' },
    'home.trust.secure':    { en: 'Secure', es: 'Seguro' },
    'home.trust.flexible':  { en: 'Flexible', es: 'Flexible' },
    'home.trust.simple':    { en: 'Easy to use', es: 'Fácil de usar' },
    'home.features.eyebrow': { en: 'Built for momentum', es: 'Diseñado para avanzar' },
    'home.features.title':  { en: 'Everything stays within reach', es: 'Todo permanece a tu alcance' },
    'home.feature.organize.title': { en: 'Organize clearly', es: 'Organiza con claridad' },
    'home.feature.organize.text': {
        en: 'Keep projects, tasks and documents in one calm, structured workspace.',
        es: 'Mantén proyectos, tareas y documentos en un espacio ordenado y tranquilo.'
    },
    'home.feature.collaborate.title': { en: 'Work together', es: 'Trabaja en equipo' },
    'home.feature.collaborate.text': {
        en: 'Share context and keep conversations close to the work that matters.',
        es: 'Comparte contexto y mantén las conversaciones cerca del trabajo importante.'
    },
    'home.feature.grow.title': { en: 'Adapt as you grow', es: 'Adáptate al crecer' },
    'home.feature.grow.text': {
        en: 'Shape workflows around your team today and evolve them tomorrow.',
        es: 'Configura flujos para tu equipo de hoy y evoluciónalos mañana.'
    },
    'home.footer.copy':     {
        en: 'A modern workspace for focused teams.',
        es: 'Un espacio moderno para equipos enfocados.'
    },
};

/**
 * Get a translated string.
 * @param {string} key   — translation key (e.g. 'menu.area1')
 * @param {string} lang  — language code: 'en' | 'es'
 * @returns {string}
 */
export function t(key, lang = 'en') {
    const entry = translations[key];
    if (!entry) {
        console.warn(`[i18n] Missing translation for key: "${key}"`);
        return key;
    }
    const shortLang = String(lang).split(/[-_]/)[0];
    return entry[lang] ?? entry[shortLang] ?? entry.en_US ?? entry.en ?? key;
}
