'use strict';

$.getJSON('/static/phenotypes.json').then(function(data) {
    $(document).ready(function() {
        var table = new Tabulator('#table', {
//            height: 600, // setting height lets Tabulator's VirtualDOM load really fast but makes scrolling awkward
            layout: 'fitColumns',
            pagination: 'local',
            paginationSize: 100,
            columns: [
                {title: 'Code', field:'phecode', formatter:'link', formatterParams: { urlPrefix: '/pheno/' }, headerFilter:true},
                {title: 'Name', field:'phenostring', formatter:'link', formatterParams: {url: function(cell){return '/pheno/'+cell.getData().phecode;}}, headerFilter:true, widthGrow:2},
                {title: 'Category', field:'category', headerFilter:true, widthGrow:1},
                {title: '#Cases', field:'num_cases', formatter:'comma_fmt'},
                {title: '#Controls', field:'num_controls', formatter:'comma_fmt'},
                {title: 'Num p<10<sup>-4</sup> Associations', field:'num_sig_assocs', formatter:'comma_fmt', width:200},
            ],
            data: data,
            initialSort: [{column:"num_sig_assocs", dir:"desc"}],
            tooltipGenerationMode:'hover',tooltips:tabulator_tooltip_maker,tooltipsHeader:true,
        });
    });
});
