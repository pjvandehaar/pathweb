#!/usr/bin/env python3

# TODO: support gzip/brotli compression

import sqlite3
from flask import g, Flask, jsonify, abort, send_file
app = Flask(__name__)

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
def index():
    return 'foo'

@app.route('/api/pathway/<pathway_name>')
def pathway_api(pathway_name):
    matches = list(get_db().execute('SELECT id,url,category,genesettype,genes_comma FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    pathway_id = matches[0][0]
    df = get_df('SELECT phecode,pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pheno ON pheno_pathway_assoc.pheno_id=pheno.id WHERE pathway_id=? LIMIT 40', (pathway_id,))
    return jsonify(dict(url=matches[0][1], category=matches[0][2], genesettype=matches[0][3], genes=matches[0][4].split(','), phenos=df))

@app.route('/api/pheno/<phecode>')
def pheno_api(phecode):
    matches = list(get_db().execute('SELECT id FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)
    pheno_id = matches[0][0]
    df = get_df('SELECT name,category,genesettype,pval FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=? LIMIT 40', (pheno_id,))
    return jsonify(df)

@app.route('/api/pathway_pheno_assoc/<pathway_name>/<phecode>')
def pathway_pheno_assoc_api(pathway_name, phecode):
    matches = list(get_db().execute('SELECT id FROM pheno WHERE phecode=?', (phecode,)))
    if not matches: return abort(404)

    matches = list(get_db().execute('SELECT id,url,category,genesettype FROM pathway WHERE name = ?', (pathway_name,)))
    if not matches: return abort(404)
    pathway_id = matches[0][0]

    df = get_df('SELECT pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=? AND pathway_id=?', (pheno_id, pathway_id))
    return jsonify(df)

@app.route('/api/phenos.json')
def phenos():
    return send_file('phenos.json')
@app.route('/api/pathways.json')
def pathways():
    return send_file('pathways.json')

if __name__ == '__main__':
    from kpa.http_utils import run_gunicorn
    run_gunicorn(app)
