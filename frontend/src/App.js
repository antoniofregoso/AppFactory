import { Router } from '@customerjourney/cj-router';
import { home, login, passwordReset, dashboard } from './app/pages';

export const App = new Router();
App.on('/', home);
App.on('/login', login).setName("login");
App.on('/password_reset', passwordReset)
App.on('/dashboard', dashboard).setName("dash");
App.on('/dashboard/{area}', dashboard);
App.on('/dashboard/{area}/{model}', dashboard);
App.on('/dashboard/{area}/{model}/{uuid}', dashboard);
 
