#!/usr/bin/env python3

import sqlite3
conn = sqlite3.connect('pheno_pathway_assoc.db')
def iterlen(iterable): return sum(1 for _ in iterable)
def print_row(cursor):
    colnames = [x[0] for x in cursor.description]
    for key, val in zip(colnames, curs.fetchone()):
        print(' - {:12} - {}'.format(key, val))
    print('... {} more'.format(iterlen(cursor)))

# GIVEN PATHWAY NAME, GET PHEWAS DATA (INCLUDING SELECTED GENES FOR P<.01)
pathway_name = 'ABBUD_LIF_SIGNALING_1_DN'
matches = list(conn.execute('SELECT id,url,category,genesettype FROM pathway WHERE name = ?', (pathway_name,)))
assert matches
print(' :: '.join(reversed(matches[0][1:])))
pathway_id = matches[0][0]
curs = conn.execute('SELECT phecode,pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pheno ON pheno_pathway_assoc.pheno_id=pheno.id WHERE pathway_id=?', (pathway_id,))
print_row(curs)

# GIVEN PHECODE, GET PATHWAS (INCLUDING SELECTED GENES FOR P<.01)
phecode = '965.2'
pheno_id = list(conn.execute('SELECT id FROM pheno WHERE phecode=?', (phecode,)))[0][0]
print('\n'+phecode)
curs = conn.execute('SELECT name,url,category,genesettype,pval,selected_genes_comma,genes_comma FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=?', (pheno_id,))
print_row(curs)

# GIVEN PATHWAY NAME + PHECODE, GET CONNECTED GENES
print('\nassoc')
curs = conn.execute('SELECT pval,selected_genes_comma FROM pheno_pathway_assoc LEFT JOIN pathway ON pheno_pathway_assoc.pathway_id=pathway.id WHERE pheno_id=? AND pathway_id=?', (pheno_id, pathway_id))
print_row(curs)
