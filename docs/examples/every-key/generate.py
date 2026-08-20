#!/usr/bin/env python3
"""Build the every-key fixture.

    python docs/examples/every-key/generate.py

This pack exists to *show* every key the Lost Cities codecs declare, in a file that
loads and generates. It is a reference fixture, not a tutorial: nobody should copy
it wholesale, and `first-city` is the pack to learn from.

Why generated rather than hand-written: the point of the pack is completeness, and
completeness is checked by `docs/examples/key-coverage.py`. Keeping the source in
one place makes it possible to add a key and regenerate rather than hunt through
fifteen files for where it belongs.

Every shape here was taken from the mod's own shipped assets rather than guessed.
Where a key appears on two different types under the same name, both are shown on
purpose: `palette` on a building and `palette` on a part are different keys.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = "ek"
ROOT = os.path.join(HERE, "data", NS, "lostcities")

G, D, W, A = "G", "D", "#", "_"      # gold, diamond, white concrete, air


def write(folder, name, doc):
    path = os.path.join(ROOT, folder)
    os.makedirs(path, exist_ok=True)
    with io.open(os.path.join(path, name + ".json"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=2) + "\n")


def rows(ch, n=16):
    return [ch * 16 for _ in range(n)]


def slab(ch, height):
    return [rows(ch) for _ in range(height)]


# --------------------------------------------------------------------- palettes
# PaletteRE + PaletteEntry + BlockEntry. Every optional entry key is here, each on
# its own character so none of them interfere.
write("palettes", "main", {
    "palette": [
        {"char": A, "block": "minecraft:air"},
        {"char": G, "block": "minecraft:gold_block"},
        {"char": D, "block": "minecraft:diamond_block"},
        {"char": W, "block": "minecraft:white_concrete"},
        # `blocks` is a weighted list, and `damaged` is what the ruin pass turns
        # this character into.
        # A weighted list fills a fixed array of 128 slots. Under 128 the mod
        # throws at load, so the last entry is deliberately oversized and gets
        # clipped to whatever is left. See the Palette reference.
        {"char": "b", "blocks": [{"random": 8, "block": "minecraft:cracked_stone_bricks"},
                                 {"random": 1000, "block": "minecraft:stone_bricks"}],
         "damaged": "minecraft:iron_bars"},
        # `variant` defers to a variant asset; `tag` is block entity NBT.
        {"char": "v", "variant": NS + ":demo"},
        {"char": "c", "block": "minecraft:chest", "loot": NS + ":demoloot",
         "tag": {"Items": [{"Slot": 0, "id": "minecraft:coal", "Count": 4}]}},
        {"char": "s", "block": "minecraft:spawner", "mob": NS + ":demomobs"},
        {"char": "T", "block": "minecraft:wall_torch[facing=north]", "torch": True},
        {"char": "h", "block": "minecraft:chain"},
        {"char": "g", "block": "minecraft:grass_block"},
        {"char": "l", "block": "minecraft:oak_leaves"},
        {"char": "i", "block": "minecraft:iron_bars"},
        {"char": "o", "block": "minecraft:glowstone"},
        {"char": "r", "block": "minecraft:dirt"},
    ]
})

# A second palette, so `frompalette` has somewhere to copy a character from and the
# three-layer merge has something to merge.
write("palettes", "alt", {
    "palette": [
        {"char": "@", "frompalette": W},
        {"char": "w", "block": "minecraft:white_stained_glass"},
    ]
})

# ----------------------------------------------------------------------- variant
# A variant is a weighted list under the same 128-slot rule as a palette's `blocks`.
write("variants", "demo", {
    "blocks": [
        {"random": 32, "block": "minecraft:polished_andesite"},
        {"random": 1000, "block": "minecraft:andesite"},
    ]
})

# ------------------------------------------------------------------------ style
# StyleRE + PaletteSelector. Each inner list is one layer of the palette stack.
# The mod's own palettes come first, because this pack points its street, highway
# and railway keys at the mod's shipped parts, and those parts use the mod's
# characters. Dropping `common` and `default` here fails them at generation with
# "Could not find entry 'S'".
write("styles", "demo", {
    "randompalettes": [
        [{"factor": 1.0, "palette": "common"}],
        [{"factor": 1.0, "palette": "default"}],
        [{"factor": 1.0, "palette": NS + ":main"}],
        [{"factor": 1.0, "palette": NS + ":alt"}],
    ]
})

# -------------------------------------------------------------------- conditions
# ConditionRE + ConditionPart. Every selector a condition part accepts, spread
# across entries so the pack still resolves to something.
write("conditions", "demoloot", {
    "values": [
        {"factor": 8, "value": "minecraft:chests/simple_dungeon", "range": "4,100"},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon", "cellar": True},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon", "floor": 0},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon", "ground": True},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon", "top": True},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon",
         "inpart": NS + ":body"},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon",
         "belowpart": NS + ":body"},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon",
         "inbuilding": NS + ":tower"},
        {"factor": 2, "value": "minecraft:chests/simple_dungeon", "isbuilding": True},
        {"factor": 1, "value": "minecraft:chests/simple_dungeon", "issphere": False},
        {"factor": 1, "value": "minecraft:chests/simple_dungeon",
         "chunkx": 8, "chunkz": 8},
        # `inbiome` is one biome name as a plain string. It is NOT a
        # BiomeMatcher, despite the `biomes` keys elsewhere being one, and the
        # accepted shape is not the same on every version: 7.5.1 takes a list or
        # a string, 8.2.2 takes only a string, and 7.4.12 accepted an object and
        # did nothing with it. A bare string is the form all of them accept.
        {"factor": 1, "value": "minecraft:chests/simple_dungeon",
         "inbiome": "minecraft:plains"},
    ]
})

write("conditions", "demomobs", {
    "values": [{"factor": 1, "value": "minecraft:zombie"}]
})

# ------------------------------------------------------------------------- parts
# BuildingPartRE. `palette` inline on a part, `refpalette` by name, and `meta`
# with every value type it accepts.
write("parts", "body", {
    "xsize": 16, "zsize": 16,
    "refpalette": NS + ":main",
    "slices": slab(G, 2),
})

# Two things about this part are load-bearing and neither is obvious.
#
# The embedded palette is a whole PaletteRE, so the entry list sits under a
# SECOND "palette" key. Writing the list bare is the natural guess and it fails
# silently: the optional field decodes to nothing, the characters resolve to
# nothing, and the filler quietly takes the part's whole volume with no error.
#
# It also has two slices rather than one. A single-slice version of this exact
# part, with an identical palette, drew nothing at all and left the same silent
# filler behind. Two slices draw.
# `Q` is defined ONLY here, in this part's own embedded palette. That is what
# makes this part a real test of the key: if the embedded palette were ignored,
# the character would resolve to nothing and no emerald would appear.
write("parts", "top", {
    "xsize": 16, "zsize": 16,
    "palette": {"palette": [{"char": "Q", "block": "minecraft:emerald_block"}]},
    "slices": slab("Q", 2),
})

write("parts", "meta_demo", {
    "xsize": 16, "zsize": 16,
    "refpalette": NS + ":main",
    "meta": [
        {"key": "support", "char": "v"},
        {"key": "enabled", "boolean": True},
        {"key": "weight", "float": 0.5},
        {"key": "count", "integer": 3},
        {"key": "label", "string": "demo"},
    ],
    "slices": slab(W, 1),
})

write("parts", "front", {
    "xsize": 16, "zsize": 16,
    "refpalette": NS + ":main",
    "slices": slab(A, 1),
})

write("parts", "support", {
    "xsize": 16, "zsize": 16,
    "refpalette": NS + ":main",
    "slices": slab(W, 1),
})

# --------------------------------------------------------------------- buildings
# BuildingRE + PartRef. Every optional building key, and every PartRef selector.
write("buildings", "tower", {
    "filler": W,
    "rubble": "b",
    "refpalette": NS + ":main",
    # A building's embedded palette, same nesting as a part's.
    "palette": {"palette": [{"char": "h", "block": "minecraft:chain"}]},
    "minfloors": 2, "maxfloors": 2,
    "mincellars": 0, "maxcellars": 0,
    "overrideFloors": True,
    "allowDoors": False,
    "allowFillers": False,
    "preferslonely": 0.0,   # a chance from 0 to 1, not a boolean
    # Every level collects EVERY entry whose conditions match and then picks one
    # at random with equal probability. It is not a first-match list. So each
    # entry below carries `top: false`, exactly as the mod's own buildings do,
    # or the roof entry competes with all of them at the top level and loses
    # twelve times out of thirteen.
    "parts": [
        {"part": NS + ":top", "top": True},
        {"part": NS + ":body", "top": False, "ground": True},
        {"part": NS + ":body", "top": False, "cellar": False},
        {"part": NS + ":body", "top": False, "floor": 1},
        {"part": NS + ":body", "top": False, "range": "0,1"},
        {"part": NS + ":body", "top": False, "inpart": NS + ":body"},
        {"part": NS + ":body", "top": False, "belowpart": NS + ":body"},
        {"part": NS + ":body", "top": False, "inbuilding": NS + ":tower"},
        {"part": NS + ":body", "top": False, "isbuilding": True},
        {"part": NS + ":body", "top": False, "issphere": False},
        {"part": NS + ":body", "top": False, "chunkx": 8, "chunkz": 8},
        # `inbiome` is deliberately NOT used on a part reference. On 8.2.2 it
        # reads a biome out of a neighbouring chunk while that chunk is still
        # generating, which 1.21 refuses, and every chunk in the grid dies with
        # "Exception generating new chunk". It is demonstrated on a condition
        # instead, where it is evaluated later and is safe.
        {"part": NS + ":body", "top": False},
    ],
    # parts2 is the second pass, and arrives in 7.5.
    "parts2": [{"part": NS + ":meta_demo"}],
})

write("buildings", "annex", {
    "filler": W,
    "refpalette": NS + ":main",
    "minfloors": 1, "maxfloors": 1,
    "mincellars": 0, "maxcellars": 0,
    "overrideFloors": True,
    "parts": [{"part": NS + ":support"}],
})

# ---------------------------------------------------------------- multibuilding
write("multibuildings", "demo", {
    "dimx": 2, "dimz": 1,
    "buildings": [[NS + ":annex"], [NS + ":annex"]],
})

# ------------------------------------------------ infrastructure part overrides
# Every key of StreetParts, HighwayParts and RailwayParts, each pointing at the
# part the mod itself defaults to. Setting them to their own defaults keeps the
# pack generating exactly as it would without them, so these demonstrate the
# shape without changing the result.
STREET_PARTS = {
    "full": "street_full", "straight": "street_straight", "end": "street_end",
    "bend": "street_bend", "t": "street_t", "none": "street_none",
    "all": "street_all", "connector": "street_large_connector",
    "stair": "street_stair",
}

HIGHWAY_PARTS = {
    "open": "highway_open", "open_bend": "highway_open_bend",
    "open_bi": "highway_open_bi", "open_t": "highway_open_t",
    "bridge": "highway_bridge", "bridge_bend": "highway_bridge_bend",
    "bridge_bi": "highway_bridge_bi", "bridge_t": "highway_bridge_t",
    "tunnel": "highway_tunnel", "tunnel_bend": "highway_tunnel_bend",
    "tunnel_bi": "highway_tunnel_bi", "tunnel_t": "highway_tunnel_t",
}

RAILWAY_PARTS = {
    "railsflat": "rails_flat", "railsbend": "rails_bend",
    "railsdown1": "rails_down1", "railsdown2": "rails_down2",
    "railshorizontal": "rails_horizontal",
    "railshorizontalend": "rails_horizontal_end",
    "railshorizontalwater": "rails_horizontal_water",
    "railsvertical": "rails_vertical",
    "railsverticalwater": "rails_vertical_water",
    "rails3split": "rails_3split",
    "stationopen": "station_open", "stationopenroof": "station_openroof",
    "stationstaircase": "station_staircase",
    "stationstaircasesurface": "station_staircase_surface",
    "stationunderground": "station_underground",
    "stationundergroundstairs": "station_underground_stairs",
}

# -------------------------------------------------------------------- city style
# CityStyleRE and every settings block it holds, plus all nine selector lists.
def sel(value, extra=None):
    out = {"factor": 1.0, "value": value}
    if extra:
        out.update(extra)
    return [out]


write("citystyles", "demo", {
    "inherit": "citystyle_common",
    "style": NS + ":demo",
    "explosionchance": 0.0,
    "buildingsettings": {
        "buildingchance": 1.0,
        "minfloors": 2, "maxfloors": 2,
        "mincellars": 0, "maxcellars": 0,
    },
    "streetblocks": {
        "street": "b", "streetbase": "b", "streetvariant": "b",
        "border": "b", "wall": "b", "width": 6,
        # StreetParts, three times over. Each value may be one part name or a
        # list of them, which is why these keys were missed by an extractor
        # looking only for fieldOf.
        "parts": STREET_PARTS,
        "largeparts": STREET_PARTS,
        "tertiaryparts": STREET_PARTS,
        "frontchance": 1.0,
        "fountainchance": 0.0,
    },
    # elevation and grass are palette CHARACTERS. parkborder and parkelevation
    # are booleans despite reading like block slots.
    "parkblocks": {
        "elevation": "b", "grass": "g",
        "parkchance": 0.0, "parkborder": False, "parkelevation": False,
        "parkstreetthreshold": 3, "avoidfoliage": True,
    },
    "corridorblocks": {"roof": "b", "glass": "w", "corridorchance": 0.0},
    "railblocks": {"railmain": "b"},
    "sphereblocks": {"glass": "w", "border": "b", "inner": "b"},
    # All four are characters too. A block name here resolves to nothing and the
    # chunk dies later in generateRandomVegetation with a null block state.
    "generalblocks": {"glowstone": "o", "ironbars": "i",
                      "leaves": "l", "rubbledirt": "r"},
    "profile_overrides": {"openLotParkChance": 0.0},
    "stuff_tags": ["demo"],
    "selectors": {
        # ObjectSelector carries three extra keys beyond factor and value.
        # feather is an int, not a fraction.
        "buildings": sel(NS + ":tower", {"feather": 1,
                                         "minSpawnDistance": 0,
                                         "maxSpawnDistance": 10000}),
        "multibuildings": sel(NS + ":demo"),
        "fronts": sel(NS + ":front"),
        "bridges": sel(NS + ":support"),
        "largebridges": sel(NS + ":support"),
        "fountains": sel(NS + ":support"),
        "parks": sel(NS + ":support"),
        "raildungeons": sel(NS + ":support"),
        "stairs": sel(NS + ":support"),
    },
})

# ------------------------------------------------------------------- world style
write("worldstyles", "demo", {
    "outsidestyle": "outside",
    "citystyles": [{"factor": 1.0, "citystyle": NS + ":demo",
                    "biomes": {"if_any": ["minecraft:plains"]}},
                   {"factor": 1.0, "citystyle": NS + ":demo"}],
    "citybiomemultipliers": [
        {"multiplier": 0.1, "biomes": {"if_any": ["#minecraft:is_ocean"]}}],
    "settings": {
        "railwayavoidance": "ignore", "railpartheight6": 1,
        # These four are BLOCK STATES, not chances. A number here is silently
        # dropped on 7.5.1 and refuses to load at all on 8.4.1 and later.
        "vinenorth": {"Name": "minecraft:vine"},
        "vinesouth": {"Name": "minecraft:vine"},
        "vineeast": {"Name": "minecraft:vine"},
        "vinewest": {"Name": "minecraft:vine"},
    },
    "multisettings": {"areasize": 10, "minimum": 1, "maximum": 5,
                      "correctstylefactor": 0.8, "attempts": 50},
    "cityspheres": {"centerpart": NS + ":support", "centerpartoffset": 0,
                    "centerpartorigin": "ground", "centertype": "default"},
    # PartSelector. No shipped worldstyle sets this, so these three objects are
    # the only worked examples of them anywhere.
    "parts": {
        "highways": HIGHWAY_PARTS,
        "railways": RAILWAY_PARTS,
        "monorails": {"both": "monorails_both", "station": "monorails_station",
                      "vertical": "monorails_vertical"},
    },
    "scattered": {
        "areasize": 8, "chance": 0.0, "weightnone": 100,
        "list": [{"name": NS + ":demo", "weight": 1, "maxheightdiff": 3,
                  "allowvoid": False, "nearhighway": False,
                  "biomes": {"excluding": ["#minecraft:is_ocean"]}}],
    },
})

# --------------------------------------------------------------------- scattered
write("scattered", "demo", {
    "buildings": [NS + ":annex"],
    "multibuilding": NS + ":demo",
    "terrainheight": "highest", "terrainfix": "repeatslice",
    "heightoffset": 0, "rotatable": True,
    "clearhighwayrailing": True, "supportpart": NS + ":support",
})

# ------------------------------------------------------------------------- stuff
write("stuff", "demo", {
    "column": "h", "mincount": 1, "maxcount": 2, "attempts": 4,
    "minheight": 40, "maxheight": 120,
    "inbuilding": True, "seesky": False,
    "tags": ["demo"],
    "upperblocks": {"if_any": ["minecraft:air"]},
    "biomes": {"excluding": ["#minecraft:is_ocean"]},
    "blocks": {"if_any": ["minecraft:gold_block"],
               "if_all": ["minecraft:gold_block"],
               "excluding": ["minecraft:bedrock"]},
    "buildings": {"if_any": [NS + ":tower"], "excluding": [NS + ":annex"]},
})

# -------------------------------------------------------- predefined city, sphere
write("predefinedcities", "demo", {
    "dimension": "lostcities:lostcity",
    "chunkx": 8, "chunkz": 8, "radius": 8,
    "citystyle": NS + ":demo",
    "buildings": [
        {"building": NS + ":tower", "chunkx": 0, "chunkz": 0,
         "multi": False, "preventruins": True},
    ],
    "streets": [{"chunkx": 1, "chunkz": 0}],
})

write("predefinedspheres", "demo", {
    "dimension": "lostcities:lostcity",
    "chunkx": 20, "chunkz": 20,
    "centerx": 328, "centerz": 328, "radius": 40,
})

# -------------------------------------------------------------------- pack files
with io.open(os.path.join(HERE, "pack.mcmeta"), "w",
             encoding="utf-8", newline="\n") as f:
    f.write(json.dumps({"pack": {
        "pack_format": 15,
        "description": "Lost Cities wiki: every asset key, in a pack that loads"
    }}, indent=2) + "\n")

profile = os.path.join(HERE, "profile")
os.makedirs(profile, exist_ok=True)
with io.open(os.path.join(profile, "ekdemo.json"), "w",
             encoding="utf-8", newline="\n") as f:
    f.write(json.dumps({
        "lostcity": {
            "worldStyle": NS + ":demo",
            "ruinChance": 0.0,
            "generateLoot": False,
            "buildingMinFloors": 2, "buildingMaxFloors": 2,
            "buildingMinCellars": 0, "buildingMaxCellars": 0,
        },
        "cities": {"cityChance": 0.0},
        "explosions": {"explosionChance": 0.0, "miniExplosionChance": 0.0},
    }, indent=2) + "\n")

# ============================================================== the full profile
# `ekdemo` above is a minimal profile: it sets the handful of keys the tests need
# and leaves everything else alone. `ekfull` is the opposite. It sets EVERY profile
# key the mod declares, so that a reader can see the shape and the section of each
# one in a file that actually runs.
#
# Each key is written at its own documented default, read straight out of
# `mod-keys.json`. That is what makes the file safe: a profile setting every key to
# the value the mod would have used anyway generates the same world as one setting
# none of them, so the fixture proves the keys parse without changing what it builds.
# The handful of keys the test itself depends on are overridden below.
#
# The five `client` keys are deliberately absent. Fog and horizon exist only on the
# client, so a headless server can neither read nor demonstrate them.

KEYS = json.load(io.open(os.path.join(HERE, "..", "mod-keys.json"),
                         encoding="utf-8"))
PROFILE_KEYS = max(
    KEYS["versions"].values(),
    key=lambda v: len(v["profile"]))["profile"]

# Keys whose default is null. A null means "unset", which demonstrates nothing, so
# each gets a real value pointing at something this pack defines.
FILL_IN = {
    "cityStyleAlternative": NS + ":demo",
    "outsideProfile": "bio_wasteland",
    "spawnCity": NS + ":demo",
    "spawnSphere": NS + ":demo",
    "spawnBiome": "minecraft:plains",
    "forceSpawnBuildings": [NS + ":tower"],
    "forceSpawnParts": [NS + ":body"],
    "icon": "minecraft:stone",
    "warning": "A reference fixture. Not a playable profile.",
    "extraDescription": "Sets every profile key the mod declares.",
}

# What the test needs, overriding the defaults.
OVERRIDE = {
    "worldStyle": NS + ":demo",
    "cityChance": 0.0,            # only the pinned city generates
    "ruinChance": 0.0,
    "explosionChance": 0.0,
    "miniExplosionChance": 0.0,
    "generateLoot": False,
    "buildingMinFloors": 2, "buildingMaxFloors": 2,
    "buildingMinCellars": 0, "buildingMaxCellars": 0,
}


def profile_value(name, meta):
    if name in OVERRIDE:
        return OVERRIDE[name]
    if name in FILL_IN:
        return FILL_IN[name]
    default, kind = meta.get("default"), meta.get("type", "")
    if kind == "Boolean":
        return bool(default)
    if default is None:
        # No default and no fill-in: fall back to something of the right shape,
        # so the key is still present and still parses.
        return [] if kind == "StringList" else ""
    return default


full = {}
for name, meta in sorted(PROFILE_KEYS.items()):
    section = meta.get("section")
    if section == "client":
        continue
    full.setdefault(section, {})[name] = profile_value(name, meta)

io.open(os.path.join(profile, "ekfull.json"), "w",
        encoding="utf-8", newline="\n").write(json.dumps(full, indent=2) + "\n")
print("ekfull.json: %d keys across %d sections"
      % (sum(len(v) for v in full.values()), len(full)))

print("every-key pack written to", HERE)
