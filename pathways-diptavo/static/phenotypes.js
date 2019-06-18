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
                {title: '#Cases', field:'num_cases'},
                {title: '#Controls', field:'num_controls'},
                {title: 'Num p<10<sup>-4</sup> Associations', field:'num_sig_assocs', width:200},
            ],
            tooltipGenerationMode: 'hover', // generate tooltips just-in-time when the data is hovered
            tooltips: function(cell) {
                // this function attempts to check whether an ellipsis ('...') is hiding part of the data.
                // to do so, I compare element.clientWidth against element.scrollWidth;
                // when scrollWidth is bigger, that means we're hiding part of the data.
                // unfortunately, the ellipsis sometimes activates too early, meaning that even with clientWidth == scrollWidth some data is hidden by the ellipsis.
                // fortunately, these tooltips are just a convenience so I don't mind if they fail to show.
                // I don't know whether clientWidth or offsetWidth is better. clientWidth was more convenient in Chrome74.
                var e = cell.getElement();
                //return '' + e.offsetWidth + ' || ' + e.scrollWidth + ' || ' + e.clientWidth;
                if (e.clientWidth >= e.scrollWidth) {
                    return false; // all the text is shown, so there is no '...', so no tooltip is needed
                } else {
                    return cell.getValue();
                }
            },
            data: data,
            initialSort: [{column:"num_sig_assocs", dir:"desc"}],
        });
    });
});
