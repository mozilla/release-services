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

const routeToProgram = route => routes.Route.match(route, {
  Releases: () => Releases,
  NotFound: () => NotFound,
  Error: () => Error,
});

export default ({ history }) => createSPA({
  router: createRouter(history, routes),
  getRouteProgram: routeToProgram,
  initialProgram: Releases,
  errorProgram: Error,
});


// import navbar from './programs/navbar';

// //
// //
// // const getRouteProgram = route => routes.Route.match(route, {
// //   Releases: () => Releases,
// //   NotFound: () => NotFound,
// // });
// //
// // const router = createRouter(routes);
//
//
//
// // -- EFFECTS --
//
// // const navigateToUrl = url => () => {
// //   history.push(url);
// // };
//
//
// // -- MESSAGES --
//
// export const Msg = union([
//   'SET_LOCATION',
//   'LAYOUT',
// ]);
//
// const programs = {
//   layout: mapProgram(layout, msg => Msg.LAYOUT(msg)),
// };
//
// export const init = effects => [
//   {
//     location: null,
//     auth: {
//       auth0: null, // null or { ??? }
//       taskcluster: null, // null or { ??? }
//     },
//     layout: layout.init[0],
//   },
//   effects.setLocation,
// ];
//
// export const update = effects => (msg, model) => {
//   console.log('--UPDATE--');
//   console.log('MSG', msg);
//   console.log('MODEL', model);
//   const [newModel, newEffect] = Msg.match(msg, {
//     SET_LOCATION: location => ([{ ...model, location }]),
//     LAYOUT: (subMsg) => {
//       const [layoutModel, layoutEffect] = layout.update(subMsg, model.layout);
//       return [{ ...model, layout: layoutModel }, mapEffect(layoutEffect, layoutMsg)];
//     },
//   });
//   console.log('NEW MODEL', newModel);
//   console.log('NEW EFFECT', newEffect);
//   return [newModel, newEffect];
// };
//
// export const view = effects => (model, dispatch) => {
//   console.log('--VIEW--');
//   console.log('MODEL', model);
//   console.log('DISPATCH', dispatch);
//   return <div>WORKS</div>;
// };
//
// const effects = ({ history }) => ({
//   initRouting: dispatch =>
//   setLocation: dispatch => dispatch(Msg.SET_LOCATION(history.location)),
//   navigateTo: url => dispatch => {
//     history.push(url);
//     dispatch(Msg.SET_LOCATION(history.location));
//   },
// });
//
