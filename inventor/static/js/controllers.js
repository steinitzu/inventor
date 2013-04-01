function ItemListCtrl($scope, $http) {

    
    $http.get('items').success(function(data) {
         $scope.items = data;
         });    
    //$scope.orderProp = 'id';
};

function ItemDetailCtrl($scope, $http) {
    $http.get('item/:item_id').success(function(data) {
        $scope.item = data;
        });
};
//function ItemDetailCtrl($scope, $http) {
//    $http.get('item/:item_id', (
