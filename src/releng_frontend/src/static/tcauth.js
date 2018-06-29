(function() {

window.tcauth = {};

window.tcauth.get_header = function(url, method) {
    var tc_auth = window.localStorage.getItem('tc_auth');

    try {
        tc_auth = JSON.parse(tc_auth);
    } catch(err) {
        tc_auth = null;
    }

    if (tc_auth == null) {
        return '';
    }

    if (tc_auth.credentials &&
        tc_auth.credentials.clientId &&
        tc_auth.credentials.accessToken) {

        var extData = null;
        if (tc_auth.credentials.certificate) {
            extData = new buffer.Buffer(JSON.stringify({
                certificate: JSON.parse(tc_auth.credentials.certificate)
            })).toString('base64');
        }

        var header = hawk.client.header(
            url,
            method || 'GET',
            {
                credentials: {
                    id: tc_auth.credentials.clientId,
                    key: tc_auth.credentials.accessToken,
                    algorithm: 'sha256'
                },
                ext: extData,
            }
        );
    };

    return header.field;
};

window.tcauth.setup = function(service, default_service_url) {
    var $login = $('#login');
    var $loggedin = $('#loggedin');
    var $logout= $('#logout');
    var $email = $('#email');
    var service_url = $('body').attr('data-releng-' + service + '-url') || default_service_url;

    var auth = window.localStorage.getItem('auth');

    try {
        auth = JSON.parse(auth);
    } catch(err) {
        auth = null;
    }
    if (auth != null && auth.access_token) {
        $.ajax({
            url: 'https://login.taskcluster.net/v1/oidc-credentials/mozilla-auth0',
            async: false,
            beforeSend: function (xhr) {
                xhr.setRequestHeader("Authorization", "Bearer " + auth.access_token);
            },
            error: function(xhr, status, error) {
            },
            success: function(data, status, xhr) {
                $email.html('<span>' + data.credentials.clientId + '</span>' + '<span class="caret"></span/>');
                $login.toggleClass('hidden');
                $loggedin.toggleClass('hidden');
                window.localStorage.setItem('tc_auth', JSON.stringify(data));
                $.ajax({
                    url: service_url + '/init',
                    async: false,
                    beforeSend: function (xhr, config) {
                        xhr.setRequestHeader("Authorization", tcauth.get_header(config.url, config.method));
                    },
                    success: function(data, status, xhr) {
                        angular.module('initial_data', []).constant('initial_data', data || {});
                    }
                });
            }
        });
    } else {
        angular.module('initial_data', []).constant('initial_data', {});
    }

    $login.on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var url = $('body').attr('data-releng-treestatus-url') || 'https://localhost:8000';
        $.ajax({
            url: url + '/auth0/login',
            error: function(xhr, status, error) {
            },
            success: function(redirect_url, status, xhr) {
                window.location = redirect_url;
            }

        });
    });

    $logout.on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        window.localStorage.removeItem('auth');
        window.localStorage.removeItem('tc_auth');
        window.location.reload();
    });
};

})();
