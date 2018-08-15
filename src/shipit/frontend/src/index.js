/* TODO: explain what this file is about
 *
 */
import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import createSagaMiddleware from 'redux-saga';
import raven from 'raven-js';
import { ConnectedRouter, routerMiddleware, connectRouter } from 'connected-react-router';
import { Provider } from 'react-redux';
import { Route, Switch } from 'react-router';
import { applyMiddleware, compose, createStore } from 'redux';
import { createBrowserHistory } from 'history';
import { render } from 'react-dom';

import Releases from './pages/releases';
import {
  RELEASE_VERSION,
  RELEASE_CHANNEL,
  SENTRY_DSN,
} from './config';


// import { AUTH0_KEY, TASKCLUSTER_KEY } from './localstorage';
const AUTH0_KEY = 'auth-auth0';
const TASKCLUSTER_KEY = 'auth-taskcluster';

// import actions from './actions';
const initialState = {
  auth0: localStorage.getItem(AUTH0_KEY),
  taskclusterAuth: localStorage.getItem(TASKCLUSTER_KEY),
};
function reducer(state = initialState, action) {
  switch (action.type) {
    default:
      return state;
  }
}


// import sagas from './sagas';
function* sagas() {
  yield;
}


const history = createBrowserHistory();
const sagaMiddleware = createSagaMiddleware();
/* eslint-disable no-underscore-dangle */
const composeEnhancer = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
/* eslint-enable */
const store = createStore(
  connectRouter(history)(reducer),
  initialState,
  composeEnhancer(applyMiddleware(routerMiddleware(history), sagaMiddleware)),
);

sagaMiddleware.run(sagas);

// TODO: more routes
// <Route path="/new" component={NewRelease} />
// <Route path="/login" component={Login} />
// <Route component={ErrorPage} />
const load = () => {
  render(
    <Provider store={store}>
      <ConnectedRouter history={history}>
        <Switch>
          <Route exact path="/" component={Releases} />
        </Switch>
      </ConnectedRouter>
    </Provider>,
    document.getElementById('root'),
  );
};

// When SENTRY_DSN is configured send logs to Sentry
if (SENTRY_DSN !== null) {
  raven
    .config(
      SENTRY_DSN,
      {
        debug: true,
        release: RELEASE_VERSION,
        environment: RELEASE_CHANNEL,
        tags: {
          server_name: 'mozilla/release-services',
          site: 'shipit/frontend',
        },
      },
    )
    .install()
    .context(load);
} else {
  load();
}
