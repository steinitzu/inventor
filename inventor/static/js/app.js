angular.module('inventor', []).
    config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/items', {
                templateUrl: 'static/item-list.html', controller: ItemListCtrl
            }).
            when('/item/:itemId', {
                templateUrl: 'static/item-detail.html', controller: ItemDetailCtrl
            }).
            otherwise({
                redirectTo: '/items'
            });
    }]);
