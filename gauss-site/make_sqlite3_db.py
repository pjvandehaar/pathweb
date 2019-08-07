#!/usr/bin/env python3

import re, gzip, sqlite3, itertools, csv
from pathlib import Path
dir_path = Path(__file__).absolute().parent
input_dir_path = dir_path.parent / 'input_data'
pheno_dir_path = input_dir_path / 'pathways'
gmt_dir_path = input_dir_path / 'GMT_files'

# make list of phenotypes: phecode
filenames = [path.name for path in pheno_dir_path.iterdir()]
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
for row in csv.DictReader(open(input_dir_path / 'phenotype-colors.csv')):
    def _int(s): num = int(s.replace(',','')); assert num >= 0, s; return num
    phenos[row['PheCode']] = {
        'phenostring': row['Phenotype.Description'],
        'category': row['Phenotype.Category'],
        'num_cases': _int(row['Number.of.cases']),
        'num_controls': _int(row['Number.of.controls']),
        'num_excluded_controls': _int(row['Number.of.excluded.controls']),
    }
for phecode in phecodes: assert phecode in phenos, phecode
assert 2 <= len(set(p['category'] for p in phenos.values())) < 100

# make list of pathways: name, url, genesettype(Curated/GO), category, genes
assert genesettypes == {'GO', 'Curated'} # sanity-check
pathways = {}
for genesettype in genesettypes:
    with open(gmt_dir_path / '{}_Subclass.dat'.format(genesettype)) as f:
        for row in csv.DictReader(f, delimiter=' ', fieldnames=['name','url','category']):
            if row['name'] == 'NA': continue
            assert row['name'] not in pathways, row
            pathways[row['name']] = dict(url=row['url'], category=row['category'], genesettype=genesettype)
print(len(pathways), 'pathways')
for gmt_filepath in gmt_dir_path.glob('*.gmt.dat'):
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
        assert gmt_filepath.name.startswith(('C2', 'C5'))
    elif num_matching == 0:
        assert not gmt_filepath.name.startswith(('C2', 'C5'))
    else:
        raise Exception('some but not all pathway names match in {}'.format(gmt_filepath))
assert set(d['category'] for d in pathways.values()) == set('KEGG MOLECULAR BIOCARTA BIOLOGICAL_PROC OTHER-CANONICAL CELLULAR CGP REACTOME'.split())


# make mapping of (phenotype, pathway) -> (pval, selected_genes)
# store in sqlite3 as table (pheno, pathway, pval, selected_genes)
phecode_ids = {phecode: id_ for id_, phecode in enumerate(sorted(phecodes))}
pathway_ids = {name: id_ for id_, name in enumerate(sorted(pathways.keys()))}
def pheno_row_generator():
    for phecode,id_ in phecode_ids.items():
        p = phenos[phecode]
        yield (id_, phecode, p['phenostring'], p['category'], p['num_cases'], p['num_controls'], p['num_excluded_controls'])

def pathway_row_generator():
    for pathwayname, id_ in pathway_ids.items():
        d = pathways[pathwayname]
        yield (id_, pathwayname, d['url'], d['category'], d['genesettype'], ','.join(d['genes']))

def pheno_pathway_assoc_row_generator(): # doesn't output primary key, let's sqlite3 auto-increment instead
    for i, (phecode, genesettype) in enumerate(itertools.product(phecodes, genesettypes)):
        phecode_id = phecode_ids[phecode]
        filename = 'PheCode_{}_{}.wConditional.txt.gz'.format(phecode, genesettype)
        print(i, filename)
        with gzip.open(pheno_dir_path / filename, 'rt') as f:
            for line in f:
                name, url, pval_string, selected_genes_string = line.split()
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

db_path = dir_path / 'pheno_pathway_assoc.db'
db_tmp_path = db_path.with_name(db_path.name+'.tmp')
if db_tmp_path.exists(): db_tmp_path.unlink()
conn = sqlite3.connect(str(db_tmp_path))
with conn: # this commits insertions
    conn.execute('create table pheno (id INT PRIMARY KEY, phecode TEXT, phenostring TEXT, category TEXT, num_cases INT, num_controls INT, num_excluded_controls INT)')
    conn.execute('create table pathway (id INT PRIMARY KEY, name TEXT, url TEXT, category TEXT, genesettype TEXT, genes_comma TEXT)')
    conn.execute('create table pheno_pathway_assoc (id INT PRIMARY KEY, pheno_id INT, pathway_id INT, pval REAL, selected_genes_comma TEXT, FOREIGN KEY(pheno_id) REFERENCES pheno(id), FOREIGN KEY(pathway_id) REFERENCES pathway(id))')

    conn.executemany('INSERT INTO pheno VALUES (?,?,?,?,?,?,?)', pheno_row_generator())
    conn.executemany('INSERT INTO pathway VALUES (?,?,?,?,?,?)', pathway_row_generator())
    conn.executemany('INSERT INTO pheno_pathway_assoc (pheno_id, pathway_id, pval, selected_genes_comma) VALUES (?,?,?,?)', pheno_pathway_assoc_row_generator())

    conn.execute('CREATE INDEX idx_assoc_pheno_id ON pheno_pathway_assoc (pheno_id)')
    conn.execute('CREATE INDEX idx_assoc_pathway_id ON pheno_pathway_assoc (pathway_id)')

if db_path.exists(): db_path.unlink()
db_tmp_path.rename(db_path)
