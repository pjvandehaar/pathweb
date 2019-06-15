'use strict';

$.getJSON('/static/phenotypes.json').then(function(phenotypes) {
    console.log(phenotypes);
    $(document).ready(function() {
        var table = new Tabulator('#phenotypes_table', {
            height: 600,
            layout: 'fitColumns',
            pagination: 'local',
            paginationSize: 100,
            columns: [
                {title: 'Name', field:'phecode', formatter:'link', formatterParams: { urlPrefix: '/pheno/' }},
                {title: 'Num Associations p<10^-4', field:'num_sig_assocs'},
                {title: 'Best Pathway', field:'best_assoc'},
                {title: 'Best P-value', field:'best_pval'},
            ],
        });
        table.setData(phenotypes);
    });
});
