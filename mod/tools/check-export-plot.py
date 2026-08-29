#!/usr/bin/env python3
"""Exporting one plot writes that plot, and nothing that claims to be a world.

    python mod/tools/check-export-plot.py

Needs the wiki's test rig, the same way the other server checks do.

`/lcdev export <name> plot` compiles the plot you are standing on and leaves the
rest of the workshop out. It is for lifting one building out of a workshop to drop
into a pack, which means two things have to hold at once and neither is enough on
its own:

  * the plot you stood on is in the pack, with the palette its characters resolve
    through, or the fragment is unusable
  * the plot you did not stand on is absent, or it is not a fragment at all

And a third that is a judgement rather than a mechanism: a fragment writes **no
city style and no world style**. A pack carrying a world style is installable, and
installing a one building world style generates a world made of that building. What
somebody exporting a single plot wants is files to copy, not a world.

The flags are built into a tree rather than typed out, so the orderings are worth
exercising: `plot -f` and `-f plot` have to reach the same place.
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


def files_in(export):
    """Every asset path the pack wrote, as `kind/name`."""
    root = os.path.join(EXPORTS, export, "data")
    out = []
    for path in glob.glob(os.path.join(root, "*", "lostcities", "**", "*.json*"),
                          recursive=True):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        out.append("/".join(rel.split("/")[2:]))
    return sorted(out)


for path in (WORLD, EXPORTS, BACKUPS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
print("fresh world, jar installed: %s\n" % os.path.basename(JAR))

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}

        # Two buildings, different blocks, so the pack says which one it holds
        # rather than only how many.
        mine = plots["building/1x1/0"]
        theirs = plots["building/1x1/1"]
        for p, block in ((mine, "minecraft:gold_block"),
                         (theirs, "minecraft:iron_block")):
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            con.command("execute in %s run forceload add %d %d %d %d"
                        % (WORKSHOP, x, z, x + 15, z + 15))
            for f in range(2):
                y = BASE + f * STRIDE
                con.command("execute in %s run fill %d %d %d %d %d %d %s hollow"
                            % (WORKSHOP, x, y, z, x + 15, y + STRIDE - 1, z + 15,
                               block))
        for p, name in ((mine, "mine"), (theirs, "theirs")):
            con.command("execute in %s positioned %d 10 %d run lcdev plot set name "
                        "%s" % (WORKSHOP, p["chunkX"] * 16 + 8,
                                p["chunkZ"] * 16 + 8, name))
            con.command("execute in %s positioned %d 10 %d run lcdev plot set floors "
                        "1" % (WORKSHOP, p["chunkX"] * 16 + 8, p["chunkZ"] * 16 + 8))
            # Named so the whole export actually writes a city style. Without this
            # the fragment having none proves nothing, because neither would.
            con.command("execute in %s positioned %d 10 %d run lcdev plot set "
                        "citystyles mycity" % (WORKSHOP, p["chunkX"] * 16 + 8,
                                               p["chunkZ"] * 16 + 8))

        print("=" * 72)
        print("the whole workshop, for comparison")
        con.command("lcdev export whole")
        whole = files_in("whole")
        print("  files: %d" % len(whole))
        print("  kinds: %s" % sorted({f.split("/")[0] for f in whole}))
        if not any(f.startswith("buildings/mine") for f in whole):
            fail("the whole export is missing the plot this check is about")
        # Every kind the fragment must not have, the whole export must have, or
        # the assertions below pass for the wrong reason.
        for kind in ("worldstyles", "citystyles", "styles"):
            if not any(f.startswith(kind + "/") for f in whole):
                fail("the whole export wrote no %s, so the fragment lacking one "
                     "proves nothing" % kind)

        print("\n" + "=" * 72)
        print("one plot, standing on it")
        x, z = mine["chunkX"] * 16 + 8, mine["chunkZ"] * 16 + 8
        said = con.command("execute in %s positioned %d 10 %d run lcdev export one "
                           "plot" % (WORKSHOP, x, z)).rstrip()
        print(said[-260:])
        one = files_in("one")
        print("\n  files: %d" % len(one))
        for f in one:
            print("      " + f)

        if not any(f.startswith("buildings/mine") for f in one):
            fail("the plot that was stood on is not in the fragment")
        if any(f.startswith("buildings/theirs") for f in one):
            fail("the neighbouring plot is in the fragment, so `plot` exported "
                 "more than the one plot")
        if not any(f.startswith("palettes/") for f in one):
            fail("no palette, so the fragment's characters resolve to nothing")
        for kind in ("worldstyles", "citystyles", "styles"):
            if any(f.startswith(kind + "/") for f in one):
                fail("the fragment wrote a %s, which makes it installable as a "
                     "world of one building" % kind)

        print("\n" + "=" * 72)
        print("the flags reach the same place in either order")
        con.command("execute in %s positioned %d 10 %d run lcdev export ord1 plot -f"
                    % (WORKSHOP, x, z))
        con.command("execute in %s positioned %d 10 %d run lcdev export ord2 -f plot"
                    % (WORKSHOP, x, z))
        a, b = files_in("ord1"), files_in("ord2")
        print("  plot -f: %d files, -f plot: %d files" % (len(a), len(b)))
        if a != b or a != one:
            fail("the two orderings did not produce the same fragment")

        print("\n" + "=" * 72)
        print("standing nowhere is refused rather than exporting everything")
        said = con.command("execute in %s positioned 3000 10 3000 run lcdev export "
                           "nope plot" % WORKSHOP).rstrip()
        print("  " + said.replace("\n", " ")[:140])
        if os.path.isdir(os.path.join(EXPORTS, "nope")):
            fail("`plot` off a plot wrote a pack anyway, which would be the whole "
                 "workshop under a name that says one plot")
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
print("one plot exports as a fragment: its own assets, its palette, no world")
print("all checks passed")
