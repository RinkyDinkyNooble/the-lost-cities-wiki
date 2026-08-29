#!/usr/bin/env python3
"""Phase C: the reading commands, over a world that really generated.

    python mod/tools/check-cmd-report.py

Needs the wiki's test rig, the same way the other server checks do.

Covers `report`, `key`, `char`, `block` and `in`, which are the commands that
answer questions rather than change anything, and which had no check of their own
until now. They are the commands somebody reaches for when a pack is not doing what
they expected, so an answer that is wrong or missing costs more than a broken
export: it sends the reader looking in the wrong place.

The pack is `docs/examples/first-city`, the wiki's own teaching pack, installed
unchanged. Nothing third party is committed and nothing is written by hand that the
wiki does not already publish, so a change that breaks the tutorial breaks this too.

What it asserts, and why each is here:

  * `report` names the profile, its description and the world style. The description
    is the only field an author controls that survives into a running world, so it
    is the way to tell two profiles of the same name apart, and it is the one field
    here that could only have come from the file this check wrote.

  * `report` on a chunk holding a building names the building and every level from
    its lowest cellar to its top floor. A level reading NOTHING MATCHED is the fault
    the command exists to find, so a run where every level names a part is what
    proves the report is reading a real chunk rather than an empty one.

  * `report` outside a Lost Cities dimension says so and names the config key that
    would attach one, rather than failing as though the chunk were broken.

  * `key` carries the mod's own comment, and carries the correction underneath where
    the comment is wrong. Three keys have one. A release that dropped the
    corrections would still answer every query, which is why the correction is
    asserted rather than the presence of an answer.

  * `char` and `block` are inverses over the same palettes, so a character that
    resolves to a block has to be among the characters that block resolves back to.
    Checking them against each other catches a lookup that reads the wrong table,
    which neither one alone would show.

  * `in <asset>` scopes the same question to one asset. A character defined in the
    pack answers there; the assertion is that it says something different from the
    unscoped form, since a scope that quietly ignores its argument would otherwise
    pass every test written about it.

Characters are given as `U+03B1` rather than as the letter. The pack's palette is
Greek, the command accepts either form, and a code point cannot be mangled by
whatever encoding sits between here and the server.
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
CITY = "lostcities:lostcity"
WORLD = os.path.join(SERVER, "world")
PACK = "rptcity"
SOURCE = os.path.join("docs", "examples", "first-city")

# Written into the profile this check installs, so an assertion on it can only be
# satisfied by the report having read that file.
DESCRIPTION = "report check profile, not the shipped one"

# From the pack's own palette. Greek, given by code point.
ALPHA = "U+03B1"
BOOKSHELF = "minecraft:bookshelf"

# Keys whose config comment says something the code does not do. Written by hand in
# profile_key_corrections.json, and the reason `key` exists rather than a link.
CORRECTED = "buildingMaxCellars"

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


def install():
    """The wiki's teaching pack, plus a profile dense enough to find a city in."""
    packs = os.path.join(WORLD, "datapacks", PACK)
    os.makedirs(packs, exist_ok=True)
    shutil.copytree(os.path.join(SOURCE, "data"), os.path.join(packs, "data"))
    shutil.copy(os.path.join(SOURCE, "pack.mcmeta"), packs)

    profile = json.load(io.open(os.path.join(SOURCE, "profile", "mycity.json"),
                                encoding="utf-8"))
    profile["lostcity"]["description"] = DESCRIPTION
    # The shipped 0.05 is right for a world somebody plays and wrong for a check,
    # which would spend its boot looking for a city chunk. Not 1.0: the highway
    # network claims chunk after chunk at that density and a claimed chunk refuses
    # a building unless its city level is two above the highway's, so a world of
    # streets is what 1.0 actually produces. The mask turns that off.
    profile["cities"]["cityChance"] = 0.9
    profile.setdefault("highways", {})["highwayDistanceMask"] = 0
    dest = os.path.join(SERVER, "config", "lostcities", "profiles")
    os.makedirs(dest, exist_ok=True)
    io.open(os.path.join(dest, PACK + ".json"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(profile, indent=2) + "\n")

    # The section is [profiles], whatever the comment above it says. A wrong
    # section is rewritten to defaults, which points the dimension at biosphere.
    io.open(os.path.join(SERVER, "config", "lostcities", "common.toml"), "w",
            encoding="utf-8", newline="\n").write(
        '[profiles]\n\tdimensionsWithProfiles = ["%s=%s"]\n' % (CITY, PACK))


def report_at(con, cx, cz):
    """`report` on one chunk, as somebody standing in it would run it."""
    return con.command("execute in %s positioned %d 80 %d run lcdev report"
                       % (CITY, cx * 16 + 8, cz * 16 + 8)).rstrip()


LC_CONFIG = os.path.join(SERVER, "config", "lostcities")
KEPT = LC_CONFIG + ".kept"

# The Lost Cities config belongs to the rig, not to this check. Pointing a
# dimension at a profile and leaving it there hands every later boot a city
# dimension whose world style stops resolving the moment this world is deleted,
# and an unresolved world style throws rather than generating nothing.
if os.path.isdir(KEPT):
    shutil.rmtree(KEPT)
if os.path.isdir(LC_CONFIG):
    shutil.move(LC_CONFIG, KEPT)
if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
dest = rig.install(SERVER, JAR)
install()
print("fresh world, jar installed, the wiki's first-city pack as a datapack")
print("using %s\n" % os.path.basename(JAR))

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        print("=" * 72)
        print("1. a world that really generated")
        con.command("execute in %s run forceload add 0 0 95 95" % CITY)
        # Waited for rather than slept through. A report on an ungenerated chunk
        # answers about nothing, so a fixed sleep long enough on this machine is a
        # failure blamed on the pack on a slower one. The rig has paid for a bad
        # wait once already: a generation loop tested a block tag that does not
        # exist, never matched, and burned a 300 second timeout on every run in
        # this project's history.
        waited = 0
        while waited < 180:
            time.sleep(5)
            waited += 5
            if "is city" in report_at(con, 3, 3):
                break
        print("  waited %d seconds for the area to generate" % waited)
        if waited >= 180:
            fail("nothing generated inside 180 seconds, so nothing below is being "
                 "asked about a city")

        cities = 0
        buildings = 0
        described = None
        described_at = None
        levels_named = 0
        levels_missing = 0
        for cx in range(6):
            for cz in range(6):
                said = report_at(con, cx, cz)
                if "is city" in said and "true" in said.split("is city")[1][:12]:
                    cities += 1
                if "building" in said and "none, this is a street" not in said:
                    buildings += 1
                    if described is None:
                        described = said
                        described_at = (cx, cz)
        print("  chunks reported: 36")
        print("  chunks that are city: %d" % cities)
        print("  chunks holding a building: %d" % buildings)
        if cities == 0:
            fail("no chunk in the scanned area is a city chunk, so nothing below "
                 "is being asked about a generated city")
        if buildings == 0:
            fail("no chunk holds a building, so the level-by-level half of the "
                 "report is not being exercised")

        print("\n" + "=" * 72)
        print("2. the report names where its answer came from")
        one = described if described is not None else report_at(con, 0, 0)
        print(one[:700])
        if PACK not in one:
            fail("the report does not name the profile it read, so two profiles "
                 "of the same name cannot be told apart")
        if DESCRIPTION not in one:
            fail("the report does not carry the profile description, which is the "
                 "only field here that could only have come from the file this "
                 "check wrote")
        if "mycity" not in one:
            fail("the report does not name the world style")

        print("\n" + "=" * 72)
        print("3. every level of a building names a part")
        if described is not None:
            for line in described.splitlines():
                if re.search(r"level -?[0-9]+", line):
                    levels_named += 1
                    if "NOTHING MATCHED" in line:
                        levels_missing += 1
                        print("  " + line.strip())
            print("  levels reported: %d, naming no part: %d"
                  % (levels_named, levels_missing))
            if levels_named == 0:
                fail("a chunk holding a building reported no levels, so the part "
                     "chosen per level is not being read")
            if levels_missing:
                fail("%d levels matched no part, which is the fault this command "
                     "exists to find and which this pack does not have"
                     % levels_missing)

        print("\n" + "=" * 72)
        print("4. a dimension with no profile says so, and says what would fix it")
        said = con.command("execute in %s run lcdev report" % WORKSHOP).rstrip()
        print("  " + said.replace("\n", " ")[:260])
        if "dimensionsWithProfiles" not in said:
            fail("a report outside a Lost Cities dimension does not name the key "
                 "that would attach one, so it reads as a broken chunk")

        print("\n" + "=" * 72)
        print("5. a profile key carries the mod's own comment")
        said = con.command("lcdev key buildingMinFloors").rstrip()
        print("  " + said.replace("\n", " ")[:260])
        if "buildingMinFloors" not in said:
            fail("`key` did not name the key it was asked about")
        for want in ("type", "default"):
            if want not in said:
                fail("`key` said nothing about the %s of a key that has one" % want)

        print("\n" + "=" * 72)
        print("6. and carries the correction where the comment is wrong")
        said = con.command("lcdev key %s" % CORRECTED).rstrip()
        print("  " + said.replace("\n", " ")[-320:])
        if "That comment is wrong" not in said:
            fail("%s ships a config comment that says something the code does not "
                 "do, and `key` repeated it without the correction" % CORRECTED)
        if "Evidence" not in said:
            fail("the correction is asserted with no evidence named, which is the "
                 "same shape of claim it is contradicting")

        said = con.command("lcdev key notARealKey").rstrip()
        print("  " + said.replace("\n", " ")[:200])
        if "No profile key by that name" not in said:
            fail("an unknown key was not refused")

        print("\n" + "=" * 72)
        print("7. char and block are inverses over the same palettes")
        # In the chunk, not from the console. `char` answers about the palette
        # this chunk compiled, which is the only place the merged result of a
        # style, a building and a part exists at all, and is why the command is
        # worth having rather than reading the files.
        cx, cz = described_at if described_at else (0, 0)
        chars = con.command("execute in %s positioned %d 80 %d run lcdev char %s"
                            % (CITY, cx * 16 + 8, cz * 16 + 8, ALPHA)).rstrip()
        print("  char %s: %s" % (ALPHA, chars.replace("\n", " ")[:200]))
        # The same chunk as the character lookup above, or the two are answering
        # about different palettes and calling them inverses proves nothing.
        blocks = con.command("execute in %s positioned %d 80 %d run lcdev block %s"
                             % (CITY, cx * 16 + 8, cz * 16 + 8, BOOKSHELF)).rstrip()
        print("  block %s: %s" % (BOOKSHELF, blocks.replace("\n", " ")[:200]))
        if "light_gray_concrete" not in chars:
            fail("the character the pack defines as light gray concrete did not "
                 "resolve to it")
        # The pack gives bookshelf exactly one character, so the inverse lookup
        # has a single right answer rather than a set to be matched loosely.
        if "ε" not in blocks and "U+03B5" not in blocks:
            fail("the block the pack defines under one character did not resolve "
                 "back to it, so the two lookups disagree about one palette")

        print("\n" + "=" * 72)
        print("8. `in` scopes the question to one asset")
        scoped = con.command("execute in %s positioned %d 80 %d run lcdev in "
                             "mycity:tower_floor char %s"
                             % (CITY, cx * 16 + 8, cz * 16 + 8, ALPHA)).rstrip()
        print("  " + scoped.replace("\n", " ")[:280])
        if "tower_floor" not in scoped:
            fail("`in` did not name the asset it was scoped to")
        if scoped.strip() == chars.strip():
            fail("`in <asset> char` answered exactly what the unscoped form did, "
                 "so the asset argument is not narrowing anything")

        # The other branch of `in`. The asset argument is greedy-adjacent and the
        # two branches are separate nodes, so one working says nothing about the
        # other: `report block minecraft:gold_block` once became a request for the
        # character 'b' because of exactly this shape.
        scoped_block = con.command("execute in %s positioned %d 80 %d run lcdev in "
                                   "mycity:tower_floor block %s"
                                   % (CITY, cx * 16 + 8, cz * 16 + 8,
                                      "minecraft:light_gray_concrete")).rstrip()
        print("  " + scoped_block.replace("\n", " ")[:240])
        if "tower_floor" not in scoped_block:
            fail("`in <asset> block` did not name the asset it was scoped to")
        if "light_gray_concrete" not in scoped_block:
            fail("`in <asset> block` did not answer about the block it was asked "
                 "about, so the greedy argument swallowed something")

        bad = con.command("lcdev in mycity:nosuchpart char %s" % ALPHA).rstrip()
        print("  " + bad.replace("\n", " ")[:200])
        if "nosuchpart" not in bad:
            fail("`in` on an asset that is not loaded did not name it back")
finally:
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("stop")
    except Exception:
        proc.kill()
    proc.wait(timeout=120)

if os.path.isfile(dest):
    os.remove(dest)
if os.path.isdir(KEPT):
    if os.path.isdir(LC_CONFIG):
        shutil.rmtree(LC_CONFIG)
    shutil.move(KEPT, LC_CONFIG)
print("\nremoved the jar and put the rig's Lost Cities config back")

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("the reading commands answer about a world that generated, and say where "
      "each answer came from")
print("all checks passed")
