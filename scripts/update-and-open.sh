#!/bin/bash
# Update the AI Safety Weekly Digest and open it in the browser.
# Used by the macOS Launch Agent for automatic Monday updates.

set -e

PROJECT_DIR="/Users/sambhavmaheshwari/projects/ai-safety-digest"
cd "$PROJECT_DIR"

# Fetch papers and render the site
/usr/bin/python3 scripts/fetch.py 2>> /tmp/ai-safety-digest.log
/usr/bin/python3 scripts/render.py 2>> /tmp/ai-safety-digest.log

# Open in default browser
open "$PROJECT_DIR/site/index.html"
