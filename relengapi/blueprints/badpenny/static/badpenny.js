/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('badpenny', ['relengapi', 'initial_data', 'angularMoment']);

angular.module('badpenny').controller('TasksController',
                                    function($scope, restapi, initial_data) {
    var tasksByName = function(taskArray) {
        var byName = {};
        angular.forEach(taskArray, function(task) {
            byName[task.name] = task;
        });
        return byName;
    };

    $scope.tasks = tasksByName(initial_data.tasks);

    var loadJobs = function(task) {
        restapi.get('/badpenny/tasks/' + task.name, {while: 'fetching task'})
        .then(function (data, status, headers, config) {
            $scope.tasks[task.name] = data.data.result;
        });
    };

    $scope.toggleTask = function(task) {
        if (task.jobs) {
            task.jobs = null;
        } else {
            loadJobs(task);
        }
    };

    var loadLogs = function(job) {
        job.logs = 'loading';
        restapi.get('/badpenny/jobs/' + job.id + '/logs',
                    {while: 'fetching logs', expectedStatus: 404})
        .then(function (data, status, headers, config) {
            job.logs = data.data.result.content;
        }, function (data, status, header, config) {
            if (data.status == 404) {
                job.logs = '(no logs)';
            }
        });
    };

    $scope.toggleJob = function(job) {
        if (job.logs) {
            job.logs = null;
        } else {
            loadLogs(job);
        }
    };

    $scope.humanJobDuration = function(job) {
        var dur = moment.duration(moment(job.started_at).diff(job.completed_at));
        if (dur < 100) {
            return "instantly";
        } else if (dur < 10000) {
            // humanize just says "a few seconds", which isn't good enough
            return "in " + (dur / 1000).toFixed(2) + ' seconds';
        } else {
            return "in " + moment.duration(diff).humanize();
        }
    };

    $scope.refresh = function() {
        restapi.get('/badpenny/tasks', {while: 'refreshing tasks'})
        .then(function (data, status, headers, config) {
            // re-request any existing job data, and start refreshing it
            angular.forEach(data.data.result, function(task) {
                if ($scope.tasks[task.name] && $scope.tasks[task.name].jobs) {
                    task.jobs = $scope.tasks[task.name].jobs;
                    loadTask(task);
                }
            });
            $scope.tasks = tasksByName(data.data.result);
        });
    };
});

angular.module('badpenny').directive('statusIcon', function() {
    var refresh = function(scope) {
        if (scope.good) {
            scope.status = 'good';
        } else if (scope.bad) {
            scope.status = 'bad';
        } else if (scope.gray) {
            scope.status = 'gray';
        } else {
            scope.status = '';
        }
    };

    return {
        restrict: 'E',
        replace: true,
        templateUrl: 'static/statusIcon.html',
        scope: {
            bad: '=badWhen',
            good: '=goodWhen',
            gray: '=grayWhen',
        },
        link: function(scope, element, attrs) {
            scope.$watch('bad', function() { refresh(scope); });
            scope.$watch('good', function() { refresh(scope); });
            scope.$watch('gray', function() { refresh(scope); });
        },
    };
});
