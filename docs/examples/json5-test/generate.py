"""Generate the three JSON5 test packs from one definition.

pure-json    every asset .json
pure-json5   every asset .json5, with comments and trailing commas
fighting     both, where the .json twin is wrong wherever a wrong answer can be
             seen in blocks

All three are built to produce the SAME three towers: gold at x 136, diamond at
x 168, lapis at x 200. Any difference between the three is a fault.
"""
import io
import json
import os
import shutil
import zipfile

OUT = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(OUT, "packs")
NS = "j5"


def rows(char):
    """A solid floor, then five slices of wall, so a tower is easy to spot."""
    solid = [char * 16] * 16
    wall = [char * 16] + [char + "_" * 14 + char] * 14 + [char * 16]
    return [solid] + [wall] * 5


def part_body(char):
    slices = ",\n".join(
        "    [\n" + ",\n".join('      "%s"' % r for r in s) + "\n    ]"
        for s in rows(char))
    return ('{\n  "xsize": 16,\n  "zsize": 16,\n'
            '  "refpalette": "%s:demo",\n  "slices": [\n%s\n  ]\n}\n' % (NS, slices))


def building_body(part):
    return ('{\n'
            '  "filler": "#",\n'
            '  "refpalette": "%s:demo",\n'
            '  "minfloors": 3,\n  "maxfloors": 3,\n'
            '  "mincellars": 0,\n  "maxcellars": 0,\n'
            '  "overrideFloors": true,\n'
            '  "parts": [\n    { "part": "%s:%s" }\n  ]\n}\n' % (NS, NS, part))


def palette_body(gold, diamond, lapis):
    return ('{\n  "palette": [\n'
            '    { "char": "_", "block": "minecraft:air" },\n'
            '    { "char": "#", "block": "minecraft:white_concrete" },\n'
            '    { "char": "G", "block": "%s" },\n'
            '    { "char": "D", "block": "%s" },\n'
            '    { "char": "L", "block": "%s" },\n'
            '    { "char": "W", "block": "minecraft:redstone_block" }\n'
            '  ]\n}\n' % (gold, diamond, lapis))


def city_body(dimension, offset):
    return ('{\n'
            '  "dimension": "%s",\n'
            '  "chunkx": 8,\n  "chunkz": 8,\n  "radius": 8,\n'
            '  "citystyle": "%s:demo",\n'
            '  "buildings": [\n'
            '    { "building": "%s:gold",   "chunkx": 0, "chunkz": %d },\n'
            '    { "building": "%s:shadow", "chunkx": 2, "chunkz": %d },\n'
            '    { "building": "%s:lapis",  "chunkx": 4, "chunkz": %d }\n'
            '  ]\n}\n' % (dimension, NS, NS, offset, NS, offset, NS, offset))


WORLDSTYLE = ('{\n  "outsidestyle": "outside",\n'
              '  "citystyles": [\n    { "factor": 1.0, "citystyle": "%s:demo" }\n'
              '  ]\n}\n' % NS)

CITYSTYLE = ('{\n  "inherit": "citystyle_common",\n'
             '  "style": "standard",\n'
             '  "buildingsettings": { "buildingchance": 1.0 },\n'
             '  "selectors": {\n'
             '    "buildings": [\n      { "factor": 1.0, "value": "%s:gold" }\n    ]\n'
             '  }\n}\n' % NS)

PACK_MCMETA = ('{\n  "pack": {\n    "pack_format": 15,\n'
               '    "description": "%s"\n  }\n}\n')

# folder, name, correct content, wrong twin for the fighting pack.
# A wrong twin of None means the twin is content identical: it still has to be
# detected and reported, but no block can tell which one won.
ASSETS = [
    ("worldstyles", "demo", WORLDSTYLE, None),
    ("citystyles", "demo", CITYSTYLE, None),
    ("palettes", "demo",
     palette_body("minecraft:gold_block", "minecraft:diamond_block",
                  "minecraft:lapis_block"),
     palette_body("minecraft:redstone_block", "minecraft:redstone_block",
                  "minecraft:redstone_block")),
    ("predefinedcities", "demo_overworld",
     city_body("minecraft:overworld", 0), city_body("minecraft:overworld", 2)),
    ("predefinedcities", "demo_lostcity",
     city_body("lostcities:lostcity", 0), city_body("lostcities:lostcity", 2)),
    ("parts", "p_gold", part_body("G"), part_body("W")),
    ("parts", "p_diamond", part_body("D"), part_body("W")),
    ("parts", "p_lapis", part_body("L"), part_body("W")),
    ("buildings", "gold", building_body("p_gold"), building_body("p_diamond")),
    ("buildings", "shadow", building_body("p_diamond"), building_body("p_gold")),
    ("buildings", "lapis", building_body("p_lapis"), building_body("p_gold")),
]


def to_json5(text, note):
    """The same content, written the way an author would write JSON5.

    Built from the parsed object rather than by editing the text, so a trailing
    comma lands only where one is legal and never twice.
    """
    lines = json.dumps(json.loads(text), indent=2).split("\n")
    out = []
    for i, line in enumerate(lines):
        nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
        # A trailing comma before every close, which is the whole point of the
        # format and the thing strict JSON rejects.
        if nxt[:1] in ("]", "}") and not line.rstrip().endswith((",", "[", "{")):
            line += ","
        # A comment on the line an author would comment.
        if '"char"' in line:
            line += "  /* one marker per claim */"
        out.append(line)
    return "// %s\n" % note + "\n".join(out) + "\n"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def build(kind, root, description):
    write(os.path.join(root, "pack.mcmeta"), PACK_MCMETA % description)
    base = os.path.join(root, "data", NS, "lostcities")
    for folder, name, correct, wrong in ASSETS:
        if kind == "json":
            write(os.path.join(base, folder, name + ".json"), correct)
        elif kind == "json5":
            write(os.path.join(base, folder, name + ".json5"),
                  to_json5(correct, "%s/%s, as .json5" % (folder, name)))
        else:
            write(os.path.join(base, folder, name + ".json5"),
                  to_json5(correct, "The winner. Its .json twin is %s."
                           % ("wrong" if wrong else "identical")))
            write(os.path.join(base, folder, name + ".json"),
                  wrong if wrong else correct)


def zip_up(root, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _, files in os.walk(root):
            for f in sorted(files):
                full = os.path.join(dirpath, f)
                z.write(full, os.path.relpath(full, root).replace("\\", "/"))


if __name__ == "__main__":
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    made = []
    for kind, folder, description in (
            ("json", "j5-pure-json", "JSON5 test: every asset .json"),
            ("json5", "j5-pure-json5", "JSON5 test: every asset .json5"),
            ("fight", "j5-fighting", "JSON5 test: every asset both, .json5 wins")):
        root = os.path.join(DEST, folder)
        build(kind, root, description)
        zip_up(root, os.path.join(DEST, folder + ".zip"))
        made.append(folder)
    for name in made:
        print("built", name)
