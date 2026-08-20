#!/usr/bin/env python3
"""Check the built site for the two faults Markdown-level checks cannot see.

    mkdocs build --strict
    python docs/examples/check_render.py

Both need the rendered HTML, because both are about what the page turned into
rather than what was written.

**Broken anchors.** `--strict` validates that a linked page exists. It does not
validate the fragment after the `#`, so rewording a heading leaves every link that
named its old anchor pointing at the top of the page instead of the section it
names. Nothing errors and nothing looks wrong. That matters more here than on most
sites: every verification label is a link to a numbered register entry, and a label
that stops resolving is a claim that looks cited and is not.

**Tables that stopped being tables.** Anything inserted between a table's rows,
or appended after a row's closing pipe, makes Markdown abandon the table and render
every row as one run-on paragraph. It has happened twice on this wiki. The first
time it took out **116 rows across 21 files** and every gate passed throughout,
because none of them looked at the rendered output; a human reading a page caught
it. The symptom in the HTML is a paragraph full of pipe characters.
"""
import io
import os
import re
import sys
from urllib.parse import unquote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(REPO, "site")


def pages():
    for root, _, files in os.walk(SITE):
        for name in sorted(files):
            if name.endswith(".html"):
                path = os.path.join(root, name)
                rel = os.path.relpath(path, SITE).replace("\\", "/")
                yield rel, io.open(path, encoding="utf-8", errors="replace").read()


def check_anchors(rendered):
    ids = {rel: set(re.findall(r'\sid="([^"]+)"', html))
           for rel, html in rendered.items()}
    bad = 0
    for rel, html in rendered.items():
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:")) or "#" not in href:
                continue
            page, frag = href.split("#", 1)
            frag = unquote(frag)
            if not frag:
                continue
            if page in ("", "."):
                target = rel
            else:
                target = os.path.normpath(
                    os.path.join(os.path.dirname(rel), page)).replace("\\", "/")
                if target.endswith("/"):
                    target += "index.html"
                elif not target.endswith(".html"):
                    target = target.rstrip("/") + "/index.html"
            # Anything that is not a built page is an asset, and mkdocs has
            # already checked those.
            if target in ids and frag not in ids[target]:
                bad += 1
                print(f"  broken anchor  {rel} -> {page}#{frag}")
    return bad


def check_tables(rendered):
    bad = 0
    for rel, html in rendered.items():
        for para in re.findall(r"<p>(.*?)</p>", html, re.S):
            if para.count("|") >= 3:
                bad += 1
                flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", para)).strip()
                print(f"  table not rendering  {rel}: {flat[:90]}")
    return bad


def main():
    if not os.path.isdir(SITE):
        raise SystemExit("no site/ directory. Run `mkdocs build --strict` first.")
    rendered = dict(pages())
    bad = check_anchors(rendered) + check_tables(rendered)
    print(f"\n{len(rendered)} rendered pages, {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
