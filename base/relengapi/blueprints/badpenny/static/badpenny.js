/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('badpenny', ['initial_data']);

angular.module('badpenny').controller('TasksController',
                                    function($scope, $http, initial_data) {
    var tasksByName = function(taskArray) {
        var byName = {};
        angular.forEach(taskArray, function(task) {
            byName[task.name] = task;
        });
        return byName;
    };

    $scope.tasks = tasksByName(initial_data.tasks);
    $scope.expandedTask = null;
    $scope.expandedLogs = null;

    $scope.expandTask = function(name) {
        $scope.expandedTask = name;

        $http.get('/badpenny/tasks/' + name)
        .then(function (data, status, headers, config) {
            $scope.tasks[name] = data.data.result;
        }, function (data, status, header, config) {
            alertify.error("Failed getting task details: " + data);
        });
    };

    $scope.expandJob = function(job) {
        $scope.expandedLogs = job.logs;
    };

    $scope.closeJob = function() {
        $scope.expandedLogs = null;
    };

    $scope.refresh = function() {
        $http.get('/badpenny/tasks?active=1')
        .then(function (data, status, headers, config) {
            // copy over the job from the expanded task
            var newTasks = tasksByName(data.data.result);
            var expandedTask = $scope.tasks[$scope.expandedTask];
            if (expandedTask) {
                newTasks[expandedTask.name].jobs = expandedTask.jobs;
            }
            $scope.tasks = newTasks;
        }, function (data, status, header, config) {
            alertify.error("Failed getting task list: " + data);
        });

        // reload the currently expanded task simultaneously
        if ($scope.expandedTask) {
            $scope.expandTask($scope.expandedTask);
        }
    };
});
