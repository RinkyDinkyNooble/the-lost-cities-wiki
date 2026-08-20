#!/usr/bin/env python3
"""Check that every key the mod declares is named on the page that documents it.

    python docs/examples/check_pages.py

`validate.py` checks one direction: every key a reference table names has to exist
in the mod. This checks the other: every key the mod declares has to be named on a
page. Nothing else was checking it, and the gap was real. When it was first run it
found **26** keys that existed in the codecs and appeared on no page as a key,
including the six highway shapes 7.5 added for its planned road network.

"Named on a page" means the key appears in backticks somewhere on the page that
owns its type. A key shown only inside a JSON example does not count: a reader
searching the page for the key finds nothing, and neither does the site search.

Measured against the version declaring the most keys, since a key absent there is
not a key.
"""
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
REPO = os.path.dirname(DOCS)

# Every codec type the mod declares, and the page that documents it. A type
# missing from this map is an error: it means the mod grew an asset shape nobody
# has written up, which is exactly what this file exists to notice.
OWNER = {
    "BuildingRE": "reference/building.md",
    "PartRef": "reference/building.md",
    "BuildingPartRE": "reference/part.md",
    "PartMeta": "reference/part.md",
    "PaletteRE": "reference/palette.md",
    "PaletteEntry": "reference/palette.md",
    "BlockEntry": "reference/palette.md",
    "StyleRE": "reference/style.md",
    "PaletteSelector": "reference/style.md",
    "VariantRE": "reference/variant.md",
    "ConditionRE": "reference/condition.md",
    "ConditionPart": "reference/condition.md",
    "CityStyleRE": "reference/citystyle.md",
    "CityProfileOverrides": "reference/citystyle.md",
    "BuildingSettings": "reference/citystyle.md",
    "StreetSettings": "reference/citystyle.md",
    "ParkSettings": "reference/citystyle.md",
    "CorridorSettings": "reference/citystyle.md",
    "RailSettings": "reference/citystyle.md",
    "SphereSettings": "reference/citystyle.md",
    "GeneralSettings": "reference/citystyle.md",
    "Selectors": "reference/citystyle.md",
    "ObjectSelector": "reference/citystyle.md",
    "WorldStyleRE": "reference/worldstyle.md",
    "CityStyleSelector": "reference/worldstyle.md",
    "CityBiomeMultiplier": "reference/worldstyle.md",
    "MultiSettings": "reference/worldstyle.md",
    "CitySphereSettings": "reference/worldstyle.md",
    "ScatteredSettings": "reference/worldstyle.md",
    "WorldSettings": "reference/worldstyle.md",
    "PartSelector": "concepts/infrastructure-parts.md",
    "HighwayParts": "concepts/infrastructure-parts.md",
    "RailwayParts": "concepts/infrastructure-parts.md",
    "MonorailParts": "concepts/infrastructure-parts.md",
    "StreetParts": "concepts/infrastructure-parts.md",
    "MultiBuildingRE": "reference/multibuilding.md",
    "ScatteredRE": "reference/scattered.md",
    "ScatteredReference": "reference/scattered.md",
    "StuffSettingsRE": "reference/stuff.md",
    "PredefinedCityRE": "reference/predefined.md",
    "PredefinedSphereRE": "reference/predefined.md",
    "PredefinedBuilding": "reference/predefined.md",
    "PredefinedStreet": "reference/predefined.md",
    "BiomeMatcher": "concepts/matchers.md",
    "BlockMatcher": "concepts/matchers.md",
    "ResourceLocationMatcher": "concepts/matchers.md",
    "IdentifierMatcher": "concepts/matchers.md",
}


def richest(versions):
    return max(versions, key=lambda v: sum(len(t) for t in versions[v]["codec"].values()))


def main():
    data = json.load(io.open(os.path.join(HERE, "mod-keys.json"), encoding="utf-8"))
    version = richest(data["versions"])
    codec = data["versions"][version]["codec"]

    text, errors = {}, 0
    for typ, keys in sorted(codec.items()):
        page = OWNER.get(typ)
        if not page:
            print(f"  no owner page mapped for codec type {typ}")
            errors += 1
            continue
        if page not in text:
            text[page] = io.open(os.path.join(DOCS, page), encoding="utf-8").read()
        gaps = [k for k in sorted(keys)
                if not re.search(r"`%s`" % re.escape(k), text[page])]
        if gaps:
            errors += len(gaps)
            print(f"  {page}: {typ} declares {', '.join(gaps)}, not named on the page")

    print(f"\nmeasured against {version}, the richest key set")
    print(f"  codec types      {len(codec)}")
    print(f"  keys            {sum(len(t) for t in codec.values())}")
    print(f"  undocumented    {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
