/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

angular.module('slaveloan', ['relengapi', 'initial_data']);

angular.module('slaveloan').controller('slaveloanController',
                                    function($scope, restapi, initial_data) {
    $scope.machineTypes = initial_data.machine_types;
    $scope.user = initial_data.user.authenticated_email;
    $scope.loanRequestUrl = initial_data.loan_request_url;

    $scope.newLoan = {
        ldap_email: $scope.user,
        bugzilla_email: '',
        slavetype: '',
    };

    $scope.origNewLoan = angular.copy($scope.newLoan);

    $scope.submitLoanRequest = function() {
        var ldap = $scope.newLoan.ldap_email;
        var bugzilla = $scope.newLoan.bugzilla_email;
        var slavetype = $scope.newLoan.slavetype;

        restapi({
            url: $scope.loanRequestUrl,
            method: 'POST',
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            data: JSON.stringify({
                ldap_email: ldap,
                bugzilla_email: bugzilla,
                requested_slavetype: slavetype,
            }),
            while: 'Submitting Loan Request',
        }).then(function(response) {
            if (response.data.result) {
                var r = response.data.result;
                $scope.newLoan = angular.copy($scope.origNewLoan);
                $scope.newLoanForm.$setPristine();
                alertify.success("Loan id " + r.id + " successfully filed")
            } else {
                alertify.error("Error submitting loan");
            }
        });
    };

});
