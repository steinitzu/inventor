function ItemListCtrl($scope, $http) {
    $http.get('items').success(function(data) {
         $scope.items = data;
         });
};



function ItemDetailCtrl($scope, $http, $routeParams, $filter, $location) {
    $scope.url = 'item';
    $scope.entityId = $routeParams.itemId;
    $scope.fetch = function() {
        $http({
            method:'GET', 
            url:'item',
            params:{'entity_id':$scope.entityId}}).success(
                function(data) {
                    $scope.item = data;
                    $scope.item.quantity = Number($scope.item.quantity);
                    $scope.item.sale_price = Number($scope.item.quantity);
                });
    };
    $scope.submit = function() {
        $http({
            method:'POST',
            url:'item',
            data:$filter('json')($scope.item)}).success(
                function(data) {
                    $scope.entityId = data;
                    $location.path('/item/'+data);
                });
    };
    $scope.fetch();
};


function LabelsCtrl($scope, $http) {
    $scope.url = 'labels';
    $scope.entityId = null;
    $scope.fetch = function() {

        $http({
            method: 'GET',
            url: 'labels',
            params:{'entity_id':$scope.entityId,'entity':'item'}}).success(
                function(data) {
                    $scope.labels = data;
                });
    };

    $scope.typeaheadFn = function(substring, callback) {
        console.log('fetching');
        $http({
            method: 'GET',
            url: $scope.url,
            params: {
                'entity': 'item',
                'substring': substring}
            }).success(function (stations) {
                callback(stations);
            });
    };
};
