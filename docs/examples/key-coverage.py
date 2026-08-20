#!/usr/bin/env python3
"""Report which Lost Cities asset keys no example datapack demonstrates.

    python docs/examples/key-coverage.py
    python docs/examples/key-coverage.py --pack every-key
    python docs/examples/key-coverage.py --missing

The wiki documents every key the mod's codecs declare. That is not the same as
showing one. A reader who wants to know what `frompalette` looks like in a real
file is not helped by a table cell describing it, and until a pack uses it there is
nothing to point at.

Two things are checked, and they are deliberately different in strength.

  Own keys      Every key a top-level asset type declares must appear in a file of
                that type's own folder. This is the strong check: it distinguishes
                `palette` on a building from `palette` on a part, which are
                different keys that happen to share a name.

  Key names     Every key name any codec declares must appear somewhere. Nested
                data classes are checked this way because the mod's key export
                records what each class declares, not which class nests in which.

Coverage is measured against the richest version, since a key absent there does not
exist at all.
"""
import argparse
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = os.path.join(HERE, "mod-keys.json")

# Which codec describes the files in each registry folder. Only the top-level
# types appear here; everything else is nested inside one of them.
FOLDER_TYPE = {
    "buildings": "BuildingRE",
    "parts": "BuildingPartRE",
    "palettes": "PaletteRE",
    "styles": "StyleRE",
    "variants": "VariantRE",
    "conditions": "ConditionRE",
    "citystyles": "CityStyleRE",
    "worldstyles": "WorldStyleRE",
    "multibuildings": "MultiBuildingRE",
    "scattered": "ScatteredRE",
    "stuff": "StuffSettingsRE",
    "predefinedcities": "PredefinedCityRE",
    "predefinedcites": "PredefinedCityRE",
    "predefinedcitites": "PredefinedCityRE",
    "predefinedspheres": "PredefinedSphereRE",
}


def richest_version(data):
    """The version declaring the most keys. A key absent there is not a key."""
    return max(data["versions"],
               key=lambda v: sum(len(x) for x in data["versions"][v]["codec"].values()))


def walk_keys(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            out.add(k)
            walk_keys(v, out)
    elif isinstance(node, list):
        for item in node:
            walk_keys(item, out)


# Fog and horizon. They exist only on the client, so a headless server can never
# demonstrate them, and counting them as gaps would misreport the work as unfinished.
CLIENT_ONLY = "client"


def scan_profiles(pack_root):
    """Every profile key any profile file in this pack sets."""
    seen = set()
    for root, _, files in os.walk(pack_root):
        if os.path.basename(root) != "profile":
            continue
        for name in files:
            if not name.endswith(".json"):
                continue
            try:
                doc = json.load(io.open(os.path.join(root, name), encoding="utf-8"))
            except Exception:
                continue
            for section, body in doc.items():
                if isinstance(body, dict):
                    seen |= set(body)
                else:
                    seen.add(section)
    return seen


def scan(pack_root):
    """Return (keys seen anywhere, keys seen per registry folder)."""
    everywhere = set()
    by_folder = {}
    for root, _, files in os.walk(pack_root):
        folder = os.path.basename(root)
        for name in files:
            if not name.endswith(".json") or name == "pack.mcmeta":
                continue
            try:
                doc = json.load(io.open(os.path.join(root, name), encoding="utf-8"))
            except Exception:
                continue
            seen = set()
            walk_keys(doc, seen)
            everywhere |= seen
            if folder in FOLDER_TYPE:
                by_folder.setdefault(folder, set()).update(seen)
    return everywhere, by_folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", help="only this pack under docs/examples/")
    ap.add_argument("--missing", action="store_true",
                    help="list the uncovered keys and nothing else")
    args = ap.parse_args()

    data = json.load(io.open(KEYS, encoding="utf-8"))
    version = richest_version(data)
    codec = data["versions"][version]["codec"]
    all_names = {k for keys in codec.values() for k in keys}

    roots = ([os.path.join(HERE, args.pack)] if args.pack
             else [os.path.join(HERE, d) for d in sorted(os.listdir(HERE))
                   if os.path.isdir(os.path.join(HERE, d))])
    everywhere, by_folder = set(), {}
    for r in roots:
        e, f = scan(r)
        everywhere |= e
        for k, v in f.items():
            by_folder.setdefault(k, set()).update(v)

    missing_names = sorted(all_names - everywhere)

    profile = data["versions"][version]["profile"]
    prof_used = set()
    for r in roots:
        prof_used |= scan_profiles(r)
    prof_all = {k for k, meta in profile.items()
                if meta.get("section") != CLIENT_ONLY}
    prof_missing = sorted(prof_all - prof_used)
    prof_client = sorted(k for k, meta in profile.items()
                         if meta.get("section") == CLIENT_ONLY)

    own_gaps = []
    for folder, typename in FOLDER_TYPE.items():
        if typename not in codec:
            continue
        seen = by_folder.get(folder)
        if seen is None:
            continue
        for key in sorted(codec[typename]):
            if key not in seen:
                own_gaps.append((folder, typename, key))
    # A type with several folder spellings only needs covering under one of them.
    covered_types = {t for f, t in FOLDER_TYPE.items() if by_folder.get(f)}
    own_gaps = [g for g in own_gaps
                if not any(g[1] == t and g[2] in by_folder.get(f, set())
                           for f, t in FOLDER_TYPE.items() if t == g[1])]

    if args.missing:
        for k in missing_names:
            owners = sorted(t for t, ks in codec.items() if k in ks)
            print(f"{k:<24} {', '.join(owners)}")
        for k in prof_missing:
            print(f"{k:<24} profile [{profile[k].get('section')}]")
        return 1 if (missing_names or prof_missing) else 0

    covered = len(all_names) - len(missing_names)
    pct = 100 * covered // len(all_names) if all_names else 0
    print(f"measured against {version}, the richest key set\n")
    print(f"  key names demonstrated   {covered}/{len(all_names)}  ({pct}%)")
    print(f"  top-level types checked  {len(covered_types)}/{len(set(FOLDER_TYPE.values()))}")
    print(f"  own-key gaps             {len(own_gaps)}")
    pdone = len(prof_all) - len(prof_missing)
    ppct = 100 * pdone // len(prof_all) if prof_all else 0
    print(f"  profile keys set         {pdone}/{len(prof_all)}  ({ppct}%)"
          f"   [{len(prof_client)} client-only keys excluded]")

    if own_gaps:
        print("\nkeys a top-level type declares that no file of that type uses:")
        for folder, typename, key in own_gaps[:40]:
            print(f"  {folder}/  {typename}.{key}")
        if len(own_gaps) > 40:
            print(f"  ... and {len(own_gaps) - 40} more")
    if prof_missing:
        print("\n%d profile keys no example sets, for example: %s"
              % (len(prof_missing), ", ".join(prof_missing[:6])))
    if missing_names:
        print("\n%d key names no example uses. Run with --missing for the list "
              "and who declares them." % len(missing_names))
    elif not prof_missing:
        print("\nEvery key the codecs and the profile declare appears in an "
              "example, apart from the %d client-only keys, which a headless "
              "server cannot show." % len(prof_client))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
