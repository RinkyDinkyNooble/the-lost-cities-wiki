#!/usr/bin/env python3
"""What a block is carrying reaches the pack, and only the parts you asked for.

    python mod/tools/check-tag-export.py

Needs the wiki's test rig, the same way the other server checks do.

`check-tags.py` proves the filter decides correctly. This proves the filter is
actually consulted, that the setting reaches it from the place somebody would set
it, and that the flag turns the whole thing off. Those are three different failures
and none of them are visible in the filter's own unit cases.

Four things, in one boot:

  * a chest built in the workshop exports carrying its inventory, because that is
    what "read the NBT" means and a furnished building is a real thing to want
  * `tagkeys` naming keys plainly keeps only those, so the same chest can ship its
    name and leave its contents behind
  * `!` drops a key and keeps the rest, which is only separable from the case above
    because the chest carries a third key neither of them names the same way
  * `/lcdev export <name> notags` writes a pack with no tag anywhere

The chest is the case worth testing rather than a command block: a command block's
tag is small and wanted, while a chest's is large and mostly accidental, which is
the situation the filter exists for.
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
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
BACKUPS = os.path.join(SERVER, "config", "lostcitiesdevtool", "backups")
BASE = -63

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


def entries(export):
    """Every palette entry the pack wrote, wherever the palette ended up."""
    out = []
    for path in glob.glob(os.path.join(EXPORTS, export, "data", "*", "lostcities",
                                       "**", "*.json*"), recursive=True):
        text = io.open(path, encoding="utf-8").read()
        try:
            body = json.loads(text)
        except ValueError:
            # A json5 pack is not what this fixture writes, and guessing at one
            # here would hide a real change in what the export produces.
            raise SystemExit("%s is not plain JSON, which this check assumes"
                             % os.path.relpath(path))
        palette = body.get("palette")
        if isinstance(palette, dict):
            palette = palette.get("palette")
        if isinstance(palette, list):
            out.extend(e for e in palette if isinstance(e, dict))
    return out


def chest_tag(export):
    """The tag on the entry that is a chest, or None."""
    for e in entries(export):
        if "chest" in str(e.get("block", "")) and "tag" in e:
            return e["tag"]
    return None


def has_any_tag(export):
    return any("tag" in e for e in entries(export))


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
        plot = plots["selector/parks/0"]
        x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))

        print("=" * 72)
        print("a park plot with a floor and one furnished, named chest")
        con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone"
                    % (WORKSHOP, x, BASE, z, x + 15, BASE, z + 15))
        # Three keys on purpose. With only CustomName and Items, keeping CustomName
        # and dropping Items give the same answer, and the check could not tell an
        # export that honoured `!` from one that ignored it and treated every entry
        # as a keep-list. Lock is the third, and it is what separates them.
        con.command(
            'execute in %s run setblock %d %d %d minecraft:chest{CustomName:'
            '\'{"text":"crate"}\',Lock:"opensesame",'
            'Items:[{Slot:0b,id:"minecraft:diamond",Count:7b}]}'
            % (WORKSHOP, x + 4, BASE, z + 4))
        con.command("execute in %s positioned %d 10 %d run lcdev plot set name yard"
                    % (WORKSHOP, x + 8, z + 8))

        print("\n" + "=" * 72)
        print("1. by default, what the chest carries reaches the pack")
        con.command("lcdev export t1")
        tag = chest_tag("t1")
        print("  chest tag: %s" % json.dumps(tag)[:120])
        if tag is None:
            fail("the chest exported with no tag at all, so nothing below this "
                 "check is testing what it claims")
        else:
            for key in ("Items", "CustomName", "Lock"):
                if key not in tag:
                    fail("the chest's %s was not exported by default" % key)

        print("\n" + "=" * 72)
        print("2. tagkeys naming keys plainly keeps only those")
        con.command("execute in %s positioned %d 10 %d run lcdev plot set tagkeys "
                    "CustomName" % (WORKSHOP, x + 8, z + 8))
        con.command("lcdev export t2")
        tag = chest_tag("t2")
        print("  chest tag: %s" % json.dumps(tag))
        if tag is None:
            fail("keeping CustomName dropped the whole tag")
        else:
            # Lock is the one that separates this from the next case: a keep-list
            # naming CustomName has to lose it, and a drop-list naming Items has to
            # keep it.
            for key in ("Items", "Lock"):
                if key in tag:
                    fail("a keep-list naming only CustomName still exported %s"
                         % key)
            if "CustomName" not in tag:
                fail("a keep-list naming CustomName did not export CustomName")

        print("\n" + "=" * 72)
        print("3. a ! entry drops one key and keeps the rest")
        con.command("execute in %s positioned %d 10 %d run lcdev plot set tagkeys "
                    "!Items" % (WORKSHOP, x + 8, z + 8))
        con.command("lcdev export t3")
        tag = chest_tag("t3")
        print("  chest tag: %s" % json.dumps(tag))
        if tag is None:
            fail("dropping Items dropped the whole tag")
        else:
            if "Items" in tag:
                fail("!Items still exported Items")
            for key in ("CustomName", "Lock"):
                if key not in tag:
                    fail("!Items also lost %s, which it did not name" % key)

        print("\n" + "=" * 72)
        print("4. notags writes a pack with no tag anywhere")
        con.command("execute in %s positioned %d 10 %d run lcdev plot clear tagkeys"
                    % (WORKSHOP, x + 8, z + 8))
        said = con.command("lcdev export t4 notags").rstrip()
        print(said[-200:])
        count = sum(1 for e in entries("t4") if "tag" in e)
        print("  palette entries carrying a tag: %d" % count)
        if count:
            fail("notags still wrote %d tagged palette entries" % count)
        # And the blocks are still there: notags drops the NBT, not the block.
        blocks = len(entries("t4"))
        print("  palette entries in total: %d" % blocks)
        if blocks < 2:
            fail("notags wrote a pack with %d palette entries, so it dropped the "
                 "blocks rather than only their NBT" % blocks)
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
print("tags reach the pack, tagkeys decides which, and notags turns it off")
print("all checks passed")
