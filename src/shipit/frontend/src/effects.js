
const redirectTo = url => () => {
  window.location = url;
};

const redirectToLogin = baseUrl => redirectTo(`${baseUrl}/auth0/login`);

export default options => ({
  redirectTo,
  redirectToLogin: redirectToLogin(options.backendUrl),
});
