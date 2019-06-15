'use strict';

LocusZoom.TransformationFunctions.set("underscore_breaker", function(x) { return x.replace(/_/g, '_<wbr>'); });
LocusZoom.TransformationFunctions.set("space_after_comma", function(x) { return x.replace(/,/g, ', '); });

$.getJSON('/api/pathway/'+model.pathway_name).then(function(resp) {
    // fields = phecode, pval, selected_genes_comma
    var assocs = resp.assocs;
    assocs.id = assocs.phecode;
    assocs.trait_label = assocs.phecode;
    assocs.log_pvalue = assocs.pval.map(function(p) { return -Math.log10(Math.max(1e-6, p)); });
    assocs.trait_group = assocs.id.map(function(x, i) { return (i < assocs.id.length*.7) ? 'category_a' : 'category_b'; });

    var significance_threshold = -Math.log10(0.05 / assocs.id.length);
    var best_nlpval = d3.max(assocs.log_pvalue);

    var data_sources = new LocusZoom.DataSources().add('phewas', ['StaticJSON', assocs]);
    var layout = {
        width: 800,
        height: 400,
        min_width: 800,
        min_height: 400,
        responsive_resize: 'width_only',
        mouse_guide: false,
        dashboard: {components: [ {type: 'download', position: 'right', color: 'gray' } ]},
        panels: [
            LocusZoom.Layouts.get('panel', 'phewas', {
                margin: {top: 5, right: 5, bottom: 80, left: 50 }
            })
        ],
    }

    layout.panels[0].data_layers[0].offset = significance_threshold;
    layout.panels[0].data_layers[1].fields.push('phewas:selected_genes_comma');
    layout.panels[0].data_layers[1].tooltip.html =
        ("<strong>{{phewas:trait_label|htmlescape}}</strong><br>" +
         "Category: <strong>{{phewas:trait_group|htmlescape}}</strong><br>" +
         "P-value: <strong>{{phewas:log_pvalue|logtoscinotation|htmlescape}}</strong><br>" +
         "Selected Genes: <strong>{{phewas:selected_genes_comma|space_after_comma|htmlescape}}</strong><br>"
        );
    layout.panels[0].data_layers[1].behaviors.onclick = [{action: 'link', href: '/pathway_pheno_assoc/'+model.pathway_name+'/{{phewas:trait_label}}'}];
    layout.panels[0].data_layers[1].y_axis.min_extent = [0, significance_threshold*1.1];

    if (assocs.log_pvalue.filter(function(nlpval) { return nlpval == best_nlpval; }).length >= 13){
        layout.panels[0].data_layers[1].label = false; // if 13 are all tied for 1st, it'll be a mess so don't show any labels
    } else if (assocs.id.length <= 10) {
        layout.panels[0].data_layers[1].label.filters = []; // if len(assocs)<=10, show all labels
    } else {
        var tenth_best_nlpval = _.sortBy(assocs.log_pvalue).reverse()[10];
        layout.panels[0].data_layers[1].label.filters = [
            {field: 'phewas:log_pvalue', operator: '>', value: significance_threshold},
            {field: 'phewas:log_pvalue', operator: '>', value: best_nlpval*0.5}, // must be in top half of screen
            {field: 'phewas:log_pvalue', operator: '>=', value: tenth_best_nlpval} // must be in top 10
        ];
    }

    window._debug.assocs = assocs;
    $(function() {
        window._debug.plot = LocusZoom.populate("#phewas_plot_container", data_sources, layout);
    });

    $(function() {
        var data = dataframe_to_objects(assocs);
        var table = new Tabulator('#table', {
            //height: 600, // setting height lets Tabulator's VirtualDOM load really fast but makes scrolling awkward
            layout: 'fitColumns',
            pagination: 'local',
            paginationSize: 15,
            columns: [
                {title: 'Name', field:'phecode', formatter:'link', formatterParams: { urlPrefix: '/pathway_pheno_assoc/'+model.pathway_name+'/' }},
                {title: 'P-value', field:'pval'},
                {title: 'Selected Genes', field:'selected_genes_comma', widthGrow:5, formatter: function(cell) { return cell.getValue().replace(/,/g, ', ') }},
            ],
            data: data,
            initialSort: [{column:'pval', dir:'asc'}],
        });
    });
});
