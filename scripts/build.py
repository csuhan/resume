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
    css = drop_unused_rules(css)
    return f'<style data-src="{href}">{css}</style>'


# Selectors whose classes are added at runtime by js/main.js or the inline
# Scholar script, so they never appear in the static HTML.
RUNTIME_CLASSES = {
    "citation-tag", "menus-open", "menus-close", "is-open", "is-close",
    "nav-open", "nav-close", "is-visible",
}


def _page_vocab():
    body = SRC.read_text(encoding="utf-8").split("<body>", 1)[1]
    classes = {c for v in re.findall(r'class="([^"]*)"', body) for c in v.split()}
    ids = set(re.findall(r'id="([^"]*)"', body))
    tags = {t.lower() for t in re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)", body)} | {"html", "body"}
    js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
    runtime = set(re.findall(r"[\"']([a-z][a-z0-9_-]+)[\"']", js)) | RUNTIME_CLASSES
    return classes | runtime, ids, tags


def _selector_used(sel, vocab):
    classes, ids, tags = vocab
    sel = re.sub(r"::?[a-zA-Z-]+(\([^)]*\))?", "", sel)
    for part in re.split(r"[\s>+~]+", sel.strip()):
        if not part or part == "*":
            continue
        if any(c not in classes for c in re.findall(r"\.([A-Za-z0-9_-]+)", part)):
            return False
        if any(i not in ids for i in re.findall(r"#([A-Za-z0-9_-]+)", part)):
            return False
        t = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)", part)
        if t and t.group(1).lower() not in tags:
            return False
    return True


def drop_unused_rules(css):
    """Remove plain rules whose selectors match nothing on this page (e.g. the
    theme's code-highlighting styles). Keeps @media/@keyframes blocks intact
    except for their unused inner rules. Conservative: any selector it can't
    rule out is kept."""
    vocab = _page_vocab()

    def filter_rules(block):
        def keep(m):
            sels = [s for s in m.group(1).split(",") if s.strip()]
            return m.group(0) if (not sels or any(_selector_used(s, vocab) for s in sels)) else ""
        return re.sub(r"([^{}@;]+)\{[^{}]*\}", keep, block)

    out, i = [], 0
    for m in re.finditer(r"@(media|supports)[^{]*\{((?:[^{}]*\{[^{}]*\})*)[^{}]*\}", css):
        out.append(filter_rules(css[i:m.start()]))
        inner = filter_rules(m.group(2))
        if inner.strip():
            out.append(css[m.start():m.start(2)] + inner + "}")
        i = m.end()
    out.append(filter_rules(css[i:]))
    return "".join(out)


# The theme fades header/main/footer in with an "intro" animation that starts
# hidden and waits up to 0.45s. On a slow link the text is already late; don't
# hide it any longer. This override is appended after the inlined theme CSS.
NO_INTRO_CSS = "#page_header,#page_main,#page_footer{-webkit-animation:none;animation:none}"

# Icon CSS (font-awesome subset, ~4 KB gzipped of inline SVG masks) isn't
# needed to read the page. Its small base rules (icon box size) stay in <head>
# so nothing shifts; the per-icon SVG data moves to the end of <body>. Until it
# arrives the icon boxes are transparent rather than solid squares.
DEFERRED_CSS = {"/css/fontawesome-subset.css"}
ICON_PLACEHOLDER_CSS = ".fa::before,.fas::before,.fa-solid::before,.fab::before,.fa-brands::before{background-color:transparent}"


def split_icon_css(css):
    """(base rules, per-icon svg rules) of the minified font-awesome subset."""
    rules = re.findall(r"[^{}]+\{[^{}]*\}", css)
    icons = [r for r in rules if "--fa-svg:" in r]
    base = [r for r in rules if "--fa-svg:" not in r]
    return "".join(base), "".join(icons)


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

    # 1) inline local stylesheets; critical ones stay in <head>, icon CSS goes
    #    to the end of <body> so the text above it can paint first
    deferred = []

    def place(match):
        style = css_inline(match)
        if match.group(1) in DEFERRED_CSS:
            body = re.search(r">(.*)</style>", style, re.S).group(1)
            base, icons = split_icon_css(body)
            # once the icon shapes land, the colour comes back with them
            deferred.append(f'<style data-src="{match.group(1)}#icons">{icons}'
                            f'.fa::before,.fas::before,.fa-solid::before,.fab::before,.fa-brands::before{{background-color:currentColor}}</style>')
            return f'\n  <style data-src="{match.group(1)}#base">{base}{ICON_PLACEHOLDER_CSS}</style>'
        return style

    html = re.sub(r'\s*<link rel="stylesheet" href="(/css/[^"]+\.css)">', lambda m: ("\n  " + place(m)) if m.group(1) not in DEFERRED_CSS else place(m), html)
    html = html.replace("</head>", f"  <style>{NO_INTRO_CSS}</style>\n</head>", 1)
    if deferred:
        html = html.replace("</body>", "".join(deferred) + "\n</body>", 1)

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
