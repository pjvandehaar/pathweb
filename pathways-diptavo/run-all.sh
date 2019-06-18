#!/bin/sh
# This script attempts to do all the work to host the site.  It expects to be on Ubuntu 18.04+ but likely also works on 16.04.

if ! [ -e pheno_pathway_assoc.db ]; then
    echo "either populate input_data and run ./make_sqlite_db.py or copy pheno_pathway_assoc.db here"
    exit 1
fi

if ! [ -e static/phenotypes.json ] || ! [ -e static/pathways.json ]; then
    python3 make_tables.py # uses only python builtins and pheno_pathway_assoc.db
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
WorkingDirectory=/home/pjvandehaar/shawn-phewebish/pathways-diptavo/
ExecStart=/home/pjvandehaar/shawn-phewebish/pathways-diptavo/venv/bin/gunicorn -k gevent -w4 --bind localhost:8899 serve:app
[Install]
WantedBy=multi-user.target
END
    sudo systemctl daemon-reload
    sudo systemctl start gunicorn-gauss-site
    sudo systemctl enable gunicorn-guass-site
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

