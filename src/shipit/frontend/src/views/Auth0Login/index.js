import React from 'react';
import Error from '../../components/Error';
import { webAuth, userSessionFromAuthResult } from '../../components/auth/auth0';

export default class Auth0Login extends React.PureComponent {
  state = {};

  /* eslint-disable consistent-return */
  componentDidMount() {
    const { history } = this.props;

    if (!window.location.hash) {
      return webAuth.authorize();
    }

    // for silent renewal, auth0-js opens this page in an iframe, and expects
    // a postMessage back, and that's it.
    if (window !== window.top) {
      window.parent.postMessage(window.location.hash, window.origin);

      return;
    }

    webAuth.parseHash(window.location.hash, (loginError, authResult) => {
      if (loginError) {
        return this.setState({ loginError });
      }

      this.props.setUserSession(userSessionFromAuthResult(authResult));

      if (window.opener) {
        window.close();
      } else {
        history.push('/');
      }
    });
  }

  render() {
    if (this.state.loginError) {
      return <Error error={this.state.loginError} />;
    }

    if (window.location.hash) {
      return <p>Logging in..</p>;
    }

    return <p>Redirecting..</p>;
  }
}
