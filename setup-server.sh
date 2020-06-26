#!/bin/bash

# This script attempts to do all the work to host the site.  It expects to be on Ubuntu 18.04+ but likely also works on 16.04.

set -euo pipefail # exit if an error occurs rather than ignoring it
# Move to the directory containing this script (to allow relative paths)
_readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; } # cross-platform version of `readlink -f`
cd "$(dirname "$(_readlinkf "${BASH_SOURCE[0]}")")" # `cd` to the directory holding this script (which is the root of this git repo)

# Check that needed data is present.  If a missing file can be generated from other files, do that.
if ! [ -e pathweb/pheno_pathway_assoc.db ]; then
    if [ -e input_data/pathways ]; then
       python3 pathweb/make_sqlite3_db.py
    else
        echo "either populate input_data/pathways/ and run ./make_sqlite_db.py or copy pheno_pathway_assoc.db here"
        exit 1
    fi
fi

if ! [ -e pathweb/gene.db ]; then
    if [ -e input_data/genes ]; then
       python3 pathweb/make_gene_sqlite3_db.py
    else
        echo "either populate input_data/genes/ and run ./make_gene_sqlite_db.py or copy gene.db here"
        exit 1
    fi
fi

if ! [ -e pathweb/static/phenotypes.json ] || ! [ -e pathweb/static/pathways.json ]; then
    python3 pathweb/make_tables.py
fi

# Install dependencies
if ! [ -e venv ]; then
    sudo apt update && sudo apt install python3-pip python3-venv nginx
    python3 -m venv venv
    ./venv/bin/pip3 install -r requirements.txt
fi

# Make a Systemd Unit file that runs gunicorn to host the site (available only locally on this machine)
if ! [ -e /etc/systemd/system/gunicorn-pathweb.service ]; then
    sudo tee /etc/systemd/system/gunicorn-pathweb.service >/dev/null <<END
[Unit]
Description=Gunicorn instance to serve pathweb
After=network.target
[Service]
User=nobody
Group=nogroup
WorkingDirectory=$PWD/pathweb/
ExecStart=$PWD/venv/bin/gunicorn -k gevent -w4 --bind localhost:8899 serve:app
[Install]
WantedBy=multi-user.target
END
    sudo systemctl daemon-reload
    sudo systemctl start gunicorn-pathweb
    sudo systemctl enable gunicorn-pathweb
fi

# Make nginx reverse-proxy the local-only gunicorn port to an externally-accessible subdomain
if ! [ -e /etc/nginx/sites-enabled/pathweb ]; then
    sudo tee /etc/nginx/sites-available/pathweb >/dev/null <<END
server {
    listen 80;
    server_name ukb-pathway.leelabsg.org;
    location / {
        include proxy_params;
        proxy_pass http://localhost:8899;
    }
}
END
    sudo ln -s /etc/nginx/sites-available/pathweb /etc/nginx/sites-enabled/
    sudo nginx -t # check that the file is good
    sudo systemctl restart nginx
fi

# Restart gunicorn to apply any changes
sudo systemctl restart gunicorn-pathweb

echo SUCCESS
