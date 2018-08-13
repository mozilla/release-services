/* TODO: explain what this file is about
 *
 */
import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import raven from 'raven-js';
import { render } from 'react-dom';
import { Provider } from 'react-redux';
import { createStore } from 'redux';

import App from './app';
import { SENTRY_DSN } from './config';

// import actions from './actions';
const initialState = {};
function reducer(state = initialState, action) {
  switch (action.type) {
    default:
      return state;
  }
}


const store = createStore(
  reducer,
  initialState,
  /* eslint-disable no-underscore-dangle */
  window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  /* eslint-enable */
);
const root = document.getElementById('root');

const load = () => {
  render(
    <Provider store={store}>
      <App />
    </Provider>,
    root,
  );
};

// When SENTRY_DSN is configured send logs to Sentry
if (SENTRY_DSN !== null) {
  raven
    .config(
      SENTRY_DSN,
      {
        debug: true,
        // release: RELEASE_VERSION,
        // environment: RELEASE_CHANNEL,
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
