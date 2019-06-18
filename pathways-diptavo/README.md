### Usage

1. Put data in `input_data/`. There are 3 type of files:
   - `input_data/phenos-2019may/PheCode_*_*.wConditional.txt.gz` (eg, `PheCode_986_Curated.wConditional.txt.gz`) contains data about phecode `986` in the `Curated` pathways.  There is a separate file for `GO` pathways.
      - format: space-delimited. columns are `pathway_name`, `pathway_url`, `association_pvalue`, garbage, `pathway_genes_that_the_method_selected_as_meaningful`, garbage. eg, `KEGG_GLYCOLYSIS_GLUCONEOGENESIS http://www.broadinstitute.org/gsea/msigdb/cards/KEGG_GLYCOLYSIS_GLUCONEOGENESIS 0.993 1 ALDH3A2,ADH1B,HK3,ALDH1B1,FBP1,TPI1,PFKP DLAT,PGM1,ADH1C,PCK1`
   - `input_data/GMT_files/GO_Subclass.dat` and `input_data/GMT_files/Curated_Subclass.dat`:
      - format: space-delimited. columns are `pathway_name`, `pathway_url`, `pathway_category`
   - `input_data/GMT_files/C{2,5}.*.gmt.dat`:
      - contains the list of genes for each pathway
   - `input_data/phenotype-colors.csv`

2. run `pip3 install -r requirments.txt`

3. run `./make_sqlite3_db.py` to produce `pheno_pathway_assoc.db`

4. run `./make_tables.py` to produce `static/phenotypes.json` and `static/pathways.json`

5. run `gunicorn serve:app -k gevent -w4 --bind 127.0.0.1:8000`
