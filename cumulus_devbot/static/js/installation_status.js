var app = angular.module('InstallationStatusApp', ['ngSanitize']);

app.controller('InstallationStatusController', function ($scope, $http, $timeout) {

    $scope.fetchStatus = function () {
        $http.get(status_api_url).success(function(data) {
            $scope.installation = data;
            if ($scope.installation.status == 'Pending' || $scope.installation.status == 'InProgress') {
                // Refresh data every 3 seconds
                $scope.refreshInterval = 3;
            } else {
                $scope.refreshInterval = null;
            }
            if ($scope.refreshInterval != null) {
                $timeout(function() { $scope.fetchStatus(); }, $scope.refreshInterval * 1000);
            }
        });
    };

    $scope.fetchStatus();

});
