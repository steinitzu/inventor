function ItemListCtrl($scope, $http) {
    $http.get('items').success(function(data) {
         $scope.items = data;
         });
};

function ItemDetailCtrl($scope, $http, $routeParams) {
    $scope.itemId = $routeParams.itemId;    
    $http.get('item/'+$scope.itemId).success(function(data) {
        $scope.item = data;
        });    
};
