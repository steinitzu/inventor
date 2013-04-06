


inventor.factory('itemService', function($rootScope) {
    var sharedService = {};
    sharedService.entityId = null;
    sharedService.label = null;
    sharedService.labels = new Array();
    sharedService.filterLabels = new Array();
    sharedService.filterQuery = null;
    
    
    sharedService.prepForBroadCast = function(entityId) {
        this.entityId = entityId;
    };

    sharedService.newLabel = function(label) {
        // Call when we have a new label to attach.
        this.label = label;
        this.broadcast('newLabel');
    };

    sharedService.addLabel = function(label) {
        this.labels.push(label);
        this.broadcast('labelsChanged');
    };
    sharedService.removeLabel = function(label) {
        index = this.labels.indexOf(label);
        if (index == -1) {
            return
        };
        this.labels.splice(index, 1);
        this.broadcast('labelsChanged');
    };

    sharedService.addFilterLabel = function(label) {
        if (this.filterLabels.indexOf(label) == -1) {
            this.filterLabels.push(label);
            this.broadcast('filterLabelsChanged');
            this.removeLabel(label);
        };
    };

    sharedService.removeFilterLabel = function(label) {
        index = this.filterLabels.indexOf(label);
        if (index == -1) {
            return
        };
        this.filterLabels.splice(index, 1);
        this.broadcast('filterLabelsChanged');
        this.addLabel(label);
    };
    
    sharedService.setFilterQuery = function(query) {
        this.filterQuery = query;
        this.broadCast('filterQueryChanged');
    };
    
    sharedService.broadcast = function (name) {
        console.log('broadcasting: ', name);
        $rootScope.$broadcast(name);
    };

    return sharedService;    
});

function ItemListCtrl($scope, $http, itemService) {
    $scope.fetch = function(query, labels) {
        $http({
            method: 'GET',
            url: 'items',
            params: {
                'pattern': query,
                'labels': labels.join(',')
            }}).success(function(data) {
                $scope.items = data;
            });
    };

    $scope.$on('filterLabelsChanged', function() {
        $scope.fetch(itemService.filterQuery, itemService.filterLabels);
    });
    $scope.$on('filterQueryChanged', function() {
        $scope.fetch(itemService.filterQuery, itemService.filterLabels);
    });

    $scope.fetch(null, []);
};


function ItemCtrl($scope, $http, $routeParams, $filter, itemService){    

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
                    itemService.prepForBroadCast($scope.item.id);
                    itemService.broadcast('itemFetched');
                })
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
                    itemService.prepForBroadCast($scope.entityId);
                    itemService.broadcast('itemSaved');
                });
    };
    $scope.fetch();
};

// Gets and sets labels for items
function ItemLabelsCtrl($scope, $http, $filter, itemService){

    // Get the labels for item
    $scope.fetch = function(entityId) {
        console.log('Getting some labels for: ', entityId);
        if (typeof entityId === 'undefined' || entityId === null) {
            console.log('no id, empty array');
            // Empty item has no labels
            $scope.labels = new Array();
            return;
        };
        $http({
            method: 'GET',
            url: 'labels',
            params:{
                'entity': 'item',
                'entity_id': entityId
            }}).success(function(data) {
                $scope.labels = data;
        });        
    };

    $scope.attach = function(entityId, label) {
        $scope.labels.push(label);
        if (entityId) {
            $scope.store(entityId, $scope.labels);
        };
    };

    $scope.store = function(entityId, labels) {
        $http({
            method: 'POST',
            url: 'labels',
            params: {
                'entity': 'item',
                'entity_id': entityId},
            data: $filter('json')(labels)
        }).success(function(data) {
                    $scope.fetch(entityId);
        });
    };

    $scope.$on('itemFetched', function () {
        $scope.fetch(itemService.entityId);
    });
    $scope.$on('itemSaved', function () {
        $scope.store(itemService.entityId, $scope.labels);
    });
    $scope.$on('newLabel', function () {
        $scope.attach(itemService.entityId, itemService.label)
    });
};


// Controller for getting all the labels in db
function LabelsCtrl($scope, $http, itemService){
    $scope.filterLabels = itemService.filterLabels;
    $scope.labels = itemService.labels;

    $scope.fetch = function() {
        $http({
            method: 'GET',
            url: 'labels',
            params:{'entity': 'item'}
        }).success(function(data) {
            $scope.labels.length = 0
            var index;
            var length;
            for(index=0; index<data.length; ++index) {
                console.log(data[index]);
                $scope.labels.push(data[index]);
            };
        });
    };

    $scope.typeaheadFn = function(substring, callback) {
        $http({
            method: 'GET',
            url: 'labels',
            params: {
                'entity': 'item',
                'substring': substring}
        }).success(function (stations) {
            callback(stations);
        });
    };
    
    $scope.createSubmit = function() {
        itemService.newLabel($scope.typeaheadValue);
        $scope.typeaheadValue = '';
    };

    $scope.addFilter = function (label) {
        itemService.addFilterLabel(label);
    };
    $scope.removeFilter = function (label) {
        itemService.removeFilterLabel(label);
    };
    $scope.fetch();
};


ItemListCtrl.inject = ['$scope', 'itemService'];
ItemCtrl.inject = ['$scope', 'itemService'];
ItemLabelsCtrl.inject = ['$scope', 'itemService'];
LabelsCtrl.inject = ['$scope', 'itemService'];
