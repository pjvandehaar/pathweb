#!/usr/bin/env python3

# phenotypes.json - [{phecode:'008', category:'infectious diseases', num_sig_assocs:47}, ...]
# pathways.json - [{name:'KEGG_FOO', category:'GCP', num_sig_assocs:24}, ...]

# MAYBE: use sqlite instead of json so that the browser can page?

import sqlite3, json, os
conn = sqlite3.connect('pheno_pathway_assoc.db')
conn.row_factory = sqlite3.Row

pathway_by_id = {}
for row in conn.execute('SELECT * FROM pathway'):
    pathway_by_id[row['id']] = dict(
        name=row['name'], category=row['category'],
        num_sig_assocs=0, has_assocs=False)
pheno_by_id = {}
for row in conn.execute('SELECT * FROM pheno'):
    pheno_by_id[row['id']] = dict(
        phecode=row['phecode'], phenostring=row['phenostring'], category=row['category'],
        num_cases=row['num_cases'], num_controls=row['num_controls'],
        num_sig_assocs=0, has_assocs=False)

for i, row in enumerate(conn.execute('SELECT * FROM pheno_pathway_assoc')):
    if i % 1_000_000 == 0: print(i)
    pval = row['pval']
    pathway = pathway_by_id[row['pathway_id']]
    pheno = pheno_by_id[row['pheno_id']]
    pathway['has_assocs'] = pheno['has_assocs'] = True
    if pval < 1e-4:
        pheno['num_sig_assocs'] += 1
        pathway['num_sig_assocs'] += 1

pathway_by_id = {id_:pathway for for id_,pathway in pathway_by_id.items() if not pathway['has_assocs']}
pheno_by_id = {id_:pheno for for id_,pheno in pheno_by_id.items() if not pheno['has_assocs']}

if not os.path.exists('static'): os.mkdir('static')
with open('static/phenotypes.json', 'w') as f: json.dump(list(pheno_by_id.values()), f, separators=(',', ':'))
with open('static/pathways.json', 'w') as f: json.dump(list(pathway_by_id.values()), f, separators=(',', ':'))
