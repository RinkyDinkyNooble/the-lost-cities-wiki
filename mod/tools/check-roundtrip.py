#!/usr/bin/env python3
"""The round trip gate: the two halves have to agree, or one of them is wrong.

    python mod/tools/check-roundtrip.py

Needs the wiki's test rig, the same way the other three checks do.

Two claims, and neither is provable by reading the code, because the exporter and
the importer were written from the same understanding and a check written from that
understanding inherits its mistakes.

**A pack survives being opened.** Build a workshop, export it, install what was
written as a datapack, import it back into an empty workshop, and export again. The
second export must be **byte for byte the first**. Anything the importer drops, or
reads differently from the way the exporter wrote it, shows up here as a diff.

**A world survives being compiled.** The blocks in each plot before the export must
be the blocks in each plot after the import, position for position, compared in the
world by `execute if blocks` rather than by anything this script believes about the
format.

The fixture covers every row class, both orientations of a multibuilding that is
not square, block states with properties, a building that pins no floor count, one
with two cellars, one with two roofs, the weighted fields, the skip flag, two city
styles sharing a building, both non-default palette placements, the json5 output
format, the raw escape hatch, and two plots asking for the same asset name. Each of
those is here because it went red once.

The pack is installed as a datapack for the second boot, so a pack that would not
load fails here loudly rather than quietly: the world style goes missing and the
import has nothing to walk.

The world is wiped first and the jar removed afterwards, so the rig's baseline stays
what the wiki's published results were produced on.
"""
import difflib
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from rcon import Rcon  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
# Whichever jar the build produced. Naming it in full meant every version
# bump silently broke all four checks at once.
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
DEVTOOL = os.path.join(WORLD, "lostcitiesdevtool")
PLOTS = os.path.join(DEVTOOL, "plots.json")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
PACK = "rt"
NS = "mypack"
BASE = -63

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def boot():
    """Boot, and hand back the startup log as well as the process.

    The log is half the oracle: Lost Cities checks every asset when datapacks
    load, and the DevTool prints what it finds. A pack that loads with errors is
    a pack the exporter should not have written.
    """
    args = "@" + os.path.join("libraries", LOADER, "win_args.txt")
    proc = subprocess.Popen([JAVA, "@user_jvm_args.txt", args, "nogui"],
                            cwd=SERVER, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace")
    deadline = time.time() + 300
    tail = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            print("\n".join(tail[-25:]))
            raise SystemExit("server exited during startup")
        tail.append(line.rstrip())
        if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
            threading.Thread(target=lambda: [None for _ in
                                             iter(proc.stdout.readline, "")],
                             daemon=True).start()
            return proc, tail
    raise SystemExit("server did not start")


def stop(proc):
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()


def read_plots():
    return {p["id"]: p for p in
            json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}


def tree(root):
    out = {}
    for base, _, files in os.walk(root):
        for f in files:
            path = os.path.join(base, f)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            out[rel] = io.open(path, "rb").read()
    return out


# Each case: plot id, how tall to compare, the per-chunk fills, and the settings.
# A fill is (dx, dz, low, high, block) measured from the plot's own corner.
CASES = [
    # Two roofs of different heights, stacked above a floor.
    ("building/1x1/0", 24, [
        (0, 0, 0, 5, "minecraft:gold_block"),
        (0, 0, 6, 11, "minecraft:diamond_block"),
        (0, 0, 12, 14, "minecraft:emerald_block"),
        (0, 0, 15, 18, "minecraft:iron_block"),
    ], ["name tower", "floors 1", "cellars 0", "tops 3,4",
        "citystyles mycity,othercity", "factor 1.0"]),

    # Two cellars, so the filler skirt and the negative levels both have to work.
    ("building/1x1/1", 24, [
        (0, 0, 0, 5, "minecraft:cobblestone"),
        (0, 0, 6, 11, "minecraft:andesite"),
        (0, 0, 12, 17, "minecraft:bricks"),
    ], ["name cellars2", "floors 0", "cellars 2",
        "citystyles mycity", "factor 2.5", "palette building"]),

    # No pinned floor count: the parts become a bag the generator draws from.
    # It needs a roof. Unpinned bodies are all conditioned `top: false`, so with
    # no top variation the topmost level of every height matches nothing, which
    # is how the mod's own buildings are written too: nine bodies, five roofs.
    ("building/1x1/2", 24, [
        (0, 0, 0, 5, "minecraft:oak_planks"),
        (0, 0, 6, 11, "minecraft:birch_planks"),
        (0, 0, 12, 17, "minecraft:spruce_planks"),
        (0, 0, 18, 21, "minecraft:dark_oak_planks"),
    ], ["name bagbuilding", "floors 2", "cellars 0", "pinFloors false",
        "tops 4", "citystyles mycity", "factor 1.0"]),

    # Block states with properties. What the exporter writes as text is what the
    # importer has to parse back, property for property. Also a roof one block
    # tall, which is below the two a part needs to draw anything.
    ("building/1x1/3", 24, [
        (0, 0, 0, 1, "minecraft:oak_stairs[facing=east,half=top]"),
        (0, 0, 2, 3, "minecraft:oak_slab[type=top]"),
        (0, 0, 4, 4, "minecraft:oak_log[axis=x]"),
        (0, 0, 5, 5, "minecraft:oak_fence"),
        (0, 0, 6, 7, "minecraft:dark_prismarine"),
    ], ["name propshouse", "floors 0", "cellars 0", "tops 1",
        "citystyles mycity", "factor 1.0"]),

    # One chunk wide, two deep. Not square, so a transposed grid cannot hide.
    ("multibuilding/1x2/0", 12, [
        (0, 0, 0, 5, "minecraft:oak_planks"),
        (0, 1, 0, 5, "minecraft:spruce_planks"),
    ], ["name tall_ns", "floors 0", "cellars 0",
        "citystyles mycity", "factor 1.0"]),

    # Two wide, three deep, every chunk a different block: the strongest test of
    # buildings[x][z] there is.
    ("multibuilding/2x3/0", 12, [
        (0, 0, 0, 5, "minecraft:white_wool"),
        (0, 1, 0, 5, "minecraft:orange_wool"),
        (0, 2, 0, 5, "minecraft:magenta_wool"),
        (1, 0, 0, 5, "minecraft:light_blue_wool"),
        (1, 1, 0, 5, "minecraft:yellow_wool"),
        (1, 2, 0, 5, "minecraft:lime_wool"),
    ], ["name big", "floors 0", "cellars 0",
        "citystyles mycity", "factor 1.0"]),

    # A part list on a city style.
    ("street/all/0", 12, [
        (0, 0, 0, 0, "minecraft:stone_bricks"),
    ], ["name road_all", "height 6", "citystyles mycity"]),

    # A part list on the world style.
    ("highway/open/0", 12, [
        (0, 0, 0, 1, "minecraft:andesite"),
    ], ["name hiway", "height 6"]),

    ("railway/railsflat/0", 12, [
        (0, 0, 0, 0, "minecraft:polished_andesite"),
    ], ["name rails", "height 6"]),

    # The single-string kind. A list here is a load error, not a bigger row.
    ("monorail/both/0", 12, [
        (0, 0, 0, 1, "minecraft:quartz_block"),
    ], ["name mono", "height 6"]),

    # An object selector with every weighted field set.
    ("selector/parks/0", 12, [
        (0, 0, 0, 0, "minecraft:grass_block"),
    ], ["name park1", "height 6", "citystyles othercity", "factor 0.5",
        "minSpawnDistance 100", "maxSpawnDistance 5000", "feather 20"]),

    ("selector/fountains/0", 12, [
        (0, 0, 0, 2, "minecraft:prismarine"),
    ], ["name fount", "height 6", "citystyles mycity", "factor 0.25"]),

    # `palette part` is one of three documented placements: this part should carry
    # its own palette rather than reach for the pack's shared one.
    ("selector/bridges/0", 12, [
        (0, 0, 0, 2, "minecraft:deepslate_bricks"),
    ], ["name span", "height 6", "citystyles mycity", "factor 1.0",
        "palette part"]),
]

# Built and configured, but not block-compared: each one is here for what the
# export makes of it rather than for what comes back.
BUILD_ONLY = [
    # Marked skip, so nothing of it should reach the pack.
    ("selector/stairs/0", [
        (0, 0, 0, 0, "minecraft:netherrack"),
    ], ["name skipme", "height 6", "citystyles mycity", "skip true"]),
    # The same asset name as street/all/0. Two plots cannot both be one file.
    ("street/all/1", [
        (0, 0, 0, 0, "minecraft:sandstone"),
    ], ["name road_all", "height 6", "citystyles mycity"]),
]

# Written into a plot's settings by hand, because the schema does not know it and
# `plot set` will not take it. SettingsStore tells the reader it is "merged into
# the output verbatim", so the exported asset has to carry it.
RAW_PLOT = "selector/fountains/0"
RAW_VALUE = '{"scattered": "mypack:probe", "stuff": 7}'

# Scratch cells, five to a row, wide enough for the widest plot and deep enough
# for the deepest, all inside one forceloaded box.
SCRATCH = {case[0]: (4000 + (i % 5) * 48, 4000 + (i // 5) * 64)
           for i, case in enumerate(CASES)}
SCRATCH_BOX = (4000, 4000, 4224, 4224)


# ----------------------------------------------------------- half one, the build

dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
shutil.copy(JAR, dest)
print("fresh world, jar installed\n")

proc, _ = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        by_id = read_plots()

        def run(plot_id, command):
            p = by_id[plot_id]
            return con.command(
                "execute in %s positioned %d.0 %d.0 %d.0 run %s"
                % (WORKSHOP, p["chunkX"] * 16 + 8, BASE, p["chunkZ"] * 16 + 8,
                   command))

        def build(plot_id, fills, settings):
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x + p["width"] * 16 - 1,
                           z + p["height"] * 16 - 1))
            for dx, dz, lo, hi, block in fills:
                cx, cz = x + dx * 16, z + dz * 16
                reply = con.command(
                    "execute in %s run fill %d %d %d %d %d %d %s"
                    % (WORKSHOP, cx, BASE + lo, cz, cx + 15, BASE + hi,
                       cz + 15, block))
                if "Filled" not in reply and "filled" not in reply.lower():
                    fail("%s: fill of %s said %r" % (plot_id, block,
                                                     reply.strip()[:70]))
            for cmd in settings:
                reply = run(plot_id, "lcdev plot set " + cmd)
                if "error" in reply.lower() or "unknown" in reply.lower():
                    fail("%s: `plot set %s` said %r"
                         % (plot_id, cmd, reply.strip()[:80]))

        for cmd in ("lcdev plot set namespace " + NS,
                    "lcdev plot set worldStyle main",
                    "lcdev plot set inherit none",
                    "lcdev plot set format json5",
                    "lcdev plot set packName Round trip"):
            run("core", cmd)

        for plot_id, _, fills, settings in CASES:
            build(plot_id, fills, settings)
        for plot_id, fills, settings in BUILD_ONLY:
            build(plot_id, fills, settings)

        # The escape hatch, written straight into the file the way somebody
        # reaching for it would have to.
        raw_file = os.path.join(DEVTOOL, "plots", *RAW_PLOT.split("/")) + ".json5"
        text = io.open(raw_file, encoding="utf-8").read().rstrip()
        io.open(raw_file, "w", encoding="utf-8", newline="\n").write(
            text[:-1] + '\n  "raw": %s,\n}\n' % RAW_VALUE)

        # Two plots asked for one file. The export has to refuse and name both,
        # because the alternative is a pack quietly one asset short.
        print("=" * 72)
        clash = con.command("lcdev export " + PACK).rstrip()
        print(clash)
        named_both = "street/all/1" in clash and "street/all/0" in clash
        print("  the clash was refused and both plots named: %s"
              % ("yes" if named_both else "NO"))
        if not named_both:
            fail("two plots share an asset name and the export did not refuse and "
                 "name both, so one of them was silently thrown away")

        run("street/all/1", "lcdev plot set name road_alt")
        print("=" * 72)
        export_said = con.command("lcdev export " + PACK).rstrip()
        print(export_said)
        con.command("stop")
finally:
    stop(proc)

first = os.path.join(EXPORTS, PACK)
if not os.path.isdir(first):
    print("\nnothing was exported, so there is nothing to round trip")
    raise SystemExit(1)

stash = tempfile.mkdtemp(prefix="lcdev-wide-")
shutil.copytree(first, os.path.join(stash, PACK))
before = tree(os.path.join(stash, PACK))


def asset(files, kind, name):
    """One asset out of an export, whichever extension it was written under.

    This check sets `format json5` on purpose, so the files it reads back really
    can be json5. That works today only because the exporter's json5 output is
    still plain JSON content with a different extension; the moment it emits a
    comment or a trailing comma, a bare json.loads here would die.
    """
    for ext in (".json", ".json5"):
        key = "data/%s/lostcities/%s/%s%s" % (NS, kind, name, ext)
        if key in files:
            try:
                return json.loads(files[key])
            except ValueError:
                raise SystemExit("%s could not be parsed as JSON. If the exporter "
                                 "now writes real json5, this check needs a json5 "
                                 "reader rather than a tolerant one" % key)
    return None


print("\n" + "=" * 72)
print("what the first export wrote")
print("  files: %d, bytes: %d" % (len(before), sum(len(v) for v in before.values())))
print("  parts: %d, buildings: %d, multibuildings: %d"
      % (sum(1 for k in before if "/parts/" in k),
         sum(1 for k in before if "/buildings/" in k),
         sum(1 for k in before if "/multibuildings/" in k)))

world = asset(before, "worldstyles", "main")
print("  world style keys: %s" % sorted((world or {}).keys()))

# A monorail key takes a plain string. A list there is a load error, and the pack
# that carries one will not come back in the second half.
mono = ((world or {}).get("parts", {}).get("monorails", {}) or {}).get("both")
print("  worldstyle.parts.monorails.both = %r" % (mono,))
if mono is not None and not isinstance(mono, str):
    fail("the monorail key was written as %s, and its codec takes a plain string"
         % type(mono).__name__)

if asset(before, "parts", "skipme") is not None:
    fail("a plot marked skip was exported anyway")

raised = re.search(r"is set to 1 and was read as 2", export_said or "")
print("  export said it raised the one-block roof: %s" % ("yes" if raised else "no"))
if not raised:
    fail("a roof below the minimum was raised without saying so")

# The extension the assets were asked to be written under.
exts = {k.rsplit(".", 1)[-1] for k in before if "/lostcities/" in k}
print("  asset extensions: %s" % sorted(exts))
if exts != {"json5"}:
    fail("`format json5` did nothing: the assets were written as %s" % sorted(exts))

# The escape hatch, which the settings file tells its reader is merged verbatim.
fount = asset(before, "parts", "fount")
print("  raw keys reached the asset: %s"
      % sorted(k for k in (fount or {}) if k in ("scattered", "stuff")))
if fount is not None and "scattered" not in fount:
    fail("`raw` was not merged into the output, though the settings file says it is")

# Where each plot asked its palette to go.
span = asset(before, "parts", "span")
if span is not None:
    own = "palette" in span
    print("  `palette part` gave span its own palette: %s" % own)
    if not own:
        fail("`palette part` did nothing: the part still points at the shared "
             "palette")
cellars2 = asset(before, "buildings", "cellars2")
if cellars2 is not None:
    own = "palette" in cellars2
    print("  `palette building` gave cellars2 its own palette: %s" % own)
    if not own:
        fail("`palette building` did nothing: the building still points at the "
             "shared palette")

for name, want in (("tower", 2), ("propshouse", 1)):
    b = asset(before, "buildings", name)
    if b is None:
        fail("no building named %s was written" % name)
        continue
    roofs = [r for r in b.get("parts", []) if r.get("top") is True]
    if len(roofs) != want:
        fail("%s has %d roof alternatives, expected %d"
             % (name, len(roofs), want))

bag = asset(before, "buildings", "bagbuilding")
if bag is not None:
    pinned = "maxfloors" in bag
    print("  bagbuilding pins a floor count: %s" % pinned)
    if pinned:
        fail("pinFloors false still wrote a floor count")

big = asset(before, "multibuildings", "big")
if big is not None:
    grid = big.get("buildings")
    ok = (isinstance(grid, list) and len(grid) == big.get("dimx")
          and all(isinstance(c, list) and len(c) == big.get("dimz")
                  for c in grid))
    print("  big is %sx%s, grid %s"
          % (big.get("dimx"), big.get("dimz"),
             "x by z" if ok else "WRONG SHAPE"))
    if not ok:
        fail("the 2x3 multibuilding grid is not dimx lists of dimz")

# --------------------------------------------------- half two, open it again

packs = os.path.join(WORLD, "datapacks", "rtpack")
os.makedirs(packs)
shutil.copytree(os.path.join(first, "data"), os.path.join(packs, "data"))
shutil.copy(os.path.join(first, "pack.mcmeta"), packs)
shutil.rmtree(first)
shutil.rmtree(DEVTOOL)
print("\ninstalled the export as a datapack, emptied the workshop's own records")

proc, log = boot()
print("server up\n")

# What the game said while loading the pack. Only complaints about the pack this
# export wrote count: Lost Cities ships a palette carrying a 1.12 block id with an
# @meta suffix, which has never been valid here and is not this tool's to fix.
complaints = [ln for ln in log
              if re.search(r"error|fail|could not|invalid|exception", ln, re.I)]
ours = [ln for ln in complaints if NS in ln or "rtpack" in ln]
theirs = [ln for ln in complaints
          if ln not in ours and re.search(r"lostcities", ln, re.I)]
print("  complaints about the exported pack: %d" % len(ours))
for ln in ours[:8]:
    print("      " + ln.strip()[-160:])
print("  complaints about the mod's own shipped assets: %d (not ours)" % len(theirs))
for ln in theirs[:3]:
    print("      " + ln.strip()[-160:])
if ours:
    fail("the exported pack did not load cleanly")

try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        by_id = read_plots()
        con.command("execute in %s run forceload add %d %d %d %d"
                    % ((WORKSHOP,) + SCRATCH_BOX))

        for plot_id, tall, _, _ in CASES:
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            x2, z2 = x + p["width"] * 16 - 1, z + p["height"] * 16 - 1
            sx, sz = SCRATCH[plot_id]
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x2, z2))
            con.command("execute in %s run clone %d %d %d %d %d %d %d %d %d"
                        % (WORKSHOP, x, BASE, z, x2, BASE + tall - 1, z2,
                           sx, BASE, sz))
            con.command("execute in %s run fill %d %d %d %d %d %d minecraft:air"
                        % (WORKSHOP, x, BASE, z, x2, BASE + tall - 1, z2))

        print("=" * 72)
        reply = con.command('lcdev import %s:main' % NS).rstrip()
        print(reply)
        if "no world style" in reply.lower():
            fail("the exported pack's world style did not load, so the pack the "
                 "exporter wrote is not a pack the mod can read")

        print("\n" + "=" * 72)
        print("the blocks in each plot, against what was there before")
        for plot_id, tall, _, _ in CASES:
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            x2, z2 = x + p["width"] * 16 - 1, z + p["height"] * 16 - 1
            sx, sz = SCRATCH[plot_id]
            text = con.command(
                "execute in %s if blocks %d %d %d %d %d %d %d %d %d all"
                % (WORKSHOP, x, BASE, z, x2, BASE + tall - 1, z2,
                   sx, BASE, sz)).strip()
            volume = (x2 - x + 1) * (z2 - z + 1) * tall
            lower = text.lower()
            if "passed" in lower:
                print("  %-24s all %6d blocks match" % (plot_id, volume))
                continue
            if "failed" not in lower and "match" not in lower:
                fail("%s: could not tell from %r whether the blocks match"
                     % (plot_id, text))
                continue
            print("  %-24s DIFFERENT: %s" % (plot_id, text))
            fail("%s does not hold the blocks it held before the export"
                 % plot_id)
            for y in range(tall):
                layer = con.command(
                    "execute in %s if blocks %d %d %d %d %d %d %d %d %d all"
                    % (WORKSHOP, x, BASE + y, z, x2, BASE + y, z2,
                       sx, BASE + y, sz))
                if "passed" not in layer.lower():
                    print("      first difference %d blocks above the floor" % y)
                    break

        # The settings an import writes are what the next export reads, so a value
        # that changes on the way through changes the pack the next time round even
        # when this time's files matched.
        prop_file = os.path.join(DEVTOOL, "plots", "building", "1x1", "3.json5")
        if os.path.isfile(prop_file):
            body = io.open(prop_file, encoding="utf-8").read()
            got = re.search(r'"tops":\s*(\[[^\]]*\])', body)
            print("\n  propshouse was built with tops [1], raised to %s"
                  % (got.group(1) if got else "nothing"))
            if got and got.group(1) != "[2]":
                fail("a roof set to 1 should be raised to the 2 a part needs to "
                     "draw anything, and came back as %s" % got.group(1))

        print("\n" + "=" * 72)
        print(con.command("lcdev export " + PACK).rstrip())
        con.command("stop")
finally:
    stop(proc)

print("\n" + "=" * 72)
print("the second export, against the first")
if not os.path.isdir(first):
    fail("the imported pack did not export again")
else:
    after = tree(first)
    print("  files: %d, bytes: %d"
          % (len(after), sum(len(v) for v in after.values())))
    only_before = sorted(set(before) - set(after))
    only_after = sorted(set(after) - set(before))
    if only_before:
        fail("%d file(s) lost: %s" % (len(only_before), ", ".join(only_before)))
    if only_after:
        fail("%d file(s) appeared: %s" % (len(only_after), ", ".join(only_after)))
    differ = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    print("  files with the same name and different contents: %d" % len(differ))
    if differ:
        fail("%d file(s) came back different: %s"
             % (len(differ), ", ".join(differ[:6])))
        for rel in differ[:4]:
            a = before[rel].decode("utf-8", "replace").splitlines()
            b = after[rel].decode("utf-8", "replace").splitlines()
            print("\n  --- %s" % rel)
            for line in list(difflib.unified_diff(a, b, "first", "second",
                                                  lineterm="", n=1))[:20]:
                print("    " + line)

shutil.rmtree(stash, ignore_errors=True)
if os.path.isfile(dest):
    os.remove(dest)
print("\nremoved the jar, rig baseline is clean again")
print("\n" + ("FAILURES (%d):\n  " % len(failures)) + "\n  ".join(failures)
      if failures else "\nall checks passed")
