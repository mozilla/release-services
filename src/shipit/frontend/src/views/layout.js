import {
  Container,
  Navbar,
  NavbarBrand,
  NavbarToggler,
} from 'reactstrap';

export default (model, dispatch, content) => {
  console.log('layout');
  console.log(model);
  console.log(dispatch);
  console.log(content);
  return (
    <div>
      <Navbar color="dark" dark expand="md">
        <Container id="wrapper">
          <NavbarBrand href="/">ShipIt</NavbarBrand>
          <NavbarToggler />
        </Container>
      </Navbar>
    </div>
  );
};
