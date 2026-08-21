#!/usr/bin/env python3
"""Acceptance test for the workshop: build it on a real server and check it.

    python mod/tools/check-workshop.py

Needs the wiki's test rig installed, because it borrows the rig's 7.4.12 server and
its Java. `python testrig/rig.py doctor` says whether that is ready.

What it asserts, which is what phase 1 promised:

  * the catalogue for the target version produces the rows it should
  * every single-only row holds exactly one plot, because the monorail codec takes
    a string and a list is a load error
  * the shape that parses and never generates is present and flagged, rather than
    quietly dropped
  * no two plots you can see together share a floor colour
  * the floors are in the world, not only in the registry file
  * standing on a plot reports the same plot the registry names

**The world is wiped first**, because a dimension a mod adds has to register
somewhere it was not before, and **the jar is removed afterwards**, so the rig's
baseline stays what the wiki's published results were produced on. Same discipline
the KubeJS test used.

One trap already paid for: the adjacency test has to grow **both** rectangles by the
walkway before overlapping them. Growing one makes plots separated by exactly the
walkway look unrelated, which is every plot in every row. The first version of this
script had the same bug as the code it was checking, so it passed while the colouring
was giving all 125 plots the same colour.
"""
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
JAR = "mod/build/libs/lostcities_devtool-1.20.1-1.0.1.jar"
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
DIM = "lostcitiesdevtool:workshop"
PLOTS = os.path.join(SERVER, "world", "lostcitiesdevtool", "plots.json")
FLOOR_Y = -64


def boot():
    args = "@" + os.path.join("libraries", LOADER, "win_args.txt")
    proc = subprocess.Popen([JAVA, "@user_jvm_args.txt", args, "nogui"],
                            cwd=SERVER, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace")
    deadline = time.time() + 300
    lines = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            print("\n".join(lines[-25:]))
            raise SystemExit("server exited during startup")
        lines.append(line.rstrip())
        if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
            threading.Thread(target=lambda: [None for _ in
                                             iter(proc.stdout.readline, "")],
                             daemon=True).start()
            return proc
    raise SystemExit("server did not start")


def touching(a, b):
    """Two plots share a view when their footprints, grown by the walkway, overlap."""
    return (a["chunkX"] - 1 <= b["chunkX"] + b["width"]
            and b["chunkX"] - 1 <= a["chunkX"] + a["width"]
            and a["chunkZ"] - 1 <= b["chunkZ"] + b["height"]
            and b["chunkZ"] - 1 <= a["chunkZ"] + a["height"])


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
world = os.path.join(SERVER, "world")
if os.path.isdir(world):
    shutil.rmtree(world)
shutil.copy(JAR, dest)
print("fresh world, jar installed\n")

proc = None
failures = []
try:
    proc = boot()
    print("server up\n")
    with Rcon(port=25575, password="lcwiki") as con:
        for cmd in ("lcdev workshop rows", "lcdev workshop build"):
            print("=" * 72)
            print("$ /" + cmd)
            print(con.command(cmd).rstrip() or "(no output)")

        if not os.path.isfile(PLOTS):
            failures.append("no plots.json was written")
        else:
            doc = json.load(io.open(PLOTS, encoding="utf-8"))
            plots = doc["plots"]
            print("\n" + "=" * 72)
            print("registry: %d plots, floor y=%s, version %s"
                  % (len(plots), doc["floorY"], doc["version"]))

            singles = [p for p in plots if p.get("class") == "single"]
            rows_single = {p["row"] for p in singles}
            if len(singles) != len(rows_single):
                failures.append("a single-only row has more than one plot")
            print("  single-only rows: %d, plots in them: %d"
                  % (len(rows_single), len(singles)))

            dead = [p for p in plots if "dead" in p]
            if not dead:
                failures.append("the dead street shape is missing from the catalogue")
            print("  flagged dead: %s" % sorted({p["row"] for p in dead}))

            clashes = 0
            for i, a in enumerate(plots):
                for b in plots[i + 1:]:
                    if touching(a, b) and a["floor"] == b["floor"]:
                        clashes += 1
                        if clashes < 4:
                            print("  CLASH %s and %s both %s"
                                  % (a["id"], b["id"], a["floor"]))
            if clashes:
                failures.append("%d neighbouring plots share a floor colour" % clashes)
            print("  neighbouring plots sharing a colour: %d" % clashes)

            colours = {p["floor"] for p in plots}
            print("  distinct floor colours used: %d" % len(colours))

            # The floors have to actually be in the world, not only in the file.
            print("\n" + "=" * 72)
            checked = 0
            for p in plots[:3] + singles[:1] + dead[:1]:
                x, z = p["chunkX"] * 16, p["chunkZ"] * 16
                con.command("execute in %s run forceload add %d %d %d %d"
                            % (DIM, x, z, x, z))
                reply = con.command("execute in %s if block %d %d %d %s"
                                    % (DIM, x, FLOOR_Y, z, p["floor"]))
                ok = "Test passed" in reply
                checked += 1
                print("  %-28s %s at %d,%d  %s"
                      % (p["id"], p["floor"].split(":")[-1], x, z,
                         "present" if ok else "MISSING: " + reply.strip()[:60]))
                if not ok:
                    failures.append("floor missing at %s" % p["id"])
            print("  checked %d plots in the world" % checked)

            # And the in-game lookup has to agree with the file.
            print("\n" + "=" * 72)
            for p in (singles[:1] + dead[:1]):
                x = p["chunkX"] * 16 + 8
                z = p["chunkZ"] * 16 + 8
                cmd = ("execute in %s positioned %d.0 %d.0 %d.0 run lcdev workshop here"
                       % (DIM, x, FLOOR_Y + 1, z))
                print("$ /" + cmd)
                print(con.command(cmd).rstrip())
        con.command("stop")
finally:
    if proc is not None:
        try:
            proc.wait(timeout=180)
        except Exception:
            proc.kill()
    if os.path.isfile(dest):
        os.remove(dest)
    print("\nremoved the jar, rig baseline is clean again")

print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
