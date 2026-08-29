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
import atexit
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
WANT = 1000

AIR_BLOCK = "minecraft:air"

# What half two is allowed to look for: blocks nothing but this pack can have put
# there. The claim rests on finding a block that could only have come from the pack,
# so a block terrain also makes proves nothing, which the first draft learned by
# counting andesite and cobblestone.
#
# **Named rather than excluded, because the two fail in opposite directions.** This
# was an exclusion list, and an exclusion list fails open: a naturally occurring
# block added to PLAIN and forgotten here gets sampled, is found because terrain made
# it rather than because the building drew it, and the count passes proving nothing.
# An inclusion list fails closed. A block nobody added here is simply not sampled,
# and if that empties the sample the check says so instead of passing.
#
# Deliberately shorter than it could be. Every entry has to be something no worldgen
# produces, so anything that shows up in a village, a bastion, an end city, a fossil
# or a shipwreck is left out even where it is also crafted.
#
# The stone brick family is out on evidence rather than on principle. A run counting
# it found 5794 cracked and 1830 mossy against 7 of each plank, and 7 is one per
# building in the sampled area. Those two were coming from somewhere that is not this
# pack, which is exactly the contamination being guarded against. **A count far above
# the building count is that signature**, and it is worth looking at rather than
# celebrating.
MANMADE = {
    "minecraft:oak_planks", "minecraft:spruce_planks", "minecraft:birch_planks",
    "minecraft:jungle_planks", "minecraft:acacia_planks",
    "minecraft:dark_oak_planks", "minecraft:cherry_planks",
    "minecraft:bamboo_planks", "minecraft:crimson_planks",
    "minecraft:warped_planks", "minecraft:bamboo_block",
    "minecraft:mud_bricks", "minecraft:mud_brick_slab",
    "minecraft:ochre_froglight", "minecraft:verdant_froglight",
    "minecraft:pearlescent_froglight",
}

# `/clone` refuses more than 32768 blocks in one go, so a region is counted one
# chunk at a time and summed. 16 by 16 by 128 is exactly the limit.
LOW = 40
HIGH = 167
CHUNKS = range(7, 11)

COLOURS = ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
           "gray", "light_gray", "cyan", "purple", "blue", "brown", "green",
           "red", "black")

# axis, three each. Nothing recalculates an axis.
PILLARS = tuple(
    ["%s_log" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                            "dark_oak", "mangrove", "cherry")]
    + ["stripped_%s_log" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                                       "dark_oak", "mangrove", "cherry")]
    + ["%s_wood" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                               "dark_oak", "mangrove", "cherry")]
    + ["stripped_%s_wood" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                                        "dark_oak", "mangrove", "cherry")]
    + ["crimson_stem", "warped_stem", "stripped_crimson_stem",
       "stripped_warped_stem", "crimson_hyphae", "warped_hyphae",
       "stripped_crimson_hyphae", "stripped_warped_hyphae",
       "hay_block", "bone_block", "basalt", "polished_basalt", "quartz_pillar",
       "purpur_pillar", "deepslate", "ochre_froglight", "verdant_froglight",
       "pearlescent_froglight", "muddy_mangrove_roots", "bamboo_block",
       "stripped_bamboo_block"])

# type=top|bottom|double, three each. Decided on placement, never revisited.
SLABS = tuple(
    ["%s_slab" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                             "dark_oak", "mangrove", "cherry", "bamboo",
                             "bamboo_mosaic", "crimson", "warped")]
    + ["stone_slab", "smooth_stone_slab", "sandstone_slab", "cut_sandstone_slab",
       "petrified_oak_slab", "cobblestone_slab", "brick_slab", "stone_brick_slab",
       "mud_brick_slab", "nether_brick_slab", "quartz_slab", "red_sandstone_slab",
       "cut_red_sandstone_slab", "purpur_slab", "prismarine_slab",
       "prismarine_brick_slab", "dark_prismarine_slab", "polished_granite_slab",
       "smooth_red_sandstone_slab", "mossy_stone_brick_slab",
       "polished_diorite_slab", "mossy_cobblestone_slab", "end_stone_brick_slab",
       "smooth_sandstone_slab", "smooth_quartz_slab", "granite_slab",
       "andesite_slab", "red_nether_brick_slab", "polished_andesite_slab",
       "diorite_slab", "cobbled_deepslate_slab", "polished_deepslate_slab",
       "deepslate_brick_slab", "deepslate_tile_slab", "blackstone_slab",
       "polished_blackstone_slab", "polished_blackstone_brick_slab"]
    + ["cut_copper_slab", "exposed_cut_copper_slab", "weathered_cut_copper_slab",
       "oxidized_cut_copper_slab", "waxed_cut_copper_slab",
       "waxed_exposed_cut_copper_slab", "waxed_weathered_cut_copper_slab",
       "waxed_oxidized_cut_copper_slab"])

# facing, four each. A horizontal facing set by setblock is not revisited.
GLAZED = tuple("%s_glazed_terracotta" % c for c in COLOURS)

# facing x half x open, sixteen each. A trapdoor connects to nothing.
TRAPDOORS = tuple(
    ["%s_trapdoor" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                                 "dark_oak", "mangrove", "cherry", "bamboo",
                                 "crimson", "warped")]
    + ["iron_trapdoor"])

# facing, six each, including up and down. A block entity with no neighbour logic.
SHULKERS = tuple(["shulker_box"] + ["%s_shulker_box" % c for c in COLOURS])

# The rest of the property-bearing families, as (ids, property, values) triples.
FACING4 = ("carved_pumpkin", "jack_o_lantern", "loom", "stonecutter",
           "anvil", "chipped_anvil", "damaged_anvil")
FACING6 = ("end_rod", "lightning_rod")

# candles x lit, eight each. Supported by the stone layer beneath.
CANDLES = tuple(["candle"] + ["%s_candle" % c for c in COLOURS])
LIT4 = ("furnace", "blast_furnace", "smoker")
FACING6_PLAIN = ("dispenser", "dropper")
COMMANDS = ("command_block", "chain_command_block", "repeating_command_block")

# One state each. Most of a real build is plain blocks.
PLAIN = tuple(
    ["%s_wool" % c for c in COLOURS]
    + ["%s_concrete" % c for c in COLOURS]
    + ["%s_concrete_powder" % c for c in COLOURS]
    + ["%s_terracotta" % c for c in COLOURS]
    + ["%s_stained_glass" % c for c in COLOURS]
    + ["%s_planks" % w for w in ("oak", "spruce", "birch", "jungle", "acacia",
                                 "dark_oak", "mangrove", "cherry", "bamboo",
                                 "crimson", "warped")]
    + ["terracotta", "glass", "tinted_glass", "stone", "granite", "diorite",
       "andesite", "polished_granite", "polished_diorite", "polished_andesite",
       "cobblestone", "mossy_cobblestone", "smooth_stone", "stone_bricks",
       "mossy_stone_bricks", "cracked_stone_bricks", "chiseled_stone_bricks",
       "bricks", "cobbled_deepslate", "polished_deepslate", "deepslate_bricks",
       "cracked_deepslate_bricks", "deepslate_tiles", "cracked_deepslate_tiles",
       "chiseled_deepslate", "reinforced_deepslate", "tuff", "calcite",
       "dripstone_block", "sandstone", "chiseled_sandstone", "cut_sandstone",
       "smooth_sandstone", "red_sandstone", "chiseled_red_sandstone",
       "cut_red_sandstone", "smooth_red_sandstone", "prismarine",
       "prismarine_bricks", "dark_prismarine", "sea_lantern", "purpur_block",
       "end_stone", "end_stone_bricks", "quartz_block", "chiseled_quartz_block",
       "quartz_bricks", "smooth_quartz", "netherrack", "nether_bricks",
       "cracked_nether_bricks", "chiseled_nether_bricks", "red_nether_bricks",
       "blackstone", "polished_blackstone", "polished_blackstone_bricks",
       "cracked_polished_blackstone_bricks", "chiseled_polished_blackstone",
       "gilded_blackstone", "smooth_basalt", "obsidian", "crying_obsidian",
       "magma_block", "soul_sand", "soul_soil", "mud", "packed_mud", "mud_bricks",
       "clay", "gravel", "dirt", "coarse_dirt", "rooted_dirt", "moss_block",
       "iron_block", "gold_block", "diamond_block", "emerald_block", "lapis_block",
       "redstone_block", "coal_block", "netherite_block", "copper_block",
       "exposed_copper", "weathered_copper", "oxidized_copper", "waxed_copper_block",
       "waxed_exposed_copper", "waxed_weathered_copper", "waxed_oxidized_copper",
       "cut_copper", "exposed_cut_copper", "weathered_cut_copper",
       "oxidized_cut_copper", "waxed_cut_copper", "waxed_exposed_cut_copper",
       "waxed_weathered_cut_copper", "waxed_oxidized_cut_copper",
       "raw_iron_block", "raw_gold_block", "raw_copper_block",
       "coal_ore", "deepslate_coal_ore", "iron_ore", "deepslate_iron_ore",
       "copper_ore", "deepslate_copper_ore", "gold_ore", "deepslate_gold_ore",
       "lapis_ore", "deepslate_lapis_ore", "diamond_ore", "deepslate_diamond_ore",
       "emerald_ore", "deepslate_emerald_ore", "nether_gold_ore",
       "nether_quartz_ore", "ancient_debris",
       "bookshelf", "crafting_table", "cartography_table", "fletching_table",
       "smithing_table", "melon", "pumpkin", "dried_kelp_block", "honeycomb_block",
       "slime_block", "honey_block", "sponge", "wet_sponge", "glowstone",
       "shroomlight", "amethyst_block", "budding_amethyst", "ice", "packed_ice",
       "blue_ice", "snow_block", "nether_wart_block", "warped_wart_block",
       "mangrove_roots", "sculk", "bamboo_mosaic"])


failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def states():
    """Every distinct block state this places, in a fixed order."""
    out = []
    for name in PILLARS:
        out.extend("minecraft:%s[axis=%s]" % (name, a) for a in ("x", "y", "z"))
    for name in SLABS:
        out.extend("minecraft:%s[type=%s]" % (name, t)
                   for t in ("top", "bottom", "double"))
    for name in GLAZED + FACING4:
        out.extend("minecraft:%s[facing=%s]" % (name, f)
                   for f in ("north", "south", "east", "west"))
    for name in TRAPDOORS:
        for f in ("north", "south", "east", "west"):
            for h in ("top", "bottom"):
                for o in ("true", "false"):
                    out.append("minecraft:%s[facing=%s,half=%s,open=%s]"
                               % (name, f, h, o))
    for name in SHULKERS + FACING6 + FACING6_PLAIN:
        out.extend("minecraft:%s[facing=%s]" % (name, f)
                   for f in ("north", "south", "east", "west", "up", "down"))
    for name in LIT4:
        for f in ("north", "south", "east", "west"):
            out.extend("minecraft:%s[facing=%s,lit=%s]" % (name, f, l)
                       for l in ("true", "false"))
    for name in COMMANDS:
        for f in ("north", "south", "east", "west", "up", "down"):
            out.extend("minecraft:%s[facing=%s,conditional=%s]" % (name, f, c)
                       for c in ("true", "false"))
    for name in CANDLES:
        for n in ("1", "2", "3", "4"):
            out.extend("minecraft:%s[candles=%s,lit=%s]" % (name, n, l)
                       for l in ("true", "false"))
    out.append("minecraft:chain[axis=x]")
    out.append("minecraft:chain[axis=y]")
    out.append("minecraft:chain[axis=z]")
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

# A name in MANMADE that the fixture never places can never be found in the world,
# so it silently shrinks the sample half two draws from instead of failing. Asked
# here, before anything is built, because it is a typo rather than a result.
stray = MANMADE - {block_of(state) for state in ALL}
if stray:
    raise SystemExit("MANMADE names blocks the fixture never places, so they could "
                     "only ever be missing: %s" % ", ".join(sorted(stray)))
print("of them vouched for as impossible in terrain: %d"
      % len(MANMADE & {block_of(state) for state in ALL}))

# The Lost Cities config belongs to the rig. Half two points a dimension at the
# profile this writes, and leaving that behind hands every later boot a city
# dimension whose world style stops resolving as soon as this world is deleted.
#
# Registered with atexit rather than left at the bottom of the file, because the
# bottom of the file is only reached when nothing raised. A failed boot, a timed out
# RCON call or a malformed asset would otherwise walk out past the restore and leave
# every later check booting into an unresolved world style.
if os.path.isdir(KEPT_CONFIG):
    shutil.rmtree(KEPT_CONFIG)
if os.path.isdir(LC_CONFIG):
    shutil.copytree(LC_CONFIG, KEPT_CONFIG)


def restore():
    jar = globals().get("dest")
    if jar and os.path.isfile(jar):
        os.remove(jar)
    if os.path.isdir(KEPT_CONFIG):
        if os.path.isdir(LC_CONFIG):
            shutil.rmtree(LC_CONFIG)
        shutil.move(KEPT_CONFIG, LC_CONFIG)
        print("removed the jar and put the rig's Lost Cities config back")


atexit.register(restore)
for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
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

        # Alternating floors, not one floor per storey. `floors 1` with `cellars 0`
        # is two levels of six, which is twelve layers: the even ones are stone and
        # the odd ones carry states. Six usable layers of 256 is 1536 slots.
        #
        # **Every state layer sits directly on stone**, and that is the reason for
        # the alternation rather than a stack. A block that needs support under it
        # pops the moment its neighbour updates, and a fixture that quietly loses a
        # row is exactly the failure this whole tool exists to catch.
        floors = [BASE + n for n in range(0, 12, 2)]
        layers = [BASE + n for n in range(1, 12, 2)]
        if len(ALL) > len(layers) * 256:
            raise SystemExit("%d states will not fit in %d slots. Add a level."
                             % (len(ALL), len(layers) * 256))
        for low in floors:
            con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone"
                        % (WORKSHOP, x, low, z, x + 15, low, z + 15))
        placed = 0
        refused = 0
        for i, state in enumerate(ALL):
            layer = layers[i // 256]
            spot = i % 256
            reply = con.command(
                "execute in %s run setblock %d %d %d %s"
                % (WORKSHOP, x + (spot % 16), layer, z + (spot // 16), state))
            if "Could not set" in reply or "Unknown block" in reply:
                if refused < 10:
                    fail("%s was refused (%s)" % (state, reply.strip()[:60]))
                refused += 1
            else:
                placed += 1
        print("placed %d of %d states across %d layers"
              % (placed, len(ALL), len(layers)))
        if refused:
            fail("%d states were refused, so the fixture names blocks this version "
                 "does not have" % refused)

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

# Which families collapsed, by name. Comparing whole state strings does not work:
# the exporter writes every property a state carries, so an intended
# `oak_trapdoor[facing=north,half=bottom,open=false]` comes back with `powered` and
# `waterlogged` on it too. Counting distinct palette entries per block id says the
# same thing without the mismatch, and names what to remove.
wanted = {}
for state in ALL:
    wanted[block_of(state)] = wanted.get(block_of(state), 0) + 1
got = {}
for blk in chars.values():
    got[block_of(blk)] = got.get(block_of(blk), 0) + 1
collapsed = sorted((name, n, got.get(name, 0)) for name, n in wanted.items()
                   if got.get(name, 0) < n)
if collapsed:
    print("  families that did not survive placement intact: %d" % len(collapsed))
    for name, asked, kept in collapsed[:12]:
        print("      %-44s asked %2d, kept %2d"
              % (name.replace("minecraft:", ""), asked, kept))
    print("      (a family that keeps fewer states than it asked for reads its own "
          "properties off a neighbour, and does not belong in this fixture)")
else:
    print("  every family survived placement intact")
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
                            & MANMADE)[:12]
            if not sample:
                fail("no block with an exotic character is one this check will "
                     "vouch for as impossible in terrain, so nothing here can tell "
                     "the pack apart from the world it generated into. Widen "
                     "MANMADE, or check that the fixture still places what it names")

            # Generation is asynchronous. Poll on a block the terrain cannot supply,
            # rather than sleeping a fixed time.
            # Stops at the first chunk holding one. The poll only needs to know
            # whether anything has generated, and asking all sixteen every five
            # seconds for four minutes is most of a thousand clone calls to answer a
            # yes or no.
            def anywhere(name):
                for cx in CHUNKS:
                    for cz in CHUNKS:
                        bx, bz = cx * 16, cz * 16
                        reply = con.command(
                            "execute in %s run clone %d %d %d %d %d %d 992 %d 992 "
                            "filtered %s"
                            % (CITY, bx, LOW, bz, bx + 15, HIGH, bz + 15, LOW, name))
                        m = re.search(r"([0-9]+) block", reply)
                        if m and int(m.group(1)) > 0:
                            return True
                return False

            deadline = time.time() + 240
            while sample and time.time() < deadline:
                if anywhere(sample[0]):
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
    # Only what this tool writes. `rmtree(OUT)` took README.md with it, which is
    # hand written, is not regenerated, and is the file that tells somebody to run
    # this command. The second run destroyed the documentation for the first.
    os.makedirs(OUT, exist_ok=True)
    for gone in (os.path.join(OUT, "data"), os.path.join(OUT, "pack.mcmeta"),
                 os.path.join(OUT, PACK + ".json")):
        if os.path.isdir(gone):
            shutil.rmtree(gone)
        elif os.path.isfile(gone):
            os.remove(gone)
    shutil.copytree(os.path.join(src, "data"), os.path.join(OUT, "data"))
    shutil.copy(os.path.join(src, "pack.mcmeta"), OUT)
    if os.path.isfile(profile):
        shutil.copy(profile, OUT)
    print("\npack written to %s" % OUT)

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("a building of %d distinct block states, lettered past the old pool, "
      "generating in a real city" % len(chars))
print("done")
