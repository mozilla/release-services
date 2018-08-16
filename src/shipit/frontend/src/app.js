import React from 'react';
import spa from 'raj-spa';
import { createRoutes } from 'tagged-routes';
import { program } from 'raj-react';

import createRouter from './router';
import NotFound from './pages/not_found';
import Releases from './pages/releases';

const routes = createRoutes(
  {
    Releases: '/',
  },
  'NotFound',
);

const getRouteProgram = route => routes.Route.match(route, {
  Releases: () => Releases,
  NotFound: () => NotFound,
});

const router = createRouter(routes);
const Spa = spa({
  router,
  getRouteProgram,
  initialProgram: Releases,
});
const App = program(React.Component, () => Spa);

export default App;
