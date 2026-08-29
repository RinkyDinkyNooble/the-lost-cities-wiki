#!/usr/bin/env python3
"""Clearing the workshop has to leave nothing, and has to stay possible.

    python mod/tools/check-clear.py

Needs the wiki's test rig, the same way the other server checks do.

Two faults reported against 1.3.0, both of which end with a workshop somebody
cannot empty.

**Blocks outlive their settings.** A wipe reads each plot's settings to decide how
far up to clear, then deletes those settings. Anything standing above that ceiling
survives with nothing left pointing at it, so the next `clear` reports an empty
workshop while the tops of buildings float over bare plots. `check-import-twice.py`
counts settings files and therefore passes while this is happening, which is how it
shipped: the count it asserts on is the count the bug leaves at zero.

**One short name, two plots.** An asset is named by its plot's `name` setting, and
the import takes that from the asset's name with the namespace cut off. Two packs
that both call a building `tower` therefore land on two plots claiming one file, and
the export refuses. A backup is an export, and a wipe insists on a backup, so the
refusal makes the workshop unclearable by the ordinary route.

The pack is written here rather than exported by a first server, so the whole check
is one boot.
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
SETTINGS = os.path.join(WORLD, "lostcitiesdevtool", "plots")
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


def write_pack(root):
    """One city style, two buildings, one short name.

    `nsa:tower` and `nsb:tower` are different assets in different namespaces, which
    is ordinary in a modpack: two authors both reach for the obvious word. The
    import cuts the namespace off, so both plots end up named `tower`.
    """
    layer = ["#" * 16 for _ in range(16)]
    common = {
        "styles/main": {"randompalettes": [[{"factor": 1.0,
                                             "palette": "nsa:main"}]]},
        "palettes/main": {"palette": [{"char": "#",
                                       "block": "minecraft:gold_block"}]},
    }
    packs = {
        "nsa": dict(common, **{
            "worldstyles/main": {
                "outsidestyle": "nsa:outside",
                "citystyles": [{"factor": 1.0, "citystyle": "nsa:city"}],
            },
            "citystyles/city": {
                "style": "nsa:main",
                "streetblocks": {"border": "y", "wall": "w", "street": "S",
                                 "streetbase": "b", "streetvariant": "B",
                                 "width": 8},
                "selectors": {"buildings": [
                    {"factor": 1.0, "value": "nsa:tower"},
                    {"factor": 1.0, "value": "nsb:tower"},
                ]},
            },
            "styles/outside": {"randompalettes": [[{"factor": 1.0,
                                                    "palette": "nsa:main"}]]},
            "buildings/tower": {
                "refpalette": "nsa:main", "filler": "#",
                "minfloors": 0, "maxfloors": 0, "mincellars": 0, "maxcellars": 0,
                "overrideFloors": True,
                "parts": [{"part": "nsa:floor", "floor": 0}],
            },
            "parts/floor": {"xsize": 16, "zsize": 16, "refpalette": "nsa:main",
                            "slices": [layer for _ in range(6)]},
        }),
        "nsb": {
            "buildings/tower": {
                "refpalette": "nsa:main", "filler": "#",
                "minfloors": 0, "maxfloors": 0, "mincellars": 0, "maxcellars": 0,
                "overrideFloors": True,
                "parts": [{"part": "nsb:floor", "floor": 0}],
            },
            "parts/floor": {"xsize": 16, "zsize": 16, "refpalette": "nsa:main",
                            "slices": [layer for _ in range(6)]},
        },
    }
    for ns, assets in packs.items():
        data = os.path.join(root, "data", ns, "lostcities")
        for name, body in assets.items():
            path = os.path.join(data, *name.split("/")) + ".json"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            io.open(path, "w", encoding="utf-8", newline="\n").write(
                json.dumps(body, indent=2) + "\n")
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "clearcheck"}},
                indent=2))


def settings_written():
    out = []
    for base, _, files in os.walk(SETTINGS):
        for f in files:
            if f.endswith(".json5"):
                rel = os.path.relpath(os.path.join(base, f), SETTINGS)
                name = rel[:-len(".json5")].replace(os.sep, "/")
                if name != "core":
                    out.append(name)
    return sorted(out)


def solid_in(con, plot, top):
    """Non-air blocks standing on one plot, from its floor up to `top`.

    Counted with a filtered clone, which reports how many it moved, so the answer
    comes from the world rather than from anything the mod chose to say.
    """
    x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
    x1 = x + plot["width"] * 16 - 1
    z1 = z + plot["height"] * 16 - 1
    con.command("execute in %s run forceload add %d %d %d %d"
                % (WORKSHOP, x, z, x1, z1))
    con.command("execute in %s run forceload add 6000 6000 6031 6031" % WORKSHOP)
    total = 0
    for y0 in range(BASE, top, 30):
        y1 = min(y0 + 29, top)
        reply = con.command(
            "execute in %s run clone %d %d %d %d %d %d 6000 %d 6000 filtered "
            "minecraft:air" % (WORKSHOP, x, y0, z, x1, y1, z1, y0))
        m = re.search(r"([0-9]+) block", reply)
        air = int(m.group(1)) if m else 0
        volume = (x1 - x + 1) * (z1 - z + 1) * (y1 - y0 + 1)
        total += volume - air
    return total


for path in (WORLD, EXPORTS, BACKUPS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
write_pack(os.path.join(WORLD, "datapacks", "clearpack"))
print("fresh world, jar installed, a two-namespace pack beside Lost Cities' own")
print("using %s\n" % os.path.basename(JAR))

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")

        print("=" * 72)
        print("one city style naming nsa:tower and nsb:tower")
        said = con.command("lcdev import nsa:main").rstrip()
        print(said[-400:])
        written = settings_written()
        towers = [p for p in written if p.startswith("building/1x1/")]
        print("\n  building plots filled: %d" % len(towers))
        if len(towers) < 2:
            fail("the pack names two buildings and only %d plot was filled, so "
                 "this check is not testing what it claims" % len(towers))

        names = {}
        for p in towers:
            body = io.open(os.path.join(SETTINGS, *p.split("/")) + ".json5",
                           encoding="utf-8").read()
            m = re.search(r'"name"\s*:\s*"([^"]+)"', body)
            names[p] = m.group(1) if m else "?"
        for p in sorted(names):
            print("    %-20s name: %s" % (p, names[p]))
        if len(set(names.values())) < len(names):
            fail("two plots were given the same name, so the export cannot write "
                 "both: %s" % sorted(names.values()))

        print("\n" + "=" * 72)
        print("something taller than the settings describe")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
        sample = towers[0]
        p = plots[sample]
        high = BASE + 120
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, p["chunkX"] * 16, p["chunkZ"] * 16,
                       p["chunkX"] * 16, p["chunkZ"] * 16))
        con.command("execute in %s run setblock %d %d %d minecraft:diamond_block"
                    % (WORKSHOP, p["chunkX"] * 16 + 1, high, p["chunkZ"] * 16 + 1))
        print("  a diamond block at y=%d on %s, well above its floors"
              % (high, sample))

        before = solid_in(con, p, high + 2)
        print("  solid blocks on %s: %d" % (sample, before))

        print("\n" + "=" * 72)
        print("clearing")
        done = con.command("lcdev workshop clear confirm").rstrip()
        print(done[-400:])
        if "backup failed" in done or "Nothing was cleared" in done:
            fail("a confirmed clear refused to run: the backup could not be "
                 "written, which leaves no supported way to empty the workshop")
            done = con.command("lcdev workshop clear confirm anyway").rstrip()
            print("\n  falling back to `anyway`:")
            print(done[-300:])

        packs = sorted(glob.glob(os.path.join(BACKUPS, "*", "pack.mcmeta")))
        print("\n  backup packs written: %d" % len(packs))

        after_settings = settings_written()
        print("  plots still holding settings: %d" % len(after_settings))
        if after_settings:
            fail("%d plots survived a confirmed clear" % len(after_settings))

        after = solid_in(con, p, high + 2)
        print("  solid blocks still standing on %s: %d" % (sample, after))
        if after:
            fail("a confirmed clear left %d blocks standing on %s with no "
                 "settings pointing at them" % (after, sample))

        print("\n" + "=" * 72)
        print("and the workshop has to know they are there")
        again = con.command("lcdev workshop clear").rstrip()
        print(again[-300:])
        if after and "already empty" in again:
            fail("the workshop reports itself empty while %d blocks stand on %s"
                 % (after, sample))
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
print("a confirmed clear leaves nothing standing, and two packs sharing a "
      "short name do not stop it")
print("all checks passed")
