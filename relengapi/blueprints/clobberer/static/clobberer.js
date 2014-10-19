/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('clobberer', ['relengapi', 'initial_data']);

angular.module('clobberer').controller('ClobberController',
                                    function($scope, restapi, initial_data) {

    $scope.branches = initial_data.branches;
    $scope.selectedBranch = $scope.branches[0];
});
