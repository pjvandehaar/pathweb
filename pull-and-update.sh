#!/bin/bash

# This script pulls new commits from github and then restarts the server to use the new code

set -euo pipefail # exit if an error occurs rather than ignoring it
# Move to the directory containing this script (to allow relative paths)
_readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; }
cd "$(dirname "$(_readlinkf "${BASH_SOURCE[0]}")")"

git pull --ff-only
echo

sudo systemctl restart gunicorn-gauss-site
echo

echo SUCCESSFUL UPDATE
