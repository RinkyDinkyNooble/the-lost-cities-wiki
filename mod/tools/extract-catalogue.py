#!/usr/bin/env python3
"""Build the workshop catalogue: which rows of plots the target version needs.

    python mod/tools/extract-catalogue.py

Writes `mod/src/main/resources/data/lostcitiesdevtool/catalogue.json`.

The **keys** come from `docs/examples/mod-keys.json`, which is extracted from the
jars and checked against the wiki's published tables, so the catalogue cannot claim
a shape the version does not declare. The **classification** below is knowledge, not
data: which family is a weighted selector, which is a plain list, which asset owns
it, and how many variations each can hold. It is written here with its reasoning
rather than inferred, because a wrong guess would silently produce a catalogue that
teaches the wrong thing.

Three row classes, and the difference decides what a plot's settings need:

  part-list   Streets, highways and railways. `Tools.listOrStringList`, so a bare
              string or an unbounded list, picked uniform random with no weight.
  single      Monorails. Plain `Codec.STRING`. A list is a load error, so exactly
              one plot, ever.
  selector    Buildings, multibuildings, parks and the rest. `ObjectSelector`, so
              each entry carries a required `factor` and optional distance gating.
"""
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
REPO = os.path.dirname(MOD)
KEYS = os.path.join(REPO, "docs", "examples", "mod-keys.json")
OUT = os.path.join(MOD, "src", "main", "resources", "data", "lostcitiesdevtool",
                   "catalogue.json")
VERSION = "7.4.12"

# How many plots a row of one-chunk shapes starts with. A row is not a limit: any
# row grows on demand, from an import or from `/lcdev workshop grow`. This is only
# how many are laid out before anybody asks for more.
DEFAULT_PLOTS = 8

# family -> how its rows behave. `owner` is the asset the names end up in, which is
# what decides whether a plot has to name a city style.
FAMILIES = [
    # codec type,       area,   class,       owner,        default plots per row
    ("StreetParts",     "west", "part-list", "citystyle",  DEFAULT_PLOTS),
    ("HighwayParts",    "west", "part-list", "worldstyle", DEFAULT_PLOTS),
    ("RailwayParts",    "west", "part-list", "worldstyle", DEFAULT_PLOTS),
    ("MonorailParts",   "west", "single",    "worldstyle", 1),
]

# The selector families that are parts of one chunk, so one plot each. `buildings`
# and `multibuildings` are not here: they are the whole east area.
SELECTOR_ROWS = ["fronts", "parks", "fountains", "bridges", "stairs", "raildungeons"]

# Every multi-building footprint, up to the largest one that can exist.
#
# The ceiling is the world style's `multisettings.areasize`, which defaults to 10:
# a multi-building is placed inside one area of that many chunks square, so 10x10
# is the largest that fits. `multisettings.maximum` caps what the generator will
# actually roll and defaults to 5, so anything above that needs the world style
# raising it as well as the plots existing here.
#
# 1x2 and 2x1 are both here because they are not rotations of each other: the mod
# places them on different axes. 1x1 is not, because that is the buildings row.
MULTI_CEILING = 10

# Laying out every size at full width would paint several thousand chunks of floor
# for shapes most packs never use, so the big ones are declared and left empty until
# somebody grows one. `/lcdev workshop rows` lists them either way.
MULTI_LAID_OUT_UP_TO = 3
MULTI_PLOTS = 4

MULTI_SIZES = [(w, h)
               for w in range(1, MULTI_CEILING + 1)
               for h in range(1, MULTI_CEILING + 1)
               if (w, h) != (1, 1)]

# Shapes that parse and are never reached. Kept in the catalogue and flagged, rather
# than hidden, because the DevTool ships the fix that makes this one live.
DEAD = {
    "full": "Never generates in unmodded Lost Cities: nextInt(0, values().length - 2) "
            "can only return 0. Live with the DevTool's street-full fix enabled."
}


def main():
    codec = json.load(io.open(KEYS, encoding="utf-8"))["versions"][VERSION]["codec"]
    rows = []

    for typ, area, kind, owner, plots in FAMILIES:
        keys = codec.get(typ)
        if not keys:
            print("  %s declares nothing in %s, skipped" % (typ, VERSION))
            continue
        for key in sorted(keys):
            row = {"id": typ.replace("Parts", "").lower() + "/" + key,
                   "family": typ, "key": key, "area": area, "class": kind,
                   "owner": owner, "plots": plots, "size": [1, 1]}
            if key in DEAD:
                row["dead"] = DEAD[key]
            rows.append(row)

    selectors = codec.get("Selectors") or {}
    for key in SELECTOR_ROWS:
        if key not in selectors:
            print("  Selectors has no %s in %s, skipped" % (key, VERSION))
            continue
        rows.append({"id": "selector/" + key, "family": "Selectors", "key": key,
                     "area": "west", "class": "selector", "owner": "citystyle",
                     "plots": DEFAULT_PLOTS, "size": [1, 1]})

    if "buildings" in selectors:
        rows.append({"id": "building/1x1", "family": "Selectors", "key": "buildings",
                     "area": "east", "class": "selector", "owner": "citystyle",
                     "plots": DEFAULT_PLOTS, "size": [1, 1]})
    if "multibuildings" in selectors:
        for w, h in MULTI_SIZES:
            laid = MULTI_PLOTS if max(w, h) <= MULTI_LAID_OUT_UP_TO else 0
            rows.append({"id": "multibuilding/%dx%d" % (w, h), "family": "Selectors",
                         "key": "multibuildings", "area": "east", "class": "selector",
                         "owner": "citystyle", "plots": laid, "size": [w, h]})

    doc = {"_about": "Generated by mod/tools/extract-catalogue.py. Do not edit.",
           "version": VERSION, "rows": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, indent=1) + "\n")

    by_area = {}
    for r in rows:
        by_area[r["area"]] = by_area.get(r["area"], 0) + 1
    print("%d rows written to %s" % (len(rows), os.path.relpath(OUT, REPO)))
    for area, n in sorted(by_area.items()):
        print("  %-6s %d rows" % (area, n))
    empty = sum(1 for r in rows if r["plots"] == 0)
    chunks = sum(r["plots"] * r["size"][0] * r["size"][1] for r in rows)
    print("  %d rows declared but not laid out until grown" % empty)
    print("  %d chunks of plot laid out by default" % chunks)
    print("  %d rows hold exactly one plot" % sum(1 for r in rows if r["plots"] == 1))
    print("  %d rows are flagged dead" % sum(1 for r in rows if "dead" in r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
