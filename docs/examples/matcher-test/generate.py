#!/usr/bin/env python3
"""Build the matcher-test pack.

    python docs/examples/matcher-test/generate.py

One question: does a biome matcher actually gate what it is attached to, and do
`if_all`, `if_any` and `excluding` mean what the reference says they mean?

The pack answers it with three city styles that differ in exactly one thing. Each
builds out of its own block, and each is reached only through a `citystyles` entry
carrying one matcher:

    if_any    [minecraft:the_void]   gold      must not be selected
    if_all    [minecraft:the_void]   diamond   must not be selected
    excluding [minecraft:the_void]   emerald   must be selected

The void biome is what an empty world returns and does not occur in an overworld,
so the expected outcome is the same on every version and every seed. Naming a real
biome instead would tie the result to what the seed happened to put at the test
chunk, and biome generation is not stable across Minecraft versions.

No predefined city here, deliberately. A predefined city names its `citystyle`
directly, which bypasses the worldstyle's selection list, and the selection list is
the whole subject. `cityChance` is 1.0 instead, so every chunk in the grid is a city
chunk and the style comes from the worldstyle every time.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = "mt"
ROOT = os.path.join(HERE, "data", NS, "lostcities")

# char, block, and the citystyle each one belongs to
MARKERS = [
    ("gold", "G", "minecraft:gold_block", {"if_any": ["minecraft:the_void"]}),
    ("diamond", "D", "minecraft:diamond_block", {"if_all": ["minecraft:the_void"]}),
    ("emerald", "E", "minecraft:emerald_block", {"excluding": ["minecraft:the_void"]}),
]


def write(folder, name, doc):
    path = os.path.join(ROOT, folder)
    os.makedirs(path, exist_ok=True)
    with io.open(os.path.join(path, name + ".json"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=2) + "\n")


write("palettes", "main", {
    "palette": [
        {"char": "_", "block": "minecraft:air"},
        {"char": "#", "block": "minecraft:white_concrete"},
    ] + [{"char": ch, "block": block} for _, ch, block, _ in MARKERS]
})

for name, ch, _, _ in MARKERS:
    # Six slices, solid. A part of a single slice draws nothing, which cost a round
    # to find on the every-key fixture and is recorded as EK-3.
    write("parts", name, {
        "xsize": 16,
        "zsize": 16,
        "refpalette": NS + ":main",
        "slices": [[ch * 16 for _ in range(16)] for _ in range(6)],
    })

    write("buildings", name, {
        "filler": "#",
        "refpalette": NS + ":main",
        "minfloors": 1,
        "maxfloors": 1,
        "mincellars": 0,
        "maxcellars": 0,
        "overrideFloors": True,
        "preferslonely": 0.0,
        "parts": [{"part": NS + ":" + name}],
    })

    write("citystyles", name, {
        "inherit": "citystyle_common",
        "style": "standard",
        "explosionchance": 0.0,
        "buildingsettings": {"buildingchance": 1.0},
        "selectors": {
            "buildings": [{"factor": 1.0, "value": NS + ":" + name}]
        },
    })

write("worldstyles", "test", {
    "outsidestyle": "outside",
    "citystyles": [
        {"factor": 1.0, "citystyle": NS + ":" + name, "biomes": matcher}
        for name, _, _, matcher in MARKERS
    ],
})

# The control. Identical in every respect except that its one entry carries no
# `biomes` key at all, so nothing can gate it. Without this, "no emerald" is
# ambiguous: it could mean the matcher rejected, or it could mean the pack, the
# profile or `cityChance` never built anything to begin with. The control tells the
# two apart, and it is the only reason the test result can be read.
write("worldstyles", "control", {
    "outsidestyle": "outside",
    "citystyles": [{"factor": 1.0, "citystyle": NS + ":emerald"}],
})

profile = os.path.join(HERE, "profile")
os.makedirs(profile, exist_ok=True)


def profile_doc(worldstyle):
    return {
        "lostcity": {
            "worldStyle": NS + ":" + worldstyle,
            "ruinChance": 0.0,
            "generateLoot": False,
            "buildingMinFloors": 1,
            "buildingMaxFloors": 1,
            "buildingMinCellars": 0,
            "buildingMaxCellars": 0,
            # Highways and railways off. Both are needed, and the reason is not
            # obvious: at `cityChance: 1.0` the whole world is one city, so the
            # highway network claims chunk after chunk, and a chunk the network has
            # claimed refuses a building unless its city level is at least two
            # above the highway. Every chunk came back a street until these two
            # were set, with no error anywhere to say why.
            # `highwayDistanceMask: 0` is the off switch: the level lookup returns
            # -1 before it reads anything else.
            "highwayDistanceMask": 0,
            "railwaysEnabled": False,
            # Set in both places on purpose. The city style's `buildingchance` is
            # what the mod prefers, and the profile's is the fallback when the
            # style leaves it unset. Setting only the style left roughly one chunk
            # in eight holding a building, which is not enough to assert on.
            "buildingChance": 1.0,
        },
        # Every chunk is a city chunk, so the worldstyle picks a style every time
        # rather than once somewhere the probe cannot see.
        "cities": {"cityChance": 1.0},
        "explosions": {"explosionChance": 0.0, "miniExplosionChance": 0.0},
    }


for prof, worldstyle in (("mtdemo", "test"), ("mtcontrol", "control")):
    with io.open(os.path.join(profile, prof + ".json"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(profile_doc(worldstyle), indent=2) + "\n")

with io.open(os.path.join(HERE, "pack.mcmeta"), "w",
             encoding="utf-8", newline="\n") as f:
    f.write(json.dumps({
        "pack": {
            "pack_format": 15,
            "description": "Lost Cities wiki: biome matcher gating on a worldstyle",
        }
    }, indent=2) + "\n")

print("matcher-test written to", HERE)
