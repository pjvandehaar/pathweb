### Usage

1. Put data in `input_data/`. There are 4 type of files:
   - `input_data/phenos-2019may/PheCode_*_{GO,Curated}.wConditional.txt.gz`
      - eg, `PheCode_986_Curated.wConditional.txt.gz`) contains data about phecode `986` in the `Curated` pathways.
      - format: space-delimited. columns are `pathway_name`, `pathway_url`, `association_pvalue`, garbage, `pathway_genes_that_the_method_selected_as_meaningful`, garbage.
         - eg, `KEGG_GLYCOLYSIS_GLUCONEOGENESIS http://www.broadinstitute.org/gsea/msigdb/cards/KEGG_GLYCOLYSIS_GLUCONEOGENESIS 0.993 1 ALDH3A2,ADH1B,HK3,ALDH1B1,FBP1,TPI1,PFKP DLAT,PGM1,ADH1C,PCK1`
   - `input_data/GMT_files/GO_Subclass.dat` and `input_data/GMT_files/Curated_Subclass.dat`:
      - format: space-delimited. columns are `pathway_name`, `pathway_url`, `pathway_category`
   - `input_data/GMT_files/C{2,5}.*.gmt.dat`:
      - contains the list of genes for each pathway
   - `input_data/phenotype-colors.csv` (included in repo)

2. run `pip3 install -r requirments.txt`

3. run `python3 gauss-site/make_sqlite3_db.py` to produce `gauss-site/pheno_pathway_assoc.db`

4. run `python3 gauss-site/make_tables.py` to produce `gauss-site/static/phenotypes.json` and `gauss-site/static/pathways.json`

5. run the server using one of these:
   - `python3 gauss-site/serve.py` (insecure and slow for development/debugging)
   - `cd gauss-site && gunicorn serve:app -k gevent -w4 --bind 0.0.0.0:8000` (fast for production)
