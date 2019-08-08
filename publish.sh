#!/bin/bash

# This script pushes new commits to github and the server and restarts the server to use the new code

set -euo pipefail # exit if an error occurs rather than ignoring it
# Move to the directory containing this script (to allow relative paths)
_readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; }
cd "$(dirname "$(_readlinkf "${BASH_SOURCE[0]}")")"

git push
echo

gcloud compute --project "pheweb" ssh --zone "us-central1-a" "pjvandehaar@phewebish-instance" --command /home/pjvandehaar/gauss-site/pull-and-update.sh
echo

echo SUCCESSFUL PUBLISH
