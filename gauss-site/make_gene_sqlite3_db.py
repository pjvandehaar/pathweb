#!/usr/bin/env python3
'''
This script creates `gene.db` which contains the pvalue for each (phenotype, gene) pair.
It's data populates the table at /pathway_pheno_assoc/GO_ODORANT_BINDING/079.1 .
It does not contain information about which genes are selected for each (phenotype, pathway) pair.
'''

import sqlite3, gzip, csv, os, itertools, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))

db_filepath = 'gene.db'

# get phenotypes
with sqlite3.connect('pheno_pathway_assoc.db') as conn:
    phecodes = sorted(row[0] for row in conn.execute('SELECT phecode FROM pheno'))
print('found', len(phecodes), 'phecodes')

# get genes
with sqlite3.connect('pheno_pathway_assoc.db') as conn:
    genes_in_pathways = set(itertools.chain.from_iterable(row[0].split(',') for row in conn.execute('SELECT genes_comma FROM pathway')))
with open('../input_data/gene_info.txt') as f:
    rows = csv.DictReader(f, delimiter='\t')
    gene_info = {row['Gene']: {'chrom':row['CHR'], 'num_snps':row['nSNP']} for row in rows if row['Gene'] in genes_in_pathways}

# make generator functions for populating the sqlite3 database
phecode_ids = {phecode:id_ for id_,phecode in enumerate(sorted(phecodes))}
gene_ids = {gene:id_ for id_,gene in enumerate(sorted(gene_info.keys()))}
def pheno_row_generator():
    for phecode,id_ in phecode_ids.items():
        yield (id_, phecode)
def gene_row_generator():
    for gene,id_ in gene_ids.items():
        g = gene_info[gene]
        yield (id_, gene, g['chrom'], g['num_snps'])
def pheno_gene_assoc_row_generator():
    for phecode, pheno_id in phecode_ids.items():
        print(' - reading pheno#{}: {}'.format(pheno_id, phecode))
        filepath = '../input_data/genes/OUTF_PheCode_{}.txt.gz'.format(phecode)
        with gzip.open(filepath, 'rt') as f:
            for row in csv.reader(f, delimiter='\t'):
                gene, pval_str = row
                if gene in gene_ids and pval_str != "NA":
                    yield (pheno_id, gene_ids[gene], float(pval_str))

# make the sqlite3 database
db_tmp_filepath = db_filepath + '.tmp.db'
if os.path.exists(db_tmp_filepath): os.unlink(db_tmp_filepath)
conn = sqlite3.connect(db_tmp_filepath)
with conn:
    conn.execute('CREATE TABLE pheno ('
                 'id INT PRIMARY KEY, '
                 'phecode TEXT)')
    conn.execute('CREATE TABLE gene ('
                 'id INT PRIMARY KEY,'
                 'name TEXT,'
                 'chrom TEXT,'
                 'num_snps INT)')
    conn.execute('CREATE TABLE pheno_gene ('
                 'id INT PRIMARY KEY,'
                 'pheno_id INT,'
                 'gene_id INT,'
                 'pval REAL,'
                 'FOREIGN KEY(pheno_id) REFERENCES pheno(id),'
                 'FOREIGN KEY(gene_id) REFERENCES gene(id))')
    conn.executemany('INSERT INTO pheno VALUES (?,?)', pheno_row_generator())
    conn.executemany('INSERT INTO gene VALUES (?,?,?,?)', gene_row_generator())
    conn.executemany('INSERT INTO pheno_gene (pheno_id, gene_id, pval) VALUES (?,?,?)',
                     pheno_gene_assoc_row_generator())
    conn.execute('CREATE INDEX idx_phenogene_ids ON pheno_gene (pheno_id,gene_id)')
print('finished ', db_tmp_filepath)
if os.path.exists(db_filepath): os.unlink(db_filepath)
os.rename(db_tmp_filepath, db_filepath)
print('moved to ', db_filepath)
