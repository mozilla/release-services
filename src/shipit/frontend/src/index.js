/* TODO: explain what this file is about
 *
 */

import raven from 'raven-js';
import app from './app';
import { RELEASE_VERSION, RELEASE_CHANNEL, SENTRY_DSN } from './config';

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
    .context(app);
} else {
  app();
}
