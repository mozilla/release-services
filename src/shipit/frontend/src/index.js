/* TODO: explain what this file is about
 *
 */

import 'bootstrap/dist/css/bootstrap.min.css';

import React from 'react';
import createHistory from 'history/createBrowserHistory';
import raven from 'raven-js';
import { program } from 'raj-react';
import { render } from 'react-dom';

import './index.css';
import createApp from './app';
import { RELEASE_VERSION, RELEASE_CHANNEL, SENTRY_DSN } from './config';

const loadApp = () => {
  const history = createHistory();
  const App = createApp({
    history,
    releaseVersion: RELEASE_VERSION,
    releaseChannel: RELEASE_CHANNEL,
  });
  const ReactApp = program(React.Component, () => App);
  render(<ReactApp />, document.getElementById('root'));
};

if (SENTRY_DSN !== null) {
  raven
    .config(SENTRY_DSN, {
      debug: true,
      release: RELEASE_VERSION,
      environment: RELEASE_CHANNEL,
      tags: {
        server_name: 'mozilla/release-services',
        site: 'shipit/frontend',
      },
    })
    .install()
    .context(loadApp);
} else {
  loadApp();
}
