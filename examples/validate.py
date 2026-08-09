#!/usr/bin/env python3
"""Validate a Lost Cities datapack against the rules documented in this wiki.

Every check below corresponds to a documented rule. If a check fails here, either
the datapack is wrong or the wiki page it came from is wrong. Usage:

    python examples/validate.py examples/first-city
"""
import json
import sys
import unicodedata
from pathlib import Path

errors: list[str] = []
warnings: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        err(path.name, f"not valid JSON: {exc}")
        return None


def check_palette(path: Path, data) -> set[str]:
    """palette.md: char is one UTF-16 code unit; weighted lists must reach 128."""
    chars: set[str] = set()
    for entry in data.get("palette", []):
        c = entry.get("char")
        if c is None:
            err(path.name, "palette entry has no 'char'")
            continue
        if len(c.encode("utf-16-le")) // 2 != 1:
            err(path.name, f"char {c!r} is not a single UTF-16 code unit (emoji?)")
        if c in chars:
            err(path.name, f"duplicate char {c!r} within one file")
        chars.add(c)

        kinds = [k for k in ("block", "variant", "blocks", "frompalette") if k in entry]
        if len(kinds) != 1:
            err(path.name, f"char {c!r} must have exactly one of block/variant/blocks/frompalette, has {kinds}")

        if "blocks" in entry:
            total = sum(b.get("random", 0) for b in entry["blocks"])
            if total < 128:
                err(path.name, f"char {c!r} weighted list totals {total}, must reach 128")
            running = 0
            for i, b in enumerate(entry["blocks"]):
                if running >= 128:
                    err(path.name, f"char {c!r} entry #{i} ({b.get('block')}) is unreachable, 128 slots already filled")
                running += b.get("random", 0)
    return chars


def check_part(path: Path, data) -> set[str]:
    """part.md: 16x16, rows exactly xsize long, zsize rows, counted in UTF-16 units."""
    xs, zs = data.get("xsize"), data.get("zsize")
    if xs != 16 or zs != 16:
        err(path.name, f"xsize/zsize are {xs}/{zs}, must both be 16")
    used: set[str] = set()
    for si, layer in enumerate(data.get("slices", [])):
        if len(layer) != zs:
            err(path.name, f"slice {si} has {len(layer)} rows, expected zsize={zs}")
        for ri, row in enumerate(layer):
            units = len(row.encode("utf-16-le")) // 2
            if units != xs:
                err(path.name, f"slice {si} row {ri} is {units} UTF-16 units, expected xsize={xs}")
            used.update(row)
    n = len(data.get("slices", []))
    if n != 6:
        warn(path.name, f"{n} slices; a floor level is 6 blocks tall, so anything else over/underfills")
    if "metadata" in data:
        err(path.name, "key is 'meta', not 'metadata'")
    return used


def check_building(path: Path, data) -> None:
    """building.md: filler required; parts must cover every floor index."""
    if "filler" not in data:
        err(path.name, "'filler' is required")
    parts = data.get("parts", [])
    if not parts:
        err(path.name, "'parts' is required and must not be empty")
    condition_keys = {"top", "ground", "cellar", "isbuilding", "issphere", "floor",
                      "chunkx", "chunkz", "range", "inpart", "belowpart", "inbuilding", "inbiome"}
    if not any(not (condition_keys & set(p)) for p in parts):
        err(path.name, "no unconditioned part reference; some floor will match nothing and crash generation")
    for key, lo, hi in (("minfloors", 0, 60), ("maxfloors", 0, 60),
                        ("mincellars", 0, 20), ("maxcellars", 0, 20)):
        if key in data and not (lo <= data[key] <= hi):
            err(path.name, f"{key}={data[key]} outside the {lo}-{hi} window")


def check_stuff(path: Path, data) -> None:
    """stuff.md: both min/max pairs are used as random(max-min), so max must exceed min."""
    for lo, hi in (("mincount", "maxcount"), ("minheight", "maxheight")):
        if lo in data and hi in data and data[hi] <= data[lo]:
            err(path.name, f"{hi} ({data[hi]}) must be strictly greater than {lo} ({data[lo]})")
    if data.get("attempts", 1) < 1:
        err(path.name, "attempts must be at least 1 or nothing is ever placed")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "examples/first-city")
    data_dir = root / "data"
    if not data_dir.is_dir():
        print(f"no data/ directory under {root}")
        return 2

    declared_chars: set[str] = set()
    used_chars: set[str] = set()
    part_names: set[str] = set()

    for ns_dir in sorted(data_dir.iterdir()):
        lc = ns_dir / "lostcities"
        if not lc.is_dir():
            warn(ns_dir.name, "no 'lostcities' directory; assets live at data/<ns>/lostcities/<type>/")
            continue
        for type_dir in sorted(lc.iterdir()):
            for f in sorted(type_dir.glob("*.json")):
                data = load(f)
                if data is None:
                    continue
                kind = type_dir.name
                if kind == "palettes":
                    declared_chars |= check_palette(f, data)
                elif kind == "parts":
                    used_chars |= check_part(f, data)
                    part_names.add(f"{ns_dir.name}:{f.stem}")
                elif kind == "buildings":
                    check_building(f, data)
                elif kind == "stuff":
                    check_stuff(f, data)

    # A space is air only because the shipped 'common' palette says so.
    unknown = used_chars - declared_chars - {" "}
    if unknown:
        warn("parts", "chars not defined by this pack's own palettes (must come from the "
                      f"style's merged palette or generation throws): {sorted(unknown)}")

    for line in warnings:
        print(f"  warn  {line}")
    for line in errors:
        print(f" ERROR  {line}")
    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
