#!/bin/bash
set -euo pipefail

git push
gcloud compute --project "pheweb" ssh --zone "us-central1-a" "pjvandehaar@phewebish-instance" --command /home/pjvandehaar/shawn-phewebish/pull-and-update.sh

echo SUCCESSFUL PUBLISH
