function ItemListCtrl($scope, $http) {
    $http.get('items').success(function(data) {
         $scope.items = data;
         });
};

function ItemDetailCtrl($scope, $http, $routeParams, $filter) {
    $scope.itemId = $routeParams.itemId;
    $http.get('item/'+$scope.itemId).success(function(data) {
        $scope.item = data;
        $scope.item.quantity = Number($scope.item.quantity);
        $scope.item.sale_price = Number($scope.item.quantity);
        });
    $scope.submit = function() {
        $http.post('item', data=$filter('json')($scope.item));
        }
};
