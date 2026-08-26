#!/usr/bin/env python3
"""A settings file written outside the game reaches the pack.

    python mod/tools/check-sync.py

Needs the wiki's test rig, the same way the other server checks do.

Two halves, and the first is a premise worth proving rather than assuming.

**Values need no syncing.** Every command loads a plot's settings off disk when it
is asked, so a number changed in an editor is already what the next export
compiles. If that were not true, `sync` would be a cache refresh and would have to
run before everything. The first case here writes a file behind the server's back
and exports without syncing, which is the only way to know.

**What does need syncing is whether the plot exists at all.** A settings file names
a plot, a plot belongs to a row, and a row lays out a fixed number of plots. Write
`building/1x1/20.json5` into a row holding eight and nothing is wrong with the
file: it describes a plot the catalogue does not lay out, so every command walking
the catalogue steps past it and the export writes a pack without it, silently. That
is what `sync` looks for, by walking the files rather than the plots.

It also reads each file for keys the plot has no use for, because a mistyped key is
ignored everywhere else: `floor` where `floors` was meant gives a one storey
building and no complaint from anything.
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
SETTINGS = os.path.join(WORLD, "lostcitiesdevtool", "plots")
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


def write_settings(plot_id, body):
    path = os.path.join(SETTINGS, *plot_id.split("/")) + ".json5"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(body, indent=2) + "\n")


def names_in(export):
    """The building assets a pack holds, by file name."""
    out = []
    for path in glob.glob(os.path.join(EXPORTS, export, "data", "*", "lostcities",
                                       "buildings", "*.json*")):
        out.append(os.path.basename(path).split(".")[0])
    return sorted(out)


def plot_count(row):
    doc = json.load(io.open(PLOTS, encoding="utf-8"))
    return sum(1 for p in doc["plots"] if p["id"].startswith(row + "/"))


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
        before = plot_count("building/1x1")
        print("plots the 1x1 building row lays out: %d" % before)

        near = plots["building/1x1/0"]
        x, z = near["chunkX"] * 16, near["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))
        con.command("execute in %s run fill %d %d %d %d %d %d "
                    "minecraft:gold_block hollow"
                    % (WORKSHOP, x, BASE, z, x + 15, BASE + STRIDE - 1, z + 15))

        print("\n" + "=" * 72)
        print("1. a file written behind the server's back is read without syncing")
        write_settings("building/1x1/0", {"name": "edited", "floors": 0})
        con.command("lcdev export v1")
        got = names_in("v1")
        print("  buildings in the pack: %s" % got)
        if "edited" not in got:
            fail("a settings file written outside the game was not picked up, so "
                 "values do need syncing and sync has to run before everything")

        print("\n" + "=" * 72)
        print("2. a file for a plot the catalogue does not lay out")
        far = "building/1x1/%d" % (before + 12)
        write_settings(far, {"name": "faraway", "floors": 0})
        con.command("lcdev export v2")
        got = names_in("v2")
        print("  wrote %s.json5" % far)
        print("  buildings in the pack: %s" % got)
        # Not a bug in itself: the plot does not exist, so nothing walks it. The
        # bug would be nothing ever saying so, which is what sync is for.
        if "faraway" in got:
            fail("a plot beyond the row's length was exported without growing the "
                 "row, so this check is not testing what it claims")

        print("\n" + "=" * 72)
        print("3. sync finds it, says so, and grows the row")
        said = con.command("lcdev workshop sync").rstrip()
        print(said[-400:])
        after = plot_count("building/1x1")
        print("\n  plots the row lays out now: %d (was %d)" % (after, before))
        if after <= before:
            fail("sync did not grow the row, so the file still describes a plot "
                 "that does not exist")
        if after < before + 13:
            fail("the row grew to %d, which does not reach the plot the file names"
                 % after)

        con.command("lcdev export v3")
        got = names_in("v3")
        print("  buildings in the pack after syncing: %s" % got)
        if "faraway" not in got:
            fail("the plot is laid out and still not in the pack")
        if "edited" not in got:
            fail("growing the row lost the plot that was already there")

        print("\n" + "=" * 72)
        print("4. a mistyped key is reported rather than ignored")
        # `floor` is not a key any plot has. Everything else in the mod steps over
        # it in silence, which is how a one storey building happens by accident.
        write_settings("building/1x1/1", {"name": "typo", "floor": 3})
        said = con.command("lcdev workshop sync").rstrip()
        print("  " + said.replace("\n", " ")[-200:])
        if "floor" not in said:
            fail("sync said nothing about a key no plot uses")

        print("\n" + "=" * 72)
        print("5. a file naming no row at all")
        write_settings("nosuchrow/0", {"name": "orphan"})
        said = con.command("lcdev workshop sync").rstrip()
        print("  " + said.replace("\n", " ")[-200:])
        if "nosuchrow" not in said:
            fail("sync said nothing about a file naming a row the catalogue "
                 "does not have")

        print("\n" + "=" * 72)
        print("6. with nothing to do, sync says so and changes nothing")
        os.remove(os.path.join(SETTINGS, "nosuchrow", "0.json5"))
        write_settings("building/1x1/1", {"name": "typo", "floors": 3})
        steady = plot_count("building/1x1")
        said = con.command("lcdev workshop sync").rstrip()
        print("  " + said.replace("\n", " ")[-180:])
        if plot_count("building/1x1") != steady:
            fail("a sync with nothing to do changed the layout anyway")
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
print("files edited outside the game are read, and sync lays out the plots they "
      "name")
print("all checks passed")
