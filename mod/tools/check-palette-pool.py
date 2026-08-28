#!/usr/bin/env python3
"""What exhausts the palette pool, and whether a per-part palette helps.

    python mod/tools/check-palette-pool.py

Needs the wiki's test rig, the same way the other server checks do.

Written to settle a bug report: two buildings and one road part, the export refused
with "ran out of palette characters", and setting the plot to use its own part
palette changed nothing.

Three things are being separated here, because the report could be any of them:

  * **A cell is a block state, not a block.** `PaletteLedger.describe` writes every
    property, so `oak_stairs[facing=north,half=bottom,shape=straight]` and the same
    stairs facing east are two cells. One stair type in varied orientations is up to
    40 states before waterlogging, and a pane is up to 32. Two detailed buildings
    reaching 120 is unremarkable once that is understood.

  * **The ledger is global and never reclaims.** It is keyed by cell across the whole
    workshop and across every export the world has ever done, so iterating on a build
    spends characters that are never given back.

  * **A per-part palette does not reduce what the ledger spends.** The palette is
    written into the part, but the character still comes from the one global pool.
    That is what makes the reporter's fix useless, and it is the part worth calling a
    bug rather than a limit: a character in a part's own palette only has to be
    unique inside that part.

The last case is the one to read. Two plots, each well under the pool on its own,
together over it, both asking for their own palette.
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
LEDGER = os.path.join(WORLD, "lostcitiesdevtool", "palette-ledger.json")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
BASE = -63

# What the pool holds: six ASCII, then Greek, then Cyrillic. A-Z, a-z and 0-9 are
# deliberately absent, because Lost Cities' own palettes use all 88 of them and a
# character this pack claims is taken away from every shipped part that used it.
# That is also the answer to "why does it not start at A".
POOL = 120

# Plain blocks with no neighbour-dependent state. The first draft of this used
# stairs in many orientations, which does not work: Minecraft recalculates a
# stair's `shape` from its neighbours the moment it is placed, so forty distinct
# states collapsed to thirteen. Panes, walls and fences connect the same way. What
# survives being placed is what a block id decides on its own.
COLOURS = ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
           "gray", "light_gray", "cyan", "purple", "blue", "brown", "green",
           "red", "black")
FAMILIES = ("wool", "concrete", "concrete_powder", "terracotta",
            "stained_glass", "glazed_terracotta")
PLAIN = ("stone", "granite", "diorite", "andesite", "deepslate", "calcite",
         "tuff", "dripstone_block", "sandstone", "red_sandstone", "bricks",
         "prismarine", "dark_prismarine", "purpur_block", "end_stone",
         "quartz_block", "netherrack", "blackstone", "obsidian",
         "oak_planks", "spruce_planks", "birch_planks", "jungle_planks",
         "acacia_planks", "dark_oak_planks", "mangrove_planks", "cherry_planks",
         "bamboo_planks", "crimson_planks", "warped_planks",
         "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks",
         "chiseled_stone_bricks", "mud_bricks", "nether_bricks",
         "red_nether_bricks", "polished_granite", "polished_diorite",
         "polished_andesite", "smooth_stone", "cobblestone", "mossy_cobblestone",
         "gravel", "clay", "packed_mud", "soul_sand", "magma_block")

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


def blocks():
    """Every distinct block id this check can place, in a fixed order."""
    out = []
    for family in FAMILIES:
        for colour in COLOURS:
            out.append("minecraft:%s_%s" % (colour, family))
    out.extend("minecraft:" + name for name in PLAIN)
    return out


ALL = blocks()


def states(count, offset=0):
    """`count` distinct blocks, none of which a block update can rewrite."""
    return ALL[offset:offset + count]


def fill(con, plot, count, offset=0):
    """One distinct block state per position, along the plot's floor."""
    x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
    con.command("execute in %s run forceload add %d %d %d %d"
                % (WORKSHOP, x, z, x + 15, z + 15))
    con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone"
                % (WORKSHOP, x, BASE, z, x + 15, BASE, z + 15))
    placed = states(count, offset)
    for i, state in enumerate(placed):
        con.command("execute in %s run setblock %d %d %d %s"
                    % (WORKSHOP, x + (i % 16), BASE + 1, z + (i // 16), state))
    return len(placed)


def ledger_size():
    if not os.path.isfile(LEDGER):
        return 0
    doc = json.load(io.open(LEDGER, encoding="utf-8"))
    body = doc.get("assigned", doc)
    return len(body) if isinstance(body, dict) else 0


def exhausted(reply):
    return "ran out of palette characters" in reply


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
shutil.copy(JAR, dest)
print("fresh world, jar installed: %s" % os.path.basename(JAR))
print("the pool holds %d: six ASCII, then Greek, then Cyrillic\n" % POOL)

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
        one = plots["selector/parks/0"]
        two = plots["selector/parks/1"]

        print("=" * 72)
        print("1. one plot of 70 blocks is well inside the pool")
        # Seventy distinct blocks is a detailed build and nothing more. On its own
        # it fits, which is what makes the second case a surprise to whoever hits
        # it: each plot is fine and the pair is not.
        n = fill(con, one, 70)
        con.command("execute in %s positioned %d 10 %d run lcdev plot set name one"
                    % (WORKSHOP, one["chunkX"] * 16 + 8, one["chunkZ"] * 16 + 8))
        con.command("execute in %s positioned %d 10 %d run lcdev plot set palette "
                    "part" % (WORKSHOP, one["chunkX"] * 16 + 8,
                              one["chunkZ"] * 16 + 8))
        said = con.command("lcdev export p1").rstrip()
        print("  %d distinct states of one block id placed" % n)
        print("  ledger entries after one plot: %d" % ledger_size())
        print("  " + said.replace("\n", " ")[-150:])
        if exhausted(said):
            fail("70 states exhausted a pool of %d on their own, so the arithmetic "
                 "below is wrong" % POOL)
        if ledger_size() < n:
            fail("%d distinct blocks produced only %d ledger entries, so the "
                 "fixture is not placing what it thinks it is"
                 % (n, ledger_size()))

        print("\n" + "=" * 72)
        print("2. a per-part palette does not reduce what the ledger spends")
        # The reporter's own fix. Each plot asks for its own palette, so each part
        # carries its own characters and only needs them unique within itself.
        n2 = fill(con, two, 70, offset=70)
        con.command("execute in %s positioned %d 10 %d run lcdev plot set name two"
                    % (WORKSHOP, two["chunkX"] * 16 + 8, two["chunkZ"] * 16 + 8))
        con.command("execute in %s positioned %d 10 %d run lcdev plot set palette "
                    "part" % (WORKSHOP, two["chunkX"] * 16 + 8,
                              two["chunkZ"] * 16 + 8))
        said = con.command("lcdev export p2 -f").rstrip()
        print("  a second plot, also %d states, also asking for its own palette" % n2)
        print("  ledger entries after both: %d" % ledger_size())
        print("  " + said.replace("\n", " ")[-260:])
        if exhausted(said):
            print("\n  REPRODUCED: two parts of %d states each, both with their own "
                  "palette," % n2)
            print("  exhaust one shared pool of %d. Neither part needs more than %d "
                  "characters" % (POOL, n2))
            print("  of its own, and a character in a part's palette only has to be "
                  "unique")
            print("  inside that part.")
        else:
            fail("the two plots did not exhaust the pool, so this check is not "
                 "reproducing the report and the numbers above need revisiting")

        print("\n" + "=" * 72)
        print("3. the ledger is what holds the characters, not the export")
        before = ledger_size()
        con.command("lcdev export p3 -f")
        after = ledger_size()
        print("  entries before a repeat export: %d, after: %d" % (before, after))
        if after < before:
            fail("the ledger gave characters back, which it is documented never to "
                 "do and which the stability of a diff depends on")
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
print("reproduced: one global pool is spent per distinct block state across the "
      "whole workshop, whatever a plot asks for its palette placement")
print("all checks passed")
