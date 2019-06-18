#!/bin/bash
# This script attempts to do all the work to host the site.  It expects to be on Ubuntu 18.04+ but likely also works on 16.04.
set -euo pipefail # notify of errors rather than ignoring them

if ! [ -e pheno_pathway_assoc.db ]; then
    if [ -e input_data/phenos-2019may ] && [ -e input_data/GMT_files ]; then
       python3 make_sqlite3_db.py
    else
        echo "either populate input_data and run ./make_sqlite_db.py or copy pheno_pathway_assoc.db here"
        exit 1
    fi
fi

if ! [ -e static/phenotypes.json ] || ! [ -e static/pathways.json ]; then
    python3 make_tables.py
fi

if ! [ -e venv ]; then
    sudo apt update && sudo apt install python3-pip python3-venv nginx
    python3 -m venv venv
    ./venv/bin/pip3 install -r requirements.txt
fi

if ! [ -e /etc/systemd/system/gunicorn-gauss-site.service ]; then
    sudo tee /etc/systemd/system/gunicorn-gauss-site.service >/dev/null <<END
[Unit]
Description=Gunicorn instance to serve gauss-site
After=network.target
[Service]
User=nobody
Group=nogroup
WorkingDirectory=$PWD/
ExecStart=$PWD/venv/bin/gunicorn -k gevent -w4 --bind localhost:8899 serve:app
[Install]
WantedBy=multi-user.target
END
    sudo systemctl daemon-reload
    sudo systemctl start gunicorn-gauss-site
    sudo systemctl enable gunicorn-gauss-site
fi

if ! [ -e /etc/nginx/sites-enabled/gauss-site ]; then
    sudo tee /etc/nginx/sites-available/gauss-site >/dev/null <<END
server {
    listen 80;
    location / {
        include proxy_params;
        proxy_pass http://localhost:8899;
    }
}
END
    sudo ln -s /etc/nginx/sites-available/gauss-site /etc/nginx/sites-enabled/
    sudo nginx -t # check that the file is good
    sudo systemctl restart nginx
fi

sudo systemctl restart gunicorn-gauss-site

echo SUCCESS
