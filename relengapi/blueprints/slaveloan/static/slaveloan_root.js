angular.module('slaveloan', ['relengapi', 'initial_data']);

angular.module('slaveloan').controller('slaveloanController',
                                    function($scope, restapi, initial_data) {
    $scope.user = initial_data.user.authenticated_email;

    $scope.machineTypes = initial_data.machine_types;
});
