#!/bin/sh

if ! [ -e pheno_pathway_assoc.db ]; then
    echo "either populate input_data and run ./make_sqlite_db.py or copy pheno_pathway_assoc.db here"
    exit 1
fi

if ! [ -e static/phenotypes.json ]; then
    python3 make_tables.py
fi

if ! [ -e venv ]; then
    sudo apt update
    sudo apt install python3-pip python3-venv
    python3 -m venv venv
    ./venv/bin/pip3 install -r requirements.txt
fi

sudo ./venv/bin/gunicorn serve:app -k gevent -w2 -b 0.0.0.0:80 --access-logfile -
