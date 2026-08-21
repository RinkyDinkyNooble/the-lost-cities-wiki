#!/usr/bin/env python3
"""Acceptance test for the compiler: build something, export it, then generate it.

    python mod/tools/check-export.py

Needs the wiki's test rig installed, the same way `check-workshop.py` does.

Two halves, and the second is the one that matters.

**Export.** Fill two plots with real blocks, set their settings, run the export, and
read what was written: the palette, the parts and their slice shape, the building
that references them, the city style, the world style and the profile.

**Generate.** Take the pack the compiler just wrote, install it as an ordinary
datapack, point a dimension at the profile beside it, restart, and count the blocks
that come out of the ground. Anything short of that only proves the compiler emits
plausible JSON, and plausible JSON is exactly what a format this fiddly produces
right up until it does not load.

The world is wiped first and the jar removed afterwards, so the rig's baseline stays
what the wiki's published results were produced on.
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
WORKSHOP = "lostcitiesdevtool:workshop"
CITY = "lostcities:lostcity"
PLOTS = os.path.join(SERVER, "world", "lostcitiesdevtool", "plots.json")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
PACK = "testpack"
NS = "mypack"
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


def stop(proc):
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()


def asset(*parts):
    return os.path.join(EXPORTS, PACK, "data", NS, "lostcities", *parts)


# --------------------------------------------------------------- half one, export

dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
for path in (os.path.join(SERVER, "world"), EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
shutil.copy(JAR, dest)
print("fresh world, jar installed\n")

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = json.load(io.open(PLOTS, encoding="utf-8"))["plots"]
        by_id = {p["id"]: p for p in plots}

        def at(plot_id, dx=8, dz=8):
            p = by_id[plot_id]
            return p["chunkX"] * 16 + dx, p["chunkZ"] * 16 + dz

        def run(plot_id, command):
            x, z = at(plot_id)
            return con.command("execute in %s positioned %d.0 %d.0 %d.0 run %s"
                               % (WORKSHOP, x, BASE, z, command))

        # The pack's own settings. cityChance and the highway mask are set through
        # the raw profile object, because a world of buildings needs both: at
        # cityChance 1.0 the highway network claims chunk after chunk and refuses
        # every building, with nothing logged to say why.
        for cmd in ("lcdev plot set namespace " + NS,
                    "lcdev plot set worldStyle main",
                    "lcdev plot set packName Export test"):
            run("core", cmd)
        core_file = os.path.join(SERVER, "world", "lostcitiesdevtool", "plots",
                                 "core.json5")
        core = io.open(core_file, encoding="utf-8").read()
        core = core.rstrip()[:-1] + """
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
"""
        io.open(core_file, "w", encoding="utf-8", newline="\n").write(core)

        # A building: gold on the ground floor, diamond on the floor above.
        b = by_id["building/1x1/0"]
        bx, bz = b["chunkX"] * 16, b["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, bx, bz, bx + 15, bz + 15))
        con.command("execute in %s run fill %d %d %d %d %d %d minecraft:gold_block"
                    % (WORKSHOP, bx, BASE, bz, bx + 15, BASE + 5, bz + 15))
        con.command("execute in %s run fill %d %d %d %d %d %d minecraft:diamond_block"
                    % (WORKSHOP, bx, BASE + 6, bz, bx + 15, BASE + 11, bz + 15))
        for cmd in ("lcdev plot set name tower",
                    "lcdev plot set floors 1",
                    "lcdev plot set cellars 0",
                    "lcdev plot set citystyles mycity",
                    "lcdev plot set factor 1.0"):
            run("building/1x1/0", cmd)

        # A street, so the city style has roads of ours as well as buildings.
        s = by_id["street/all/0"]
        sx, sz = s["chunkX"] * 16, s["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, sx, sz, sx + 15, sz + 15))
        con.command("execute in %s run fill %d %d %d %d %d %d minecraft:stone_bricks"
                    % (WORKSHOP, sx, BASE, sz, sx + 15, BASE, sz + 15))
        for cmd in ("lcdev plot set name road_all",
                    "lcdev plot set height 6",
                    "lcdev plot set citystyles mycity"):
            run("street/all/0", cmd)

        print("=" * 72)
        print(con.command("lcdev export " + PACK).rstrip())
        con.command("stop")
finally:
    stop(proc)

print("\n" + "=" * 72)
print("what the compiler wrote")

expect_files = ["palettes/main.json", "parts/tower_f0.json", "parts/tower_f1.json",
                "parts/road_all.json", "buildings/tower.json",
                "citystyles/mycity.json", "worldstyles/main.json",
                "styles/main.json", "styles/outside.json"]
for rel in expect_files:
    if os.path.isfile(asset(*rel.split("/"))):
        print("  %-28s written" % rel)
    else:
        fail("%s was not written" % rel)

if os.path.isfile(asset("parts", "tower_f0.json")):
    part = json.load(io.open(asset("parts", "tower_f0.json"), encoding="utf-8"))
    slices = part["slices"]
    shape_ok = (len(slices) == 6 and all(len(layer) == 16 for layer in slices)
                and all(len(row) == 16 for layer in slices for row in layer))
    print("  %-28s %s" % ("tower_f0 shape",
                          "6 layers of 16x16" if shape_ok
                          else "WRONG: %d layers" % len(slices)))
    if not shape_ok:
        fail("the ground floor part is not 16x16x6")
    solid = len({c for layer in slices for row in layer for c in row}) == 1
    print("  %-28s %s" % ("one character throughout",
                          "yes" if solid else "no, which the fill did not ask for"))
    if not solid:
        fail("a solid fill produced more than one character")

if os.path.isfile(asset("palettes", "main.json")):
    pal = json.load(io.open(asset("palettes", "main.json"), encoding="utf-8"))
    blocks = {e.get("block") for e in pal["palette"]}
    want = {"minecraft:air", "minecraft:gold_block", "minecraft:diamond_block",
            "minecraft:stone_bricks"}
    missing = want - blocks
    print("  %-28s %d entries, %s" % ("palette", len(pal["palette"]),
                                      "all four blocks present" if not missing
                                      else "MISSING " + str(missing)))
    if missing:
        fail("the palette is missing %s" % missing)
    letters = [e["char"] for e in pal["palette"] if e.get("block") != "minecraft:air"]
    safe = all(not c.isalnum() or ord(c) > 0x300 for c in letters)
    print("  %-28s %s" % ("characters avoid the mod's",
                          "yes" if safe else "NO: " + "".join(letters)))
    if not safe:
        fail("a character was taken from the range Lost Cities uses")

if os.path.isfile(asset("buildings", "tower.json")):
    b = json.load(io.open(asset("buildings", "tower.json"), encoding="utf-8"))
    refs = [p["part"] for p in b["parts"]]
    ok = refs == [NS + ":tower_f0", NS + ":tower_f1"]
    print("  %-28s %s" % ("building references", refs if ok else "WRONG: %s" % refs))
    if not ok:
        fail("the building does not reference its two floors")

if os.path.isfile(asset("citystyles", "mycity.json")):
    c = json.load(io.open(asset("citystyles", "mycity.json"), encoding="utf-8"))
    has_building = any(e["value"] == NS + ":tower"
                       for e in c.get("selectors", {}).get("buildings", []))
    has_street = NS + ":road_all" in str(c.get("streetblocks", {}))
    print("  %-28s %s" % ("city style wiring",
                          "building and street both in"
                          if has_building and has_street else "INCOMPLETE"))
    if not (has_building and has_street):
        fail("the city style does not reference what the plots produced")

profile = os.path.join(EXPORTS, PACK, "profile", PACK + ".json")
if os.path.isfile(profile):
    prof = json.load(io.open(profile, encoding="utf-8"))
    # Each key has to land in the section the mod registered it under. cityChance is
    # in `cities`, not `lostcity`, and a key in the wrong section is never read and
    # never complained about: the setting just silently does nothing.
    ok = (prof.get("lostcity", {}).get("worldStyle") == NS + ":main"
          and prof.get("cities", {}).get("cityChance") == 1.0
          and prof.get("explosions", {}).get("explosionChance") == 0.0
          and "cityChance" not in prof.get("lostcity", {}))
    print("  %-28s %s" % ("profile sections",
                          "worldStyle, cities and explosions each in place" if ok
                          else "WRONG: " + json.dumps(prof)[:80]))
    if not ok:
        fail("profile keys did not land in their own sections")
else:
    fail("no profile was written")

# ------------------------------------------------------ half two, generate it

print("\n" + "=" * 72)
print("generating a world from the pack the compiler wrote")

src = os.path.join(EXPORTS, PACK)
if not os.path.isdir(src):
    fail("there is no pack to generate from")
else:
    world = os.path.join(SERVER, "world")
    shutil.rmtree(world)
    packs = os.path.join(world, "datapacks", PACK)
    os.makedirs(packs)
    shutil.copytree(os.path.join(src, "data"), os.path.join(packs, "data"))
    shutil.copy(os.path.join(src, "pack.mcmeta"), packs)
    profiles = os.path.join(SERVER, "config", "lostcities", "profiles")
    os.makedirs(profiles, exist_ok=True)
    shutil.copy(profile, profiles)
    io.open(os.path.join(SERVER, "config", "lostcities", "common.toml"), "w",
            encoding="utf-8", newline="\n").write(
        '[profiles]\n\tdimensionsWithProfiles = ["%s=%s"]\n' % (CITY, PACK))

    proc = boot()
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("execute in %s run forceload add 112 112 175 175" % CITY)
            con.command("execute in %s run forceload add 992 992 1023 1023" % CITY)
            time.sleep(30)
            total = 0
            for cx in range(7, 11):
                for cz in range(7, 11):
                    x, z = cx * 16, cz * 16
                    reply = con.command(
                        "execute in %s run clone %d 40 %d %d 167 %d 992 40 992 "
                        "filtered minecraft:gold_block" % (CITY, x, z, x + 15, z + 15))
                    m = re.search(r"([0-9]+) block", reply)
                    total += int(m.group(1)) if m else 0
            print("  gold blocks in the generated city: %d" % total)
            if total == 0:
                fail("the exported pack generated no buildings")
            reply = con.command("execute in %s run clone 128 40 128 143 167 143 "
                                "992 40 992 filtered minecraft:stone_bricks" % CITY)
            m = re.search(r"([0-9]+) block", reply)
            print("  street blocks in one chunk: %s" % (m.group(1) if m else 0))
            con.command("stop")
    finally:
        stop(proc)

if os.path.isfile(dest):
    os.remove(dest)
print("\nremoved the jar, rig baseline is clean again")
print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
