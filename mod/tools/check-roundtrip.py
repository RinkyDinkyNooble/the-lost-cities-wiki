#!/usr/bin/env python3
"""The round trip gate: the two halves have to agree, or one of them is wrong.

    python mod/tools/check-roundtrip.py

Needs the wiki's test rig, the same way the other three checks do.

Two claims, and neither of them is provable by reading the code, because the
exporter and the importer were written from the same understanding and a check
written from that understanding inherits its mistakes.

**A pack survives being opened.** Build a workshop, export it, install what was
written as a datapack, import it back into an empty workshop, and export again. The
second export must be **byte for byte the first**. Anything the importer drops, or
reads differently from the way the exporter wrote it, shows up here as a diff.

**A world survives being compiled.** The blocks in each plot before the export must
be the blocks in each plot after the import, position for position, compared in the
world by `execute if blocks` rather than by anything this script believes about the
format.

The fixture is chosen for the things that have gone wrong before: a building with
two roof alternatives of different heights, a building with a cellar so the filler
has to resolve, a multibuilding whose two chunks are made of different wood so a
transpose or a shared setting cannot hide, a street part, and a highway part that
belongs to the world style rather than to a city style.

The world is wiped first and the jar removed afterwards, so the rig's baseline stays
what the wiki's published results were produced on.
"""
import difflib
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
JAR = "mod/build/libs/lostcities_devtool-1.20.1-1.0.1.jar"
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

# As tall as anything the fixture builds, plus room to prove nothing was left above.
TALL = 24

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def boot():
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
            print("\n".join(tail[-20:]))
            raise SystemExit("server exited during startup")
        tail.append(line.rstrip())
        if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
            threading.Thread(target=lambda: [None for _ in
                                             iter(proc.stdout.readline, "")],
                             daemon=True).start()
            return proc
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
    """Every file under a directory, by path relative to it."""
    out = {}
    for base, _, files in os.walk(root):
        for f in files:
            path = os.path.join(base, f)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            out[rel] = io.open(path, "rb").read()
    return out


# The fixture. Each entry: plot id, and the fills and settings that make it.
FIXTURE = [
    ("building/1x1/0", [
        (0, 5, "minecraft:gold_block"),
        (6, 11, "minecraft:diamond_block"),
        (12, 14, "minecraft:emerald_block"),
        (15, 18, "minecraft:iron_block"),
    ], ["name tower", "floors 1", "cellars 0", "tops 3,4",
        "citystyles mycity", "factor 1.0"]),
    ("building/1x1/1", [
        (0, 5, "minecraft:cobblestone"),
        (6, 11, "minecraft:bricks"),
    ], ["name cellartower", "floors 0", "cellars 1",
        "citystyles mycity", "factor 2.5"]),
    ("street/all/0", [
        (0, 0, "minecraft:stone_bricks"),
    ], ["name road_all", "height 6", "citystyles mycity"]),
    ("highway/open/0", [
        (0, 1, "minecraft:andesite"),
    ], ["name hiway", "height 6"]),
]

# The multibuilding is filled a chunk at a time, so a transposed grid or a setting
# shared where it should not be shows up as the wrong wood in the wrong chunk.
MULTI = ("multibuilding/2x1/0",
         [(0, "minecraft:oak_planks"), (1, "minecraft:spruce_planks")],
         ["name twin", "floors 0", "cellars 0", "citystyles mycity", "factor 1.0"])

ALL_PLOTS = [f[0] for f in FIXTURE] + [MULTI[0]]

# Where each plot's blocks are stashed before the import, laid out along x with room
# between them. All inside one forceloaded box.
SCRATCH_Z = 4000
SCRATCH = {plot: (4000 + i * 40, SCRATCH_Z) for i, plot in enumerate(ALL_PLOTS)}
SCRATCH_BOX = (3984, 3984, 4192, 4032)


# ----------------------------------------------------------- half one, the build

dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
shutil.copy(JAR, dest)
print("fresh world, jar installed\n")

proc = boot()
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

        def load(plot_id):
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x + p["width"] * 16 - 1,
                           z + p["height"] * 16 - 1))

        # The pack's own settings. `inherit none` is the one that matters here: a
        # city style that inherits citystyle_common accumulates the mod's own
        # buildings on top of the workshop's, so a pack exported that way opens
        # again as a much larger pack than it was written from.
        for cmd in ("lcdev plot set namespace " + NS,
                    "lcdev plot set worldStyle main",
                    "lcdev plot set inherit none",
                    "lcdev plot set packName Round trip"):
            run("core", cmd)

        for plot_id, fills, settings in FIXTURE:
            load(plot_id)
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            for lo, hi, block in fills:
                con.command("execute in %s run fill %d %d %d %d %d %d %s"
                            % (WORKSHOP, x, BASE + lo, z, x + 15, BASE + hi,
                               z + 15, block))
            for cmd in settings:
                run(plot_id, "lcdev plot set " + cmd)

        load(MULTI[0])
        p = by_id[MULTI[0]]
        for dx, block in MULTI[1]:
            x, z = p["chunkX"] * 16 + dx * 16, p["chunkZ"] * 16
            con.command("execute in %s run fill %d %d %d %d %d %d %s"
                        % (WORKSHOP, x, BASE, z, x + 15, BASE + 5, z + 15, block))
        for cmd in MULTI[2]:
            run(MULTI[0], "lcdev plot set " + cmd)

        print("=" * 72)
        print(con.command("lcdev export " + PACK).rstrip())
        con.command("stop")
finally:
    stop(proc)

first = os.path.join(EXPORTS, PACK)
if not os.path.isdir(first):
    print("\nnothing was exported, so there is nothing to round trip")
    raise SystemExit(1)

stash = tempfile.mkdtemp(prefix="lcdev-roundtrip-")
shutil.copytree(first, os.path.join(stash, PACK))
before = tree(os.path.join(stash, PACK))
print("\n" + "=" * 72)
print("the first export")
print("  files: %d, bytes: %d" % (len(before), sum(len(v) for v in before.values())))
pal = json.loads(before["data/%s/lostcities/palettes/main.json" % NS])
chars = [e["char"] for e in pal["palette"]]
print("  palette: %d entries, characters %s"
      % (len(chars), "".join(chars).replace(" ", "_")))
if chars != sorted(chars):
    fail("the palette is not written in character order, so two exports of the "
         "same workshop can differ over nothing")

city = json.loads(before["data/%s/lostcities/citystyles/mycity.json" % NS])
print("  city style inherits: %s" % city.get("inherit", "nothing"))
if "inherit" in city:
    fail("the city style still inherits, so importing it will pull in the mod's "
         "own catalogue as well")

tower = json.loads(before["data/%s/lostcities/buildings/tower.json" % NS])
roofs = [r for r in tower["parts"] if r.get("top") is True]
print("  roof alternatives on tower: %d" % len(roofs))
if len(roofs) != 2:
    fail("the fixture's two roofs did not both reach the building")

# --------------------------------------------------- half two, open it again

packs = os.path.join(WORLD, "datapacks", "rtpack")
os.makedirs(packs)
shutil.copytree(os.path.join(first, "data"), os.path.join(packs, "data"))
shutil.copy(os.path.join(first, "pack.mcmeta"), packs)
shutil.rmtree(first)
# The plot settings, the registry and the palette ledger all go, so the import
# starts from an empty catalogue rather than from what it is about to replace.
shutil.rmtree(DEVTOOL)
print("\ninstalled the export as a datapack, emptied the workshop's own records")

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        by_id = read_plots()
        con.command("execute in %s run forceload add %d %d %d %d"
                    % ((WORKSHOP,) + SCRATCH_BOX))

        # Stash what is standing, then empty the plots. The comparison afterwards is
        # against the stash, so it tests the blocks the import placed rather than
        # anything left over from the build.
        for plot_id in ALL_PLOTS:
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            x2, z2 = x + p["width"] * 16 - 1, z + p["height"] * 16 - 1
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x2, z2))
            sx, sz = SCRATCH[plot_id]
            con.command("execute in %s run clone %d %d %d %d %d %d %d %d %d"
                        % (WORKSHOP, x, BASE, z, x2, BASE + TALL - 1, z2,
                           sx, BASE, sz))
            con.command("execute in %s run fill %d %d %d %d %d %d minecraft:air"
                        % (WORKSHOP, x, BASE, z, x2, BASE + TALL - 1, z2))

        print("=" * 72)
        print(con.command('lcdev import "%s:main"' % NS).rstrip())

        print("\n" + "=" * 72)
        print("the blocks in each plot, against what was there before")
        for plot_id in ALL_PLOTS:
            p = by_id[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            x2, z2 = x + p["width"] * 16 - 1, z + p["height"] * 16 - 1
            sx, sz = SCRATCH[plot_id]
            reply = con.command(
                "execute in %s if blocks %d %d %d %d %d %d %d %d %d all"
                % (WORKSHOP, x, BASE, z, x2, BASE + TALL - 1, z2, sx, BASE, sz))
            text = reply.strip()
            volume = (x2 - x + 1) * (z2 - z + 1) * TALL
            lower = text.lower()
            if "passed" in lower:
                print("  %-24s all %d blocks match" % (plot_id, volume))
                continue
            if "failed" not in lower and "match" not in lower:
                # An answer nothing recognises is not a pass. Say what came back
                # rather than reading silence as agreement.
                fail("%s: could not tell from the reply %r whether the blocks match"
                     % (plot_id, text))
                continue
            print("  %-24s DIFFERENT: %s" % (plot_id, text))
            fail("%s does not hold the blocks it held before the export" % plot_id)
            # Narrow it to a layer, so the report says where rather than only that.
            for y in range(TALL):
                layer = con.command(
                    "execute in %s if blocks %d %d %d %d %d %d %d %d %d all"
                    % (WORKSHOP, x, BASE + y, z, x2, BASE + y, z2,
                       sx, BASE + y, sz))
                if "passed" not in layer.lower():
                    print("      first difference at y %d, %d above the floor"
                          % (BASE + y, y))
                    break

        print("\n" + "=" * 72)
        print(con.command("lcdev export " + PACK).rstrip())
        con.command("stop")
finally:
    stop(proc)

# ------------------------------------------------------------- the two exports

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
        fail("%d file(s) the first export wrote are gone: %s"
             % (len(only_before), ", ".join(only_before[:5])))
    if only_after:
        fail("%d file(s) appeared that were not in the first export: %s"
             % (len(only_after), ", ".join(only_after[:5])))

    differ = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    print("  files with the same name and different contents: %d" % len(differ))
    if differ:
        fail("%d file(s) came back different: %s"
             % (len(differ), ", ".join(differ[:5])))
        for rel in differ[:2]:
            a = before[rel].decode("utf-8", "replace").splitlines()
            b = after[rel].decode("utf-8", "replace").splitlines()
            print("\n  --- %s" % rel)
            for line in list(difflib.unified_diff(a, b, "first", "second",
                                                  lineterm="", n=1))[:24]:
                print("    " + line)

shutil.rmtree(stash, ignore_errors=True)
if os.path.isfile(dest):
    os.remove(dest)
print("\nremoved the jar, rig baseline is clean again")
print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
