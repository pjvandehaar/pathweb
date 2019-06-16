#!/usr/bin/env python3

import os, re, glob, gzip, sqlite3, itertools, csv

# make list of phenotypes: phecode
filenames = os.listdir('input_data/phenos-2019may')
for fname in filenames:
    assert re.match(r'PheCode_([0-9]{3,4}(?:\.[0-9]{1,2})?)_(Curated|GO).wConditional.txt.gz$', fname), fname
phecode_and_genesettype = set(re.match(r'PheCode_([0-9]{3,4}(?:\.[0-9]{1,2})?)_(Curated|GO).wConditional.txt.gz$', fname).groups() for fname in filenames)
assert len(phecode_and_genesettype) == len(filenames) # all unique
phecodes = set(p_g[0] for p_g in phecode_and_genesettype)
genesettypes = set(p_g[1] for p_g in phecode_and_genesettype)
for phecode in phecodes:
    for genesettype in genesettypes:
        assert (phecode, genesettype) in phecode_and_genesettype, (phecode, genesettype)
print(len(phecodes), 'phecodes')
phenos = {}
for i, row in enumerate(csv.reader(open('input_data/Phenotype_Color.csv'), delimiter=',')):
    # "Number.of.excluded.controls" contains a variable number of commas and so does "Phenotype.Description"
    if i==0: continue
    phecode = row[0]
    num_cases = int(row[1])
    num_controls = int(row[2])
    # phenostring = row[6]
    # category = row[7]
    url_idx = [idx for idx,cell in enumerate(row) if cell.startswith('http')][0]
    last_int_idx = [idx for idx,cell in enumerate(row) if cell.isdigit()][-1]
    category = row[url_idx-1]
    phenostring = ','.join(row[last_int_idx+1:url_idx-1])
    assert 3 <= len(phenostring) < 200, repr(phenostring)
    phenos[phecode] = {
        'phenostring': phenostring,
        'num_cases': num_cases,
        'num_controls': num_controls,
        'category': category,
    }
for phecode in phecodes: assert phecode in phenos, phecode
assert 2 <= len(set(p['category'] for p in phenos.values())) < 100

# make list of pathways: name, url, genesettype(Curated/GO), category, genes
assert genesettypes == {'GO', 'Curated'} # sanity-check
pathways = {}
for genesettype in genesettypes:
    with open('input_data/GMT_files/' + genesettype + '_Subclass.dat') as f:
        for row in csv.DictReader(f, delimiter=' ', fieldnames=['name','url','category']):
            if row['name'] == 'NA': continue
            assert row['name'] not in pathways, row
            pathways[row['name']] = dict(url=row['url'], category=row['category'], genesettype=genesettype)
print(len(pathways), 'pathways')
for gmt_filepath in glob.glob('input_data/GMT_files/*.gmt.dat'):
    # note: `.gmt.dat` files appear to just be reformatted versions of the `.gmt` files
    num_matching, num_lines = 0, 0
    with open(gmt_filepath) as f:
        for i, line in enumerate(f):
            if i == 0:
                assert line.split() == 'GeneSet DESC Genes'.split(), (gmt_filepath, line)
            else:
                name, url, genes_string = line.split()
                genes = genes_string.split(',')
                for gene in genes:
                    assert re.match(r'^[-A-Za-z0-9\.@]+$', gene), gene # who named `TRB@`?
                if name in pathways: num_matching += 1
                num_lines += 1
                assert len(genes) >= 1
                if name in pathways:
                    assert pathways[name]['url'] == url
                    pathways[name]['genes'] = genes
    # print(f'{num_matching/num_lines:.2f} {num_matching:4} {num_lines:4} {gmt_filepath}')
    if num_matching == num_lines:
        assert os.path.basename(gmt_filepath).startswith(('C2', 'C5'))
    elif num_matching == 0:
        assert not os.path.basename(gmt_filepath).startswith(('C2', 'C5'))
    else:
        raise Exception('some but not all pathway names match in ' + gmt_filepath)
assert set(d['category'] for d in pathways.values()) == set('KEGG MOLECULAR BIOCARTA BIOLOGICAL_PROC OTHER-CANONICAL CELLULAR CGP REACTOME'.split())


# make mapping of (phenotype, pathway) -> (pval, selected_genes)
# store in sqlite3 as table (pheno, pathway, pval, selected_genes)
phecode_ids = {phecode: id_ for id_, phecode in enumerate(sorted(phecodes))}
pathway_ids = {name: id_ for id_, name in enumerate(sorted(pathways.keys()))}
def pheno_row_generator():
    for phecode,id_ in phecode_ids.items():
        p = phenos[phecode]
        yield (id_, phecode, p['phenostring'], p['category'])

def pathway_row_generator():
    for pathwayname, id_ in pathway_ids.items():
        d = pathways[pathwayname]
        yield (id_, pathwayname, d['url'], d['category'], d['genesettype'], ','.join(d['genes']))

def pheno_pathway_assoc_row_generator(): # note: primary key not included
    for i, (phecode, genesettype) in enumerate(itertools.product(phecodes, genesettypes)):
        phecode_id = phecode_ids[phecode]
        filename = 'PheCode_{}_{}.wConditional.txt.gz'.format(phecode, genesettype)
        print(i, filename)
        with gzip.open('input_data/phenos-2019may/' + filename, 'rt') as f:
            for line in f:
                name, url, pval_string, _, selected_genes_string, _ = line.split()
                if pval_string == 'NA' and selected_genes_string == 'NA':
                    # I don't know why these lines exist but there's a lot of them.
                    continue
                selected_genes = selected_genes_string.split(',')
                try:
                    assert name in pathways, line
                    assert pathways[name]['url'] == url, line
                    assert pval_string == '0' or 1e-6 <= float(pval_string) <= 1, line
                    assert 1 <= len(selected_genes) < 20e3, line
                    assert all(g in pathways[name]['genes'] for g in selected_genes), line
                except Exception: raise Exception(line)
                pval = 1e-6 if pval_string=='0' else float(pval_string)
                yield (phecode_id, pathway_ids[name], pval, selected_genes_string)

db_fname = 'pheno_pathway_assoc.db'
if os.path.exists(db_fname): raise Exception(db_fname + ' already exists, please delete')
conn = sqlite3.connect(db_fname)
with conn: # this commits insertions
    conn.execute('create table pheno (id INTEGER PRIMARY KEY, phecode VARCHAR, phenostring VARCHAR, category VARCHAR)')
    conn.execute('create table pathway (id INTEGER PRIMARY KEY, name VARCHAR, url VARCHAR, category VARCHAR, genesettype VARCHAR, genes_comma VARCHAR)')
    conn.execute('create table pheno_pathway_assoc (id INTEGER PRIMARY KEY, pheno_id INTEGER, pathway_id INTEGER, pval REAL, selected_genes_comma VARCHAR, FOREIGN KEY(pheno_id) REFERENCES pheno(id), FOREIGN KEY(pathway_id) REFERENCES pathway(id))')

    conn.executemany('INSERT INTO pheno VALUES (?,?,?,?)', pheno_row_generator())
    conn.executemany('INSERT INTO pathway VALUES (?,?,?,?,?,?)', pathway_row_generator())
    conn.executemany('INSERT INTO pheno_pathway_assoc (pheno_id, pathway_id, pval, selected_genes_comma) VALUES (?,?,?,?)', pheno_pathway_assoc_row_generator())

    conn.execute('CREATE INDEX idx_assoc_pheno_id ON pheno_pathway_assoc (pheno_id)')
    conn.execute('CREATE INDEX idx_assoc_pathway_id ON pheno_pathway_assoc (pathway_id)')
