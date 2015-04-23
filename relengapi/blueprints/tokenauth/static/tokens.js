/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('tokens', ['relengapi', 'initial_data']);

angular.module('tokens').controller('TokenController',
                                    function($scope, restapi, initial_data) {
    $scope.available_permissions = initial_data.user.permissions;
    $scope.tokens = initial_data.tokens;

    // calculate permissions; it's up to the server to actually *enforce* the
    // permissions -- this is just used to decide which pages to show.
    $scope.can_view = false;
    $scope.can_issue = false;
    angular.forEach(['view', 'issue'], function (action) {
        var re = new RegExp("^base\.tokens\.[^.]*\." + action + "(?:\.my|\.all)?");
        angular.forEach(initial_data.user.permissions, function (perm) {
            if (perm.name.match(re)) {
                $scope['can_' + action] = true;
            }
        });
    });

    $scope.can = function(query_perm) {
        return initial_data.user.permissions.some(function(perm) {
            return perm.name == query_perm;
        });
    };
    $scope.any = function(token_typ) {
        return initial_data.tokens.some(function(token) {
            return token.typ == token_typ;
        });
    };

    // 'can_revoke' := 'can_the_current_user_revoke_any_of_the_active_tokens'
    $scope.can_revoke = false;

    // 'prm' tokens exist & user can revoke
    if ($scope.any('prm') && $scope.can('base.tokens.prm.revoke')) {
        $scope.can_revoke = true;
    }

    // 'usr' tokens exist & user can revoke
    if ($scope.any('usr')) {
        if ($scope.can('base.tokens.usr.revoke.all')) {
            $scope.can_revoke = true;
        } else {
            if ($scope.can('base.tokens.usr.revoke.my')) {
                angular.forEach(initial_data.tokens, function (token) {
                    if (token.user == initial_data.user.authenticated_email) {
                        $scope.can_revoke = true;
                    }
                });
            }
        }
    }

    $scope.canRevokeToken = function(token) {
        if (token.typ == 'usr') {
            if ($scope.can('base.tokens.usr.revoke.all')) {
                return true;
            }
            if ($scope.can('base.tokens.usr.revoke.my')) {
                if (token.user == initial_data.user.authenticated_email) {
                    return true;
                }
            }
        } else {
            return $scope.can('base.tokens.' + token.typ + '.revoke');
        }
    };

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
        typ: '',
        permissions: [],
        description: '',
    };
    // resulting token
    $scope.token = null;

    $scope.can_issue_usr = $scope.can('base.tokens.usr.issue');
    $scope.can_issue_prm = $scope.can('base.tokens.prm.issue');
    $scope.default_typ = $scope.can_issue_usr ? 'usr' : 'prm';
    $scope.newtoken.typ = $scope.default_typ;

    $scope.issueToken = function() {
        var typ = $scope.newtoken.typ
        var permissions = $scope.newtoken.permissions;
        var description = $scope.newtoken.description;

        restapi({
            url: '/tokenauth/tokens',
            method: 'POST',
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            data: JSON.stringify({
                typ: typ,
                permissions: permissions,
                description: description,
            }),
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
