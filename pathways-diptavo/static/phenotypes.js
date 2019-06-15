'use strict';

$.getJSON('/static/phenotypes.json').then(function(phenotypes) {
    console.log(phenotypes);
    $(document).ready(function() {
        var table = new Tabulator('#phenotypes_table', {
//            height: 600, // setting height lets Tabulator's VirtualDOM load really fast but makes scrolling awkward
            layout: 'fitColumns',
            pagination: 'local',
            paginationSize: 100,
            columns: [
                {title: 'Name', field:'phecode', formatter:'link', formatterParams: { urlPrefix: '/pheno/' }},
                {title: 'Num p<10<sup>-4</sup> Associations', field:'num_sig_assocs', width:200},
                {title: 'Best Pathway', field:'best_assoc', widthGrow:5},
                {title: 'Best P-value', field:'best_pval'},
            ],
        });
        table.setData(phenotypes);
    });
});
