#!/usr/bin/env python3

import sqlite3, re, itertools
from flask import g, Flask, jsonify, abort, render_template, request, url_for, redirect
from flask_compress import Compress
app = Flask(__name__)
Compress(app)

app.config['LZJS_VERSION'] = '0.9.0'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60*5

DATABASE = 'pheno_pathway_assoc.db'
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
def get_df(query, args=()):
    '''get a dataframe (eg, `{phecode:['008','008.5'],pval:[0.3,0.01]}`) from the database'''
    cur = get_db().execute(query, args)
    colnames = [x[0] for x in cur.description]
    rows = cur.fetchall()
    cur.close()
    return {colname: [row[i] for row in rows] for i, colname in enumerate(colnames)}


@app.route('/')
def index_page():
    return render_template('index.html')
@app.route('/about')
def about_page():
    return render_template('about.html')
@app.route('/phenotypes')
def phenotypes_page():
    return render_template('phenotypes.html')
@app.route('/pathways')
def pathways_page():
    return render_template('pathways.html')

@app.route('/pathway/<pathway_name>')
def pathway_page(pathway_name):
    matches = list(get_db().execute('SELECT id,url,category,genesettype,genes_comma FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    url, category, genesettype, genes_comma = matches[0][1:]
    return render_template('pathway.html', pathway_name=pathway_name, url=url, category=category, genesettype=genesettype, genes_comma=genes_comma)

@app.route('/pheno/<phecode>')
def pheno_page(phecode):
    matches = list(get_db().execute('SELECT id,phenostring,category FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)
    phenostring, category = matches[0][1:]
    return render_template('pheno.html', phecode=phecode, phenostring=phenostring, category=category)

@app.route('/pathway_pheno_assoc/<pathway_name>/<phecode>')
def pathway_pheno_assoc_page(pathway_name, phecode):
    matches = list(get_db().execute('SELECT id,phenostring,category FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)
    pheno_id, phenostring, pheno_category = matches[0]

    matches = list(get_db().execute('SELECT id,url,category,genesettype,genes_comma FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    pathway_id, pathway_url, pathway_category, pathway_genesettype = matches[0][:-1]
    genes = matches[0][-1].split(',')

    matches = list(get_db().execute('SELECT pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=? AND pathway_id=?', (pheno_id, pathway_id)))
    if not matches: return abort(404)
    pval, selected_genes = matches[0][0], matches[0][1].split(',')
    return render_template('pathway_pheno_assoc.html',
                           phecode=phecode, phenostring=phenostring, pheno_category=pheno_category,
                           pathway_name=pathway_name, pathway_url=pathway_url, pathway_category=pathway_category, pathway_genesettype=pathway_genesettype,
                           pval=pval, genes=genes, selected_genes=selected_genes)


@app.route('/api/pathway/<pathway_name>')
def pathway_api(pathway_name):
    matches = list(get_db().execute('SELECT id,url,category,genesettype,genes_comma FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    pathway_id = matches[0][0]
    df = get_df('SELECT phecode,phenostring,category,num_cases,num_controls,pval,selected_genes_comma FROM pheno_pathway_assoc '
                'LEFT JOIN pheno ON pheno_pathway_assoc.pheno_id=pheno.id '
                'WHERE pathway_id=? '
                'ORDER BY phecode', (pathway_id,))
    return jsonify(dict(url=matches[0][1], category=matches[0][2], genesettype=matches[0][3], genes=matches[0][4].split(','), assocs=df))

@app.route('/api/pheno/<phecode>')
def pheno_api(phecode):
    matches = list(get_db().execute('SELECT id FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)
    pheno_id = matches[0][0]
    df = get_df('SELECT name,category,genesettype,pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=?', (pheno_id,))
    for i in range(len(df['name'])):
        if not df['pval'][i] <= 1e-5:
            df['selected_genes_comma'][i] = ''
    return jsonify(dict(assocs=df))


class Autocompleter:
    def __init__(self):
        phenos_df = get_df('SELECT phecode,phenostring,category FROM pheno')
        self.phenos = [{key: phenos_df[key][i] for key in phenos_df} for i in range(len(next(iter(phenos_df.values()))))]
        self.phenos.sort(key=lambda p:float(p['phecode']))
        for p in self.phenos:
            p['phenostring--processed'] = self.process_string(p['phenostring'])
        pathway_names = sorted(get_df('SELECT name FROM pathway')['name'])
        self.pathways = [{'pathway_name': name} for name in pathway_names]
        for p in self.pathways:
            p['pathway_name--processed'] = self.process_string(p['pathway_name']).replace('_', ' ')
    non_word_regex = re.compile(r"(?:_|[^\w\.])") # Most of the time we want to include periods in words but not underscores
    def process_string(self, string):
        # Cleaning inspired by <https://github.com/seatgeek/fuzzywuzzy/blob/6353e2/fuzzywuzzy/utils.py#L69>
        return ' ' + self.non_word_regex.sub(' ', string).lower().strip()
    def get_completions(self, query):
        processed_query = self.process_string(query) # replace junk with spaces and use lower-case
        for f in [self.get_completions_on_phecode, self.get_completions_on_phenostring, self.get_completions_on_pathwayname]:
            results = list(itertools.islice(f(processed_query), 0, 10))
            if results: return results
        return []
    def get_best_completion(self, query):
        completions = self.get_completions(query)
        if not completions: return None
        return completions[0] # TODO
    def get_completions_on_phecode(self, processed_query):
        processed_query = processed_query.strip()
        if not re.match(r'^[0-9]+(?:\.[0-9]*)?$', processed_query): return
        for p in self.phenos:
            if p['phecode'].startswith(processed_query):
                yield {
                    'value': p['phecode'],
                    'display': '{} ({})'.format(p['phecode'], p['phenostring']),
                    'url': url_for('pheno_page', phecode=p['phecode'])
                }
    def get_completions_on_phenostring(self, processed_query):
        if len(processed_query) == 0: return
        for p in self.phenos:
            if processed_query in p['phenostring--processed']:
                yield {
                    'value': p['phenostring'],
                    'display': '{} ({})'.format(p['phenostring'], p['phecode']),
                    'url': url_for('pheno_page', phecode=p['phecode'])
                }
    def get_completions_on_pathwayname(self, processed_query):
        if len(processed_query) == 0: return
        for p in self.pathways:
            if processed_query in p['pathway_name--processed']:
                yield {
                    'value': p['pathway_name'],
                    'display': p['pathway_name'],
                    'url': url_for('pathway_page', pathway_name=p['pathway_name']),
                }

def get_autocompleter():
    a = getattr(g, '_autocompleter', None)
    if a is None: a = g._autocompleter = Autocompleter()
    return a
@app.route('/api/autocomplete')
def autocomplete_api():
    '''generate suggestions for the searchbox'''
    query = request.args.get('query', '')
    suggestions = get_autocompleter().get_completions(query)
    if suggestions:
        return jsonify(sorted(suggestions, key=lambda sugg: sugg['display']))
    return jsonify([])
@app.route('/go')
def go():
    '''attempt to send the user to a relevant page after they hit enter on the searchbox'''
    query = request.args.get('query', None)
    if query is None: return redirect(url_for('index_page'))
    best_suggestion = get_autocompleter().get_best_completion(query)
    if not best_suggestion: return redirect(url_for('index_page'))
    return redirect(best_suggestion['url'])



if __name__ == '__main__':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
    app.run(port=5000, debug=True)
