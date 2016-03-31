/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('tooltool', ['relengapi', 'angularMoment']);

angular.module('tooltool').controller('TTSearchController',
                                    function($scope, restapi) {
    $scope.search_query = ''
    $scope.show_help = true;

    $scope.file_results = []
    $scope.batch_results = []

    // temp
    $scope.startSearch = function() {
        $scope.show_help = false;
        var q = $scope.search_query;

        // search for files and batches at the same time
        restapi({
            url: '/tooltool/file?q=' + q,
            method: 'GET',
            while: 'searching files',
        }).then(function(response) {
            $scope.file_results = response.data.result;
        });

        restapi({
            url: '/tooltool/upload?q=' + q,
            method: 'GET',
            while: 'searching upload batches',
        }).then(function(response) {
            var batches = response.data.result;

            // put the filename into each file record
            angular.forEach(batches, function (batch) {
                angular.forEach(batch.files, function(file, filename) {
                    file.filenames = [filename];
                });
            });
            $scope.batch_results = batches;
        });
    }
});

angular.module('tooltool').directive('ttResultFile', function() {
    return {
        restrict: 'E',
        replace: true,
        priority: 1001, // run after ng-repeat
        templateUrl: 'static/tt-result-file.html',
        scope: {
            res: '=',
        },  
    };  
});

angular.module('tooltool').directive('ttResultBatch', function() {
    return {
        restrict: 'E',
        replace: true,
        priority: 1001, // run after ng-repeat
        templateUrl: 'static/tt-result-batch.html',
        scope: {
            res: '=',
        },  
        link: function(scope, element, attrs) {
            scope.details = false;
        },
    };  
});

angular.module('tooltool').directive('ttDigest', function() {
    return {
        restrict: 'E',
        replace: true,
        template: '<span ng-click="limit = 128" class="tt-sha512">{{digest|limitTo:limit}}</span>',
        scope: {
            algorithm: '@',
            digest: '@',
        },  
        link: function(scope, element, attrs) {
            scope.limit = 8;
        },
    };  
});
