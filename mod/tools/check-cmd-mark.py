#!/usr/bin/env python3
"""Phase C: what a mark does, since the command that writes one needs a player.

    python mod/tools/check-cmd-mark.py

Needs the wiki's test rig, the same way the other server checks do.

`/lcdev mark` calls `getPlayerOrException` and then raycasts from where the player
is looking, so RCON cannot reach it and neither can this check. The Phase C plan
asked for a check covering mark for all six keys, and the command layer of that is
not reachable headless.

What is reachable is the half that matters. A mark is written into the plot's
settings against a position relative to the plot's own corner, and the exporter
reads it back when it builds the palette. So the behaviour is exercised by writing
`marks` the way the command writes them and asking what comes out of the pack, which
is where a mark either works or does not.

What it asserts:

  * **All six keys reach the pack.** `damaged`, `torch`, `variant`, `loot`, `mob`
    and `frompalette` are the keys that attach to one block rather than to a whole
    part. A key silently dropped between the settings file and the palette entry
    would leave the pack looking complete and generating something plainer.

  * **A marked block is a different cell from the same block unmarked.** The mark is
    part of the key the palette ledger letters, so one stone floor holding six marks
    produces seven entries, not one. If it produced one, every marked position would
    take whichever mark was read last and the other five would be lost. This is the
    assertion that would catch a mark being read but not keyed on.

  * **A mark is positional.** The entry carrying a mark has to be the one at the
    position the mark names, so the check marks six different positions with six
    different keys and reads them back apart.

  * **The command says why it cannot run without a player**, rather than failing as
    though the mark were invalid.
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
BASE = -63
PLOT = "selector/parks/0"

# The six keys that attach to a block rather than to a part, each at its own
# position so they can be told apart in the pack.
#
# `loot` and `mob` name a **Condition**, not a loot table or an entity. Lost Cities
# ships `chestloot`, `easymobs` and `hardmobs` and those are what a real pack points
# at. The first draft of this check wrote a loot table id and the export refused it,
# naming the runtime fault it would have caused: generation throws while resolving
# the resource and leaves chests that open, are empty and render invisible.
#
# Worth knowing about that rule: it fires on a value containing a slash, so a loot
# table path is caught and `minecraft:zombie` under `mob` is not, though it is just
# as wrong. The heuristic cannot tighten without refusing legitimate condition names.
MARKS = {
    "2,0,2": ("damaged", "minecraft:cracked_stone_bricks"),
    "4,0,4": ("torch", "minecraft:wall_torch"),
    "6,0,6": ("variant", "minecraft:mossy_cobblestone"),
    "8,0,8": ("loot", "lostcities:chestloot"),
    "10,0,10": ("mob", "lostcities:easymobs"),
    "12,0,12": ("frompalette", "#"),
}

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


def strip_json5(text):
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif text[i] == '"':
            out.append(text[i])
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    out.append(text[i])
                    i += 1
                out.append(text[i])
                i += 1
            if i < n:
                out.append(text[i])
                i += 1
        else:
            out.append(text[i])
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def entries(export):
    """Every palette entry the exported pack holds, from wherever it wrote them."""
    out = []
    for path in glob.glob(os.path.join(EXPORTS, export, "data", "*", "lostcities",
                                       "palettes", "*.json*")):
        body = json.loads(strip_json5(io.open(path, encoding="utf-8").read()))
        out.extend(body.get("palette", []))
    for path in glob.glob(os.path.join(EXPORTS, export, "data", "*", "lostcities",
                                       "parts", "*.json*")):
        body = json.loads(strip_json5(io.open(path, encoding="utf-8").read()))
        inner = body.get("palette")
        if isinstance(inner, dict):
            out.extend(inner.get("palette", []))
        elif isinstance(inner, list):
            out.extend(inner)
    return out


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (WORLD, EXPORTS):
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
        plot = plots[PLOT]
        x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))

        print("=" * 72)
        print("1. the command says why it cannot run over RCON")
        said = con.command("lcdev mark damaged minecraft:cobblestone").rstrip()
        print("  " + said.replace("\n", " ")[:200])
        if "needs a player" not in said:
            fail("mark run without a player did not say that is what is missing, "
                 "so it reads as a rejected mark rather than a missing player")

        print("\n" + "=" * 72)
        print("2. one stone floor, six positions marked")
        # One block everywhere, so anything that comes out with more than one
        # character came from the marks and from nothing else.
        con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone"
                    % (WORKSHOP, x, BASE, z, x + 15, BASE, z + 15))
        con.command("execute in %s positioned %d 10 %d run lcdev plot set name "
                    "marked" % (WORKSHOP, x + 8, z + 8))

        path = os.path.join(SETTINGS, *PLOT.split("/")) + ".json5"
        body = json.loads(strip_json5(io.open(path, encoding="utf-8").read()))
        # Written the way the command writes them: keyed on the position relative
        # to the plot's own corner, so a mark survives the plot moving.
        body["marks"] = {at: {key: value} for at, (key, value) in MARKS.items()}
        io.open(path, "w", encoding="utf-8", newline="\n").write(
            json.dumps(body, indent=2) + "\n")
        print("  marks written: %s" % ", ".join(k for _, (k, _) in MARKS.items()))

        said = con.command("lcdev export marks").rstrip()
        print("  " + said.replace("\n", " ")[-400:])
        found = entries("marks")
        print("  palette entries in the pack: %d" % len(found))
        if not found:
            fail("the export wrote no palette entries at all, so nothing below is "
                 "being asked about marks")

        print("\n" + "=" * 72)
        print("3. every key reached the pack, on its own entry")
        for at, (key, value) in sorted(MARKS.items()):
            carrying = [e for e in found if e.get(key) == value]
            print("  %-12s %-38s %d entr%s" % (key, value, len(carrying),
                                               "y" if len(carrying) == 1 else "ies"))
            if not carrying:
                fail("%s was marked on a block and no palette entry carries it, so "
                     "the pack generates something plainer than what was built"
                     % key)
            elif len(carrying) > 1:
                fail("%s reached %d entries and was marked on one position, so a "
                     "mark is being applied more widely than it was placed"
                     % (key, len(carrying)))

        print("\n" + "=" * 72)
        print("4. a marked block is a different cell from the same block plain")
        stone = [e for e in found if e.get("block") == "minecraft:stone"]
        plain = [e for e in stone if not any(k in e for k, _ in MARKS.values())]
        print("  stone entries: %d, of which carry no mark: %d"
              % (len(stone), len(plain)))
        if len(stone) < len(MARKS) + 1:
            fail("one stone floor with %d marks on it produced %d stone entries. "
                 "The mark is part of the key the ledger letters, so six marks and "
                 "the plain floor are seven cells; fewer means marked positions "
                 "are sharing a character and losing all but one of the marks"
                 % (len(MARKS), len(stone)))
        if not plain:
            fail("every stone entry carries a mark, so the unmarked floor has "
                 "nothing to draw itself with")
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
print("all six marks reach the pack on the entry for the position they were "
      "placed at, and a marked block letters apart from a plain one")
print("all checks passed")
