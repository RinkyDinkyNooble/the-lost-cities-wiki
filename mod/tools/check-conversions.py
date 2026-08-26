#!/usr/bin/env python3
"""A placeholder block becomes a different block per plot, per chunk, per level.

    python mod/tools/check-conversions.py

Needs the wiki's test rig, the same way the other server checks do.

`conversions` turns a block placed in the workshop into a different block in the
pack. It is how somebody builds with wool where the real asset wants a command
block: placing the command block would fire it, so a placeholder stands in and the
export swaps it.

Pack-wide already worked. What did not, and what this checks:

  * a plot's table overrides the pack's, rather than the pack's winning
  * a chunk's and a level's table override the plot's, and a chunk's own level is
    narrower still
  * a narrower scope adds to the wider one rather than replacing it whole, so a
    chunk wanting one more mapping does not have to restate the plot's

The last is the one worth stating plainly. `Settings.resolve` replaces a value
outright, which is right for `floors: 3` and wrong for a table, and conversions had
been going through it.

Everything here reads out of the written pack rather than out of the mod's own
report, because the pack is what somebody ships.
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
    """Straight to the file, because chunks and levels have no command."""
    path = os.path.join(SETTINGS, *plot_id.split("/")) + ".json5"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(body, indent=2) + "\n")


def blocks_in(export):
    """Every block id any palette entry in the pack names."""
    out = set()
    for path in glob.glob(os.path.join(EXPORTS, export, "data", "*", "lostcities",
                                       "**", "*.json*"), recursive=True):
        text = io.open(path, encoding="utf-8").read()
        try:
            body = json.loads(text)
        except ValueError:
            raise SystemExit("%s is not plain JSON, which this check assumes"
                             % os.path.relpath(path))
        palette = body.get("palette")
        if isinstance(palette, dict):
            palette = palette.get("palette")
        if isinstance(palette, list):
            for e in palette:
                if isinstance(e, dict) and isinstance(e.get("block"), str):
                    out.add(e["block"])
    return out


def expect(export, want, unwanted, what):
    got = blocks_in(export)
    print("  %-42s %s" % (what, sorted(b.split(":")[-1] for b in got)))
    for b in want:
        if b not in got:
            fail("%s: %s is not in the pack" % (what, b))
    for b in unwanted:
        if b in got:
            fail("%s: %s reached the pack and should not have" % (what, b))


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
        p = plots["building/1x1/0"]
        x, z = p["chunkX"] * 16, p["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))

        # Three levels, all white wool. Which block each becomes is entirely the
        # conversion table's doing, so any difference between them is scope.
        print("=" * 72)
        print("a three level building, every level the same placeholder")
        for f in range(3):
            y = BASE + f * STRIDE
            con.command("execute in %s run fill %d %d %d %d %d %d "
                        "minecraft:white_wool" % (WORKSHOP, x, y, z, x + 15, y, z + 15))

        base = {"name": "tower", "floors": 2, "cellars": 0}

        print("\n" + "=" * 72)
        print("1. the pack's table applies where nothing says otherwise")
        con.command("execute in %s positioned %d 10 %d run lcdev plot set name tower"
                    % (WORKSHOP, x + 8, z + 8))
        con.command("execute in %s positioned %d 10 %d run lcdev plot set floors 2"
                    % (WORKSHOP, x + 8, z + 8))
        # Written rather than read back: the settings files carry comments, so
        # they are json5 and json.loads would choke, and the export reads them off
        # disk on every run so nothing needs reloading.
        write_settings("core", {
            "namespace": "mypack",
            "conversions": {"minecraft:white_wool": "minecraft:gold_block"},
        })
        con.command("lcdev export c1")
        expect("c1", ["minecraft:gold_block"], ["minecraft:white_wool"],
               "core says gold")

        print("\n" + "=" * 72)
        print("2. the plot's table overrides the pack's")
        write_settings("building/1x1/0", dict(
            base, conversions={"minecraft:white_wool": "minecraft:iron_block"}))
        con.command("lcdev export c2")
        expect("c2", ["minecraft:iron_block"],
               ["minecraft:gold_block", "minecraft:white_wool"],
               "plot says iron")

        print("\n" + "=" * 72)
        print("3. a level's table overrides the plot's, for that level only")
        write_settings("building/1x1/0", dict(
            base,
            conversions={"minecraft:white_wool": "minecraft:iron_block"},
            levels={"1": {"conversions":
                          {"minecraft:white_wool": "minecraft:diamond_block"}}}))
        con.command("lcdev export c3")
        # Both have to be there: diamond proves the level won, iron proves it did
        # not win everywhere.
        expect("c3", ["minecraft:iron_block", "minecraft:diamond_block"],
               ["minecraft:gold_block", "minecraft:white_wool"],
               "level 1 says diamond, the rest iron")

        print("\n" + "=" * 72)
        print("4. a narrower scope adds to the wider one, not replaces it")
        con.command("execute in %s run fill %d %d %d %d %d %d "
                    "minecraft:black_wool" % (WORKSHOP, x, BASE + STRIDE, z,
                                              x + 7, BASE + STRIDE, z + 7))
        write_settings("building/1x1/0", dict(
            base,
            conversions={"minecraft:white_wool": "minecraft:iron_block"},
            levels={"1": {"conversions":
                          {"minecraft:black_wool": "minecraft:emerald_block"}}}))
        con.command("lcdev export c4")
        # The level names only black wool. If a narrower scope replaced the plot's
        # table outright, white wool on that level would fall through to the pack's
        # gold, or to no conversion at all and reach the pack as wool.
        expect("c4", ["minecraft:iron_block", "minecraft:emerald_block"],
               ["minecraft:gold_block", "minecraft:white_wool",
                "minecraft:black_wool"],
               "level adds emerald, keeps the plot's iron")
        print("\n" + "=" * 72)
        print("5. a chunk's table overrides the plot's")
        # dx,dz is 0,0 for a one chunk plot, which is still the chunk scope: it is
        # the branch with the null guard and the nested read, and none of the cases
        # above touch it.
        write_settings("building/1x1/0", dict(
            base,
            conversions={"minecraft:white_wool": "minecraft:iron_block"},
            chunks={"0,0": {"conversions":
                            {"minecraft:white_wool": "minecraft:copper_block"}}}))
        con.command("lcdev export c5")
        expect("c5", ["minecraft:copper_block"],
               ["minecraft:iron_block", "minecraft:gold_block",
                "minecraft:white_wool"],
               "chunk says copper")

        print("\n" + "=" * 72)
        print("6. a chunk's level is narrower still")
        write_settings("building/1x1/0", dict(
            base,
            conversions={"minecraft:white_wool": "minecraft:iron_block"},
            chunks={"0,0": {
                "conversions": {"minecraft:white_wool": "minecraft:copper_block"},
                "levels": {"2": {"conversions":
                                 {"minecraft:white_wool": "minecraft:lapis_block"}}},
            }}))
        con.command("lcdev export c6")
        # Level 2 is lapis and the other levels stay copper, so the deepest scope
        # wins without winning everywhere.
        expect("c6", ["minecraft:lapis_block", "minecraft:copper_block"],
               ["minecraft:iron_block", "minecraft:gold_block",
                "minecraft:white_wool"],
               "chunk level 2 says lapis, the rest copper")

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
print("a conversion is scoped: the narrower one wins and adds to the wider")
print("all checks passed")
