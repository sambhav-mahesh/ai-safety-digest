#!/bin/bash
# Fetch papers, render the site, and open it in the default browser.
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

python3 scripts/fetch.py
python3 scripts/render.py

# macOS: open in browser; Linux: xdg-open
if command -v open &>/dev/null; then
    open "$PROJECT_DIR/site/index.html"
elif command -v xdg-open &>/dev/null; then
    xdg-open "$PROJECT_DIR/site/index.html"
else
    echo "Site rendered at: $PROJECT_DIR/site/index.html"
fi
