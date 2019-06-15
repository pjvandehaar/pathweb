#!/usr/bin/env python3

# TODO: support gzip/brotli compression
# TODO: use an in-memory redis cache

import sqlite3
from flask import g, Flask, jsonify, abort, render_template
from flask_compress import Compress
app = Flask(__name__)
Compress(app)

app.config['LZJS_VERSION'] = '0.9.0'

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
    cur = get_db().execute(query, args)
    colnames = [x[0] for x in cur.description]
    rows = cur.fetchall()
    cur.close()
    return {colname: [row[i] for row in rows] for i, colname in enumerate(colnames)}


@app.route('/')
def index_page():
    urls = '/api/pheno/041.4 /pathway/GO_COLLAGEN_BINDING /api/pathway/GO_COLLAGEN_BINDING /api/pathway_pheno_assoc/GO_ODORANT_BINDING/446.4 /static/phenos.json /static/pathways.json'.split()
    return '<br>'.join('<a href="{0}">{0}</a>'.format(url) for url in urls)

@app.route('/pathway/<pathway_name>')
def pathway_page(pathway_name):
    matches = list(get_db().execute('SELECT id,url,category,genesettype,genes_comma FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    url, category, genesettype, genes_comma = matches[0][1:]
    return render_template('pathway.html', pathway_name=pathway_name, url=url, category=category, genesettype=genesettype, genes_comma=genes_comma)

@app.route('/go')
def go():return 'autocomplete not yet implemented'
@app.route('/phenotypes')
def phenotypes_page():return 'not yet implemented'
@app.route('/pathways')
def pathways_page():return 'not yet implemented'
@app.route('/random')
def random_page():return 'not yet implemented'
@app.route('/about')
def about_page():return 'not yet implemented'


@app.route('/api/pathway/<pathway_name>')
def pathway_api(pathway_name):
    matches = list(get_db().execute('SELECT id,url,category,genesettype,genes_comma FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    pathway_id = matches[0][0]
    df = get_df('SELECT phecode,pval,selected_genes_comma FROM pheno_pathway_assoc '
                'LEFT JOIN pheno ON pheno_pathway_assoc.pheno_id=pheno.id '
                'WHERE pathway_id=? '
                'ORDER BY phecode', (pathway_id,))
    return jsonify(dict(url=matches[0][1], category=matches[0][2], genesettype=matches[0][3], genes=matches[0][4].split(','), phenos=df))

@app.route('/api/pheno/<phecode>')
def pheno_api(phecode):
    matches = list(get_db().execute('SELECT id FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)
    pheno_id = matches[0][0]
    df = get_df('SELECT name,category,genesettype,pval FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=?', (pheno_id,))
    return jsonify(df)

@app.route('/api/pathway_pheno_assoc/<pathway_name>/<phecode>')
def pathway_pheno_assoc_api(pathway_name, phecode):
    matches = list(get_db().execute('SELECT id FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)
    pheno_id = matches[0][0]

    matches = list(get_db().execute('SELECT id,url,category,genesettype FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    pathway_id = matches[0][0]

    df = get_df('SELECT pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=? AND pathway_id=?', (pheno_id, pathway_id))
    ret = {key: valuelist[0] for key,valuelist in df.items()}
    ret['selected_genes'] = ret.pop('selected_genes_comma').split(',')
    return jsonify(ret)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
    # from kpa.http_utils import run_gunicorn; run_gunicorn(app)
