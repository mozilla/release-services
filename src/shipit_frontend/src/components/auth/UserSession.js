import { OIDCCredentialAgent } from 'taskcluster-client-web';

/**
 * An object representing a user session.  Tools supports a variety of login methods,
 * so this combines them all in a single representation.
 *
 * UserSessions are immutable -- when anything about the session changes, a new instance
 * replaces the old.  The `userChanged` method is useful to distinguish changes to the
 * user identity from mere token renewals.
 *
 * Common properties are:
 *
 * - type - 'oidc' or 'credentials'
 * - name - user name
 * - clientArgs - arguments to pass to taskcluster-client-web Client constructors
 * - renewAfter - date (Date or string) after which this session should be renewed,
 *                if applicable
 *
 * When type is 'oidc':
 *
 * - oidcProvider -- the provider (see taskcluster-login)
 * - accessToken -- the accessToken to pass to taskcluster-login
 * - fullName -- user's full name
 * - picture -- URL of an image of the user
 * - oidcSubject -- the 'sub' field of the id_token (useful for debugging user issues)
 *
 * When the type is 'credentials':
 *
 * - credentials -- the Taskcluster credentials (with or without a certificate)
 *
 * To fetch Taskcluster credentials for the user regardless of type, use the getCredentials
 * method.
 */
export default class UserSession {
  constructor(options) {
    Object.assign(this, options);

    if (this.accessToken) {
      this.credentialAgent = new OIDCCredentialAgent({
        accessToken: this.accessToken,
        oidcProvider: this.oidcProvider,
      });
    }
  }

  static fromOIDC(options) {
    return new UserSession({ type: 'oidc', ...options });
  }

  // get the user's name
  get name() {
    return (
      this.fullName ||
      'unknown'
    );
  }

  static deserialize(value) {
    return new UserSession(JSON.parse(value));
  }

  serialize() {
    return JSON.stringify({ ...this, credentialAgent: undefined });
  }
}
