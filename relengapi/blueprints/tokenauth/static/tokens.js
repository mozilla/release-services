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

    $scope.refreshTokens = function() {
        return restapi.get('/tokenauth/tokens', {while: 'refreshing tokens'})
        .then(function (response) {
            $scope.tokens = response.data.result;
        });
    };
});

angular.module('tokens').controller('TokenListController', function($scope, restapi) {
    $scope.enableRevoke = function() {
        $scope.revoke_enabled = true;
    };
    $scope.revokeToken = function(id) {
        restapi.delete('/tokenauth/tokens/' + id, {while: 'revoking token'})
        .then(function() {
            alertify.success("token revoked");
            $scope.refreshTokens();
        });
    };
});

angular.module('tokens').controller('NewTokenController', function($scope, restapi) {
    $scope.newtoken = {
        permissions: [],
        description: '',
    };
    // resulting token
    $scope.token = null;

    $scope.issueToken = function() {
        var permissions = $scope.newtoken.permissions;
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
                $scope.newtoken.permissions = []
                $scope.newtoken.description = '';
                $('#tokenIssuedModal').modal();
            } else {
                alertify.error("No token received");
            }
        });
    };
});

angular.module('tokens').directive('permissionSelector', function() {
    /* select permissions in a table, and require at least one to be selected */
    return {
        restrict: 'E',
        replace: true,
        require: 'ngModel',
        templateUrl: 'static/permissionSelector.html',
        scope: {
            available_permissions: '=permissions',
            permissions: '=ngModel',
        },
        link: function(scope, element, attrs, ctrl) {
            scope.togglePermission = function(perm) {
                var perms = scope.permissions;
                console.log(perms);
                var i = perms.indexOf(perm.name)
                if (i == -1) {
                    perms.push(perm.name);
                } else {
                    perms.splice(i, 1);
                }
                ctrl.$setValidity('permissionsSelector', perms.length != 0);
            };

            // start out invalid
            ctrl.$setValidity('permissionsSelector', false);
        },
    };
});
