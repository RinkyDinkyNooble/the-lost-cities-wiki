#!/usr/bin/env python3
"""Check that every claim on a verified page carries a verification chip.

A page opts in by putting `claims: verified` in its front matter. On an opted-in
page every block of content that asserts something must carry at least one chip,
and every chip must point at a register entry that exists. Usage:

    python docs/examples/check_claims.py
    python docs/examples/check_claims.py docs/getting-started/namespaces.md

A block that genuinely asserts nothing (navigation, a scope note, a lead-in that
only introduces the thing below it) is marked with a trailing `<!-- noclaim -->`.
That is a recorded decision, not an exemption: the rule is that no block may be
left undecided, not that every block must be a claim.
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOCS = Path(__file__).resolve().parent.parent
REGISTER = DOCS / "examples" / "claim-tests.md"

CHIP = re.compile(r"\[(game test|code review|unverified)\]"
                  r"\(([^)]+)\)\{\.v \.v-([gcu])\}")
LABELS = {"game test": "g", "code review": "c", "unverified": "u"}
NOCLAIM = "<!-- noclaim -->"

# Blocks that carry no assertion of their own. A heading names the claims under
# it, a fence is quoted evidence, a rule is punctuation.
SKIP = (
    re.compile(r"^\s*#{1,6}\s"),          # heading
    re.compile(r"^\s*(-{3,}|\*{3,})\s*$"),  # horizontal rule
    re.compile(r"^\s*!!!\s"),             # admonition opener, its body is checked
    re.compile(r"^\s*\?\?\?\+?\s"),       # collapsible opener
    re.compile(r"^\s*===\s+\""),          # tab opener
    re.compile(r"^\s*<!--"),              # comment
)

errors: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def front_matter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def strip_fences(lines: list[str]) -> list[str]:
    """Blank out fenced code so its contents never read as prose.

    A fence inside an admonition is indented, so the closing fence is matched on
    its marker rather than its column.
    """
    out, fence = [], None
    for line in lines:
        marker = re.match(r"^\s*(```+|~~~+)", line)
        if fence is None and marker:
            fence = marker.group(1)[0]
            out.append("")
            continue
        if fence is not None:
            if marker and marker.group(1)[0] == fence:
                fence = None
            out.append("")
            continue
        out.append(line)
    return out


def blocks(lines: list[str]):
    """Yield (first line number, list of lines) for each blank-separated block."""
    buf, start = [], 0
    for n, line in enumerate(lines, 1):
        if line.strip():
            if not buf:
                start = n
            buf.append(line)
        elif buf:
            yield start, buf
            buf = []
    if buf:
        yield start, buf


def anchors_in_register() -> set[str]:
    """Every id the register defines, rejecting any it defines twice.

    A duplicate id is worse than a missing one. A chip naming it still resolves,
    so nothing errors and nothing looks wrong, but the reader lands on whichever
    of the two the browser reaches first, which is the older entry. The claim
    reads as cited while pointing at evidence for something else.
    """
    text = REGISTER.read_text(encoding="utf-8")
    found = re.findall(r"\{\s*#([a-z0-9-]+)\s*\}", text)
    for name in sorted({a for a in found if found.count(a) > 1}):
        err(REGISTER.name, f"register id defined more than once: #{name}")
    return set(found)


def is_table(block: list[str]) -> bool:
    return (len(block) >= 2
            and block[0].lstrip().startswith("|")
            and re.match(r"^\s*\|[\s:|-]+\|\s*$", block[1]))


def columns(row: str) -> int:
    """Count a row's cells, ignoring pipes inside code spans or link targets."""
    r = row.strip()
    r = r[1:] if r.startswith("|") else r
    r = r[:-1] if r.endswith("|") else r
    n, depth, incode = 1, 0, False
    for ch in r:
        if ch == "`":
            incode = not incode
        elif not incode and ch == "(":
            depth += 1
        elif not incode and ch == ")":
            depth -= 1
        elif not incode and depth == 0 and ch == "|":
            n += 1
    return n


def check_table_shape(where: str, block: list[str]) -> None:
    """A header wider than its separator silently destroys the whole table.

    Markdown gives up and renders every row as one run-on paragraph, which
    builds cleanly and looks catastrophic. Appending anything past a row's
    closing pipe is the way it happens.
    """
    head, sep = columns(block[0]), columns(block[1])
    if head != sep:
        err(where, f"table header has {head} columns and its separator "
                   f"declares {sep}. Markdown will not render this as a table")


def check_chips(where: str, text: str, known: set[str],
                seen: dict[str, set[str]]) -> list[str]:
    """Validate every chip in a stretch of text and return the statuses found.

    Statuses combine per claim, not per block: one paragraph may carry a
    code-reviewed claim and an unverified one side by side, but a single claim
    may not be both.
    """
    found, by_anchor = [], {}
    for label, target, cls in CHIP.findall(text):
        if LABELS[label] != cls:
            err(where, f"chip says '{label}' but is styled .v-{cls}")
        anchor = target.split("#")[-1] if "#" in target else None
        if anchor is None:
            err(where, f"chip '{label}' links to {target} with no register anchor")
        elif anchor not in known:
            err(where, f"chip '{label}' points at #{anchor}, "
                       "which is not a register entry")
        else:
            by_anchor.setdefault(anchor, set()).add(cls)
            seen.setdefault(anchor, set()).add(cls)
        found.append(cls)
    for anchor, classes in by_anchor.items():
        if "u" in classes and len(classes) > 1:
            err(where, f"#{anchor} is marked unverified and verified at once")
    return found


def check_page(path: Path, known: set[str],
               seen: dict[str, set[str]]) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(DOCS).as_posix()
    lines = strip_fences(text.splitlines())

    claimed = decided = 0
    for start, block in blocks(lines):
        body = "\n".join(block)
        where = f"{rel}:{start}"

        if any(p.match(block[0]) for p in SKIP) and not CHIP.search(body):
            continue
        if body.strip().startswith("---"):  # front matter
            continue

        statuses = check_chips(where, body, known, seen)

        if NOCLAIM in body:
            if statuses:
                err(where, "block is marked noclaim but carries a chip")
            decided += 1
            continue

        if is_table(block):
            check_table_shape(where, block)
            # A chip on a data row covers that row. A chip anywhere else in the
            # block, meaning the header or a line run on under the table, covers
            # the table as a whole. Rows may then differ from it by carrying
            # their own.
            rows = [r for r in block[2:] if r.lstrip().startswith("|")]
            covered = any(CHIP.search(ln) for i, ln in enumerate(block)
                          if i == 0 or not ln.lstrip().startswith("|"))
            if not statuses:
                err(where, f"table of {len(rows)} rows carries no chip")
            elif not covered:
                bare = [r for r in rows if not CHIP.search(r)]
                if bare:
                    err(where, f"{len(bare)} of {len(rows)} table rows carry no "
                               "chip, and nothing covers the table as a whole")
            claimed += 1
            decided += 1
            continue

        if not statuses:
            err(where, f"no chip: {body.strip().splitlines()[0][:70]!r}")
        else:
            claimed += 1
        decided += 1

    return claimed, decided


def main() -> int:
    known = anchors_in_register()
    # Resolve, so a path given relative to the working directory still lands
    # inside DOCS when the report prints it.
    targets = ([Path(a).resolve() for a in sys.argv[1:]]
               or sorted(DOCS.rglob("*.md")))

    opted, total = [], 0
    for path in targets:
        if not path.is_file():
            err(str(path), "no such file")
            continue
        # The register is the evidence, not a page that cites it. Chipping it
        # would point every entry at itself.
        if path == REGISTER:
            continue
        text = path.read_text(encoding="utf-8")
        total += 1
        if front_matter(text).get("claims") == "verified":
            opted.append(path)

    seen: dict[str, set[str]] = {}
    for path in opted:
        claimed, decided = check_page(path, known, seen)
        print(f"  {path.relative_to(DOCS).as_posix():<44} "
              f"{claimed} claims, {decided} blocks decided")

    # One claim, one status, wherever it is cited. A page calling something
    # unverified while another page calls it game tested is the failure this
    # whole scheme exists to prevent.
    for anchor, classes in sorted(seen.items()):
        if "u" in classes and len(classes) > 1:
            err("register", f"#{anchor} is cited as unverified on one page and "
                            "verified on another")
    unused = sorted(known - set(seen))
    if unused:
        print(f"  {len(unused)} register entries not cited yet: "
              f"{', '.join(unused[:8])}")

    for line in errors:
        print(f" ERROR  {line}")
    print()
    print(f"{len(opted)}/{total} pages verified, "
          f"{len(known)} register entries, {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
