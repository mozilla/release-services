/* TODO: explain what this file is about
 *
 */

import React from 'react';
import raven from 'raven-js';
import { program } from 'raj-react';
import { render } from 'react-dom';

import App from './app';
import { RELEASE_VERSION, RELEASE_CHANNEL, SENTRY_DSN } from './config';

const Root = program(React.Component, () => App);

const loadApp = () => {
  render(<Root />, document.getElementById('root'));
};

if (SENTRY_DSN !== null) {
  raven
    .config(SENTRY_DSN, {
      debug: true,
      release: RELEASE_VERSION,
      environment: RELEASE_CHANNEL,
      tags: {
        server_name: 'mozilla/release-services',
        site: 'shipit/frontend'
      }
    })
    .install()
    .context(loadApp);
} else {
  loadApp();
}
