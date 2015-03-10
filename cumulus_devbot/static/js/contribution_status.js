var app = angular.module('ContributionStatusApp', ['ngSanitize']);

app.controller('ContributionStatusController', function ($scope, $http, $timeout) {

    $scope.fetchStatus = function () {
        $http.get(status_api_url).success(function(data) {
            $scope.contribution = data;
            $scope.refreshInterval = 3;

            if ($scope.refreshInterval != null) {
                $timeout(function() { $scope.fetchStatus(); }, $scope.refreshInterval * 1000);
            }
        });
    };

    $scope.fetchStatus();

});
