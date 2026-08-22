#!/usr/bin/env python3
"""How long a command takes when a client is asking on every keystroke.

    python mod/tools/check-suggest-speed.py

Needs the wiki's test rig, the same way the other server checks do.

Tab completion is not a normal command. The client asks the server for suggestions
after every character typed, and it asks again on backspace, so anything the
suggestion provider does happens tens of times while somebody types one argument. A
provider that reads every asset the server has loaded is doing that work tens of
times.

RCON cannot ask for suggestions, so this measures the commands that run the same
work in their own body: `/lcdev import` with no argument lists the world styles, the
same call its suggestion provider makes. A command that touches no assets is timed
beside it, so the number is the asset work rather than the round trip.

The budget is what a person notices. A suggestion that takes longer than about 50 ms
is visible as lag while typing, and a keystroke is worth far less than that.
"""
import glob
import io
import os
import re
import shutil
import statistics
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
WORLD = os.path.join(SERVER, "world")

# What a suggestion may cost before a person feels it while typing.
BUDGET_MS = 50
RUNS = 40

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


def timed(con, command, runs=RUNS):
    """Median milliseconds, after a warm-up that is thrown away."""
    con.command(command)
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        con.command(command)
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples), min(samples), max(samples)


def write_bulk(root, parts):
    """A datapack of many small assets, standing in for a real modpack.

    Lost Cities ships 311 of its own. A pack on top of that is ordinary and several
    is not unusual, so the interesting question is not what one pack costs but
    whether the cost grows with how many are installed.
    """
    import json
    base = os.path.join(root, "data", "bulk", "lostcities")
    data = os.path.join(base, "parts")
    os.makedirs(data, exist_ok=True)
    os.makedirs(os.path.join(base, "palettes"), exist_ok=True)
    # A palette the parts can actually resolve through. Without it every part is
    # unreadable, which is a different measurement and a much noisier one.
    io.open(os.path.join(base, "palettes", "main.json"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"palette": [{"char": "#", "block": "minecraft:stone"}]}) + "\n")
    layer = ["#" * 16 for _ in range(16)]
    text = json.dumps({"xsize": 16, "zsize": 16, "refpalette": "bulk:main",
                       "slices": [layer for _ in range(6)]}) + "\n"
    for i in range(parts):
        io.open(os.path.join(data, "p%04d.json" % i), "w", encoding="utf-8",
                newline="\n").write(text)
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "bulk"}}))


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
shutil.copy(JAR, dest)
BULK = 600
write_bulk(os.path.join(WORLD, "datapacks", "bulkpack"), BULK)
print("fresh world, jar installed, and a datapack of %d extra parts beside Lost "
      "Cities' own 311\n" % BULK)

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")

        print("=" * 72)
        print("what a suggestion costs, median of %d" % RUNS)
        print("=" * 72)

        # The floor. This touches no assets, so it is the round trip and nothing
        # else, and every other number is only meaningful against it.
        floor_ms, _, _ = timed(con, "lcdev workshop rows")
        print("  %-42s %7.1f ms   (the round trip alone)"
              % ("workshop rows, no assets read", floor_ms))

        # Each of these runs, in its own body, the work a suggestion provider does
        # per keystroke. `import` lists the world styles, which is what completes
        # `/lcdev import <name>`. `block` walks every named asset, which is what
        # completes `/lcdev in <asset>`.
        cases = [
            ("import, lists every world style", "lcdev import"),
            ("block, walks every named asset", "lcdev block minecraft:gold_block"),
            ("char, the same walk by character", "lcdev char #"),
            ("key, reads the profile key table", "lcdev key cityChance"),
        ]
        results = {}
        for label, command in cases:
            median, low, high = timed(con, command)
            over = median - floor_ms
            results[command] = over
            print("  %-42s %7.1f ms   %+.1f over the floor  (%.0f to %.0f)"
                  % (label, median, over, low, high))

        print("\n" + "=" * 72)
        for command, over in results.items():
            if over > BUDGET_MS:
                fail("`%s` spends %.0f ms above the round trip, and a client asks "
                     "for suggestions on every keystroke" % (command, over))
        if not failures:
            print("every suggestion path is inside the %d ms budget" % BUDGET_MS)

        # The cost of caching, and the thing that matters more than the speed.
        # A cache that survives a datapack reload would answer with assets that no
        # longer exist, which is a worse fault than the lag it was fixing.
        print("\n" + "=" * 72)
        print("the cache has to notice a reload")
        before = con.command("lcdev import")
        print("  world styles before: %d"
              % sum(1 for line in before.splitlines() if ":" in line))
        if "bulk:fresh" in before:
            fail("the new world style was there before it was written")

        import json as _json
        added = os.path.join(WORLD, "datapacks", "bulkpack", "data", "bulk",
                             "lostcities", "worldstyles")
        os.makedirs(added, exist_ok=True)
        io.open(os.path.join(added, "fresh.json"), "w", encoding="utf-8",
                newline="\n").write(_json.dumps(
                    {"outsidestyle": "bulk:outside", "citystyles": []}) + "\n")
        con.command("reload")
        after = con.command("lcdev import")
        print("  bulk:fresh visible after /reload: %s"
              % ("yes" if "bulk:fresh" in after else "NO"))
        if "bulk:fresh" not in after:
            fail("a world style added and reloaded was not picked up, so the cache "
                 "outlived the datapack load that should have replaced it")

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
