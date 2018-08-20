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

const Msg = union([
  'NAV_TOGGLE',
  'REDIRECT_TO_LOGIN',
]);

const init = [{
  show_nav: false,
}];

// effects -> (msg, model) -> [model, effect]
const update = ({ redirectToLogin }) => (msg, model) => Msg.match(msg, {
  NAV_TOGGLE: () => [{ ...model, show_nav: !model.show_nav }],
  REDIRECT_TO_LOGIN: () => [model, redirectToLogin],
});


const onClickLogin = dispatch => (e) => {
  e.preventDefault();
  e.stopPropagation();
  dispatch(Msg.REDIRECT_TO_LOGIN());
};

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
            <NavLink href="/login" onClick={onClickLogin(dispatch)}>Login</NavLink>
          </NavItem>
        </Nav>
      </Collapse>
    </Container>
  </Navbar>
);
const createNavbarProgram = (options, effects) => ({ init, update: update(effects), view });

export default createMainProgram => (options, effects) => {
  const navbar = createNavbarProgram(options, effects);
  const main = createMainProgram(options, effects);
  const mainClassName = main.name === undefined ? 'page-unknown-name' : `page-${main.name}`;
  return batchPrograms(
    [navbar, main],
    ([navbarView, contentView]) => (
      <div id="wrapper" className={mainClassName}>
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
            <div>Version: <a href={`https://github.com/mozilla/release-services/releases/tag/v${options.releaseVersion}`}>v{options.releaseVersion}</a></div>
          </footer>
        </Container>
      </div>
    ),
  );
};

