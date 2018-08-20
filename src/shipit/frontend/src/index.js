import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import React from 'react';
import raven from 'raven-js';
import { render } from 'react-dom';
import App from './App';
import {
  BACKEND_URL,
  RELEASE_CHANNEL,
  RELEASE_VERSION,
  SENTRY_DSN,
} from './config';

const root = document.getElementById('root');
const load = () => {
  render(
    <App
      backend_url={BACKEND_URL}
      release_version={RELEASE_VERSION}
      release_channel={RELEASE_CHANNEL}
    />,
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
