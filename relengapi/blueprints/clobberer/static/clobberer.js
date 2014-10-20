/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('clobberer', ['relengapi', 'initial_data']);

angular.module('clobberer').controller('ClobberController',
                                    function($scope, restapi, initial_data) {

    $scope.branches = initial_data.branches;
    $scope.selectedBranch = initial_data.selected_branch || $scope.branches[0];
 
    $scope.selectedBuilders = undefined;
  
    /* When a user selects a new branch. */ 
    $scope.expandBranch = function(branch) {
        $scope.selectedBuilders = {};
        $scope.selectAllBuilders = false; 
        $scope.branchData = 'loading';
        
        restapi.get(initial_data.lastclobber_by_builder_url + branch,
                {while: 'fetching data', expected_status: 404})
        .then(function (data, status, headers, config) {
            console.log(data);
            $scope.branchData = data.data.result;
        }, function (data, status, headers, config) {
            if (data.status == 404) {
                $scope.branchData = '(no data)'
            }
        });
    };

    $scope.submitClobbers = function() {
        var clobberData = [];
        var clobberTimes = [];
        for (builderName in  $scope.selectedBuilders) {
            if ($scope.selectedBuilders[builderName] == true) {
                clobberTimes = clobberTimes.concat($scope.branchData[builderName]);
            }
        }
        var arrayLength = clobberTimes.length;
        for (var index = 0; index < arrayLength; index++) {
            clobberData.push({
                "branch": clobberTimes[index].branch,
                "builddir": clobberTimes[index].builddir
            })
        }
        restapi.post(initial_data.clobber_url, clobberData).
        then(function(response) {
            $scope.expandBranch($scope.selectedBranch);
        });
    };
  
    $scope.selectAllBuilders = false; 
    $scope.toggleSelectedBuilders = function() {
        for (builderName in $scope.branchData) {
            $scope.selectedBuilders[builderName] = !$scope.selectAllBuilders;
        }
    };
    
    if ($scope.selectedBranch != null) {
        $scope.expandBranch($scope.selectedBranch);
    }
});
