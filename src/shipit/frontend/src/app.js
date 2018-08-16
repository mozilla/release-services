import createSPA from 'raj-spa';
import { createRoutes } from 'tagged-routes';

import NotFound from './program/not_found';
import Releases from './program/releases';
import createRouter from './router';


const routes = createRoutes(
  {
    Releases: '/',
    Error: '/404',
  },
  'NotFound',
);

const routeToProgram = flags => route => routes.Route.match(route, {
  Releases: () => Releases,
  NotFound: () => NotFound,
  Error: () => Error,
})(flags);

export default flags => createSPA({
  router: createRouter(flags.history, routes),
  getRouteProgram: routeToProgram(flags),
  initialProgram: Releases(flags),
  errorProgram: Error(flags),
});


// const navigateToUrl = url => () => {
//   history.push(url);
// };
