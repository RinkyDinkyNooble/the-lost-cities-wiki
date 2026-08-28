#!/usr/bin/env python3
"""Build a city pack whose building holds well over a hundred distinct block states.

    python mod/tools/make-stress-pack.py

Needs the wiki's test rig, the same way the server checks do. Leaves the finished
pack in `research/stress-pack/` ready to drop into a world's `datapacks` folder.

**What this is for.** The palette pool used to hold 120 characters, and a user hit
the end of it with two ordinary buildings. The pool now runs through the plane, so
the interesting question is no longer whether the mod will letter a big build but
whether Lost Cities can read what the mod wrote once the characters stop being ASCII.
This produces a building that forces the question and then answers it by generating a
city from the result.

**A cell is a block state, not a block.** That is the whole reason a hundred is easy
to reach: `oak_log[axis=x]` and `oak_log[axis=y]` are two cells and get two
characters. So the fixture is built mostly out of families where one block id yields
several states.

**Only states that survive being placed.** Minecraft recalculates a stair's `shape`,
and a pane's or fence's connections, from its neighbours the moment it lands, so a
fixture built from those collapses to a fraction of what it asked for. Axis pillars
and slab types are decided by the block itself and are not touched again. Nothing
here is redstone: an observer or a piston changes state when a neighbour does, and
this places thousands of neighbours in a row.

The last section is the one that matters. It finds the blocks whose characters came
from past the old pool, generates a city, and counts *those* blocks in the world. A
character Lost Cities could not read would leave them missing.
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

sys.path.insert(0, "mod/tools")
from palettechars import OLD_POOL, unsafe  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORKSHOP = "lostcitiesdevtool:workshop"
CITY = "lostcities:lostcity"
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
LC_CONFIG = os.path.join(SERVER, "config", "lostcities")
KEPT_CONFIG = LC_CONFIG + ".kept"
OUT = os.path.join("research", "stress-pack")
PACK = "stresspack"
NS = "stresspack"
PLOT = "building/1x1/0"
BASE = -63

# How many distinct states the pack has to reach to be worth calling a stress test.
WANT = 100

AIR_BLOCK = "minecraft:air"

# Blocks that turn up in ordinary terrain, so counting one in a generated world says
# nothing about whether the building drew it. The whole claim in half two rests on
# finding blocks that could only have come from the pack, so these are excluded from
# what it looks for. Learned by counting andesite and cobblestone and proving
# nothing.
NATURAL = {
    "minecraft:stone", "minecraft:granite", "minecraft:diorite",
    "minecraft:andesite", "minecraft:calcite", "minecraft:tuff",
    "minecraft:dripstone_block", "minecraft:sandstone", "minecraft:deepslate",
    "minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:obsidian",
    "minecraft:netherrack", "minecraft:blackstone", "minecraft:end_stone",
    "minecraft:prismarine", "minecraft:dark_prismarine", "minecraft:air",
    "minecraft:oak_log", "minecraft:spruce_log", "minecraft:birch_log",
    "minecraft:jungle_log", "minecraft:acacia_log", "minecraft:dark_oak_log",
    "minecraft:mangrove_log", "minecraft:cherry_log", "minecraft:basalt",
    "minecraft:muddy_mangrove_roots", "minecraft:crimson_stem",
    "minecraft:warped_stem", "minecraft:hay_block",
}

# `/clone` refuses more than 32768 blocks in one go, so a region is counted one
# chunk at a time and summed. 16 by 16 by 128 is exactly the limit.
LOW = 40
HIGH = 167
CHUNKS = range(7, 11)

# One block id, three states, and nothing recalculates an axis.
PILLARS = ("oak_log", "spruce_log", "birch_log", "jungle_log", "acacia_log",
           "dark_oak_log", "mangrove_log", "cherry_log", "crimson_stem",
           "warped_stem", "stripped_oak_log", "stripped_birch_log",
           "stripped_spruce_log", "hay_block", "bone_block", "basalt",
           "polished_basalt", "quartz_pillar", "purpur_pillar", "deepslate",
           "ochre_froglight", "verdant_froglight", "pearlescent_froglight",
           "muddy_mangrove_roots", "bamboo_block")

# One block id, three states. A slab's type is decided when it is placed and is not
# revisited; `double` is a full block and still a separate palette entry.
SLABS = ("stone_slab", "smooth_stone_slab", "sandstone_slab", "cobblestone_slab",
         "brick_slab", "stone_brick_slab", "quartz_slab", "oak_slab",
         "spruce_slab", "birch_slab", "purpur_slab", "blackstone_slab",
         "deepslate_brick_slab", "mud_brick_slab")

# Margin, and a reminder that most of a real build is plain blocks.
PLAIN = ("stone", "granite", "diorite", "andesite", "calcite", "tuff",
         "dripstone_block", "sandstone", "bricks", "prismarine",
         "dark_prismarine", "purpur_block", "end_stone", "quartz_block",
         "netherrack", "blackstone", "obsidian", "oak_planks", "spruce_planks",
         "birch_planks", "jungle_planks", "acacia_planks", "dark_oak_planks",
         "cherry_planks", "bamboo_planks", "crimson_planks", "warped_planks",
         "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks",
         "chiseled_stone_bricks", "mud_bricks", "nether_bricks",
         "red_nether_bricks", "polished_granite", "polished_diorite",
         "polished_andesite", "smooth_stone", "cobblestone", "mossy_cobblestone")

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def states():
    """Every distinct block state this places, in a fixed order."""
    out = []
    for name in PILLARS:
        for axis in ("x", "y", "z"):
            out.append("minecraft:%s[axis=%s]" % (name, axis))
    for name in SLABS:
        for kind in ("top", "bottom", "double"):
            out.append("minecraft:%s[type=%s]" % (name, kind))
    out.extend("minecraft:" + name for name in PLAIN)
    return out


ALL = states()


def block_of(state):
    """The block id inside a state string, for counting one in a generated world."""
    return state.split("[")[0]


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
            print("\n".join(tail[-25:]))
            raise SystemExit("server exited during startup")
        tail.append(line.rstrip())
        if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
            threading.Thread(target=lambda: [None for _ in
                                             iter(proc.stdout.readline, "")],
                             daemon=True).start()
            return proc, tail
    raise SystemExit("server did not start")


def stop(proc):
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("stop")
    except Exception:
        pass
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()


# --------------------------------------------------------------- half one, build

print("distinct block states this will place: %d" % len(ALL))
if len(ALL) < WANT:
    raise SystemExit("the fixture only describes %d states, which is under the %d "
                     "this is supposed to stress" % (len(ALL), WANT))

# The Lost Cities config belongs to the rig. Half two points a dimension at the
# profile this writes, and leaving that behind hands every later boot a city
# dimension whose world style stops resolving as soon as this world is deleted.
if os.path.isdir(KEPT_CONFIG):
    shutil.rmtree(KEPT_CONFIG)
if os.path.isdir(LC_CONFIG):
    shutil.copytree(LC_CONFIG, KEPT_CONFIG)
dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
shutil.copy(JAR, dest)
print("fresh world, jar installed: %s\n" % os.path.basename(JAR))

proc, log = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
        b = plots[PLOT]
        core = plots["core"]

        def at(plot, cmd):
            return con.command(
                "execute in %s positioned %d 10 %d run %s"
                % (WORKSHOP, plot["chunkX"] * 16 + 8, plot["chunkZ"] * 16 + 8, cmd))

        for cmd in ("lcdev plot set namespace " + NS,
                    "lcdev plot set worldStyle main",
                    "lcdev plot set packName Palette stress test"):
            at(core, cmd)

        # cityChance and the highway mask go through the raw profile object. A world
        # of buildings needs both: at cityChance 1.0 the highway network claims chunk
        # after chunk and refuses every building, with nothing logged to say why.
        core_file = os.path.join(WORLD, "lostcitiesdevtool", "plots", "core.json5")
        text = io.open(core_file, encoding="utf-8").read().rstrip()
        io.open(core_file, "w", encoding="utf-8", newline="\n").write(
            text[:-1] + """
  "profile": {
    "cityChance": 1.0,
    "buildingChance": 1.0,
    "highwayDistanceMask": 0,
    "railwaysEnabled": false,
    "ruinChance": 0.0,
    "explosionChance": 0.0,
    "miniExplosionChance": 0.0,
    "generateLoot": false
  },
}
""")

        x, z = b["chunkX"] * 16, b["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))

        # Two storeys, each a stone floor with a layer of distinct states above it.
        # `floors 1` with `cellars 0` is two levels of six, so the second storey's
        # floor is six above the first.
        half = (len(ALL) + 1) // 2
        for storey, (low, chunk) in enumerate(((BASE, ALL[:half]),
                                               (BASE + 6, ALL[half:]))):
            con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone"
                        % (WORKSHOP, x, low, z, x + 15, low, z + 15))
            for i, state in enumerate(chunk):
                reply = con.command(
                    "execute in %s run setblock %d %d %d %s"
                    % (WORKSHOP, x + (i % 16), low + 1, z + (i // 16), state))
                if "Could not set" in reply or "Unknown block" in reply:
                    fail("storey %d: %s was refused (%s)"
                         % (storey + 1, state, reply.strip()[:60]))
            print("storey %d: %d states placed" % (storey + 1, len(chunk)))

        for cmd in ("lcdev plot set name stresshouse", "lcdev plot set floors 1",
                    "lcdev plot set cellars 0", "lcdev plot set citystyles mycity",
                    "lcdev plot set factor 1.0"):
            at(b, cmd)

        said = con.command("lcdev export " + PACK).rstrip()
        print("\n" + said.replace("\n", " ")[-200:])
finally:
    stop(proc)

# ------------------------------------------------------ what the pack ended up with

print("\n" + "=" * 72)
print("what the export wrote")
shared = os.path.join(EXPORTS, PACK, "data", NS, "lostcities", "palettes",
                      "main.json")
entries = []
if os.path.isfile(shared):
    doc = json.load(io.open(shared, encoding="utf-8"))
    entries = doc.get("palette", [])
else:
    fail("no shared palette was written, so there is nothing to stress")

chars = {}
for e in entries:
    if isinstance(e, dict) and "char" in e and "block" in e:
        chars[e["char"]] = e["block"]

beyond = {c: blk for c, blk in chars.items()
          if c not in OLD_POOL and blk != AIR_BLOCK}
print("  palette entries: %d" % len(chars))
print("  of them past the old pool of %d: %d" % (len(OLD_POOL), len(beyond)))
print("  a sample from past the old pool: %s" % "".join(list(beyond)[:40]))
if len(chars) < WANT:
    fail("the palette holds %d entries, under the %d this is meant to stress. "
         "Some states collapsed on placement, which is what happens when a block "
         "recalculates its own properties from its neighbours" % (len(chars), WANT))
if not beyond:
    fail("nothing in the palette came from past the old pool, so this pack does "
         "not stress anything the old build could not already do")
for c, blk in chars.items():
    # Air is the one entry whose character is a space, by the mod's own convention
    # and Lost Cities', so it is the one entry these rules do not apply to.
    if blk == AIR_BLOCK:
        continue
    why = unsafe(c)
    if why:
        fail("the character for %s (U+%04X) %s" % (blk, ord(c[0]) if c else 0, why))

# ------------------------------------------------------ half two, generate from it

print("\n" + "=" * 72)
print("generating a city from the pack, and looking for the blocks that got the "
      "exotic characters")
src = os.path.join(EXPORTS, PACK)
profile = os.path.join(src, "profile", PACK + ".json")
if not os.path.isdir(src) or not os.path.isfile(profile):
    fail("there is no pack to generate from")
else:
    shutil.rmtree(WORLD)
    packs = os.path.join(WORLD, "datapacks", PACK)
    os.makedirs(packs)
    shutil.copytree(os.path.join(src, "data"), os.path.join(packs, "data"))
    shutil.copy(os.path.join(src, "pack.mcmeta"), packs)
    profiles = os.path.join(LC_CONFIG, "profiles")
    os.makedirs(profiles, exist_ok=True)
    shutil.copy(profile, profiles)
    io.open(os.path.join(LC_CONFIG, "common.toml"), "w",
            encoding="utf-8", newline="\n").write(
        '[profiles]\n\tdimensionsWithProfiles = ["%s=%s"]\n' % (CITY, PACK))

    proc, log = boot()
    complaints = [ln for ln in log
                  if re.search(r"error|fail|could not|invalid|exception", ln, re.I)]
    ours = [ln for ln in complaints if NS in ln or PACK in ln]
    print("  complaints about the pack while loading: %d" % len(ours))
    for ln in ours[:6]:
        print("      " + ln.strip()[-150:])
    if ours:
        fail("the pack did not load cleanly")

    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("execute in %s run forceload add 112 112 175 175" % CITY)
            con.command("execute in %s run forceload add 992 992 1023 1023" % CITY)

            def count(name):
                """How many of `name` stand in the city, counted a chunk at a time."""
                total = 0
                for cx in CHUNKS:
                    for cz in CHUNKS:
                        bx, bz = cx * 16, cz * 16
                        reply = con.command(
                            "execute in %s run clone %d %d %d %d %d %d 992 %d 992 "
                            "filtered %s"
                            % (CITY, bx, LOW, bz, bx + 15, HIGH, bz + 15, LOW, name))
                        m = re.search(r"([0-9]+) block", reply)
                        total += int(m.group(1)) if m else 0
                return total

            # Only blocks that could not have come from terrain. Counting one that
            # could would pass whether or not the building drew anything.
            sample = sorted({block_of(b) for b in beyond.values()}
                            - NATURAL)[:12]
            if not sample:
                fail("every block with an exotic character is one that occurs in "
                     "ordinary terrain, so nothing here can tell the pack apart "
                     "from the world it generated into")

            # Generation is asynchronous. Poll on a block the terrain cannot supply,
            # rather than sleeping a fixed time.
            deadline = time.time() + 240
            while sample and time.time() < deadline:
                if count(sample[0]) > 0:
                    break
                time.sleep(5)

            # The claim worth making. Each of these reached the pack under a
            # character the old pool did not contain and is not something terrain
            # generates, so finding it standing in a city is Lost Cities reading
            # that character correctly.
            found = 0
            for name in sample:
                n = count(name)
                print("  %-42s %d" % (name.replace("minecraft:", ""), n))
                if n:
                    found += 1
            print("  blocks with an exotic character that generated: %d of %d"
                  % (found, len(sample)))
            if sample and found == 0:
                fail("not one block whose character came from past the old pool "
                     "appears in the generated city, so those characters are not "
                     "being read")
    finally:
        stop(proc)

# --------------------------------------------------------------------- deliver it

if os.path.isdir(src):
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(src, "data"), os.path.join(OUT, "data"))
    shutil.copy(os.path.join(src, "pack.mcmeta"), OUT)
    if os.path.isfile(profile):
        shutil.copy(profile, OUT)
    print("\npack written to %s" % OUT)

if os.path.isfile(dest):
    os.remove(dest)
if os.path.isdir(KEPT_CONFIG):
    if os.path.isdir(LC_CONFIG):
        shutil.rmtree(LC_CONFIG)
    shutil.move(KEPT_CONFIG, LC_CONFIG)
print("removed the jar and put the rig's Lost Cities config back")

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("a building of %d distinct block states, lettered past the old pool, "
      "generating in a real city" % len(chars))
print("done")
