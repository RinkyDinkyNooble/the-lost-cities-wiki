#!/usr/bin/env python3
"""Acceptance test for the import: paste the mod's own pack into the workshop.

    python mod/tools/check-import.py

Needs the wiki's test rig, the same way the other two checks do.

Lost Cities ships a complete pack of its own, which makes it the fairest thing to
import: nobody wrote it for this tool, it uses inheritance, weighted selectors, part
lists, conditions and palettes that reference variants, and it is much larger than
the catalogue's default row sizes. If it comes through, a pack somebody wrote by
hand will.

What it asserts:

  * the world style is found and walked
  * rows grew to hold what the pack has, and a single-only row did not
  * plots that were filled have settings that name the asset and its city style
  * blocks really landed on a plot, not just settings files
  * the settings an import wrote are enough to export again, which is the round
    trip the whole feature rests on

The world is wiped first and the jar removed afterwards, so the rig's baseline stays
what the wiki's published results were produced on.
"""
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from rcon import Rcon  # noqa: E402
import rig  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
# Whichever jar the build produced. Naming it in full meant every version
# bump silently broke all four checks at once.
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
SETTINGS = os.path.join(WORLD, "lostcitiesdevtool", "plots")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
BASE = -63
FLOOR_Y = -64

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


for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
print("fresh world, jar installed\n")

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        print("=" * 72)
        print(con.command("lcdev import lostcities:standard").rstrip())

        plots = json.load(io.open(PLOTS, encoding="utf-8"))["plots"]
        by_id = {p["id"]: p for p in plots}
        grown = json.load(io.open(PLOTS, encoding="utf-8")).get("grownRows", {})

        print("\n" + "=" * 72)
        print("what the import made")
        print("  plots in the catalogue now: %d" % len(plots))
        print("  rows grown: %d" % len(grown))
        if not grown:
            fail("no row grew, so the pack fitted the defaults exactly, "
                 "which the mod's own pack does not")

        # A monorail row must not grow: the codec takes a string there.
        bad_single = {k: v for k, v in grown.items() if k.startswith("monorail/")}
        print("  single-only rows grown: %s" % (bad_single or "none"))
        if bad_single:
            fail("a single-only row grew: %s" % bad_single)

        written = []
        for root, _, files in os.walk(SETTINGS):
            for f in files:
                if f.endswith(".json5"):
                    rel = os.path.relpath(os.path.join(root, f), SETTINGS)
                    written.append(rel[:-len(".json5")].replace(os.sep, "/"))
        print("  plots with settings: %d" % len(written))
        if len(written) < 10:
            fail("only %d plots got settings, which is too few for that pack"
                 % len(written))

        # A building plot should name its asset, its city style and its floors.
        sample = next((p for p in written if p.startswith("building/1x1/")), None)
        if sample is None:
            fail("no building plot was filled")
        else:
            got = settings_of(sample)
            ok = (got.get("name") and got.get("citystyles")
                  and "floors" in got and "cellars" in got)
            print("  %-28s %s" % (sample, json.dumps(got)[:70]))
            if not ok:
                fail("%s did not get the settings an export needs" % sample)

        # And blocks have to have landed, not only settings.
        if sample:
            p = by_id[sample]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x + 15, z + 15))
            con.command("execute in %s run forceload add 4000 4000 4031 4031"
                        % WORKSHOP)
            reply = con.command(
                "execute in %s run clone %d %d %d %d %d %d 4000 %d 4000 filtered "
                "minecraft:air" % (WORKSHOP, x, BASE, z, x + 15, BASE + 30,
                                   z + 15, BASE))
            m = re.search(r"([0-9]+) block", reply)
            air = int(m.group(1)) if m else -1
            volume = 16 * 16 * 31
            placed = volume - air if air >= 0 else -1
            print("  solid blocks on %s: %d of %d" % (sample, placed, volume))
            # A building from the mod's own pack is walls and floors, so it is
            # thousands of blocks. A handful means the characters resolved to
            # nothing and the plot pasted as air, which a "greater than zero"
            # check waves through: the first run of this scored 12.
            if placed < 500:
                fail("only %d solid blocks pasted, so the palette did not resolve"
                     % placed)

        # Every plot the import filled has to have a floor under it. A row that
        # grew past its catalogue size is laid out by the same build that paints
        # the floors, so a building standing on bare bedrock means the two went
        # out of step.
        print("\n" + "=" * 72)
        print("floors under the plots the import filled")
        missing = []
        for rel in sorted(written):
            p = by_id.get(rel)
            if p is None:
                continue
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x + p["width"] * 16 - 1,
                           z + p["height"] * 16 - 1))
            reply = con.command("execute in %s if block %d %d %d minecraft:air"
                                % (WORKSHOP, x, FLOOR_Y, z))
            if "passed" in reply.lower():
                missing.append(rel)
        print("  plots checked: %d" % len(written))
        print("  plots with no floor: %d" % len(missing))
        for m in missing[:6]:
            print("      " + m)
        if missing:
            fail("%d filled plot(s) have no floor painted under them"
                 % len(missing))

        # The round trip that matters: what the import wrote must export again.
        print("\n" + "=" * 72)
        print(con.command("lcdev plot set namespace roundtrip"
                          if False else "lcdev export roundtrip").rstrip())
        con.command("stop")
finally:
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()

out = os.path.join(EXPORTS, "roundtrip")
if not os.path.isdir(out):
    fail("the imported pack did not export again")
else:
    counts = {}
    for folder in ("parts", "buildings", "palettes", "citystyles", "worldstyles",
                   "multibuildings"):
        d = os.path.join(out, "data", "mypack", "lostcities", folder)
        counts[folder] = len(os.listdir(d)) if os.path.isdir(d) else 0
    print("  exported again: %s" % counts)
    if counts["parts"] == 0 or counts["buildings"] == 0:
        fail("the re-export produced no parts or no buildings")

    # A condition key has to keep its own type. `top` is a boolean, and writing 0
    # there produces a building that reads as valid JSON and will not load.
    bad_types = []
    bdir = os.path.join(out, "data", "mypack", "lostcities", "buildings")
    for f in sorted(os.listdir(bdir)):
        b = json.load(io.open(os.path.join(bdir, f), encoding="utf-8"))
        for ref in b.get("parts", []):
            for key in ("top", "ground", "cellar", "isbuilding", "issphere"):
                if key in ref and not isinstance(ref[key], bool):
                    bad_types.append("%s: %s is %r" % (f, key, ref[key]))
    print("  condition keys with the wrong type: %d" % len(bad_types))
    for b in bad_types[:3]:
        print("      " + b)
    if bad_types:
        fail("%d condition keys were written with the wrong type" % len(bad_types))

    multi = os.path.join(out, "data", "mypack", "lostcities", "multibuildings")
    if os.path.isdir(multi) and os.listdir(multi):
        m = json.load(io.open(os.path.join(multi, sorted(os.listdir(multi))[0]),
                              encoding="utf-8"))
        grid = m.get("buildings")
        # buildings[x][z]: nested, outer list is X. A flat list loads and comes out
        # transposed, which is the trap the wiki documents.
        nested = (isinstance(grid, list) and grid
                  and all(isinstance(col, list) for col in grid)
                  and len(grid) == m.get("dimx"))
        print("  multibuilding grid is buildings[x][z]: %s" % ("yes" if nested
                                                               else "NO"))
        if not nested:
            fail("the multibuilding grid is not nested x by z")

if os.path.isfile(dest):
    os.remove(dest)
print("\nremoved the jar, rig baseline is clean again")
print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
