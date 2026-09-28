#!/usr/bin/env python3
"""Acceptance test for multi-building footprints past the generated catalogue.

    python mod/tools/check-multibuilding-size.py

Needs the wiki's test rig, the same way the other server checks do.

The generated catalogue stops at 10x10 because that is the default
`multisettings.areasize`, and a multi-building is placed inside one area of that
many chunks square. A pack is free to raise the area, and packs do: ChaosZPack
sets it to 16 and ships a 16x7 aircraft carrier, an 11x8 walmart and a 4x11. Those
generate in game, and an import that had no row for them dropped the largest
buildings the pack had and said so in a warning nobody could act on.

Footprints are now registered at import and appended to the catalogue. Appended,
never sorted: a row reserves a band of the world and a plot's position is written
down the first time anything is pasted onto it, so a row inserted ahead of an
existing one pushes it north and strands every build on it.

What it asserts, in two boots over one world:

  case A, a pack whose area is widened and whose multi-buildings exceed 10
  * an 11x2 and a 2x11 both get a row, so the ceiling is gone in each dimension
    independently rather than only for square footprints
  * every row that existed before the import kept its exact coordinates, which
    is the invariant the append-only design exists to hold
  * both really pasted as blocks, and only their own
  * the world record lists the footprints in the order they were registered
  * a footprint past the sanity ceiling is refused with a warning and gets no row
  * an export carries the footprints back and widens `areasize` to fit them

  case B, the same world booted again with no import
  * the registered rows come back at the same coordinates, which is what makes
    the order worth persisting

The world is wiped before case A and the jar removed afterwards, so the rig's
baseline stays what the wiki's published results were produced on.
"""
import io
import json
import os
import re
import shutil
import sys

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from rcon import Rcon  # noqa: E402
import rig  # noqa: E402
from rig import fail, failures  # noqa: E402

SERVER = rig.SERVER
JAR = rig.jar()
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
SETTINGS = os.path.join(WORLD, "lostcitiesdevtool", "plots")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")

NS = "mbig"
WIDE = (11, 2)
TALL = (2, 11)
# Past `Catalogue.MAX_MULTI`, which is 64. A pack does not ship one of these; a
# typo in dimx does.
TOOBIG = (65, 1)
WIDE_BLOCK = "minecraft:gold_block"
TALL_BLOCK = "minecraft:emerald_block"
COLUMN_BOTTOM = -64
COLUMN_TOP = -40


def ok(msg):
    print("  ok   " + msg)


def stop(proc):
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("stop")
    except Exception:
        proc.kill()
    proc.wait(timeout=120)


def registry():
    return json.load(io.open(PLOTS, encoding="utf-8"))


def coords():
    """Plot id -> where it is, for comparing one build against the next."""
    return {p["id"]: (p["chunkX"], p["chunkZ"]) for p in registry()["plots"]}


def strip_json5(text):
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif text[i] == '"':
            out.append(text[i])
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    out.append(text[i])
                    i += 1
                out.append(text[i])
                i += 1
            if i < n:
                out.append(text[i])
                i += 1
        else:
            out.append(text[i])
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def settings_of(plot_id):
    path = os.path.join(SETTINGS, *plot_id.split("/")) + ".json5"
    if not os.path.isfile(path):
        return None
    return json.loads(strip_json5(io.open(path, encoding="utf-8").read()))


def solid(ch):
    return [[ch * 16 for _ in range(16)] for _ in range(6)]


def grid(name, w, h):
    """`buildings[x][z]`, the shape Lost Cities' own multi-buildings use.

    Every cell names the same building. The footprint is what is under test, and
    132 distinct cell buildings would only make the fixture slower to paste.
    """
    return [[NS + ":" + name for _ in range(h)] for _ in range(w)]


def write_pack(root):
    data = os.path.join(root, "data", NS, "lostcities")
    assets = {
        "worldstyles/main": {
            "outsidestyle": NS + ":outside",
            # Widened, the way a pack shipping these has to widen it. A footprint
            # wider than its placement area throws during generation.
            "multisettings": {"areasize": 16, "minimum": 1, "maximum": 5,
                              "correctstylefactor": 0.9, "attempts": 100},
            "citystyles": [{"factor": 1.0, "citystyle": NS + ":city"}],
        },
        "citystyles/city": {
            "style": NS + ":main",
            "streetblocks": {"border": "y", "wall": "w", "street": "S",
                             "streetbase": "b", "streetvariant": "B",
                             "width": 8},
            "selectors": {
                "multibuildings": [
                    {"factor": 1.0, "value": NS + ":wide"},
                    {"factor": 1.0, "value": NS + ":tall"},
                    {"factor": 1.0, "value": NS + ":toobig"},
                ],
            },
        },
        "styles/main": {"randompalettes": [[{"factor": 1.0,
                                             "palette": NS + ":main"}]]},
        "styles/outside": {"randompalettes": [[{"factor": 1.0,
                                                "palette": NS + ":main"}]]},
        "palettes/main": {"palette": [
            {"char": "g", "block": WIDE_BLOCK},
            {"char": "e", "block": TALL_BLOCK},
            {"char": "y", "block": "minecraft:stone"},
            {"char": "w", "block": "minecraft:stone"},
            {"char": "S", "block": "minecraft:stone"},
            {"char": "b", "block": "minecraft:stone"},
            {"char": "B", "block": "minecraft:stone"},
        ]},
        "multibuildings/wide": {"dimx": WIDE[0], "dimz": WIDE[1],
                                "buildings": grid("wcell", *WIDE)},
        "multibuildings/tall": {"dimx": TALL[0], "dimz": TALL[1],
                                "buildings": grid("tcell", *TALL)},
        "multibuildings/toobig": {"dimx": TOOBIG[0], "dimz": TOOBIG[1],
                                  "buildings": grid("wcell", *TOOBIG)},
        "buildings/wcell": {"refpalette": NS + ":main", "filler": "g",
                            "minfloors": 0, "maxfloors": 0, "mincellars": 0,
                            "maxcellars": 0,
                            "parts": [{"part": NS + ":pw", "ground": True,
                                       "top": True}]},
        "buildings/tcell": {"refpalette": NS + ":main", "filler": "e",
                            "minfloors": 0, "maxfloors": 0, "mincellars": 0,
                            "maxcellars": 0,
                            "parts": [{"part": NS + ":pt", "ground": True,
                                       "top": True}]},
        "parts/pw": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                     "slices": solid("g")},
        "parts/pt": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                     "slices": solid("e")},
    }
    for name, body in assets.items():
        path = os.path.join(data, *name.split("/")) + ".json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write(
            json.dumps(body, indent=2) + "\n")
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "multibuilding"}}))


def blocks_at(con, plot, block):
    """How many of one block stand on a plot's first chunk.

    One chunk rather than the whole footprint: an 11 by 2 plot is 22 chunks and a
    clone over all of it passes the 32768 `/clone` refuses, which counts nothing
    rather than erroring and reads as a building that never pasted.
    """
    x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
    con.command("execute in %s run forceload add %d %d %d %d"
                % (WORKSHOP, x, z, x + 15, z + 15))
    con.command("execute in %s run forceload add 3990 3990 4031 4031" % WORKSHOP)
    reply = con.command("execute in %s run clone %d %d %d %d %d %d 4000 %d 4000 "
                        "filtered %s"
                        % (WORKSHOP, x, COLUMN_BOTTOM, z, x + 15, COLUMN_TOP,
                           z + 15, COLUMN_BOTTOM, block))
    found = re.search(r"([0-9]+) block", reply)
    if not found:
        print("    clone gave: %s" % reply.strip()[:160])
    return int(found.group(1)) if found else 0


def row_id(size):
    return "multibuilding/%dx%d" % size


# =============================================================== case A
print("check-multibuilding-size: footprints past the generated catalogue")
print("jar: %s" % os.path.basename(JAR))

for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
rig.install(SERVER, JAR)
write_pack(os.path.join(WORLD, "datapacks", "mbigpack"))
print("fresh world, jar installed, a pack with an 11x2, a 2x11 and a 65x1\n")

proc, _ = rig.boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        before = coords()
        print("rows laid out before the import: %d plots" % len(before))

        print("\n" + "=" * 72)
        output = con.command("lcdev import %s:main" % NS)
        print(output.rstrip()[-900:])
        print("=" * 72)

        after = coords()

        # The invariant. Every plot that existed before has to be where it was.
        moved = [pid for pid, xz in before.items()
                 if pid in after and after[pid] != xz]
        lost = [pid for pid in before if pid not in after]
        print("\nplots before %d, after %d, moved %d, lost %d"
              % (len(before), len(after), len(moved), len(lost)))
        if moved:
            fail("%d plots moved, so anything built on them is stranded: %s"
                 % (len(moved), moved[:5]))
        else:
            ok("no plot that existed before the import moved")
        if lost:
            fail("%d plots vanished: %s" % (len(lost), lost[:5]))
        else:
            ok("no plot that existed before the import vanished")

        # The rows themselves.
        rows_now = {p.get("row") for p in registry()["plots"]}
        for size in (WIDE, TALL):
            if row_id(size) in rows_now:
                ok("%s got a row" % row_id(size))
            else:
                fail("%s has no row, so a %dx%d was dropped"
                     % (row_id(size), size[0], size[1]))
        if row_id(TOOBIG) in rows_now:
            fail("%s got a row, but it is past the sanity ceiling"
                 % row_id(TOOBIG))
        else:
            ok("%s is refused rather than laid out" % row_id(TOOBIG))
        if "65x1" in output or "past the" in output:
            ok("the import says the oversized footprint was left out")
        else:
            fail("the import said nothing about the 65x1 being dropped")

        # Registration order, which is what makes the bands reproducible.
        extra = registry().get("extraRows")
        print("extraRows: %s" % extra)
        if extra == [row_id(WIDE), row_id(TALL)]:
            ok("the world record lists both footprints in registration order")
        else:
            fail("extraRows is %r, not %r"
                 % (extra, [row_id(WIDE), row_id(TALL)]))

        # And the blocks.
        plots = {p["id"]: p for p in registry()["plots"]}
        for size, block, other in ((WIDE, WIDE_BLOCK, TALL_BLOCK),
                                   (TALL, TALL_BLOCK, WIDE_BLOCK)):
            pid = row_id(size) + "/0"
            if pid not in plots:
                fail("%s has a row but no plot" % row_id(size))
                continue
            mine = blocks_at(con, plots[pid], block)
            theirs = blocks_at(con, plots[pid], other)
            print("  %s: %d of %s, %d of %s" % (pid, mine, block, theirs, other))
            if mine < 500:
                fail("only %d of %s on %s, so it did not paste"
                     % (mine, block, pid))
            elif theirs > 0:
                fail("%s also holds %d of %s" % (pid, theirs, other))
            else:
                ok("%s pasted, and only its own blocks" % row_id(size))

        # The export has to carry the footprint back out again.
        print("\n" + "-" * 72)
        print(con.command("lcdev export mbigout -f").rstrip()[-500:])
        root = os.path.join(EXPORTS, "mbigout")
        ns = (settings_of("core") or {}).get("namespace", "mypack")
        data = os.path.join(root, "data", ns, "lostcities")
        got = {}
        multidir = os.path.join(data, "multibuildings")
        if os.path.isdir(multidir):
            for f in os.listdir(multidir):
                d = json.load(io.open(os.path.join(multidir, f),
                                      encoding="utf-8"))
                got[f] = (d.get("dimx"), d.get("dimz"))
        print("  exported multibuildings: %s" % got)
        for size in (WIDE, TALL):
            if size in got.values():
                ok("a %dx%d was exported at its own size" % size)
            else:
                fail("no exported multibuilding is %dx%d" % size)
        wpath = os.path.join(data, "worldstyles", "main.json")
        if os.path.isfile(wpath):
            world = json.load(io.open(wpath, encoding="utf-8"))
            area = (world.get("multisettings") or {}).get("areasize")
            print("  exported areasize: %s" % area)
            if area and area >= max(WIDE[0], TALL[1]):
                ok("the export widened the placement area to fit")
            else:
                fail("exported areasize is %r, too small for the footprints "
                     "beside it, so generation would throw" % area)
        else:
            fail("no world style was exported")
finally:
    stop(proc)

# =============================================================== case B
print("\n" + "=" * 72)
print("case B: the same world again, to prove the bands are reproducible")
print("=" * 72)
was = coords()
proc, _ = rig.boot()
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        now = coords()
        drifted = [pid for pid, xz in was.items()
                   if pid in now and now[pid] != xz]
        missing = [pid for pid in was if pid not in now]
        print("  plots %d -> %d, drifted %d, missing %d"
              % (len(was), len(now), len(drifted), len(missing)))
        if drifted:
            fail("%d plots moved across a restart: %s"
                 % (len(drifted), drifted[:5]))
        elif missing:
            fail("%d plots did not come back: %s"
                 % (len(missing), missing[:5]))
        else:
            ok("every plot came back at the same coordinates")
        for size in (WIDE, TALL):
            if row_id(size) + "/0" in now:
                ok("%s survived the restart" % row_id(size))
            else:
                fail("%s was not restored, so its plots are orphaned"
                     % row_id(size))
finally:
    stop(proc)

# =============================================================== case C
print("\n" + "=" * 72)
print("case C: extraRows naming a row the catalogue already has")
print("=" * 72)
# Registering never writes one, but the registry is a file somebody may edit, and
# a generated id read back as an extra row was a second row under one id with a
# band of its own.
doc = registry()
doc["extraRows"] = list(doc.get("extraRows") or []) + ["multibuilding/2x2"]
io.open(PLOTS, "w", encoding="utf-8", newline="\n").write(json.dumps(doc, indent=2))
was = coords()
proc, _ = rig.boot()
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        extra = registry().get("extraRows") or []
        drifted = [pid for pid, xz in coords().items()
                   if pid in was and was[pid] != xz]
        print("  extraRows after a build: %s, plots drifted: %d"
              % (extra, len(drifted)))
        if "multibuilding/2x2" in extra:
            fail("a generated row named in extraRows was kept as a second row "
                 "under the same id")
        elif drifted:
            fail("%d plots moved when the duplicate was dropped" % len(drifted))
        else:
            ok("the duplicate was dropped and nothing moved")
finally:
    stop(proc)

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("PASS")
