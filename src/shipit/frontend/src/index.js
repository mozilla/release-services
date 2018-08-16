/* TODO: explain what this file is about
 *
 */

import 'bootstrap/dist/css/bootstrap.min.css';

import raven from 'raven-js';
import { render } from 'react-dom';

import { RELEASE_VERSION, RELEASE_CHANNEL, SENTRY_DSN } from './config';

import './index.css';
import ReactApp from './app';

const loadApp = () => {
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
