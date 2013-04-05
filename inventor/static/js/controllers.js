function ItemListCtrl($scope, $http) {
    $http.get('items').success(function(data) {
         $scope.items = data;
         });
};



function ItemDetailCtrl($scope, $http, $routeParams, $filter, $location, $broadcast) {
    $scope.url = 'item';
    $scope.entityId = $routeParams.itemId;
    $scope.fetch = function() {
        $http({
            method:'GET', 
            url:'item',
            params:{'entity_id':$scope.entityId}}).success(
                function(data) {
                    console.log('fetched entity', $scope.entityId);
                    $scope.item = data;
                    $scope.item.quantity = Number($scope.item.quantity);
                    $scope.item.sale_price = Number($scope.item.quantity);
                    $scope.$emit('entityFetched', {'entityId':data.id});
                });
    };
    $scope.submit = function() {
        $http({
            method:'POST',
            url:'item',
            data:$filter('json')($scope.item)}).success(
                function(data) {
                    $scope.entityId = data;
                    $scope.$emit('entitySaved', {'entityId':$scope.entityId});
                    //$location.path('/item/'+data);
                });
    };
    $scope.fetch();

//    $scope.$on('entityFetched', function() {console.log('trolololol');});
};


function LabelsCtrl($scope, $http, $broadcast) {
    $scope.url = 'labels';
    $scope.entityId = null;


    $scope.fetch = function(entityId) {
        $scope.entityId = entityId;
        if (typeof $scope.entityId === 'undefined') {
            $scope.labels = [];
            }
        else {
            $http({
                method: 'GET',
                url: 'labels',
                params:{
                    'entity_id': $scope.entityId,
                    'entity': 'item'}
            }).success(function(data) {
                        $scope.labels = data;
            });
        };
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

    $scope.submit = function($data) {
        $scope.labels.push($scope.typeaheadValue);
        console.log($scope.entityId);

        if (typeof $scope.entityId !== 'undefined'){
            $http({
                method: 'POST',
                url: $scope.url,
                params: {
                    'entity_id': $scope.entityId,
                    'entity': 'item',
                    'labels': $scope.labels}
            }).success(function () {
            });
        };
    };

    //Get the labels for entity when fetched and saved
    $scope.$on('entityFetched', function() {console.log('trolololol');});
    $scope.$on('entitySaved', $scope.fetch());
};
