/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('tokens', ['initial_data']);

angular.module('tokens').controller('TokenController',
                                    function($scope, $http, initial_data) {
    $scope.available_permissions = initial_data.user.permissions;
    $scope.tokens = initial_data.tokens;

    // calculate permissions
    $scope.can_view = false;
    $scope.can_issue = false;
    $scope.can_revoke = false;
    angular.forEach(initial_data.user.permissions, function (perm) {
        angular.forEach(['view', 'issue', 'revoke'], function (action) {
            if (perm.name == "base.tokens." + action) {
                $scope['can_' + action] = true;
            }
        });
    });

    if ($scope.can_issue) {
        $scope.view = "newtoken";
    } else {
        $scope.view = "tokenlist";
    }

    $scope.refreshTokens = function() {
        return $http.get('/tokenauth/tokens').then(function (data, status, headers, config) {
            console.log(data.data.result);
            $scope.tokens = data.data.result;
        }, function (data, status, header, config) {
            alertify.error("Failed getting token list: " + data);
        });
    };
});

angular.module('tokens').controller('TokenListController', function($scope, $http) {
    $scope.revokeToken = function(id) {
        $http.delete('/tokenauth/tokens/' + id).then(function() {
            alertify.success("token revoked");
            $scope.refreshTokens();
        }, function (error) {
            alertify.error("token revocation failed");
        });
    };
});

angular.module('tokens').controller('NewTokenController', function($scope, $http) {
    $scope.issuing = false;
    $scope.error = null;
    $scope.newtoken = {
        permissions: {}, // {permission: boolean}
        description: '',
    };
    // resulting token
    $scope.token = null;

    $scope.checkedPermissions = function() {
        var perms = $scope.newtoken.permissions;
        var rv = [];
        for (n in perms) {
            if (perms.hasOwnProperty(n) && perms[n]) {
                rv.push(n);
            }
        }
        return rv;
    };

    $scope.issueToken = function() {
        $scope.issuing = true;

        var permissions = $scope.checkedPermissions();
        var description = $scope.newtoken.description;

        $http({
            url: '/tokenauth/tokens',
            method: 'POST',
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            data: JSON.stringify({permissions: permissions,
                                  description: description})
        }).then(function(response) {
            if (response.data.result.token) {
                $scope.token = response.data.result.token;
                $scope.tokens.push(response.data.result);
                alertify.success("token issued");
            } else {
                $scope.error = "No token received";
            }
        }, function(error) {
            $scope.error = "error from server: " + jqhxr.statusText;
        });
    };

    $scope.reset = function() {
        $scope.newtoken.permissions = {};
        $scope.newtoken.description = '';
        $scope.token = null;
        $scope.error = null;
        $scope.issuing = false;
    }
});
