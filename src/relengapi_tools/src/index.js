import App from '@garbas/mozilla-neo';
import Layout, { routes } from './layout';
import createSagaMiddleware from 'redux-saga';
import { Map, fromJS } from 'immutable';

import * as clobberer from './clobberer';
import * as login from './login';


export const sagas = function*() {
  yield [
    ...clobberer.sagas,
    ...login.sagas
  ]
};

export const reducers = {
  clobberer: clobberer.reducers,
  login: login.reducers
};

export const initialState = {
};

const app_routes = routes.keySeq().map(routeName => {
  let route = routes.get(routeName);
  return {
    path: route.get('path'),
    component: require('./' + routeName).default
  };
}).toJS();

export const sagaMiddleware = createSagaMiddleware()

export const middleware = [
    sagaMiddleware,
];

export default App({
    reducers,
    initialState,
    Layout,
    middleware,
    routes: app_routes
});
