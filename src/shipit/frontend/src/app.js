import createSPA from 'raj-spa';
import { createRoutes } from 'tagged-routes';

import NotFound from './program/not_found';
import Releases from './program/releases';
import createRouter from './router';
import createEffects from './effects';


const routes = createRoutes(
  {
    Releases: '/',
    Error: '/404',
  },
  'NotFound',
);

const routeToProgram = (options, effects) => route => routes.Route.match(route, {
  Releases: () => Releases,
  NotFound: () => NotFound,
  Error: () => Error,
})(options, effects);

export default (options) => {
  const effects = createEffects(options);
  return createSPA({
    router: createRouter(options.history, routes),
    getRouteProgram: routeToProgram(options, effects),
    initialProgram: Releases(options, effects),
    errorProgram: Error(options, effects),
  });
};


// const navigateToUrl = url => () => {
//   history.push(url);
// };
