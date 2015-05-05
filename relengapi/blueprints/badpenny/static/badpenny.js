/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
angular.module('badpenny', ['relengapi', 'initial_data', 'angularMoment']);

angular.module('badpenny').controller('TasksController',
                                    function($scope, taskService) {
    $scope.tasks = taskService.tasks;

    $scope.refresh = function() {
        taskService.refresh();
    };
});

angular.module('badpenny').factory('taskService', function(restapi, initial_data) {
    /* This service handles all of the data for the page, including unfolding tasks
     * to show their jobs and unfolding jobs to show their logs. */

    var tasksByName = {};
    angular.forEach(initial_data.tasks, function(task) {
        tasksByName[task.name] = task;
    });

    var svc = {
        tasks: tasksByName
    };

    svc.loadTaskJobs = function(task, force) {
        if (task._fetched && !force) {
            return;
        }
        task._fetched = true;

        restapi.get('/badpenny/tasks/' + task.name, {while: 'fetching task'})
        .then(function (data, status, headers, config) {
            var newTask = data.data.result;
            task.last_success = newTask.last_success;
            task.schedule = newTask.schedule;

            // merge jobs
            var oldJobsById = {};
            if (task.jobs) {
                angular.forEach(task.jobs, function(oldJob) {
                    oldJobsById[oldJob.id] = oldJob;
                });
            } else {
                task.jobs = [];
            }
            angular.forEach(newTask.jobs, function(newJob) {
                var oldJob = oldJobsById[newJob.id];
                if (oldJob) {
                    oldJob.created_at = newJob.created_at;
                    oldJob.started_at = newJob.started_at;
                    oldJob.completed_at = newJob.completed_at;
                    oldJob.successful = newJob.successful;
                    // reload the logs if they've already been loaded
                    if (oldJob._fetched) {
                        svc.loadJobLogs(oldJob, true);
                    }
                } else {
                    task.jobs.push(newJob);
                }
            });
        });
    };

    svc.loadJobLogs = function(job, force) {
        if (job._fetched && !force) {
            return;
        }
        job._fetched = true;

        if (!job.logs) {
            job.logs = '..loading..';
        }

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

    svc.refresh = function() {
        restapi.get('/badpenny/tasks', {while: 'refreshing tasks'})
        .then(function (data, status, headers, config) {
            // merge the updated data in with the existing data
            angular.forEach(data.data.result, function(newTask) {
                var oldTask = svc.tasks[newTask.name];
                if (oldTask) {
                    oldTask.last_success = newTask.last_success;
                    oldTask.schedule = newTask.schedule;
                } else {
                    svc.tasks[newTask.name] = newTask;
                }
                // force-load the task if it was already loaded
                task = svc.tasks[newTask.name];
                if (task._fetched) {
                    svc.loadTaskJobs(task, true);
                }
            });
        });
    };

    return svc;
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

angular.module('badpenny').directive('bpTask',
    function(taskService, restapi, initial_data) {
    var can_force = initial_data.user.permissions.some(function(perm) {
            return perm.name == 'base.badpenny.run';
    });

    return {
        restrict: 'E',
        replace: true,
        priority: 1001, // run after ng-repeat
        templateUrl: 'static/bp-task.html',
        scope: {
            task: '=',
        },  
        link: function(scope, element, attrs) {
            scope.details = false;
            scope.can_force = can_force;

            scope.toggleDetails = function() {
                scope.details = !scope.details;
                taskService.loadTaskJobs(scope.task);
            };

            scope.runNow = function() {
                restapi.post('/badpenny/tasks/' + scope.task.name + '/run-now', '',
                             {while: 'running task ' + scope.task.name})
                .then(function (data, status, headers, config) {
                    taskService.loadTaskJobs(scope.task, true);
                });
            }
        },
    };  
});

angular.module('badpenny').directive('bpJob', function(taskService) {
    return {
        restrict: 'E',
        replace: true,
        priority: 1001, // run after ng-repeat
        templateUrl: 'static/bp-job.html',
        scope: {
            job: '=',
        },  
        link: function(scope, element, attrs) {
            scope.details = false;
            scope.toggleDetails = function() {
                scope.details = !scope.details;
                taskService.loadJobLogs(scope.job);
            };

            scope.humanJobDuration = function(job) {
                var dur = moment.duration(moment(job.completed_at).diff(job.started_at));
                var ms = dur.asMilliseconds();
                if (ms < 100) {
                    return "instantly";
                } else if (ms < 10000) {
                    // Humanize just says "a few seconds", which isn't good enough.
                    return "in " + (ms / 1000.0).toFixed(2) + ' seconds';
                } else {
                    return "in " + moment.duration(diff).humanize();
                }
            };

        },
    };  
});

