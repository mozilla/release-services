import React from 'react';
import { object } from 'prop-types';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import { Helmet } from 'react-helmet';
import { Grid } from 'react-bootstrap';

import iconUrl from './shipit.png';
import PropsRoute from '../components/PropsRoute';
import AuthController from '../components/auth/AuthController';
import Navigation from '../views/Navigation';
import NewRelease from '../views/NewRelease';
import ListReleases from '../views/ListReleases';
import NotFound from '../components/NotFound';
import Auth0Login from '../views/Auth0Login';
import Spinner from '../components/Spinner';

export default class App extends React.Component {
  /* TODO: decouple auth from App */
  static childContextTypes = {
    authController: object.isRequired,
  };

  constructor(props) {
    super(props);
    this.authController = new AuthController();
    this.state = {
      authReady: false,
    };
  }

  getChildContext() {
    return {
      authController: this.authController,
    };
  }

  componentWillMount() {
    this.authController.on(
      'user-session-changed',
      this.handleUserSessionChanged,
    );

    // we do not want to automatically load a user session on the login views; this is
    // a hack until they get an entry point of their own with no UI.
    if (!window.location.pathname.startsWith('/login')) {
      this.authController.loadUserSession();
    } else {
      this.setState({ authReady: true });
    }
  }

  componentWillUnmount() {
    this.authController.removeListener(
      'user-session-changed',
      this.handleUserSessionChanged,
    );
  }

  handleUserSessionChanged = (userSession) => {
    // Consider auth "ready" when we have no userSession, a userSession with no
    // renewAfter, or a renewAfter that is not in the past.  Once auth is
    // ready, it never becomes non-ready again.
    const authReady =
      this.state.authReady ||
      !userSession ||
      !userSession.renewAfter ||
      new Date(userSession.renewAfter) > new Date();

    this.setState({ authReady });
  };

  render() {
    const { authReady } = this.state;
    const { authController } = this;

    return (
      <Router>
        <div>
          <Helmet>
            <link rel="shortcut icon" type="image/png" href={iconUrl} />
          </Helmet>
          <PropsRoute component={Navigation} />
          <Grid fluid id="container">
            {authReady ? (
              <Switch>
                <PropsRoute path="/" exact component={ListReleases} />
                <PropsRoute
                  path="/login"
                  component={Auth0Login}
                  setUserSession={authController.setUserSession}
                />
                <PropsRoute path="/new" component={NewRelease} />
                <Route component={NotFound} />
              </Switch>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <Spinner />
                <br />
                Authenticating...
              </div>
            )}
          </Grid>
        </div>
      </Router>
    );
  }
}
