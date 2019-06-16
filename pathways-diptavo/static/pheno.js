'use strict';

LocusZoom.TransformationFunctions.set("underscore_breaker", function(x) { return x.replace(/_/g, '_<wbr>'); });
LocusZoom.TransformationFunctions.set("space_after_comma", function(x) { return x.replace(/,/g, ', '); });

$.getJSON('/api/pheno/'+model.phecode).then(function(resp) {
    // fields = genesettype, category, name, pval
    var assocs = resp.assocs;
    assocs.id = assocs.name;
    assocs.trait_label = assocs.name;
    assocs.log_pvalue = assocs.pval.map(function(p) { return -Math.log10(Math.max(1e-6, p)); });
    assocs.trait_group = assocs.category;

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
                margin: {top: 5, right: 5, bottom: 110, left: 50 }
            })
        ],
    }

    layout.panels[0].data_layers[0].offset = significance_threshold;
    layout.panels[0].data_layers[1].fields.push('phewas:genesettype');
    layout.panels[0].data_layers[1].tooltip.html =
        ("<strong>{{phewas:trait_label|htmlescape|underscore_breaker}}</strong><br>" +
         "Category: <strong>{{phewas:genesettype|htmlescape}} / {{phewas:trait_group|htmlescape}}</strong><br>" +
         "P-value: <strong>{{phewas:log_pvalue|logtoscinotation|htmlescape}}</strong><br>"
        );
    layout.panels[0].data_layers[1].behaviors.onclick = [{action: 'link', href: '/pathway_pheno_assoc/{{phewas:id}}/'+model.phecode}];
    layout.panels[0].data_layers[1].y_axis.min_extent = [0, significance_threshold*1.1];

    if (assocs.id.length <= 10) {
        layout.panels[0].data_layers[1].label.filters = [];
    } else if (assocs.log_pvalue.filter(function(nlpval) { return nlpval == best_nlpval; }).length >= 6) {
        layout.panels[0].data_layers[1].label = false; // if too many are tied for 1st, it'll be a mess so don't show any labels
    } else {
        var eighth_best_nlpval = _.sortBy(assocs.log_pvalue).reverse()[8];
        layout.panels[0].data_layers[1].label.filters = [
            {field: 'phewas:log_pvalue', operator: '>', value: significance_threshold},
            {field: 'phewas:log_pvalue', operator: '>', value: best_nlpval*0.5}, // must be in top half of screen
            {field: 'phewas:log_pvalue', operator: '>=', value: eighth_best_nlpval} // must be among the best
        ];
    }

    window._debug.assocs = assocs;
    $(function() {
        var plot = LocusZoom.populate("#phewas_plot_container", data_sources, layout);
        window._debug.plot = plot;
        // if we have >3000 assocs, hide all points with logp<1, unless that leaves <1000 assocs, in which case just show the top 2000 assocs
        if (assocs.id.length > 3000) {
            setTimeout(function() {
                // I think setTimeout is required because `plot.panels.phewas.data_layers.phewaspvalues.data` is not populated until some async happens
                // TODO: find a way to have all elements hidden during the first render and then unhide
                var visibility_nlpval_threshold = 1;
                if (plot.panels.phewas.data_layers.phewaspvalues.filter([['phewas:log_pvalue', '>', visibility_nlpval_threshold]]).length >= 1000) {
                    plot.panels.phewas.data_layers.phewaspvalues.hideElementsByFilters([['phewas:log_pvalue', '<=', visibility_nlpval_threshold]]);
                } else {
                    plot.panels.phewas.data_layers.phewaspvalues.hideElementsByFilters([['phewas:log_pvalue', '<=', _.sortBy(assocs.log_pvalue).reverse()[2000]]]);
                }
            }, 10);
        }
    });

    $(function() {
        var data = dataframe_to_objects(assocs);
        var table = new Tabulator('#table', {
            //height: 600, // setting height lets Tabulator's VirtualDOM load really fast but makes scrolling awkward
            layout: 'fitColumns',
            pagination: 'local',
            paginationSize: 15,
            columns: [
                {title: 'Category', field:'category'},
                {title: 'Pathway', field:'name', formatter:'link', formatterParams: {url:function(cell){return '/pathway_pheno_assoc/'+cell.getValue()+'/'+model.phecode}}, widthGrow:5},
                {title: 'P-value', field:'pval'},
            ],
            data: data,
            initialSort: [{column:'pval', dir:'asc'}],
        });
    });
});
