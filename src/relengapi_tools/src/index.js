import App from 'mozilla-neo';
import Layout, { routes } from './layout';

import { reducers as clobbererReducers } from './clobberer';


export const reducers = {
  clobberer: clobbererReducers
};

export const initialState = {
  clobberer: {
    taskcluster: {
      options: [
        { id: 1, title: "One" },
        { id: 2, title: "Two" },
        { id: 3, title: "Three" }
      ]
    },
    buildbot: {
      options: [
        { id: 1, title: "One" },
        { id: 2, title: "Two" },
        { id: 3, title: "Three" }
      ]
    }
  }
};

const app_routes = routes.keySeq().map(routeName => {
  let route = routes.get(routeName);
  return {
    path: route.get('path'),
    component: require('./' + routeName).default
  };
}).toJS();

export default App({
    reducers,
    initialState,
    Layout,
    routes: app_routes
});
