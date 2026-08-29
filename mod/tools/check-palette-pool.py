#!/usr/bin/env python3
"""How far the palette pool goes, and whether what it hands out is safe to write.

    python mod/tools/check-palette-pool.py

Needs the wiki's test rig, the same way the other server checks do.

Written to settle a bug report: two buildings and one road part, the export refused
with "ran out of palette characters", and setting the plot to use its own part
palette changed nothing. Both halves of that were true.

  * **A cell is a block state, not a block.** `PaletteLedger.describe` writes every
    property, so two orientations of one stair are two cells. Two detailed buildings
    reaching a hundred and twenty is unremarkable once that is understood.

  * **A per-part palette does not reduce what the ledger spends.** The palette is
    written into the part, but the character comes from one pool shared by the whole
    workshop. That is what made the reporter's own fix useless.

The pool used to hold a hundred and twenty, which is what turned an ordinary build
into a refusal. It now runs through the basic multilingual plane, about forty
thousand characters, against the twenty six thousand block states Minecraft ships.
So the arrangement that used to fail has to succeed, and this check is mostly about
proving the characters past the old limit are ones Lost Cities can actually read.

**The ceiling is the plane, and that is not a detail.** Lost Cities keys its palette
`Map<Character, PE>` from `getChr().charAt(0)` and reads a slice row with
`toCharArray()`. Above `U+FFFF` a Java character is half of a surrogate pair, so a
palette key would collide on its high half and a row would count it as two cells and
shift every block after it along. Case 3 is what stops a later change reaching past
the plane, because both of those failures are silent.
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

sys.path.insert(0, "mod/tools")
from palettechars import OLD_POOL, unsafe  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
DEVTOOL = os.path.join(WORLD, "lostcitiesdevtool")
PLOTS = os.path.join(DEVTOOL, "plots.json")
LEDGER = os.path.join(DEVTOOL, "palette-ledger.json")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
PACK = "pp"
NS = "poolpack"
BASE = -63

# The two plots the reporter's case maps onto: two buildings, each asking for its
# own palette. Block plots rather than selector rows, because a building is what a
# round trip is already known to survive.
ONE = "building/1x1/0"
TWO = "building/1x1/1"

# How tall to compare. `Boundaries.STRIDE` is 6, so this is exactly one level: the
# stone floor, the one layer of distinct blocks above it, and the air over that. A
# region that stopped mid-level would compare a part against only some of itself.
TALL = 6

# Where each plot gets copied so the import can be compared against it.
SCRATCH = {ONE: (2000, 2000), TWO: (2000, 2064)}
SCRATCH_BOX = (1984, 1984, 2079, 2143)


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

PER_PLOT = 70

# What each building needs to be a building the pack references and the import can
# put back. `floors 0` with `cellars 0` is one level, which is why TALL is a level:
# the region compared is the whole of what the part covers. Without `citystyles` the
# export warns that nothing references the building and the import finds nothing,
# which is how the first draft of this check failed.
SETTINGS = ["floors 0", "cellars 0", "citystyles mycity", "factor 1.0",
            "palette part"]

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def boot():
    """Boot, and hand back the startup log as well as the process.

    The log is half the oracle for case 4: Lost Cities checks every asset when
    datapacks load, so a palette character it cannot read shows up there rather
    than as a wrong block much later.
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


def shut():
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("stop")
    except Exception:
        pass


def blocks():
    """Every distinct block id this check can place, in a fixed order."""
    out = []
    for family in FAMILIES:
        for colour in COLOURS:
            out.append("minecraft:%s_%s" % (colour, family))
    out.extend("minecraft:" + name for name in PLAIN)
    return out


ALL = blocks()


def read_plots():
    return {p["id"]: p for p in
            json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}


def at(plot, cmd):
    """A plot command, run standing in the middle of that plot."""
    return "execute in %s positioned %d 10 %d run %s" % (
        WORKSHOP, plot["chunkX"] * 16 + 8, plot["chunkZ"] * 16 + 8, cmd)


def fill(con, plot, count, offset=0):
    """One distinct block per position, along the plot's floor."""
    x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
    con.command("execute in %s run forceload add %d %d %d %d"
                % (WORKSHOP, x, z, x + 15, z + 15))
    con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone"
                % (WORKSHOP, x, BASE, z, x + 15, BASE, z + 15))
    con.command("execute in %s run fill %d %d %d %d %d %d minecraft:air"
                % (WORKSHOP, x, BASE + 1, z, x + 15, BASE + TALL - 1, z + 15))
    placed = ALL[offset:offset + count]
    for i, state in enumerate(placed):
        con.command("execute in %s run setblock %d %d %d %s"
                    % (WORKSHOP, x + (i % 16), BASE + 1, z + (i // 16), state))
    return len(placed)


def ledger():
    """Cell key to character, as the ledger on disk holds it."""
    if not os.path.isfile(LEDGER):
        return {}
    doc = json.load(io.open(LEDGER, encoding="utf-8"))
    body = doc.get("assigned", doc)
    return body if isinstance(body, dict) else {}


def exhausted(reply):
    return "ran out of palette characters" in reply


# ------------------------------------------------------------- half one, export

for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
for stale in glob.glob(os.path.join(SERVER, "mods", "lostcities_devtool-*.jar")):
    os.remove(stale)
dest = rig.install(SERVER, JAR)
print("fresh world, jar installed: %s" % os.path.basename(JAR))
print("the pool used to hold %d; this check works past that on purpose\n"
      % len(OLD_POOL))

proc, log = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = read_plots()
        one, two = plots[ONE], plots[TWO]

        for cmd in ("lcdev plot set namespace " + NS,
                    "lcdev plot set worldStyle main",
                    "lcdev plot set inherit none",
                    "lcdev plot set packName Palette pool"):
            con.command(at(plots["core"], cmd))

        print("=" * 72)
        print("1. one building of %d blocks, asking for its own palette" % PER_PLOT)
        n1 = fill(con, one, PER_PLOT)
        for cmd in SETTINGS + ["name one"]:
            con.command(at(one, "lcdev plot set " + cmd))
        print("  %d distinct blocks placed" % n1)

        print("\n" + "=" * 72)
        print("2. a second building of %d more, the arrangement that used to refuse"
              % PER_PLOT)
        # This is the reporter's case. Each building is well inside the old pool on
        # its own and the pair was over it, and asking for a per-part palette did
        # not help because the character still came from one shared pool. The pool
        # is no longer the constraint, so the export has to succeed.
        n2 = fill(con, two, PER_PLOT, offset=PER_PLOT)
        for cmd in SETTINGS + ["name two"]:
            con.command(at(two, "lcdev plot set " + cmd))
        print("  %d more distinct blocks placed" % n2)

        # Wrapped because of the way this fails when it fails. With the pool too
        # small the exporter reports a fault for every cell it could not letter,
        # and the reply outgrows what the rig's RCON client will reassemble, so the
        # export never returns and the check sits there until the socket gives up
        # ten minutes later. That is a real regression signal arriving in the least
        # useful form there is, so it is caught and named. Verified by capping the
        # pool back to 120 and running this: without the guard it hangs, with it
        # the check says which of the two things went wrong.
        try:
            said = con.command("lcdev export " + PACK).rstrip()
        except Exception as e:
            fail("the export never returned (%s). The pool is too small: the "
                 "exporter is reporting a fault per unlettered cell and the reply "
                 "is larger than the rig can read back" % type(e).__name__)
            raise SystemExit(1)
        print("  " + said.replace("\n", " ")[-220:])
        cells = len(ledger())
        print("  cells the ledger holds: %d, against an old pool of %d"
              % (cells, len(OLD_POOL)))
        if exhausted(said):
            fail("two buildings of %d blocks still exhaust the pool, which is the "
                 "reported bug" % PER_PLOT)
        if cells <= len(OLD_POOL):
            fail("the ledger holds %d cells, inside the old pool of %d, so this "
                 "check is no longer exercising the characters past it"
                 % (cells, len(OLD_POOL)))
        if cells < n1 + n2:
            fail("%d distinct blocks produced only %d ledger entries, so the "
                 "fixture is not placing what it thinks it is" % (n1 + n2, cells))

        print("\n" + "=" * 72)
        print("3. every character handed out is one a row can hold")
        assigned = ledger()
        chars = set(assigned.values())
        beyond = [c for c in chars if c not in OLD_POOL]
        print("  characters assigned: %d, of them past the old pool: %d"
              % (len(chars), len(beyond)))
        print("  a sample from past the old pool: %s"
              % ("".join(beyond[:40]) if beyond else "none"))
        if not beyond:
            fail("no character came from past the old pool, so nothing here tests "
                 "the widening")
        seen = {}
        for key, c in assigned.items():
            why = unsafe(c)
            if why:
                fail("the character for %s (U+%04X) %s"
                     % (key[:40], ord(c[0]) if c else 0, why))
            if c in seen:
                fail("U+%04X stands for both %s and %s, so the palette draws the "
                     "wrong block" % (ord(c), seen[c][:30], key[:30]))
            seen[c] = key
        print("  distinct characters: %d for %d cells" % (len(seen), len(assigned)))

        # Everything above reads the ledger, which is what the mod decided. This
        # reads the pack, which is what it wrote. They are separate questions: an
        # exporter that lettered correctly and then mangled the character on the way
        # into the file would pass every assertion above. It also answers the third
        # thing the reporter noticed, that the palette inside a part does not start
        # at A, by saying what it does hold.
        in_pack = {}
        for base, _, files in os.walk(os.path.join(EXPORTS, PACK)):
            if "/parts" not in base.replace(os.sep, "/"):
                continue
            for f in files:
                if not f.endswith((".json", ".json5")):
                    continue
                doc = json.load(io.open(os.path.join(base, f), encoding="utf-8"))
                held = doc.get("palette")
                if held is None:
                    continue
                # An inline palette is an object holding the list, not the list.
                # A bare list decodes as no palette at all, so the part keeps its
                # characters, resolves none of them, and draws air with nothing
                # logged to say why. Asserted here because the first draft of this
                # check read the broken shape and reported the mod for it.
                if not isinstance(held, dict):
                    fail("%s writes 'palette' as a %s. It has to be an object "
                         "holding the list, or the part silently draws air"
                         % (f, type(held).__name__))
                    continue
                for entry in held.get("palette", []):
                    if isinstance(entry, dict) and "char" in entry:
                        in_pack.setdefault(entry["char"], f)
        pack_beyond = [c for c in in_pack if c not in OLD_POOL]
        print("  characters written into the parts' own palettes: %d, of them past "
              "the old pool: %d" % (len(in_pack), len(pack_beyond)))
        if not in_pack:
            fail("no part carried a palette of its own, so `palette part` did "
                 "nothing and this check is not testing the reported case")
        if not pack_beyond:
            fail("the parts' palettes hold nothing past the old pool, so the pack "
                 "does not actually exercise the widening even though the ledger "
                 "does")
        for c, where in in_pack.items():
            why = unsafe(c)
            if why:
                fail("the pack's own palette in %s carries a character that %s"
                     % (where, why))
            if c not in chars:
                fail("%s carries U+%04X, which the ledger never handed out, so the "
                     "file and the ledger disagree" % (where, ord(c[0])))

        # Copy both plots aside, then empty them, so half two has something to
        # compare the imported result against.
        con.command("execute in %s run forceload add %d %d %d %d"
                    % ((WORKSHOP,) + SCRATCH_BOX))
        for plot_id in (ONE, TWO):
            p = plots[plot_id]
            x, z = p["chunkX"] * 16, p["chunkZ"] * 16
            sx, sz = SCRATCH[plot_id]
            con.command("execute in %s run clone %d %d %d %d %d %d %d %d %d"
                        % (WORKSHOP, x, BASE, z, x + 15, BASE + TALL - 1, z + 15,
                           sx, BASE, sz))
finally:
    shut()
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()

# ------------------------------------------------- half two, read it back again

print("\n" + "=" * 72)
print("4. the pack loads, and the blocks come back")
# The point of half two. Everything above proves the mod is willing to write these
# characters; only Lost Cities reading its own datapack proves they mean anything.
# A character it cannot key on comes back as air or as the wrong block, and a
# character that is two `char`s wide shifts the rest of its row along.
first = os.path.join(EXPORTS, PACK)
if not os.path.isdir(first):
    fail("nothing was exported, so there is nothing to read back")
else:
    packs = os.path.join(WORLD, "datapacks", "pppack")
    os.makedirs(packs)
    shutil.copytree(os.path.join(first, "data"), os.path.join(packs, "data"))
    shutil.copy(os.path.join(first, "pack.mcmeta"), packs)
    shutil.rmtree(first)
    shutil.rmtree(DEVTOOL)
    print("  installed the export as a datapack, emptied the workshop's records")

    proc, log = boot()
    print("  server up")

    complaints = [ln for ln in log
                  if re.search(r"error|fail|could not|invalid|exception", ln, re.I)]
    ours = [ln for ln in complaints if NS in ln or "pppack" in ln]
    print("  complaints about the exported pack: %d" % len(ours))
    for ln in ours[:8]:
        print("      " + ln.strip()[-160:])
    if ours:
        fail("the exported pack did not load cleanly, so a character in it is one "
             "Lost Cities will not read")

    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("lcdev workshop build")
            plots = read_plots()
            con.command("execute in %s run forceload add %d %d %d %d"
                        % ((WORKSHOP,) + SCRATCH_BOX))
            for plot_id in (ONE, TWO):
                p = plots[plot_id]
                x, z = p["chunkX"] * 16, p["chunkZ"] * 16
                con.command("execute in %s run forceload add %d %d %d %d"
                            % (WORKSHOP, x, z, x + 15, z + 15))
                con.command("execute in %s run fill %d %d %d %d %d %d minecraft:air"
                            % (WORKSHOP, x, BASE, z, x + 15, BASE + TALL - 1,
                               z + 15))

            reply = con.command("lcdev import %s:main" % NS).rstrip()
            print("  " + reply.replace("\n", " ")[-200:])
            if "no world style" in reply.lower():
                fail("the exported pack's world style did not load")

            for plot_id in (ONE, TWO):
                p = plots[plot_id]
                x, z = p["chunkX"] * 16, p["chunkZ"] * 16
                sx, sz = SCRATCH[plot_id]
                text = con.command(
                    "execute in %s if blocks %d %d %d %d %d %d %d %d %d all"
                    % (WORKSHOP, x, BASE, z, x + 15, BASE + TALL - 1, z + 15,
                       sx, BASE, sz)).strip()
                lower = text.lower()
                if "passed" in lower:
                    print("  %-16s all %d blocks match" % (plot_id, 16 * 16 * TALL))
                elif "failed" in lower or "match" in lower:
                    print("  %-16s DIFFERENT: %s" % (plot_id, text))
                    fail("%s does not hold the blocks it held before the export, so "
                         "a palette character did not survive the round trip"
                         % plot_id)
                else:
                    fail("%s: could not tell from %r whether the blocks match"
                         % (plot_id, text))

            print("\n" + "=" * 72)
            print("5. the ledger keeps what it has handed out")
            # Stability is the reason the ledger exists: a character given back
            # would re-letter a pack on its next export, and every diff becomes a
            # whole-file diff.
            before = len(ledger())
            con.command("lcdev export %s -f" % PACK)
            after = len(ledger())
            print("  cells before a repeat export: %d, after: %d" % (before, after))
            if after < before:
                fail("the ledger gave characters back, which it is documented never "
                     "to do and which the stability of a diff depends on")
    finally:
        shut()
        try:
            proc.wait(timeout=180)
        except Exception:
            proc.kill()

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("two buildings past the old pool export, every character is one a row can "
      "hold, and the pack reads back block for block")
print("all checks passed")
