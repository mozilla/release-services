/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('relengapi', []);

angular.module('relengapi').config(function($httpProvider) {
    var summarize_config = function(config) {
        var meth = config.method;
        var url = config.url;
        return meth + " " + url;
    };

    // Unlike POST and PUT, Angular doesn't set the content-type for 'patch' by
    // default, but we'd like it to do so
    $httpProvider.defaults.headers.patch['Content-Type'] = $httpProvider.defaults.headers.post['Content-Type'];

    $httpProvider.interceptors.push(function($q) {
        return {
            'request': function(config) {
                if (config.is_restapi_request) {
                    var auth = window.localStorage.getItem('auth');
                    try {
                        auth = JSON.parse(auth);
                    } catch(err) {
                        auth = null;
                    }
                    if (auth != null && auth.access_token) {
                        config.beforeSend = function (xhr) {
                            xhr.setRequestHeader("Authorization", auth.access_token);
                        };
                    }

                    if (config.data) {
                        // Firefox will helpfully produce a clickable rendition of the data
                        console.log("RelengAPI request:", summarize_config(config),
                                    'body', config.data);
                    } else {
                        console.log("RelengAPI request:", summarize_config(config));
                    }
                }
                return config;
            },
            'response': function(response) {
                if (response.config.is_restapi_request) {
                    if (response.data) {
                        console.log("RelengAPI response:", summarize_config(response.config),
                                    'HTTP', response.status, 'body', response.data);
                    } else {
                        console.log("RelengAPI response:", summarize_config(response.config),
                                    'HTTP', response.status);
                    }
                }
                return response;
            },
            'responseError': function(response) {
                if (response.config.is_restapi_request) {
                    var message;
                    if (response.data.error && response.data.error.description) {
                        message = response.data.error.description;
                    } else {
                        message = response.statusText || ("HTTP Status " + response.status);
                    }

                    var action = response.config.while
                                 || (response.config.method + " " + response.config.url);
                    var expectedStatuses = response.config.expectedStatuses
                                           || [response.config.expectedStatus];
                    if (expectedStatuses.indexOf(response.status) == -1) {
                        console.log("RelengAPI call error response:", response.data);
                        alertify.error("Failure while " + action + ": " + message);
                    } else {
                        console.log("RelengAPI response:", summarize_config(response.config),
                                    'HTTP', response.status);
                    }
                }

                return $q.reject(response);
            },
        };
    });

});

angular.module('relengapi').provider('restapi', function() {
    var wrap = function(wrapped, config_pos) {
        return function() {
            var config;
            /* find the (possibly omitted) config argument at config_pos */
            var args = [].slice.apply(arguments);
            if (args.length == config_pos) {
                args.push({});
            }
            config = args[config_pos];

            /* add the flag that our interceptor uses to identify RelengAPI requests */
            config.is_restapi_request = true;

            return wrapped.apply(this, args);
        };
    };

    this.$get = function($http) {
        // wrap the $http provider specifically for access to the backend API
        var relengapi = wrap($http, 0);
        relengapi.get = wrap($http.get, 1);
        relengapi.head = wrap($http.head, 1);
        relengapi.post = wrap($http.post, 2);
        relengapi.put = wrap($http.put, 2);
        relengapi.delete = wrap($http.delete, 1);
        relengapi.jsonp = wrap($http.jsonp, 1);
        relengapi.patch = wrap($http.patch, 2);
        return relengapi;
    };
});

angular.module('relengapi').directive('perm', function(initial_data) {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            'name': '@'
        },
        template: 
            // note the trailing space!
            '<span class="label label-info" ' +
                  'data-toggle="tooltip" data-placement="top" >{{name}}</span> ',
        link: function(scope, elt) {
            elt.tooltip({
                delay: 250,
                title: function() {
                    return initial_data.perms[scope.name];
                },
            });
        }
    };
});
