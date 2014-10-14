/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('tokens', ['relengapi', 'initial_data']);

angular.module('tokens').controller('TokenController',
                                    function($scope, restapi, initial_data) {
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
        return restapi.get('/tokenauth/tokens', {while: 'refreshing tokens'})
        .then(function (response) {
            $scope.tokens = response.data.result;
        });
    };
});

angular.module('tokens').controller('TokenListController', function($scope, restapi) {
    $scope.revokeToken = function(id) {
        restapi.delete('/tokenauth/tokens/' + id, {while: 'revoking token'})
        .then(function() {
            alertify.success("token revoked");
            $scope.refreshTokens();
        });
    };
});

angular.module('tokens').controller('NewTokenController', function($scope, restapi) {
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

        restapi({
            url: '/tokenauth/tokens',
            method: 'POST',
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            data: JSON.stringify({permissions: permissions,
                                  description: description}),
            while: 'issuing token',
        }).then(function(response) {
            if (response.data.result.token) {
                $scope.token = response.data.result.token;
                $scope.tokens.push(response.data.result);
                alertify.success("token issued");
            } else {
                $scope.error = "No token received";
            }
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
