/* TODO: explain what this file is about
 *
 */
import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import raven from 'raven-js';
import { render } from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware } from 'redux';
import { BrowserRouter, Route } from 'react-router-dom';
import createSagaMiddleware from 'redux-saga';
import { composeWithDevTools } from 'redux-devtools-extension';

import App from './app';
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

const sagaMiddleware = createSagaMiddleware();
const store = createStore(
  reducer,
  initialState,
  composeWithDevTools(applyMiddleware(sagaMiddleware)),
);

sagaMiddleware.run(sagas);

const load = () => {
  render(
    <Provider store={store}>
      <BrowserRouter>
        <Route path="/" component={App} />
      </BrowserRouter>
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
