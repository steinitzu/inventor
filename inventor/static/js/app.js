var inventor = angular.module('inventor', ['$strap.directives', 'ui.bootstrap']).
    config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/items', {
                templateUrl: 'static/item-list.html', controller: ItemListCtrl
            }).
            when('/item/:itemId', {
                templateUrl: 'static/item-form.html', controller: ItemCtrl
            }).
            when('/pgright', $routeProvider.current).
            otherwise({
                redirectTo: '/items'
            });
    }]);

inventor.filter('range', function() {
    return function(input, total) {
        total = parseInt(total);
        for (var i=0; i<total; i++)
            input.push(i);
        return input;
    };
});


