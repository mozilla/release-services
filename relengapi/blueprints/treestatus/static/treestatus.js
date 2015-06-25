/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('treestatus', ['relengapi', 'initial_data']);

// constants defining the tool's behavior

angular.module('treestatus').constant('allowed_statuses', [
    'closed',
    'open',
    'approval required'
]);

angular.module('treestatus').constant('allowed_tags', {
    'checkin-compilation': 'Check-in compilation failure',
    'checkin-test': 'Check-in test failure',
    'infra': 'Infrastructure related',
    'backlog': 'Job backlog',
    'planned': 'Planned closure',
    'other': 'Other',
});


// some useful filters for the template

angular.module('treestatus').filter('urlencode', function() {
    return window.encodeURIComponent;
});

// convert a tree status to a CSS class name
angular.module('treestatus').filter('status2class', function() {
    return function(input) {
        return input.toLowerCase().replace(" ", "_", "g");
    };
});

// shorten a user identity
angular.module('treestatus').filter('shortName', function() {
    var domain_re = /@.*/;
    var human_re = /^human:/;
    return function(input) {
        return input.replace(domain_re, '').replace(human_re, '');
    };
});

// make an array into a comma-separated list
angular.module('treestatus').filter('list', function() {
    return function(input) {
        return input.join(", ");
    };
});

// borrowed from https://github.com/mozilla/treeherder/blob/d5ae8deb9f041ce538eee1a5d8d05c60f09e56be/ui/js/filters.js#L40-L71
angular.module('treestatus').filter('linkifyBugs', function($sce) {
    return function(input) {
        // perform some basic sanitization
        var str = (input || '')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('&', '&amp;');

        var bug_matches = str.match(/-- ([0-9]+)|bug.([0-9]+)/ig);
        var pr_matches = str.match(/PR#([0-9]+)/ig);

        // Settings
        var bug_title = 'bugzilla.mozilla.org';
        var bug_url = '<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=$1" ' +
            'data-bugid=$1 ' + 'title=' + bug_title + '>$1</a>';
        var pr_title = 'github.com';
        var pr_url = '<a href="https://github.com/mozilla-b2g/gaia/pull/$1" ' +
            'data-prid=$1 ' + 'title=' + pr_title + '>$1</a>';

        if (bug_matches) {
            // Separate passes to preserve prefix
            str = str.replace(/Bug ([0-9]+)/g, "Bug " + bug_url);
            str = str.replace(/bug ([0-9]+)/g, "bug " + bug_url);
            str = str.replace(/-- ([0-9]+)/g, "-- " + bug_url);
        }

        if (pr_matches) {
            // Separate passes to preserve prefix
            str = str.replace(/PR#([0-9]+)/g, "PR#" + pr_url);
            str = str.replace(/pr#([0-9]+)/g, "pr#" + pr_url);
        }

        return $sce.trustAsHtml(str);
    };
});

// Directives

// Input panel for updating trees; the "update" attribute is evaluated with
// `status`, `reason`, `tags`, and `remember` set when the form is submitted.
// Set `plural="1"` for a form that can affect multiple trees.  The `disabled`
// attribute gives an expression to disable the whole form (e.g., when no
// trees are selected)
angular.module('treestatus').directive('treeStatusControl',
function(allowed_statuses, allowed_tags) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: '/treestatus/static/treeStatusControl.html',
        scope: {
            disabled: '=disabled',
            update: '&update',
            plural: '@plural',
        },
        link: function(scope, element, attrs, ctrl) {
            scope.allowed_statuses = allowed_statuses;
            scope.allowed_tags = allowed_tags;

            scope.status = allowed_statuses[0];
            scope.tags = {};
            scope.reason = "";
            scope.remember = true;

            // ngModel handles tags as an object with boolean values, so
            // convert it to an array of tag names as the API expects
            var tagList = function(model) {
                var tags = [];
                angular.forEach(model, function(present, tag) {
                    if (present) {
                        tags.push(tag);
                    }
                });
                tags.sort();
                return tags;
            };

            // we do some whole-form validation per business rules
            scope.formInvalid = function() {
                if (scope.status == 'closed' && tagList(scope.tags).length == 0) {
                    return true;
                }
                return false;
            };

            scope.submit = function() {
                scope.update({
                    status: scope.status,
                    reason: scope.reason,
                    tags: tagList(scope.tags),
                    remember: scope.remember,
                });
                // reset the form
                scope.tags = {};
                scope.reason = '';
            };
        },
    };
});

// Controllers

// index.html
angular.module('treestatus').controller('TreeListController',
                                    function($scope, restapi, initial_data, $q) {
    $scope.trees = initial_data.trees;
    $scope.stack = initial_data.stack;

    // Pre-flight some permissions
    var perms = initial_data.user.permissions
    $scope.can_sheriff = perms.some(function(perm) {
        return perm.name == 'treestatus.sheriff';
    });
    $scope.can_admin = perms.some(function(perm) {
        return perm.name == 'treestatus.admin';
    });

    $scope.new_tree_name = '';

    // checkboxes create an object with boolean keys, but we want a list
    // of tree names
    $scope.selected_trees = [];
    $scope._selected_trees = {};
    $scope.$watchCollection('_selected_trees', function(newValue) {
        var trees = $scope.selected_trees = [];
        angular.forEach(newValue, function(present, tree) {
            if (present) {
                trees.push(tree);
            }
        });
        trees.sort();
    });

    var reloadTrees = function() {
        restapi.get('/treestatus/trees', {
            while: 'fetching tree data',
        }).then(function (data, status, headers, config) {
            $scope.trees = data.data.result;
        });
    };

    var reloadStack = function() {
        restapi.get('/treestatus/stack', {
            while: 'fetching undo stack data',
        }).then(function (data, status, headers, config) {
            $scope.stack = data.data.result;
        });
    };

    // handle the check-all checkbox
    $scope.allChecked = function() {
        var all_checked = true;
        angular.forEach($scope.trees, function(tree, name) {
            if (!$scope._selected_trees[name]) {
                all_checked = false;
            }
        });
        return all_checked;
    };

    $scope.checkAllClicked = function() {
        var newVal = !$scope.allChecked();
        angular.forEach($scope.trees, function(tree, name) {
            $scope._selected_trees[name] = newVal;
        });
    };

    $scope.revertChange = function(stack_id) {
        restapi({
            url: '/treestatus/stack/' + stack_id,
            method: 'REVERT',
            while: 'reverting change',
        }).then(function (data, status, headers, config) {
            reloadTrees();
            reloadStack();
        });
    };

    $scope.discardChange = function(stack_id) {
        restapi({
            url: '/treestatus/stack/' + stack_id,
            method: 'DELETE',
            while: 'deleting change',
        }).then(function (data, status, headers, config) {
            reloadStack();
        });
    };

    $scope.addTree = function(treename) {
        restapi({
            url: '/treestatus/trees/' + treename,
            method: 'PUT',
            data: JSON.stringify({
                tree: treename,
                status: 'closed',
                reason: 'new tree',
                message_of_the_day: '',
            }),
            headers: {'Content-Type': 'application/json'},
            while: 'adding tree ' + treename,
        }).then(function() {
            reloadTrees();
        });
    };

    $scope.deleteTrees = function() {
        var promises = [];
        angular.forEach($scope.selected_trees, function(treename) {
            promises.push(restapi({
                url: '/treestatus/trees/' + treename,
                method: 'DELETE',
                while: 'deleting tree ' + treename,
            }));
        });

        $q.all(promises).then(function() {
            $scope._selected_trees = {};
            reloadTrees();
            reloadStack();
        });
    };

    $scope.updateTrees = function(status, reason, tags, remember) {
        var update = {
            trees: $scope.selected_trees,
            status: status,
            reason: reason,
            tags: tags,
            remember: remember,
        };
        restapi({
            url: '/treestatus/trees',
            method: 'UPDATE',
            data: JSON.stringify(update),
            headers: {'Content-Type': 'application/json'},
            while: 'updating tree',
        }).then(function (data, status, headers, config) {
            reloadTrees();
            reloadStack();
        });
    };
});

// tree.html
angular.module('treestatus').controller('TreeDetailController',
                                    function($scope, restapi, initial_data) {
    $scope.tree = initial_data.tree;
    $scope.logs = initial_data.logs;
    $scope.show_all_logs = false;

    $scope.new_motd = $scope.tree.message_of_the_day;

    // Pre-flight some permissions
    var perms = initial_data.user.permissions
    $scope.can_sheriff = perms.some(function(perm) {
        return perm.name == 'treestatus.sheriff';
    });

    var treename = $scope.tree.tree;

    var reloadLogs = function() {
        var all_ext = $scope.show_all_logs ? '?all=1' : '';
        restapi.get('/treestatus/trees/' + treename + '/logs' + all_ext, {
            while: 'fetching more logs',
        }).then(function (data, status, headers, config) {
            $scope.logs = data.data.result;
        });
    };

    var reloadTree = function() {
        restapi.get('/treestatus/trees/' + treename, {
            while: 'fetching tree data',
        }).then(function (data, status, headers, config) {
            $scope.tree = data.data.result;
        });
    };

    $scope.loadAllLogs = function() {
        $scope.show_all_logs = true;
        reloadLogs();
    };

    $scope.setMotd = function(new_motd) {
        restapi({
            url: '/treestatus/trees/' + treename,
            method: 'PATCH',
            data: JSON.stringify({
                tree: treename,
                status: $scope.tree.status,
                reason: $scope.tree.reason,
                message_of_the_day: new_motd,
            }),
            while: 'updating message of the day',
        }).then(function (data, status, headers, config) {
            $scope.tree.message_of_the_day = new_motd;
        });
    };

    $scope.updateTree = function(status, reason, tags, remember) {
        var update = {
            trees: [treename],
            status: status,
            reason: reason,
            tags: tags,
            remember: remember,
        };
        restapi({
            url: '/treestatus/trees',
            method: 'UPDATE',
            data: JSON.stringify(update),
            headers: {'Content-Type': 'application/json'},
            while: 'updating tree',
        }).then(function (data, status, headers, config) {
            reloadLogs();
            reloadTree();
        });
    };
});
