
const redirectTo = url => () => {
  window.location = url;
};

const redirectToLogin = baseUrl => redirectTo(`${baseUrl}/auth0/login`);

const listReleases = api => params => (SuccessMsg, FailureMsg) => (dispatch) => {
  console.log('== LIST RELEASES ==');
  api.get('/releases', params)
    .then((response) => { dispatch(SuccessMsg(response)); })
    .catch((error) => { dispatch(FailureMsg(error)); });
};

export default options => ({
  redirectTo,
  redirectToLogin: redirectToLogin(options.backendUrl),
  listReleases: listReleases(options.backendApi),
});
