#!/usr/bin/env python3

# phenos.json - [{phecode:'008', best_pval:1e-5, best_assoc:'KEGG_FOO', num_sig_assocs:47}, ...]
# pathways.json - [{name:'KEGG_FOO', best_pval:1e-5, best_assoc:'008', num_sig_assocs:24}, ...]

# TODO: include selected_genes for the best pathways?
# MAYBE: use sqlite instead of json so that the browser can page?

import sqlite3, json
conn = sqlite3.connect('pheno_pathway_assoc.db')
conn.row_factory = sqlite3.Row

pathway_by_id = {}
for row in conn.execute('SELECT * FROM pathway'):
    pathway_by_id[row['id']] = dict(name=row['name'], best_pval=999, best_assoc=None, num_sig_assocs=0)
pheno_by_id = {}
for row in conn.execute('SELECT * FROM pheno'):
    pheno_by_id[row['id']] = dict(phecode=row['phecode'], best_pval=999, best_assoc=None, num_sig_assocs=0)

for i, row in enumerate(conn.execute('SELECT * FROM pheno_pathway_assoc')):
    if i % 1_000_000 == 0: print(i)
    pval = row['pval']
    pathway = pathway_by_id[row['pathway_id']]
    pheno = pheno_by_id[row['pheno_id']]
    if pval < pathway['best_pval']: pathway['best_pval'], pathway['best_assoc'] = pval, pheno['phecode']
    if pval < pheno['best_pval']:   pheno['best_pval'],   pheno['best_assoc'] =   pval, pathway['name']
    if pval < 1e-4:
        pheno['num_sig_assocs'] += 1
        pathway['num_sig_assocs'] += 1

with open('phenos.json', 'w') as f: json.dump(sorted(pheno_by_id.values(), key=lambda x:x['best_pval']), f, separators=(',', ':'))
with open('pathways.json', 'w') as f: json.dump(sorted(pathway_by_id.values(), key=lambda x:x['best_pval']), f, separators=(',', ':'))
