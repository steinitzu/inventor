function ItemListCtrl($scope, $http) {

    
    $http.get('items').success(function(data) {
         $scope.items = data;
         });
    //$scope.orderProp = 'id';
};
