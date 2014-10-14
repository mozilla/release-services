/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('relengapi', []);

angular.module('relengapi').config(function($httpProvider) {
    $httpProvider.interceptors.push(function($q) {
        return {
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
            var args = Array.slice(arguments);
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
/* Add an injector?  Or implement get/post/delete/etc. in a provider? */
