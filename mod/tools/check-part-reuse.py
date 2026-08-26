#!/usr/bin/env python3
"""A building whose floors are the same is one part used many times.

    python mod/tools/check-part-reuse.py

Needs the wiki's test rig, the same way the other server checks do.

Reported against 1.3.0: importing a building puts the same part on several floors,
which looks like redundancy. Half of that is right and half of it is not.

Showing the same part on several levels is **correct** and has to stay. The export
reads blocks per level, so a level nobody pasted cannot be read back, and a workshop
that showed one floor for a nine floor building would export a one floor building.

Writing a file per level is **not** correct. A nine floor building whose floors match
produced nine identical part files, which is redundancy in a pack somebody ships.
Levels that drew the same blocks now share one file.

Two properties, and the second is the one that could bite:

  * an identical floor is written once and referenced from every level that used it
  * the parts list still has one entry per level, so the building still has the
    number of floors it had

The second is what keeps the round trip safe, and check-roundtrip.py is what proves
the round trip itself. Sharing a part must not shorten the parts list: where the
profile decides a building's floor count, that list is a bag the generator draws
from, and a shorter bag is a different building.

Deduplication is scoped to one building. Two different buildings that happen to
match keep their own copies, because a pack where one building's levels point into
another is harder to read and to edit by hand.
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

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
BACKUPS = os.path.join(SERVER, "config", "lostcitiesdevtool", "backups")
BASE = -63
STRIDE = 6
FLOORS = 5

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


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (WORLD, EXPORTS, BACKUPS):
    if os.path.isdir(path):
        shutil.rmtree(path)
shutil.copy(JAR, dest)
print("fresh world, jar installed: %s\n" % os.path.basename(JAR))

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}

        # Two buildings. The first has identical floors, the second has one floor
        # deliberately different, so the check can tell "collapsed everything" from
        # "collapsed what actually matched".
        same = plots["building/1x1/0"]
        mixed = plots["building/1x1/1"]
        for p in (same, mixed):
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x + 15, z + 15))

        print("=" * 72)
        print("building/1x1/0: %d identical floors" % (FLOORS + 1))
        x, z = same["chunkX"] * 16, same["chunkZ"] * 16
        for f in range(FLOORS + 1):
            y = BASE + f * STRIDE
            con.command("execute in %s run fill %d %d %d %d %d %d "
                        "minecraft:gold_block hollow"
                        % (WORKSHOP, x, y, z, x + 15, y + STRIDE - 1, z + 15))

        print("building/1x1/1: the same, with floor 2 in iron instead")
        x2, z2 = mixed["chunkX"] * 16, mixed["chunkZ"] * 16
        for f in range(FLOORS + 1):
            y = BASE + f * STRIDE
            block = "minecraft:iron_block" if f == 2 else "minecraft:gold_block"
            con.command("execute in %s run fill %d %d %d %d %d %d %s hollow"
                        % (WORKSHOP, x2, y, z2, x2 + 15, y + STRIDE - 1, z2 + 15,
                           block))

        # `plot set` works on the plot the caller stands in, so every one of these
        # has to be positioned. Without that they land on whatever plot the command
        # source is at, which over RCON is 0,0 and therefore the core settings.
        for pid, p in (("building/1x1/0", same), ("building/1x1/1", mixed)):
            con.command("execute in %s positioned %d 10 %d run lcdev plot set floors "
                        "%d" % (WORKSHOP, p["chunkX"] * 16 + 8,
                                p["chunkZ"] * 16 + 8, FLOORS))
            con.command("execute in %s positioned %d 10 %d run lcdev plot set name "
                        "%s" % (WORKSHOP, p["chunkX"] * 16 + 8,
                                p["chunkZ"] * 16 + 8,
                                "flat" if pid.endswith("0") else "mixed"))

        print("\n" + "=" * 72)
        said = con.command("lcdev export reuse").rstrip()
        print(said[-500:])

        root = os.path.join(EXPORTS, "reuse")
        parts = glob.glob(os.path.join(root, "data", "*", "lostcities", "parts",
                                       "*.json*"))
        names = sorted(os.path.basename(p) for p in parts)
        flat = [n for n in names if n.startswith("flat_")]
        mixedp = [n for n in names if n.startswith("mixed_")]
        print("\n  part files for the all-identical building: %d %s"
              % (len(flat), flat))
        print("  part files for the one-odd-floor building:  %d %s"
              % (len(mixedp), mixedp))

        # Six levels of identical blocks is one file. Printing the names rather
        # than only the count, because "1" could also mean the export wrote
        # nothing and the building is empty.
        if len(flat) != 1:
            fail("%d part files for a building whose %d levels are identical, "
                 "expected 1" % (len(flat), FLOORS + 1))
        if len(mixedp) != 2:
            fail("%d part files for a building with one level different, "
                 "expected 2" % len(mixedp))

        building = glob.glob(os.path.join(root, "data", "*", "lostcities",
                                          "buildings", "flat.json*"))
        if not building:
            fail("no building file was written for the all-identical building")
        else:
            body = json.loads(io.open(building[0], encoding="utf-8").read())
            refs = body.get("parts", [])
            print("\n  levels in the building's parts list: %d" % len(refs))
            print("  distinct parts they name: %d"
                  % len({r.get("part") for r in refs}))
            # The saving must not cost the building its floors.
            if len(refs) != FLOORS + 1:
                fail("the parts list has %d entries for a %d level building, so "
                     "collapsing the files changed the building's shape"
                     % (len(refs), FLOORS + 1))
            if len({r.get("part") for r in refs}) != 1:
                fail("the levels do not all name the one part that was written")

finally:
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("stop")
    except Exception:
        proc.kill()
    proc.wait(timeout=120)

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("identical levels share one part file and the building keeps "
      "its floors")
print("all checks passed")
