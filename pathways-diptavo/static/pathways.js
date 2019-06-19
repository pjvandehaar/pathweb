'use strict';

$.getJSON('/static/pathways.json').then(function(data) {
    $(document).ready(function() {
        var table = new Tabulator('#table', {
//            height: 600, // setting height lets Tabulator's VirtualDOM load really fast but makes scrolling awkward
            layout: 'fitColumns',
            pagination: 'local',
            paginationSize: 100,
            columns: [
                {title: 'Category', field:'category', headerFilter:true},
                {title: 'Name', field:'name', headerFilter:true, formatter:'link', formatterParams: { urlPrefix: '/pathway/' }, widthGrow:5},
                {title: 'Num p<10<sup>-4</sup> Associations', field:'num_sig_assocs', width:200},
            ],
            data: data,
            initialSort: [{column:"num_sig_assocs", dir:"desc"}],
            tooltipGenerationMode:'hover',tooltips:tabulator_tooltip_maker,tooltipsHeader:true,
        });
    });
});
