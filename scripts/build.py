#!/usr/bin/env python3
"""Build the published index.html from src/index.html.

Why: csuhan.com is GitHub Pages behind Cloudflare, which is slow from mainland
China, and every extra request is another slow round trip. So:

  * CSS is inlined into the page. It is ~12 KB gzipped, renders with the HTML
    in a single request, and can never be served stale.
  * JS is loaded from jsDelivr pinned to the content hash of the file
    (https://cdn.jsdelivr.net/gh/csuhan/resume@<commit>/js/main.min.js), with
    csuhan.com as fallback. A changed file always gets a new URL, so a CDN can
    never serve an old version.
  * Images are left alone: they are still served from csuhan.com (GitHub).

Usage (from the repo root):
    python3 scripts/build.py              # writes ./index.html
    python3 scripts/build.py --js-ref SHA # pin JS to an existing commit
"""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "index.html"
OUT = ROOT / "index.html"
REPO = "csuhan/resume"


def css_inline(match):
    href = match.group(1)
    path = ROOT / href.lstrip("/")
    css = path.read_text(encoding="utf-8")
    # light minify: drop comments and collapse whitespace
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,>])\s*", r"\1", css).strip()
    return f'<style data-src="{href}">{css}</style>'


def last_commit_touching(path):
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return out[:12]


def file_is_committed(path):
    r = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", path], capture_output=True, text=True)
    return r.stdout.strip() == ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--js-ref", help="commit that contains the current js/main.min.js")
    args = ap.parse_args()

    html = SRC.read_text(encoding="utf-8")

    # 1) inline local stylesheets
    html = re.sub(r'<link rel="stylesheet" href="(/css/[^"]+\.css)">', css_inline, html)

    # 2) JS from jsDelivr, pinned to the commit that last changed it
    js = "js/main.min.js"
    digest = hashlib.sha256((ROOT / js).read_bytes()).hexdigest()[:10]
    ref = args.js_ref
    if not ref:
        if not file_is_committed(js):
            sys.exit(f"{js} has uncommitted changes: commit it first, then re-run")
        ref = last_commit_touching(js)
    cdn = f"https://cdn.jsdelivr.net/gh/{REPO}@{ref}/{js}"
    local = f"/{js}?v={digest}"
    tag = (
        f'<script src="{cdn}" defer crossorigin="anonymous" '
        f'onerror="var s=document.createElement(\'script\');s.src=\'{local}\';document.body.appendChild(s)"></script>'
    )
    html, n = re.subn(r'<script src="/js/main\.min\.js" defer></script>', tag, html)
    if n != 1:
        sys.exit("expected exactly one main.min.js script tag in src/index.html")

    OUT.write_text(html, encoding="utf-8")
    print(f"index.html written: css inlined, js -> {cdn}")


if __name__ == "__main__":
    main()
