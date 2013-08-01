


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

    sharedService.attachLabel = function(label) {
        // attach label to current entityId
        this.label = label;
        this.broadcast('attachLabel');
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

    // Adds label to filter list and removes it from menu
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
        this.broadcast('filterQueryChanged');
    };
    
    sharedService.broadcast = function (name) {
        console.log('broadcasting: ', name);
        $rootScope.$broadcast(name);
    };

    return sharedService;    
});




function ItemListCtrl($scope, $http, itemService) {
    $scope.query = itemService.filterQuery;
    $scope.labels = itemService.filterLabels;
    $scope.noOfPages = 1;
    $scope.currentPage = 1;
    $scope.maxSize = 7;

    $scope.fetch = function(query, labels, page) {
        $http({
            method: 'GET',
            url: 'items',
            params: {
                'pattern': query,
                'labels': labels.join(','),
                'page': page
            }}).success(function(data) {
                $scope.items = data.entities;
                $scope.noOfPages = data.pagecount;
            });
    };

    var refresh = function() {
        $scope.fetch(
            itemService.filterQuery,
            itemService.filterLabels,
            $scope.currentPage);
    };

    $scope.$on('filterLabelsChanged', function() {
        refresh();
    });
    $scope.$on('filterQueryChanged', function() {
        refresh();
    });
    $scope.$on('filterQueryChanged', function() {
        refresh();
    });
    $scope.$watch('currentPage', function() {
        refresh();
    });
    
    $scope.filter = function () {
        itemService.setFilterQuery($scope.query);
    };

    $scope.fetch($scope.query, $scope.labels, $scope.page);
};


function ItemCtrl($scope, $http, $routeParams, $filter, $location, itemService){    

    $scope.entityId = $routeParams.itemId;
    $scope.files = [];

    $scope.fetch = function() {
        $http({
            method:'GET', 
            url:'item',
            params:{'entity_id':$scope.entityId}}).success(
                function(data) {
                    $scope.item = data;
                    $scope.imageSource = '/item_image?entity_id='+$scope.item.id
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
                    $scope.fetch();
                    $scope.itemForm.$setPristine();
                });
    };

    $scope.destroy = function() {
        $http({
            method:'DELETE', 
            url:'item',
            params:{id:item.id}
        });
    };

    
    $scope.$on("fileSelected", function (event, args) {
        console.log('file selected');
        $scope.$apply(function () {
            $scope.files.push(args.file);
            
        });                      
    });

    $scope.uploadImage = function() {
        console.log('scope file '+$scope.files);
        $http({
            method: 'POST', 
            url: '/item_image',
            headers: { 'Content-Type': false},
            params: { 'entity_id': $scope.item.id },
            transformRequest: function (data) {
                var formData = new FormData();
                
                for (var i = 0;  i < data.files; i++) {
                    formData.append("file" + i, data.files[i]);
                }
                console.log('data files: '+data.files);
                console.log('formdata: '+formData);
                return formData;                
            },
            data: {'files': $scope.files}}).
            success(
                function (data, status, headers, config) {
                    alert("success!");
                }).
            error(function (data, status, headers, config) {
                alert('error');
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

    $scope.strip = function(label) {
        console.log('stripping label', [label]);
        index = $scope.labels.indexOf(label);
        if (index > -1) {
            $scope.labels.splice(index, 1);
        };
        console.log('stripping label', [label]);
        if (itemService.entityId) {
            labels = new Array();
            labels.push(label);
            $scope.remove(itemService.entityId, labels);
        };

    };

    $scope.remove = function(entityId, labels) {
        labels = labels.join(',')
        $http({
            method: 'DELETE',
            url: 'labels',
            params: {
                'entity': 'item',
                'entity_id': entityId,
                'labels': labels}
        }).success(function(data) {
                    $scope.fetch(entityId);
        });
    };

    $scope.store = function(entityId, labels) {
        labels = labels.join(',')
        $http({
            method: 'POST',
            url: 'labels',
            params: {
                'entity': 'item',
                'entity_id': entityId,
                'labels': labels}
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
    $scope.$on('attachLabel', function () {
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
            params:{'entity': 'item',
                    'siblings': $scope.filterLabels.join(',')}
        }).success(function(data) {
            $scope.labels.length = 0
            var index;
            var length;
            for(index=0; index<data.length; ++index) {
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
        itemService.attachLabel($scope.typeaheadValue);
        $scope.typeaheadValue = '';
    };

    $scope.addFilter = function (label) {
        itemService.addFilterLabel(label);
    };
    $scope.removeFilter = function (label) {
        itemService.removeFilterLabel(label);
    };
    $scope.fetch();

    $scope.$on('filterLabelsChanged', function() {
        $scope.fetch();
    });
};


ItemListCtrl.inject = ['$scope', 'itemService'];
ItemCtrl.inject = ['$scope', 'itemService'];
ItemLabelsCtrl.inject = ['$scope', 'itemService'];
LabelsCtrl.inject = ['$scope', 'itemService'];
