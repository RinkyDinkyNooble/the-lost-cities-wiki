#!/usr/bin/env python3
"""What an import loses: the variety between levels, and the NBT on a block.

    python mod/tools/check-import-fidelity.py

Needs the wiki's test rig, the same way the other server checks do.

Two things a real pack does that a simple one does not.

**Several parts can match the same level.** A building that says `range: "9,12"`
twice, naming a different part each time, is telling the generator to pick between
them on every level in that band. An import cannot roll dice, but taking the first
match every time turns four storeys of variety into the same storey four times.

**A palette entry can carry `tag`.** That is a raw NBT compound, and it is the
mechanism behind the command-block technique: the block is placed already holding
its command, and with `auto: 1` it runs on the spot and turns itself into whatever
it was there to place. An import that pastes only the block state leaves an empty
command block that does nothing.

The pack is written here rather than taken from a real one, so the check runs
anywhere. It is shaped after a pack that hit both.
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
NS = "fid"
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


def solid(ch):
    """One part: six layers of one character, with a marker at 0,0 on layer 0."""
    layer = [ch * 16 for _ in range(16)]
    first = ["C" + ch * 15] + [ch * 16 for _ in range(15)]
    return [first] + [layer for _ in range(5)]


def write_pack(root):
    data = os.path.join(root, "data", NS, "lostcities")
    assets = {
        "worldstyles/main": {
            "outsidestyle": NS + ":outside",
            "citystyles": [{"factor": 1.0, "citystyle": NS + ":city"}],
        },
        "citystyles/city": {
            "style": NS + ":main",
            "streetblocks": {"border": "y", "wall": "w", "street": "S",
                             "streetbase": "b", "streetvariant": "B", "width": 8},
            "selectors": {"buildings": [{"factor": 1.0, "value": NS + ":tower"}]},
        },
        "styles/main": {"randompalettes": [[{"factor": 1.0,
                                             "palette": NS + ":main"}]]},
        "styles/outside": {"randompalettes": [[{"factor": 1.0,
                                                "palette": NS + ":main"}]]},
        # `C` is the command-block technique: placed holding its command, and with
        # auto set it runs where it lands.
        "palettes/main": {"palette": [
            {"char": "g", "block": "minecraft:gold_block"},
            {"char": "d", "block": "minecraft:diamond_block"},
            {"char": "i", "block": "minecraft:iron_block"},
            {"char": "e", "block": "minecraft:emerald_block"},
            {"char": "C", "block": "minecraft:command_block[conditional=false,"
                                   "facing=north]",
             "tag": {"Command": "/say fidelity", "auto": 1, "conditionMet": 1}},
        ]},
        # Two parts share one band, which is the pack telling the generator to
        # pick between them per level.
        "buildings/tower": {
            "refpalette": NS + ":main", "filler": "g",
            "minfloors": 4, "maxfloors": 4, "mincellars": 0, "maxcellars": 0,
            "parts": [
                {"part": NS + ":ground", "ground": True, "top": False},
                {"part": NS + ":vara", "range": "1,3", "top": False},
                {"part": NS + ":varb", "range": "1,3", "top": False},
                {"part": NS + ":roof", "top": True},
            ],
        },
        "parts/ground": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                         "slices": solid("g")},
        "parts/vara": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                       "slices": solid("d")},
        "parts/varb": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                       "slices": solid("i")},
        "parts/roof": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                       "slices": solid("e")},
    }
    for name, body in assets.items():
        path = os.path.join(data, *name.split("/")) + ".json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write(
            json.dumps(body, indent=2) + "\n")
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "fidelity"}}))


if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
dest = rig.install(SERVER, JAR)
write_pack(os.path.join(WORLD, "datapacks", "fidpack"))
print("fresh world, jar installed, a pack with a shared band and a tagged block\n")

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        print("=" * 72)
        print(con.command("lcdev import %s:main" % NS).rstrip()[-400:])

        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
        plot = plots["building/1x1/0"]
        x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))
        # The clone destination has to be loaded too, or every count comes back
        # zero and the comparison silently measures nothing.
        con.command("execute in %s run forceload add 3990 3990 4030 4030"
                    % WORKSHOP)
        air = con.command("execute in %s run clone %d %d %d %d %d %d 4000 %d 4000 "
                          "filtered minecraft:air"
                          % (WORKSHOP, x, BASE, z, x + 15, BASE + 29, z + 15, BASE))
        m = re.search(r"([0-9]+) block", air)
        empty = int(m.group(1)) if m else 0
        print("\n  solid blocks pasted on the plot: %d of %d"
              % (16 * 16 * 30 - empty, 16 * 16 * 30))
        if 16 * 16 * 30 - empty < 100:
            fail("almost nothing was pasted, so the rest of this check is not "
                 "measuring what it claims")

        # Levels 1, 2 and 3 all sit in the "1,3" band, and the pack names two
        # different parts for it. Pasting the same one on all three is the bug.
        print("\n" + "=" * 72)
        print("the three levels sharing one band")
        distinct = set()
        for level in (1, 2, 3):
            y = BASE + level * STRIDE
            reply = con.command("execute in %s run clone %d %d %d %d %d %d "
                                "4000 %d 4000 filtered minecraft:diamond_block"
                                % (WORKSHOP, x, y, z, x + 15, y + 5, z + 15, y))
            m = re.search(r"([0-9]+) block", reply)
            diamonds = int(m.group(1)) if m else 0
            reply = con.command("execute in %s run clone %d %d %d %d %d %d "
                                "4000 %d 4000 filtered minecraft:iron_block"
                                % (WORKSHOP, x, y, z, x + 15, y + 5, z + 15, y))
            m = re.search(r"([0-9]+) block", reply)
            irons = int(m.group(1)) if m else 0
            which = "vara" if diamonds > irons else "varb"
            distinct.add(which)
            print("  level %d  diamond %-5d iron %-5d -> %s"
                  % (level, diamonds, irons, which))
        print("  distinct parts used across the band: %d" % len(distinct))
        if len(distinct) < 2:
            fail("all three levels of a band naming two parts got the same one, "
                 "so a building's variety is lost on the way in")

        # The tagged block. Lost Cities places it holding its command; an import
        # that drops the tag leaves a command block that does nothing.
        print("\n" + "=" * 72)
        print("the command block's own contents")
        got = con.command("execute in %s run data get block %d %d %d Command"
                          % (WORKSHOP, x, BASE, z))
        print("  " + got.strip()[:140])
        if "fidelity" not in got:
            fail("the command block came in without its command, so the technique "
                 "the pack is built on does not survive an import")

        con.command("stop")
finally:
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()

if os.path.isfile(dest):
    os.remove(dest)
print("\nremoved the jar, rig baseline is clean again")
print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
