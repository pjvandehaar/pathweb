#!/usr/bin/env python3

import sqlite3
from flask import g, Flask, jsonify, abort, render_template
from flask_compress import Compress
app = Flask(__name__)
Compress(app)

app.config['LZJS_VERSION'] = '0.9.0'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1

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
@app.route('/go')
def go():return 'not implemented yet'
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
    df = get_df('SELECT name,category,genesettype,pval FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=?', (pheno_id,))
    return jsonify(dict(assocs=df))

if __name__ == '__main__':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
    app.run(port=5000, debug=True)
