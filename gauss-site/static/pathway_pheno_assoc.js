'use strict';

$(function() {
    var data = window.model.genes;
    window._debug.table = new Tabulator('#table', {
        //height: 600, // setting height lets Tabulator's VirtualDOM load really fast but makes scrolling awkward
        layout: 'fitColumns',
        pagination: 'local',
        paginationSize: 100,
        columns: [
            {title: 'Gene Name', field:'name', headerFilter:true},
            {title: 'Chromosome', field:'chrom', headerFilter:true, headerFilterFunc:'='},
            {title: 'P-value', field:'pval', formatter:'2digit_fmt_nullable', sorter:function(a, b) {
                if (a === null) { a = 1.1 }
                if (b === null) { b = 1.1 }
                return a-b;
            }}, // TODO: treat `n/a` as 1.1 in sorting
            {title: '#SNPs', field:'num_snps', formatter:'comma_fmt'},
            {title: 'Selected by Method', field:'selected', headerFilter:true, },
        ],
        rowFormatter: function(row) {
            if (row.getData().selected) {
                row.getElement().style.fontWeight = 'bold';
            }
        },
        data: data,
        initialSort: [{column:'pval', dir:'asc'}, {column:'selected', dir:'desc'}], // later sorters take precedence
        tooltipGenerationMode:'hover',tooltips:tabulator_tooltip_maker,tooltipsHeader:true,
    });
 });
