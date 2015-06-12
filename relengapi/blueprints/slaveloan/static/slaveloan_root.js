angular.module('slaveloan', ['relengapi', 'initial_data']);

angular.module('slaveloan').controller('slaveloanController',
                                    function($scope, restapi, initial_data) {
    $scope.machineTypes = initial_data.machine_types;
    $scope.user = initial_data.user.authenticated_email;
    $scope.loanRequestUrl = initial_data.loanRequestUrl;

    $scope.newLoanModel = {
        ldap_email: $scope.user,
        bugzilla_email: '',
        slavetype: '',
    };

    $scope.submitLoanRequest = function() {
        var ldap = $scope.newLoanModel.ldap_email;
        var bugzilla = $scope.newLoanModel.bugzilla_email;
        var slavetype = $scope.newLoanModel.slavetype;

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
                alertify("Loan id " + r.id + " successfully filed")
            } else {
                alertify.error("Error submitting loan");
            }
        });        
    };

});
