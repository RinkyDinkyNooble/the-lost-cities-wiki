#!/usr/bin/env python3
"""Build the behaviour pack.

    python docs/examples/behaviour/generate.py

The other packs here answer "does this key parse and does the file load". This one
answers "does the feature the key names actually build something", for the features
the wiki could previously only describe from the code: cellars, `preferslonely`,
highways, railways, city spheres and monorails.

Every one of them is tested as a **pair**. One profile turns the feature on, a
second differs from it in a single key and turns it off, and both count the same
marker block over the same area. A count on its own says nothing: these features
place themselves where the world generator decides, so "found some" could be luck
and "found none" could be a broken pack. A pair separates the feature from the
fixture, and the off run is what makes the on run mean something.

Each feature gets its own block, so one count can never be another feature's
output:

    gold        an ordinary above-ground building level
    lapis       a cellar level
    iron        a highway part
    redstone    a railway part
    emerald     a monorail part
    sea lantern the glass shell of a city sphere
    white       the filler skirt

Two settings are in every profile here and are worth understanding before copying
anything out of it:

  * `cityChance` is 1.0, so the whole grid is city and a feature has somewhere to
    appear. In an ordinary world it is 0.01.
  * `highwayDistanceMask` is 0 everywhere except the highway test. At `cityChance`
    1.0 the highway network claims chunk after chunk, and a chunk it has claimed
    refuses a building unless the chunk's city level is at least two above the
    highway's. Leaving it on turns every chunk into a street with no error to say
    why.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = "bh"
ROOT = os.path.join(HERE, "data", NS, "lostcities")

# Marker characters, and why they are punctuation rather than letters.
#
# This pack layers its palette on top of the mod's own so that the shipped street
# and front parts still resolve. Layering means the last definition of a character
# wins, so any character this pack defines is taken away from every shipped part
# that used it. **The mod's palettes between them use every letter and every
# digit**, so a marker named `G` or `S` is not a new character, it is a repaint of
# an existing one, and shipped parts then draw this pack's blocks.
#
# That is not theoretical. With `S` for the sphere shell, the control that was
# supposed to place no sphere at all came back with 303 sea lanterns, drawn by the
# mod's own parts. Seven characters are free across every shipped palette, and
# these are six of them.
FILLER, GOLD, LAPIS, REDSTONE, EMERALD, IRON, SPHERE = (
    '"', "'", ",", "<", ">", "?", "]")


def write(folder, name, doc):
    path = os.path.join(ROOT, folder)
    os.makedirs(path, exist_ok=True)
    with io.open(os.path.join(path, name + ".json"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=2) + "\n")


def solid(ch, slices=6):
    """A part body. Six slices, because a part of one slice draws nothing (EK-3)."""
    return [[ch * 16 for _ in range(16)] for _ in range(slices)]


# --------------------------------------------------------------------- palette
write("palettes", "main", {
    "palette": [
        {"char": FILLER, "block": "minecraft:white_concrete"},
        {"char": GOLD, "block": "minecraft:gold_block"},
        {"char": LAPIS, "block": "minecraft:lapis_block"},
        {"char": REDSTONE, "block": "minecraft:redstone_block"},
        {"char": EMERALD, "block": "minecraft:emerald_block"},
        {"char": IRON, "block": "minecraft:iron_block"},
        {"char": SPHERE, "block": "minecraft:sea_lantern"},
    ]
})

# ----------------------------------------------------------------------- style
# A city style's own block characters, `sphereblocks.glass` among them, are resolved
# through the style named on the city style, not through the palette a part
# references. Pointing at the mod's `standard` style leaves this pack's characters
# undefined there, and the sphere shell then draws nothing at all, silently.
#
# The layers up to the last are the mod's own `standard` style with one palette each
# instead of a weighted choice, so nothing here varies run to run. Dropping the brick
# and glass layers fails the shipped parts this pack still uses for streets and
# fronts, with "Could not find entry '$'". This pack's palette goes last so its own
# characters win.
write("styles", "main", {
    "randompalettes": [
        [{"factor": 1.0, "palette": "common"}],
        [{"factor": 1.0, "palette": "default"}],
        [{"factor": 1.0, "palette": "bricks_standard"}],
        [{"factor": 1.0, "palette": "glass_full"}],
        [{"factor": 1.0, "palette": "glass_side_variant_glass"}],
        [{"factor": 1.0, "palette": NS + ":main"}],
    ]
})

# The outside style matters as much as the city one, and for a reason that is not
# obvious. A chunk that is not a city chunk compiles its palette from the world
# style's `outsidestyle`, not from the city style's `style`. A city sphere's shell
# is drawn on those chunks, so the shell character has to exist in the **outside**
# style too. Pointing `outsidestyle` at the mod's own `outside` while the shell
# character is defined only here leaves the lookup null, and the sphere feature has
# no null check: the server goes down with a bare NullPointerException during
# feature placement, naming nothing.
write("styles", "outside", {
    "randompalettes": [
        [{"factor": 1.0, "palette": "common"}],
        [{"factor": 1.0, "palette": "default"}],
        [{"factor": 1.0, "palette": "bricks_standard"}],
        [{"factor": 1.0, "palette": "glass_full"}],
        [{"factor": 1.0, "palette": "glass_side_variant_glass"}],
        [{"factor": 1.0, "palette": NS + ":main"}],
    ]
})

# ----------------------------------------------------------------------- parts
for name, ch in (("body", GOLD), ("cellar", LAPIS), ("hway", IRON),
                 ("rail", REDSTONE), ("mono", EMERALD)):
    write("parts", name, {
        "xsize": 16,
        "zsize": 16,
        "refpalette": NS + ":main",
        "slices": solid(ch),
    })

# ------------------------------------------------------------------- buildings
# Three buildings that differ only in `preferslonely`. `plain` leaves the key out
# entirely, which is what an ordinary building does.
BUILDINGS = {"plain": None, "lonely": 1.0, "crowd": 0.0}

for name, lonely in BUILDINGS.items():
    doc = {
        "filler": FILLER,
        "refpalette": NS + ":main",
        "minfloors": 1,
        "maxfloors": 1,
        # No `mincellars` or `maxcellars`. Both default to -1, which the mod reads
        # as "not set", so the profile's cellar count passes through untouched and
        # one profile key is the only thing that decides whether cellars appear.
        "parts": [
            {"part": NS + ":cellar", "cellar": True},
            {"part": NS + ":body", "cellar": False},
        ],
    }
    if lonely is not None:
        doc["preferslonely"] = lonely
    write("buildings", name, doc)

    write("citystyles", name, {
        "inherit": "citystyle_common",
        "style": NS + ":main",
        "explosionchance": 0.0,
        "buildingsettings": {"buildingchance": 1.0},
        # The sphere shell gets its own block so a sphere count can never pick up
        # a building. citystyle_common's shell is glass, which the terrain also has.
        "sphereblocks": {"glass": SPHERE, "border": FILLER,
                         "inner": FILLER},
        "selectors": {"buildings": [{"factor": 1.0, "value": NS + ":" + name}]},
    })

# --------------------------------------------------------------- world styles
def worldstyle(citystyle, extra=None):
    doc = {
        "outsidestyle": NS + ":outside",
        "citystyles": [{"factor": 1.0, "citystyle": NS + ":" + citystyle}],
    }
    doc.update(extra or {})
    return doc


for name in BUILDINGS:
    write("worldstyles", name, worldstyle(name))

# Every highway shape points at the same part, so the count does not depend on
# which shape the network happened to choose at a given chunk.
write("worldstyles", "highway", worldstyle("plain", {
    "parts": {"highways": {k: NS + ":hway" for k in
                           ("open", "open_bi", "bridge", "bridge_bi",
                            "tunnel", "tunnel_bi")}}
}))

write("worldstyles", "rail", worldstyle("plain", {
    "parts": {"railways": {k: NS + ":rail" for k in
                           ("railsflat", "railsbend", "railsdown1", "railsdown2",
                            "railshorizontal", "railshorizontalend",
                            "railshorizontalwater", "railsvertical",
                            "railsverticalwater", "rails3split", "stationopen",
                            "stationopenroof", "stationstaircase",
                            "stationstaircasesurface", "stationunderground",
                            "stationundergroundstairs")}}
}))

write("worldstyles", "sphere", worldstyle("plain", {
    "parts": {"monorails": {k: NS + ":mono"
                            for k in ("both", "station", "vertical")}},
    "cityspheres": {"centerpart": NS + ":body", "centerpartoffset": 0,
                    "centerpartorigin": "ground", "centertype": "default"},
}))

# ------------------------------------------------------------------- profiles
BASE = {
    "lostcity": {
        "ruinChance": 0.0,
        "generateLoot": False,
        "buildingMinFloors": 1,
        "buildingMaxFloors": 1,
        "buildingMinCellars": 0,
        "buildingMaxCellars": 0,
        "buildingChance": 1.0,
        "highwayDistanceMask": 0,
        "railwaysEnabled": False,
    },
    "cities": {"cityChance": 1.0},
    "explosions": {"explosionChance": 0.0, "miniExplosionChance": 0.0},
}

# name -> (worldstyle, the keys that differ from BASE)
PROFILES = {
    # Cellars. One key apart, and that key is the whole test.
    "bhcellar": ("plain", {"lostcity": {"buildingMinCellars": 1,
                                        "buildingMaxCellars": 1}}),
    "bhnocellar": ("plain", {}),

    # The same as bhnocellar with every chunk pinned to city level 0.
    # `getLevelBasedOnHeight` returns 0 as soon as the terrain height is below
    # `cityLevel0Height`, and 384 is above any terrain, so nothing reaches level 1.
    # This matters because the profile's cellar maximum is not a cap: the chunk's
    # city level is added to it, so a maximum of 0 still yields cellars on any
    # chunk above level 0. Removing the level removes the addition.
    # `cityLevel0Height` is in the `cities` section, not `lostcity`. Put in the
    # wrong section it is simply not read, and the run comes back identical to the
    # one without it, which looks like the setting having no effect.
    "bhcellarflat": ("plain", {"cities": {"cityLevel0Height": 384}}),

    # preferslonely. Nothing in the profile changes; the difference is the
    # building the city style selects, so the worldstyle is the variable.
    "bhlonely": ("lonely", {}),
    "bhcrowd": ("crowd", {}),

    # Highways. `highwayDistanceMask` is the switch: the level lookup returns -1
    # before reading anything else when it is 0 or less.
    "bhhighway": ("highway", {"lostcity": {"highwayDistanceMask": 1,
                                           "highwayRequiresTwoCities": False}}),
    "bhnohighway": ("highway", {}),

    # Railways.
    "bhrail": ("rail", {"lostcity": {"railwaysEnabled": True}}),
    "bhnorail": ("rail", {}),

    # Railway stations are governed separately. `railwaysEnabled` is checked only
    # on chunks whose rail type is not a station, so turning it off leaves every
    # station standing. Both switches are needed to clear the network.
    "bhnorailall": ("rail", {"lostcity": {"railwayStationsEnabled": False,
                                          "railwaySurfaceStationsEnabled": False}}),

    # City spheres. `landscapeType` is what turns the sphere world on at all, so
    # the off run keeps the landscape and drops the chance to zero, which leaves
    # the sphere machinery running and nothing for it to place.
    # `outsideProfile` is not optional in a sphere world, whatever the key table
    # says. Without it the sphere feature dereferences a null profile on the first
    # chunk outside a sphere, and because that feature has no try/catch the server
    # goes down rather than the chunk failing. Thirteen caught NPEs and one
    # uncaught one, for a key left unset.
    # A sphere still needs its chunk to be a city chunk, so `cityChance` stays at
    # 1.0: at the mod's default of 0.01 no sphere appeared anywhere in the grid.
    # `citySphereFactor` is lowered so two neighbouring spheres do not touch,
    # which leaves the chunks between them outside any sphere. That gap is where a
    # monorail is drawn.
    "bhsphere": ("sphere", {"lostcity": {"landscapeType": "spheres"},
                            "cityspheres": {"citySphereChance": 1.0,
                                            "citySphereFactor": 0.5,
                                            "monorailChance": 1.0,
                                            "outsideProfile": "default"}}),
    "bhnosphere": ("sphere", {"lostcity": {"landscapeType": "spheres"},
                              "cityspheres": {"citySphereChance": 0.0,
                                              "citySphereFactor": 0.5,
                                              "monorailChance": 1.0,
                                              "outsideProfile": "default"}}),
}

profile_dir = os.path.join(HERE, "profile")
os.makedirs(profile_dir, exist_ok=True)

for name, (style, diff) in sorted(PROFILES.items()):
    doc = {section: dict(keys) for section, keys in BASE.items()}
    doc["lostcity"]["worldStyle"] = NS + ":" + style
    for section, keys in diff.items():
        doc.setdefault(section, {}).update(keys)
    with io.open(os.path.join(profile_dir, name + ".json"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=2) + "\n")

with io.open(os.path.join(HERE, "pack.mcmeta"), "w",
             encoding="utf-8", newline="\n") as f:
    f.write(json.dumps({
        "pack": {
            "pack_format": 15,
            "description": "Lost Cities wiki: cellars, preferslonely, highways, "
                           "railways, spheres and monorails, each against a control",
        }
    }, indent=2) + "\n")

print("behaviour pack written to", HERE)
print("%d profiles, %d world styles" % (len(PROFILES), len(BUILDINGS) + 3))
