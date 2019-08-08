### Usage

#### 1. Put data into `input_data/`.

This repository already has a few files in `input_data/`.  You need to add data in `input_data/pathways/` and `input_data/genes/`.

The files in `input_data/pathways/` contain the associations between each phenotype and pathway.  Their format is:

 - filenames: `PheCode_*_{GO,Curated}.wConditional.txt.gz`
     - eg, `PheCode_986_Curated.wConditional.txt.gz` contains data about the Curated pathways for phecode 986.
 - format: tab-delimited with columns `pathway_name`, `pathway_url`, `association_pvalue`, `pathway_genes_that_the_method_selected_as_meaningful`.
     - eg, `KEGG_GLYCOLYSIS_GLUCONEOGENESIS http://www.broadinstitute.org/gsea/msigdb/cards/KEGG_GLYCOLYSIS_GLUCONEOGENESIS 0.993 ALDH3A2,ADH1B,HK3,ALDH1B1,FBP1,TPI1,PFKP`

The files in `input_data/genes/` contain the associations between each phenotype and gene.  Their format is:

  - filenames: `OUTF_PheCode_*.txt.gz`
      - eg, `OUTF_PheCode_803.2.txt.gz` contains data about phenotype 803.2
  - format: tab-delimited with columns `gene_name`, `pvalue_or_NA`
      - eg, `7SK NA` or `A1BG 8.35e-01`


These files can be collected from Flux by running:

    mkdir -p ~/gauss-site-data/pathways/ && cd /scratch/leeshawn_fluxod/diptavo/1000G/RESULTS/ && find . -name 'PheCode_*[dO].wConditional.txt'|sort -n|while read f; do echo $f; cat $f|cut -d' ' -f1-3,5|tr " " "\t"|gzip - > ~/gauss-site-data/pathways/$(basename $f).gz; done
    mkdir -p ~/gauss-site-data/genes/ && cd /scratch/leeshawn_fluxod/diptavo/1000G/RESULTS/ && find . -name 'OUTF_PheCode_*.txt'|sort -n|while read f; do echo $f; cat $f|perl -nae 'print "$F[0]\t";if ($F[4] eq "NA") {print("NA\n")} else {printf("%.2e\n",$F[4])}' | gzip - > ~/gauss-site-data/genes/$(basename $f).gz; done

#### 2. Populate the databases and run the server.

If you are on an Ubuntu server you can simply run `./setup-server.sh` which should install the required tools, process the data, and configure and start the Flask app and Nginx using Systemd.

If you are on a laptop or otherwise don't want to use that script, then:

1. run `pip3 install -r requirments.txt` (which may require you to set up and activate a `virtualenv` or `miniconda` or use `sudo`)

2. run `python3 gauss-site/make_sqlite3_db.py` to produce `gauss-site/pheno_pathway_assoc.db`.

3. run `python3 gauss-site/make_gene_sqlite3_db.py` to produce `gauss-site/gene.db`.

4. run `python3 gauss-site/make_tables.py` to produce  `gauss-site/static/phenotypes.json` and `gauss-site/static/pathways.json`.

5. run the server with either:
   - `python3 gauss-site/serve.py` (insecure and slow for development/debugging)
   - `cd gauss-site && gunicorn serve:app -k gevent -w4 --bind 0.0.0.0:8000` (fast for production)
