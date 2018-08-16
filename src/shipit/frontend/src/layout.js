import { batchPrograms } from 'raj-compose';
import { union } from 'tagmeme';
import {
  Collapse,
  Container,
  // DropdownItem,
  // DropdownMenu,
  // DropdownToggle,
  Nav,
  NavItem,
  NavLink,
  Navbar,
  NavbarBrand,
  NavbarToggler,
  // UncontrolledDropdown,
} from 'reactstrap';

const Msg = union(['NAV_TOGGLE']);

const init = [{
  show_nav: false,
}];

const update = (msg, model) => Msg.match(msg, {
  NAV_TOGGLE: () => [{ ...model, show_nav: !model.show_nav }],
});

const view = (model, dispatch) => (
  <Navbar color="dark" dark expand="md">
    <Container id="wrapper">
      <NavbarBrand href="/">ShipIt</NavbarBrand>
      <NavbarToggler onClick={() => dispatch(Msg.NAV_TOGGLE())} />
      <Collapse isOpen={model.show_nav} navbar>
        <Nav className="mr-auto" navbar>
          <NavItem>
            <NavLink href="/">Releases</NavLink>
          </NavItem>
          <NavItem>
            <NavLink href="/new">New release</NavLink>
          </NavItem>
        </Nav>
        <Nav className="ml-auto" navbar>
          <NavItem>
            <NavLink href="/login">Login</NavLink>
          </NavItem>
        </Nav>
      </Collapse>
    </Container>
  </Navbar>
);
const navbar = { init, update, view };

export default content => batchPrograms([navbar, content], ([navbarView, contentView]) => (
  <div id="wrapper" className={`page-${content.id}`}>
    {navbarView()}
    <Container>
      <div id="content"><Container>{contentView()}</Container></div>
      <footer>
        <hr />
        <ul>
          <li><a href="https://docs.mozilla-releng.net">Documentation</a></li>
          <li><a href="https://github.com/mozilla/release-services/blob/master/CONTRIBUTING.rst">Contribute</a></li>
          <li><a href="https://github.com/mozilla/release-services/issues/new">Contact</a></li>
        </ul>
      </footer>
    </Container>
  </div>
));
