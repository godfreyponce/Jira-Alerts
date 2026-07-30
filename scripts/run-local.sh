#!/bin/zsh
# Runs one polling cycle with the repo's .env. Used by the launchd timer
# (see docs/HISTORY.md #10) but safe to invoke by hand.
cd "$(dirname "$0:A")/.." || exit 1
set -a; source .env; set +a
exec python3 -m src.run
