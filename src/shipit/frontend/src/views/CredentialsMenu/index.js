import React from 'react';
import { object } from 'prop-types';
import { Glyphicon, NavDropdown, NavItem } from 'react-bootstrap';
import Auth0LoginMenuItem from '../../components/auth/Auth0LoginMenuItem';

export default class CredentialsMenu extends React.PureComponent {
  static contextTypes = {
    authController: object.isRequired,
  };

  componentDidMount() {
    this.context.authController.on(
      'user-session-changed',
      this.handleUserSessionChanged,
    );
  }

  componentWillUnmount() {
    this.context.authController.off(
      'user-session-changed',
      this.handleUserSessionChanged,
    );
  }

  handleUserSessionChanged = () => {
    this.forceUpdate();
  };

  renderWithoutUser = () => <Auth0LoginMenuItem />;

  renderWithUser(userSession) {
    const { authController } = this.context;
    const icon = userSession.picture ? (
      <img
        alt={userSession.name}
        src={userSession.picture}
        style={{ width: 18, height: 18, borderRadius: 9 }}
      />
    ) : (
      <Glyphicon glyph="user" />
    );
    const title = (
      <span>
        {icon}&nbsp;{userSession.name}
      </span>
    );

    return (
      <NavDropdown id="sign-in-menu" key="sign-in-menu" title={title}>
        <NavItem onSelect={() => authController.setUserSession(null)}>
          <Glyphicon glyph="log-out" /> Sign Out
        </NavItem>
      </NavDropdown>
    );
  }

  render() {
    // note: an update to the userSession will cause a forceUpdate
    const userSession = this.context.authController.getUserSession();

    return userSession
      ? this.renderWithUser(userSession)
      : this.renderWithoutUser();
  }
}
