/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('clobberer', ['relengapi', 'initial_data']);
angular
  .module('clobberer')
  .controller('ClobberController', function($scope, restapi, initial_data) {

    $scope.branches = initial_data.branches;
    $scope.selectedBranch = initial_data.selected_branch || $scope.branches[0];

    /* Tracks all checkbox models */ 
    $scope.selectedBuilders = null;
  
    /* When a user selects a new branch. */ 
    $scope.expandBranch = function(branch) {
        $scope.selectedBuilders = {};
        $scope.selectAllBuilders = false; 
        $scope.branchData = undefined;
        $scope.builderFilter = undefined;
         
        restapi.get('/clobberer/lastclobber/branch/by-builder/' + branch).
            then(function (data, status, headers, config) {
                console.log(data);
                $scope.branchData = data.data.result;
            });
    };

    /* Returns builder names from branchData filtered by builderFilter. */
    $scope.availableBuilders = function() {
        var builders = [];
        for (builder in $scope.branchData) {
                if ($scope.builderFilter == undefined ||
                    builder.toLowerCase().match(
                      $scope.builderFilter.toLowerCase()) != null) {
                    builders.push(builder);
                }
        }
        return builders; 
    };

    $scope.submitClobbers = function() {
        var clobberData = [];
        var clobberTimes = [];
        /* Break transformation of branchData into steps to avoid deep loops */
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
        restapi.post('/clobberer/clobber', clobberData).
        then(function(response) {
            $scope.expandBranch($scope.selectedBranch);
        });
    };
  
    $scope.selectAllBuilders = false; 
    $scope.toggleSelectedBuilders = function() {
        var builders = $scope.availableBuilders();
        for (index in builders) {
            $scope.selectedBuilders[builders[index]] = !$scope.selectAllBuilders;
        }
    };
    
    /*To determine if any ng-checkbox models in an object are checked*/
    $scope.objHasSelectedCheckboxes = function(obj) {
        for (key in obj) {
            if (obj[key] == true) {
                return true;
            }
        }
        return false;
    };
    
    if ($scope.selectedBranch != null) {
        $scope.expandBranch($scope.selectedBranch);
    }

    // Taskcluster

    $scope.purgeCacheButtonDisabled = function() {
      if ($scope.TCBranches === null) {
        return true;
      } else {
        return false;
      }
    };

    $scope.toggleWorkerTypes = function() {
      if ($scope.currentWorkerTypes().length > 0) {
        for (let workerType in $scope.selectedTCBranch.workerTypes) {
          $scope.selectedTCWorkerTypes[workerType] = false;
        }
        $scope.toggleWorkerTypesButton = false;

      } else {
        for (let workerType in $scope.selectedTCBranch.workerTypes) {
          $scope.selectedTCWorkerTypes[workerType] = true;
        }
        $scope.toggleWorkerTypesButton = true;
      }
    };

    $scope.clearSelectedTCWorkerTypes = function() {
      $scope.selectedTCWorkerTypes = {};
    };

    $scope.currentWorkerTypes = function() {
      return Object.keys($scope.selectedTCWorkerTypes)
                .filter(function(i) { return $scope.selectedTCWorkerTypes[i] === true; });
    };

    $scope.listWorkerTypes = function() {
      workerTypes = [];
      if ($scope.selectedTCBranch !== null) {
        for (let workerType in $scope.selectedTCBranch.workerTypes) {
          workerTypes.push($scope.selectedTCBranch.workerTypes[workerType]);
        }
      }
      return workerTypes;
    };

    $scope.loadBranches = function() {
        $scope.TCBranches = null;
        $scope.selectedTCBranch = null;
        $scope.selectedTCWorkerTypes = {};

        restapi.get('/clobberer/tc/branches').then(function (data) {
            $scope.TCBranches = data.data.result;
        });
    };

    $scope.purgeCache = function() {
      let provisionerId = $scope.selectedTCBranch.provisionerId;
      let workerTypes = $scope.currentWorkerTypes();

      for (let workerType of $scope.currentWorkerTypes()) {
        let cacheNames = $scope.selectedTCBranch.workerTypes[workerType].caches

        for (let cacheName of cacheNames) {
          restapi
            .post('/clobberer/tc/purgecache', [{ provisionerId: provisionerId,
                                                 workerType: workerType,
                                                 cacheName: cacheName }])
            .then(function(response) {
              alertify.success(
                  'Cache with name `' + cacheName + '` on worker type `' + workerType  + '` purged sucessfully.');
            });
        }
      }
    };

    $scope.loadBranches();
});
