fs = require('fs');

const envs = {
    //XXX once migrate away from using in code configuration we remove CONFIG env
    CONFIG: process.env.CONFIG || 'staging',
    SHIPIT_WORKFLOW_URL: process.env.SHIPIT_WORKFLOW_URL,
    RELEASE_CHANNEL: process.env.RELEASE_CHANNEL,
    RELEASE_VERSION: process.env.RELEASE_VERSION,
    SENTRY_DSN: process.env.SENTRY_DSN || null,
    HOST: process.env.HOST,
    PORT: process.env.PORT,
};

// Set environment variables to their default values if not defined
Object.keys(envs).forEach(env => {
  if (envs[env] !== undefined) {
    process.env[env] = envs[env];
  }
});

// HTTPS can be disabled by setting HTTPS_DISABLED environment variable to
// true. Otherwise it will enforced either using automatically generated
// certificates or pre-generated ones.
const HTTPS = process.env.HTTPS_DISABLED ? false :
  (process.env.SSL_CERT && process.env.SSL_KEY && process.env.SSL_CACERT) ?
    {
      cert: fs.readFileSync(process.env.SSL_CERT),
      key: fs.readFileSync(process.env.SSL_KEY),
      ca: fs.readFileSync(process.env.SSL_CACERT)
    }
    : true;

module.exports = {
  use: [
    '@neutrinojs/jest',
    '@neutrinojs/hot',
    [
      '@neutrinojs/airbnb',
      {eslint: {
        rules: {
            'react/jsx-filename-extension': [1, { 'extensions': ['.js'] }],
            'react/prop-types': 'off',
            'react/no-multi-comp': 'off',
            'no-console': 'off',
          }
        }
      }
    ],
    [
      '@neutrinojs/react',
      {
        html: {
          title: 'Ship-it!',
          mobile: true,
          meta: [
            {
              name: 'description',
              content: 'Web interface for starting and managing Firefox releases'
            },
            {
              name: 'author',
              content: 'Mozilla Release Engineering Team'
            }
          ]
        },
        devServer: {
          host: envs.HOST,
          port: envs.PORT,
          https: HTTPS,
          disableHostCheck: true,
          historyApiFallback: {
            rewrites: [
              { from: '__heartbeat__', to: 'views/ok.html' },
              { from: '__lbheartbeat__', to: 'views/ok.html' },
              { from: '__version__', to: 'views/version.json' },
            ],
          },
        },
      }
    ],
    ['@neutrinojs/env', Object.keys(envs)],
    (neutrino) => {
        neutrino.config.when(process.env.NODE_ENV === 'production', config => {
            config.devtool('source-map');
        });
    }
  ]
};
