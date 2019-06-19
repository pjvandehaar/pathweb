#!/bin/bash
set -euo pipefail
_readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; }
cd "$(dirname "$(_readlinkf "${BASH_SOURCE[0]}")")"

git push
echo

gcloud compute --project "pheweb" ssh --zone "us-central1-a" "pjvandehaar@phewebish-instance" --command /home/pjvandehaar/shawn-phewebish/pull-and-update.sh
echo

echo SUCCESSFUL PUBLISH
