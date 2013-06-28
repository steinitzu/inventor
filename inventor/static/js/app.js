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

inventor.directive('fileUpload', function () {
    return {
        scope: true,        //create a new scope
        link: function (scope, el, attrs) {
            el.bind('change', function (event) {
                var files = event.target.files;
                //iterate files since 'multiple' may be specified on the element
                for (var i = 0;i<files.length;i++) {
                    //emit event upward
                    scope.$emit("fileSelected", { file: files[i] });
                }                                       
            });
        }
    };
});


