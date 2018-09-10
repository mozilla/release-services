module.exports = {
  API_URL: process.env.SHIPIT_API_URL || 'https://shipit-api.mozilla-releng.net',
  TREEHERDER_URL: 'https://treeherder.mozilla.org',
  TASKCLUSTER_TOOLS_URL: 'https://tools.taskcluster.net',
  AUTH0: {
    domain: 'auth.mozilla.auth0.com',
    clientID: '2dXygwTNP3p7iLTSaEWbdoiJFkjSBqm4',
    redirectUri: new URL('/login', window.location).href,
    scope: 'full-user-credentials openid profile email',
  },
  PRODUCTS: [
    {
      product: 'firefox',
      prettyName: 'Firefox Desktop',
      appName: 'browser',
      branches: [
        {
          prettyName: 'Beta',
          project: 'mozilla-beta',
          branch: 'releases/mozilla-beta',
          repo: 'https://hg.mozilla.org/releases/mozilla-beta',
        },
      ],
      enablePartials: true,
    },
    {
      product: 'fennec',
      prettyName: 'Firefox Mobile',
      // TODO: The actual appName is `mobile/android` but it gets the version from `browser`.
      appName: 'browser',
      branches: [
        {
          prettyName: 'Beta',
          project: 'mozilla-beta',
          branch: 'releases/mozilla-beta',
          repo: 'https://hg.mozilla.org/releases/mozilla-beta',
        },
      ],
      enablePartials: false,
    },
    {
      product: 'devedition',
      prettyName: 'Firefox Developer Edition',
      appName: 'browser',
      branches: [
        {
          prettyName: 'Beta',
          project: 'mozilla-beta',
          branch: 'releases/mozilla-beta',
          repo: 'https://hg.mozilla.org/releases/mozilla-beta',
        },
      ],
      enablePartials: true,
    },
  ],
};
