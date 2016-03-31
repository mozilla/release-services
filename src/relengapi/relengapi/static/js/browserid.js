/* this is based on auth.js from Flask-Browserid, with the urls and button ID's hard-coded */
$(function() {
  var gotAssertion, logoutCallback, loginURL, logoutURL;

  gotAssertion = function(assertion) {
    if (assertion) {
      return $.ajax({
        type: 'POST',
        url: '/userauth/login',
        data: {
          assertion: assertion
        },
        success: function(res, status, xhr) {
          return location.reload(true);
        },
        error: function(res, status, xhr) {
          alertify.log("login failure: " + status, 'error', 0);
        }
      });
    }
  };
  logoutCallback = function(event) {
    $.ajax({
      type: 'POST',
      url: '/userauth/logout',
      success: function() {
        return location.reload(true);
      },
      error: function(res, status, xhr) {
        console.log(res);
          alertify.log("logout failure: " + status, 'error', 0);
      }
    });
    return false;
  };
  return $(function() {
    $('#login').click(function() {
      navigator.id.get(gotAssertion);
      return false;
    });
    $('#logout').click(function() {
      navigator.id.logout(logoutCallback);
      return false;
    });
  });
});

