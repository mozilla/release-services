const getConfigFromBody = (name, _default) => {
  let value = document.body.getAttribute(`data-${name}`);
  if (value === null) {
    value = _default;
  }
  if (value === undefined) {
    throw Error(`You need to set "data-${name}"`);
  }
  return value;
};

export const SHIPIT_API_URL = getConfigFromBody('shipit-api-url', JSON.parse(process.env.SHIPIT_API_URL));
export const RELEASE_CHANNEL = getConfigFromBody('release-channel', JSON.parse(process.env.RELEASE_CHANNEL));
export const RELEASE_VERSION = getConfigFromBody('release-version', JSON.parse(process.env.RELEASE_VERSION));
export const SENTRY_DSN = getConfigFromBody('sentry-dsn', JSON.parse(process.env.SENTRY_DSN) || null);
