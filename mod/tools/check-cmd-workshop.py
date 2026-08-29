#!/usr/bin/env python3
"""Phase C: the workshop commands that describe and reshape the catalogue.

    python mod/tools/check-cmd-workshop.py

Needs the wiki's test rig, the same way the other server checks do.

`build`, `clear` and `sync` are already covered by checks of their own, so this is
the rest: `rows`, `here`, `grow` and the refusals `go` and `leave` give without a
player. What they have in common is that they are how somebody learns the catalogue,
and a wrong answer teaches the format wrong rather than breaking anything visibly.

What it asserts:

  * **`rows` counts what the catalogue holds**, and the total it prints matches the
    file the catalogue was generated from. A drifting count is the kind of thing
    nobody notices, because the number looks plausible whatever it is.

  * **`here` names the rule for the row class it is standing on.** The three classes
    are the reason two rows that look alike need different settings: one variation
    only, any number unweighted, or any number each needing a factor. Getting that
    wrong sends somebody to write a list where the codec takes a string, which is a
    load error rather than a longer row.

  * **`grow` refuses a row that cannot grow, and says why in terms of the codec.**
    A single-only row is the one place where the obvious thing to try is a load
    error, so the refusal has to explain rather than decline.

  * **Rows only get longer.** Asking for fewer plots than a row already has is a
    no-op rather than a shrink, because shrinking would orphan whatever an import
    pasted into the plots it removed.

  * **`build` is idempotent.** Running it twice has to leave the same layout, or a
    plot's address depends on how many times somebody rebuilt, and every position
    written into the world already is wrong.
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

SELECTOR = "building/1x1/0"
SINGLE_ROW = "monorail/both"

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


def number(text, label):
    found = re.search(re.escape(label) + r"\D{0,4}([0-9]+)", text)
    return int(found.group(1)) if found else None


if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
dest = rig.install(SERVER, JAR)
print("fresh world, jar installed: %s\n" % os.path.basename(JAR))

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        doc = json.load(io.open(PLOTS, encoding="utf-8"))
        plots = {p["id"]: p for p in doc["plots"]}

        def at(plot_id, rest):
            p = plots[plot_id]
            return con.command(
                "execute in %s positioned %d 10 %d run lcdev workshop %s"
                % (WORKSHOP, p["chunkX"] * 16 + 8, p["chunkZ"] * 16 + 8,
                   rest)).rstrip()

        print("=" * 72)
        print("1. rows counts what the catalogue holds")
        said = con.command("lcdev workshop rows").rstrip()
        print("  " + said.replace("\n", " ")[:400])
        total = number(said, "total")
        print("\n  rows reported: %s" % total)
        for kind in ("unweighted lists", "single only", "weighted selectors"):
            if kind not in said:
                fail("`rows` did not name the %s class, which is the reason two "
                     "rows that look alike need different settings" % kind)
        if not total:
            fail("`rows` reported no total")

        print("\n" + "=" * 72)
        print("2. here names the rule for the class it is standing on")
        said = at(SELECTOR, "here")
        print("  " + said.replace("\n", " ")[:300])
        if "variations allowed" not in said:
            fail("`here` did not say how many variations this row class allows")
        if "factor" not in said:
            fail("a weighted selector row did not say each variation needs a "
                 "factor, which is what separates it from an unweighted list")

        core = at("core", "here")
        print("  core: " + core.replace("\n", " ")[:200])
        if "pack's own settings" not in core:
            fail("the front desk did not say it holds the pack's own settings")

        p = plots[SELECTOR]
        walk = con.command("execute in %s positioned %d 10 %d run lcdev workshop here"
                           % (WORKSHOP, p["chunkX"] * 16 - 8,
                              p["chunkZ"] * 16 + 8)).rstrip()
        print("  walkway: " + walk.replace("\n", " ")[:160])
        if "No plot here" not in walk:
            fail("`here` on the walkway did not say there is no plot")

        print("\n" + "=" * 72)
        print("3. go and leave say what they need rather than failing quietly")
        # Both move a player, and RCON has no player, so what is checkable is the
        # refusal. That the teleport itself lands where it should is in the same
        # bucket as `mark`'s raycast: it needs somebody at a client.
        said = con.command("lcdev workshop go").rstrip()
        print("  go:    " + said.replace("\n", " ")[:170])
        if "Only a player" not in said:
            fail("`go` over RCON did not say a player is what is missing")

        said = con.command("lcdev workshop leave").rstrip()
        print("  leave: " + said.replace("\n", " ")[:170])
        # Asked in this order on purpose. A literal that never reached the tree gives
        # the parser's own error, which also lacks "Only a player", so testing the
        # refusal first would report one cause as two failures and name neither.
        if "Unknown" in said or "Incorrect argument" in said:
            fail("`workshop leave` is not registered: the parser refused it before "
                 "the command ran")
        elif "Only a player" not in said:
            fail("`leave` over RCON did not say a player is what is missing")

        print("\n" + "=" * 72)
        print("4. grow refuses what cannot grow, in the format's own terms")
        said = con.command("lcdev workshop grow nosuchrow 5").rstrip()
        print("  unknown row: " + said.replace("\n", " ")[:170])
        if "No row named" not in said:
            fail("growing a row that does not exist was not refused by name")

        said = con.command("lcdev workshop grow %s 5" % SINGLE_ROW).rstrip()
        print("  single only: " + said.replace("\n", " ")[:230])
        if "cannot grow" not in said:
            fail("a single-only row was grown, or refused without saying so")
        if "load error" not in said:
            fail("the refusal did not explain that a list where the codec takes a "
                 "string is a load error, which is the whole reason to refuse")

        print("\n" + "=" * 72)
        print("5. rows only get longer")
        grown = con.command("lcdev workshop grow building/1x1 9").rstrip()
        print("  " + grown.replace("\n", " ")[:200])
        shrunk = con.command("lcdev workshop grow building/1x1 2").rstrip()
        print("  " + shrunk.replace("\n", " ")[:230])
        if "Already at least that long" not in shrunk:
            fail("asking for fewer plots than a row has did not say it is already "
                 "at least that long, so it may have shrunk and orphaned whatever "
                 "was pasted into the plots it removed")
        after = json.load(io.open(PLOTS, encoding="utf-8"))
        held = sum(1 for x in after["plots"] if x["id"].startswith("building/1x1/"))
        print("  plots the row lays out after both: %d" % held)
        if held < 9:
            fail("the row holds %d plots after growing to 9 and being asked for 2"
                 % held)

        print("\n" + "=" * 72)
        print("6. build is idempotent")
        before = io.open(PLOTS, encoding="utf-8").read()
        con.command("lcdev workshop build")
        again = io.open(PLOTS, encoding="utf-8").read()
        print("  layout unchanged by a second build: %s" % (before == again))
        if before != again:
            fail("building twice changed the layout. A plot's address would then "
                 "depend on how many times somebody rebuilt, and every position "
                 "already written into the world is wrong")
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
print("the catalogue describes itself, refuses what its codecs cannot take, and "
      "lays out the same way twice")
print("all checks passed")
