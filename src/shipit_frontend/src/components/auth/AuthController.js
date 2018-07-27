import mitt from 'mitt';
import UserSession from './UserSession';

import { renew as auth0Renew } from './auth0';

/**
 * Controller for authentication-related pieces of the site.
 *
 * This encompasses knowledge of which authentication mechanisms are enabled, including
 * credentials menu items, ongoing expiration monitoring, and any additional required UI.
 * It also handles synchronizing sign-in status across tabs.
 */
export default class AuthController {
  constructor() {
    const events = mitt();

    this.on = events.on;
    this.off = events.off;
    this.emit = events.emit;

    this.renewalTimer = null;

    window.addEventListener('storage', ({ storageArea, key }) => {
      if (storageArea === localStorage && key === 'userSession') {
        this.loadUserSession();
      }
    });
  }

  /**
   * Reset the renewal timer based on the given user session.
   */
  resetRenewalTimer(userSession) {
    if (this.renewalTimer) {
      window.clearTimeout(this.renewalTimer);
      this.renewalTimer = null;
    }

    if (userSession && userSession.renewAfter) {
      let timeout = Math.max(0, new Date(userSession.renewAfter) - new Date());

      // if the timeout is in the future, apply up to a few minutes to it
      // randomly.  This avoids multiple tabs all trying to renew at the
      // same time.
      if (timeout > 0) {
        timeout += Math.random() * 5 * 60 * 1000;
      }

      this.renewalTimer = window.setTimeout(() => {
        this.renewalTimer = null;
        this.renew({ userSession });
      }, timeout);
    }
  }

  /**
   * Load the current user session (from localStorage).
   *
   * This will emit the user-session-changed event, but does not
   * return the user session.
   */
  loadUserSession() {
    const storedUserSession = localStorage.getItem('userSession');
    const userSession = storedUserSession
      ? UserSession.deserialize(storedUserSession)
      : null;

    this.userSession = userSession;
    this.resetRenewalTimer(userSession);
    this.emit('user-session-changed', userSession);
  }

  /**
   * Get the current userSession instance
   */
  getUserSession() {
    return this.userSession;
  }

  /**
   * Set the current user session, or (if null) delete the current user session.
   *
   * This will change the user session in all open windows/tabs, eventually triggering
   * a call to any onSessionChanged callbacks.
   */
  setUserSession = (userSession) => {
    if (!userSession) {
      localStorage.removeItem('userSession');
    } else {
      localStorage.setItem('userSession', userSession.serialize());
    }

    // localStorage updates do not trigger event listeners on the current window/tab,
    // so invoke it directly
    this.loadUserSession();
  };

  /**
   * Renew the user session.  This is not possible for all auth methods, and will trivially succeed
   * for methods that do not support it.  If it fails, the user will be logged out.
   */
  async renew({ userSession }) {
    try {
      await auth0Renew({ userSession, authController: this });
    } catch (err) {
      this.setUserSession(null);
    }
  }
}
