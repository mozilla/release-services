/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('auth', ['initial_data', 'relengapi']);

angular.module('auth').controller('AuthController',
                                  function($scope, initial_data) {
    $scope.initial_data = initial_data;
});
