import App from '@garbas/mozilla-neo';
import Layout, { routes } from './layout';
import createSagaMiddleware from 'redux-saga';
import * as clobberer from './clobberer';


export const sagas = function*() {
  yield [
    ...clobberer.sagas
  ]
};

export const sagaMiddleware = createSagaMiddleware()

export const middleware = [
    sagaMiddleware
];

export const reducers = {
  clobberer: clobberer.reducers
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

export default App({
    reducers,
    initialState,
    Layout,
    middleware,
    routes: app_routes
});
