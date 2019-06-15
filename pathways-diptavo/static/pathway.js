'use strict';

LocusZoom.TransformationFunctions.set("space_after_comma", function(x) { return x.replace(/,/g, ', '); });
LocusZoom.TransformationFunctions.set("linewrap", function(x) { return x.replace(/,/g, ', '); });

$.getJSON('/api/pathway/'+model.pathway_name).then(function(resp) {
    var phenos = resp.phenos;
    phenos.id = phenos.phecode;
    phenos.trait_label = phenos.phecode;
    phenos.log_pvalue = phenos.pval.map(function(p) { return -Math.log10(Math.max(1e-6, p)); });
    phenos.trait_group = phenos.phecode.map(function(phecode, i) {
        return (i < phenos.id.length*.7) ? 'category_a' : 'category_b';
    });

    var significance_threshold = -Math.log10(0.05 / phenos.id.length);
    var best_nlpval = d3.max(phenos.log_pvalue);

    var data_sources = new LocusZoom.DataSources().add('phewas', ['StaticJSON', phenos]);
    var layout = {
        width: 800,
        height: 400,
        min_width: 800,
        min_height: 400,
        responsive_resize: 'width_only',
        mouse_guide: false,
        dashboard: {components: [ {type: 'download', position: 'right', color: 'gray' } ]},
        panels: [
            LocusZoom.Layouts.get('panel', 'phewas')
        ],
    }
    layout.panels[0].data_layers[0].offset = significance_threshold;
    layout.panels[0].data_layers[1].fields.push('phewas:selected_genes_comma');
    layout.panels[0].data_layers[1].tooltip.html =
        ("<strong>Phecode</strong> {{phewas:trait_label|htmlescape}}<br>" +
         "<strong>Category:</strong> {{phewas:trait_group|htmlescape}}<br>" +
         "<strong>P-value:</strong> {{phewas:log_pvalue|logtoscinotation|htmlescape}}<br>" +
         "<strong>Selected Genes:</strong> {{phewas:selected_genes_comma|space_after_comma|htmlescape}}<br>");
    layout.panels[0].data_layers[1].behaviors.onclick = [{action: 'link', href: '/pheno/{{phewas:trait_label}}'}];

    if (phenos.log_pvalue.filter(function(nlpval) { return nlpval == best_nlpval; }).length >= 13){
        layout.panels[0].data_layers[1].label = false; // if 13 are all tied for 1st, it'll be a mess so don't show any labels
    } else if (phenos.id.length <= 10) {
        layout.panels[0].data_layers[1].label.filters = []; // if len(phenos)<=10, show all labels
    } else {
        var tenth_best_nlpval = _.sortBy(phenos.log_pvalue).reverse()[10];
        layout.panels[0].data_layers[1].label.filters = [
            {field: 'phewas:log_pvalue', operator: '>', value: significance_threshold},
            {field: 'phewas:log_pvalue', operator: '>', value: best_nlpval*0.5}, // must be in top half of screen
            {field: 'phewas:log_pvalue', operator: '>=', value: tenth_best_nlpval} // must be in top 10
        ];
    }

    window._debug.phenos = phenos;
    $(function() {
        window._debug.plot = LocusZoom.populate("#phewas_plot_container", data_sources, layout);
    });
});
