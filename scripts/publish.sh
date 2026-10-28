#!/usr/bin/env bash
# Edit src/index.html, css/*.css or js/main.js, then run:  scripts/publish.sh
#
# 1. re-minifies js/main.js -> js/main.min.js (if esbuild/npx is available)
# 2. commits and pushes source changes (so jsDelivr can see the JS commit)
# 3. builds index.html (CSS inlined, JS pinned to that commit on jsDelivr)
# 4. commits and pushes index.html
#
# Because the JS URL contains the commit, a new JS file always gets a new URL
# and no CDN or browser cache can serve the old one. CSS is inside index.html,
# so it updates together with the page. Images stay on csuhan.com.
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v npx >/dev/null 2>&1; then
  npx --yes esbuild@0.25 js/main.js --minify --target=es2018 --outfile=js/main.min.js --log-level=warning
fi

git add -A src css js img attaches scripts 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "${1:-update}"
  git push
fi

python3 scripts/build.py
git add index.html
if ! git diff --cached --quiet; then
  git commit -m "build index.html"
  git push
fi
echo "published"
