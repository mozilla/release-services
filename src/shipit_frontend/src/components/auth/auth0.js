import { fromNow } from 'taskcluster-client-web';
import { WebAuth } from 'auth0-js';
import UserSession from './UserSession';
import config from '../../config';

export const webAuth = new WebAuth({
  domain: config.AUTH0.domain,
  clientID: config.AUTH0.clientID,
  redirectUri: config.AUTH0.redirectUri,
  audience: `https://${config.AUTH0.domain}/api/v2/`,
  responseType: 'token id_token',
  scope: config.AUTH0.scope,
});

export function userSessionFromAuthResult(authResult) {
  return UserSession.fromOIDC({
    oidcProvider: 'mozilla-auth0',
    accessToken: authResult.accessToken,
    fullName: authResult.idTokenPayload.name,
    email: authResult.idTokenPayload.email,
    picture: authResult.idTokenPayload.picture,
    oidcSubject: authResult.idTokenPayload.sub,
    // per https://wiki.mozilla.org/Security/Guidelines/OpenID_connect#Session_handling
    renewAfter: fromNow('15 minutes'),
  });
}

/* eslint-disable consistent-return */
export async function renew({ userSession, authController }) {
  if (
    !userSession ||
    userSession.type !== 'oidc' ||
    userSession.oidcProvider !== 'mozilla-auth0'
  ) {
    return;
  }

  return new Promise((accept, reject) =>
    webAuth.renewAuth({}, (err, authResult) => {
      if (err) {
        return reject(err);
      } else if (!authResult) {
        return reject(new Error('no authResult'));
      }

      authController.setUserSession(userSessionFromAuthResult(authResult));
      accept();
    }));
}
