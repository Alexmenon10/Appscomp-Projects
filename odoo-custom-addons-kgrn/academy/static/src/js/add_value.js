zzodoo.define('academy.add_value', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    var timeout;

//creating a new widget and adding our method to perform action. and registering to publicwidget
    publicWidget.registry.addValue = publicWidget.Widget.extend({

//    Selction particular template class js taken to load only in particular section
    selector: '.oe_add_value',
//    based on button class intializing  function
    events: {
        'click .addValueBtn': '_onAddValue',
    },
    console.log("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
//   function called when we click sumbit button
     _onAddValue: function (ev) {

        var num1 = $("input[name='add1']").val();
        var num2 = $("input[name='add2']").val();

//         this rpc method calling python function and sending value as json format
        this._rpc({
            route: "/add/value/sum",
            params: {
                num1: parseInt(num1, 10),
                num2: parseInt(num2, 10),
            },
        }).then(function (data) {
//            data  received from python
            $("input[name='sum']").val(data['sum'])
        });

     },


});


return {
    AcademyAddValue: publicWidget.registry.addValue,
};

});