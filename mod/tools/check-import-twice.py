#!/usr/bin/env python3
"""Import one city, then another. The first must not be left lying around.

    python mod/tools/check-import-twice.py

Needs the wiki's test rig, the same way the other server checks do.

An import fills the plots the pack it read needs and leaves every other plot alone,
which is right: somebody may have built by hand on the ones it did not touch. What
is not right is that the plots the *previous* import filled keep their blocks and
their settings, so the workshop ends up holding two cities at once and the next
export writes both of them into one pack without saying so.

The second pack here is smaller than the first on purpose. Lost Cities' own pack
fills 42 plots; this one fills one. Everything in the gap is the bug.

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
DEVTOOL = os.path.join(WORLD, "lostcitiesdevtool")
SETTINGS = os.path.join(DEVTOOL, "plots")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
BACKUPS = os.path.join(SERVER, "config", "lostcitiesdevtool", "backups")
NS = "tiny"

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
    """The smallest pack that imports: one building, on one plot."""
    data = os.path.join(root, "data", NS, "lostcities")
    layer = ["#" * 16 for _ in range(16)]
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
        "palettes/main": {"palette": [{"char": "#",
                                       "block": "minecraft:gold_block"}]},
        "buildings/tower": {
            "refpalette": NS + ":main", "filler": "#",
            "minfloors": 0, "maxfloors": 0, "mincellars": 0, "maxcellars": 0,
            "overrideFloors": True,
            "parts": [{"part": NS + ":floor", "floor": 0}],
        },
        "parts/floor": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                        "slices": [layer for _ in range(6)]},
    }
    for name, body in assets.items():
        path = os.path.join(data, *name.split("/")) + ".json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write(
            json.dumps(body, indent=2) + "\n")
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "tiny"}}, indent=2))


def settings_written():
    """Plots holding settings, not counting the front desk.

    `core` is the pack's own identity, its namespace and name, which belongs to
    whoever is building rather than to any city they imported. A wipe keeps it and
    says so, so counting it here would make a correct wipe look incomplete.
    """
    out = []
    for base, _, files in os.walk(SETTINGS):
        for f in files:
            if f.endswith(".json5"):
                rel = os.path.relpath(os.path.join(base, f), SETTINGS)
                name = rel[:-len(".json5")].replace(os.sep, "/")
                if name != "core":
                    out.append(name)
    return sorted(out)


for path in (WORLD, EXPORTS, BACKUPS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
write_pack(os.path.join(WORLD, "datapacks", "tinypack"))
print("fresh world, jar installed, a one-plot pack beside Lost Cities' own\n")

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")

        print("=" * 72)
        print(con.command("lcdev import lostcities:standard").rstrip()[-300:])
        first = settings_written()
        print("\n  after importing Lost Cities' own pack: %d plots" % len(first))
        if len(first) < 10:
            fail("the first import filled only %d plots, so this check is not "
                 "testing what it claims" % len(first))

        print("\n" + "=" * 72)
        said = con.command("lcdev import %s:main" % NS).rstrip()
        print(said[-600:])
        second = settings_written()
        leftover = [p for p in second if p in first]
        print("\n  after importing the one-plot pack: %d plots" % len(second))
        print("  plots still holding the first city: %d" % len(leftover))

        # Leaving other plots alone is deliberate: an import has no business
        # deleting what somebody built by hand. Leaving them alone in silence is
        # the bug, because the next export writes them out as well.
        warned = "already hold something" in said
        print("  the import said so: %s" % ("yes" if warned else "NO"))
        if leftover and not warned:
            fail("%d plots still hold the first city and the import said nothing"
                 % len(leftover))

        print("\n" + "=" * 72)
        print("clearing, which has to be asked for twice")
        dry = con.command("lcdev workshop clear").rstrip()
        print(dry[-320:])
        still = settings_written()
        print("\n  plots after the unconfirmed clear: %d" % len(still))
        if len(still) != len(second):
            fail("an unconfirmed clear removed something")
        if "confirm" not in dry:
            fail("the unconfirmed clear did not say how to confirm")

        done = con.command("lcdev workshop clear confirm").rstrip()
        print(done[-320:])
        after = settings_written()
        print("\n  plots after the confirmed clear: %d" % len(after))
        if after:
            fail("%d plots survived a confirmed clear" % len(after))

        packs = sorted(glob.glob(os.path.join(BACKUPS, "*", "pack.mcmeta")))
        print("  backup packs written: %d" % len(packs))
        if not packs:
            fail("a confirmed clear destroyed the workshop without a backup")
        else:
            parts = glob.glob(os.path.join(os.path.dirname(packs[0]), "data", "*",
                                           "lostcities", "parts", "*.json*"))
            print("  parts in the backup: %d" % len(parts))
            if len(parts) < 10:
                fail("the backup holds %d parts, so it is not the workshop that "
                     "was cleared" % len(parts))

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
