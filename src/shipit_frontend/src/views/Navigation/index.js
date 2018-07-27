import React from 'react';
import { Navbar, Nav } from 'react-bootstrap';
import { NavLink } from 'react-router-dom';

import CredentialsMenu from '../../views/CredentialsMenu';

export default function Navigation() {
  return (
    <div>
      <Navbar fluid inverse staticTop collapseOnSelect>
        <Navbar.Header>
          <Navbar.Brand>
            <NavLink to="/">Releases</NavLink>
          </Navbar.Brand>
          <Navbar.Brand>
            <NavLink to="/new">New Release</NavLink>
          </Navbar.Brand>
        </Navbar.Header>
        <Nav pullRight>
          <CredentialsMenu />
        </Nav>
      </Navbar>
    </div>
  );
}
