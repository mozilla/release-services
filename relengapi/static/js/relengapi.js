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
    $httpProvider.interceptors.push(function($q) {
        return {
            'request': function(config) {
                if (config.is_restapi_request) {
                    if (config.data) {
                        // Firefox will helpfully produce a clickable rendition of the data
                        console.log("RelengAPI request:", summarize_config(config),
                                    'body', JSON.parse(config.data));
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
    var wrap = function(wrapped) {
        return function() {
            var config;
            /* find the (possibly omitted) config argument */
            var args = [].slice.apply(arguments);
            if (typeof args[0] === 'string') {
                if (args.length < 2) {
                    args.push({});
                }
                config = args[1];
            } else {
                config = args[0];
            }

            /* add the flag that our interceptor uses to identify RelengAPI requests */
            config.is_restapi_request = true;

            return wrapped.apply(this, args);
        };
    };

    this.$get = function($http) {
        // wrap the $http provider specifically for access to the backend API
        var relengapi = wrap($http);
        relengapi.get = wrap($http.get);
        relengapi.head = wrap($http.head);
        relengapi.post = wrap($http.post);
        relengapi.put = wrap($http.put);
        relengapi.delete = wrap($http.delete);
        relengapi.jsonp = wrap($http.jsonp);
        relengapi.patch = wrap($http.patch);
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
