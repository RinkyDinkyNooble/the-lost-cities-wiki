#!/usr/bin/env python3
"""Two faults reported from the field, and the guards that stop them returning.

    python mod/tools/check-version-and-grow.py

Needs the wiki's test rig, the same way the other server checks do.

Both were found by the author running the built jar, not by this suite, which is
the reason both are checked here now.

**A version on screen that was not the one running.** `/lcdev workshop go` printed
"Workshop version 7.5.4" on a server running Lost Cities 7.5.4, and would have
printed the same on 7.5.5. The number came from `catalogue.json`, which is
generated against one jar at build time. Labelled "version" with no subject it
reads as the mod reporting what it found. The catalogue being older than the
running game is allowed, the range spans five versions; saying so ambiguously is
not.

**A footprint that could not be built by hand.** Multi-building rows past the
generated catalogue were added only when an import walked a pack that held one.
`/lcdev workshop grow multibuilding/11x11 1` answered "No row named
multibuilding/11x11" in a freshly cleared workshop, so the only way to get a plot
for a footprint was to already own a pack containing it. That is backwards for a
tool whose job is authoring.

What it asserts, in one boot:

  1. every place that shows a version names which version it means, and none of
     them shows a bare number that could be read as the running game
  2. the running Lost Cities version is recorded in the world registry beside the
     catalogue's own, because they are two facts
  3. a footprint past the generated catalogue can be grown by hand, in a workshop
     that has never imported anything
  4. it lands as a real plot of the right size, and nothing already laid out moved
  5. it survives a rebuild, and growing it again does not add a second row
  6. a footprint past the sanity ceiling is still refused
  7. an id that is not a footprint at all is still refused

The world is wiped first and the jar removed afterwards, so the rig's baseline
stays what the wiki's published results were produced on.
"""
import glob
import io
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from rcon import Rcon  # noqa: E402
import rig  # noqa: E402
from rig import fail, failures  # noqa: E402

SERVER = rig.SERVER
JAR = rig.jar()
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
MODS = os.path.join(SERVER, "mods")

WANT = (11, 11)
TOOBIG = (65, 1)


def ok(msg):
    print("  ok   " + msg)


def registry():
    return json.load(io.open(PLOTS, encoding="utf-8"))


def coords():
    return {p["id"]: (p["chunkX"], p["chunkZ"]) for p in registry()["plots"]}


def installed_lostcities():
    """What Lost Cities jar the rig actually has, read off the file name.

    The check has to know the answer independently of the mod, or it would be
    asking the thing under test to mark its own work.
    """
    for f in os.listdir(MODS):
        m = re.match(r"lostcities-1\.20-(\d+\.\d+\.\d+)\.jar$", f)
        if m:
            return m.group(1)
    return None


row_id = "multibuilding/%dx%d" % WANT

print("check-version-and-grow: the two faults reported from the field")
print("jar: %s" % os.path.basename(JAR))

if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
rig.install(SERVER, JAR)
running = installed_lostcities()
print("rig runs Lost Cities %s\n" % running)

proc, _ = rig.boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        built = con.command("lcdev workshop build")
        rows_out = con.command("lcdev workshop rows")
        print("=" * 72)
        print(built.rstrip()[:400])
        print("-" * 72)
        print(rows_out.rstrip()[:200])
        print("=" * 72)

        # ---------------------------------------------------- 1. the version line
        #
        # A bare "version <number>" is the exact shape that misled. Every place
        # that shows one has to name which version it is talking about.
        bare = []
        for name, text in (("workshop build", built), ("workshop rows", rows_out)):
            for m in re.finditer(r"version\s+(\d+\.\d+\.\d+)", text):
                bare.append("%s: %s" % (name, m.group(0)))
        if bare:
            fail("a bare version number is still shown, which is what read as the "
                 "running game: %s" % bare)
        else:
            ok("no bare version number is shown")

        for name, text in (("workshop build", built), ("workshop rows", rows_out)):
            if "for Lost Cities" in text:
                ok("%s says which version it means" % name)
            else:
                fail("%s does not name the version's subject: %r"
                     % (name, text.strip()[:120]))

        if running and running in built:
            # The rig runs the version the catalogue was generated from, so no
            # mismatch warning is expected. Printed either way rather than
            # asserted, because the rig's Lost Cities may move.
            print("  --   catalogue and running version agree (%s)" % running)

        # ------------------------------------------------- 2. both, on the record
        reg = registry()
        print("\nregistry versions: catalogue=%r running=%r"
              % (reg.get("catalogueForLostCities"), reg.get("runningLostCities")))
        if reg.get("catalogueForLostCities"):
            ok("the registry records which version the catalogue was built for")
        else:
            fail("the registry has no catalogueForLostCities")
        if reg.get("runningLostCities"):
            ok("the registry records the Lost Cities actually running")
        else:
            fail("the registry has no runningLostCities, so the two facts are "
                 "still indistinguishable on disk")
        if running and reg.get("runningLostCities") \
                and running not in reg["runningLostCities"]:
            fail("the registry says the running version is %r and the rig has %s"
                 % (reg.get("runningLostCities"), running))
        elif running and reg.get("runningLostCities"):
            ok("the recorded running version matches the jar on disk")

        # ------------------------------------------ 3, 4. grow one by hand
        before = coords()
        print("\nplots before growing by hand: %d" % len(before))
        out = con.command("lcdev workshop grow %s 1" % row_id)
        print(out.rstrip()[:600])
        if "No row named" in out:
            fail("%s still cannot be grown by hand, which is the reported fault"
                 % row_id)
        else:
            ok("%s can be grown by hand with nothing imported" % row_id)

        after = coords()
        moved = [p for p, xz in before.items() if p in after and after[p] != xz]
        if moved:
            fail("%d plots moved when the row was added: %s"
                 % (len(moved), moved[:5]))
        else:
            ok("no plot that existed before moved")

        plot = {p["id"]: p for p in registry()["plots"]}.get(row_id + "/0")
        if not plot:
            fail("%s/0 is not in the registry, so the row has no plot" % row_id)
        elif (plot["width"], plot["height"]) != WANT:
            fail("%s/0 is %dx%d, not %dx%d"
                 % (row_id, plot["width"], plot["height"], WANT[0], WANT[1]))
        else:
            ok("%s/0 is a real %dx%d plot" % (row_id, WANT[0], WANT[1]))

        extra = registry().get("extraRows", [])
        print("extraRows: %s" % extra)
        if extra.count(row_id) == 1:
            ok("the row is recorded once, so a rebuild puts it back")
        else:
            fail("extraRows holds %r, expected exactly one %s" % (extra, row_id))

        # ------------------------------------------------- 5. idempotent
        con.command("lcdev workshop grow %s 1" % row_id)
        con.command("lcdev workshop build")
        again = registry().get("extraRows", [])
        if again.count(row_id) == 1:
            ok("growing it twice does not add a second row")
        else:
            fail("after a second grow extraRows holds %r" % (again,))
        rebuilt = coords()
        drifted = [p for p, xz in after.items()
                   if p in rebuilt and rebuilt[p] != xz]
        if drifted:
            fail("%d plots moved across a rebuild: %s"
                 % (len(drifted), drifted[:5]))
        else:
            ok("a rebuild puts every plot back where it was")

        # ------------------------------------------------- 6, 7. still refused
        too = con.command("lcdev workshop grow multibuilding/%dx%d 1" % TOOBIG)
        if "No row named" in too:
            ok("a footprint past the ceiling is still refused")
        else:
            fail("multibuilding/%dx%d was accepted: %s"
                 % (TOOBIG[0], TOOBIG[1], too.strip()[:160]))
        junk = con.command("lcdev workshop grow building/nonsense 1")
        if "No row named" in junk:
            ok("an id that is not a footprint is still refused")
        else:
            fail("building/nonsense was accepted: %s" % junk.strip()[:160])

        # ------------------------------------------- 8. the area, not just the count
        #
        # MAX_PLOTS_IN_ROW bounds how many plots a row holds and says nothing about
        # how big each is. That was harmless while nothing exceeded 10x10. It is not
        # now: 512 plots of 64x64 is two million chunks of floor, painted on the
        # server thread before the command answers.
        greedy = con.command("lcdev workshop grow multibuilding/64x64 512")
        if "chunks of floor" in greedy or "limit" in greedy:
            ok("a row whose area would be absurd is refused with a workable number")
        else:
            fail("grow multibuilding/64x64 512 was accepted: %s"
                 % greedy.strip()[:200])
        # And the refusal must not have left the row behind. Registering before
        # deciding would add a band for a command that answered no, and bands are
        # never taken back.
        #
        # The build is the point. A refused grow writes no registry, so reading the
        # file straight afterwards shows the state from the last successful build
        # and would pass whether or not the row leaked. Only a build asks the
        # catalogue what it currently holds.
        con.command("lcdev workshop build")
        left = registry().get("extraRows", [])
        if "multibuilding/64x64" in left:
            fail("the refused 64x64 was registered anyway: %s" % left)
        else:
            ok("a refused footprint leaves no row behind")

        one = con.command("lcdev workshop grow multibuilding/64x64 1")
        if "No row named" in one or "chunks of floor" in one:
            fail("a single 64x64 plot should still be allowed: %s"
                 % one.strip()[:160])
        else:
            ok("a single plot at the ceiling footprint is still allowed")

        # ------------------------------------------------- 9. the written numbers
        #
        # `mod/README.md` and the CurseForge page both state the row count, and both
        # said 138 while the catalogue held 146. Nothing noticed, because nothing
        # was looking. A number in prose that nothing checks goes stale the first
        # time the catalogue moves, which is every port.
        shipped = len(json.load(io.open(
            "mod/src/main/resources/data/lostcitiesdevtool/catalogue.json",
            encoding="utf-8"))["rows"])
        print("\ncatalogue.json holds %d rows" % shipped)
        for page in ("mod/README.md", "mod/description/curseforge.md"):
            text = io.open(page, encoding="utf-8").read()
            claimed = set(int(n) for n in re.findall(r"(\d+) rows", text))
            if not claimed:
                print("  --   %s states no row count" % page)
            elif claimed == {shipped}:
                ok("%s states %d rows, which is what ships" % (page, shipped))
            else:
                fail("%s states %s rows and the catalogue holds %d"
                     % (page, sorted(claimed), shipped))

        # The release procedure lists every check by name twice, once to run and
        # once to tick off. A check added without being listed is a check nobody
        # runs at release, which is the same failure as a stale row count and
        # quieter.
        on_disk = sorted(os.path.basename(p)[:-3]
                         for p in glob.glob("mod/tools/check-*.py"))
        rel = io.open("mod/RELEASING.md", encoding="utf-8").read()
        to_run = set(re.findall(r"^python mod/tools/(check-[\w-]+)\.py",
                                rel, re.M))
        to_tick = set(re.findall(r"^- \[ \] `(check-[\w-]+)`", rel, re.M))
        print("\nchecks on disk %d, listed to run %d, listed to tick %d"
              % (len(on_disk), len(to_run), len(to_tick)))
        for label, listed in (("run", to_run), ("tick off", to_tick)):
            missing = [c for c in on_disk if c not in listed]
            extra = [c for c in listed if c not in on_disk]
            if missing or extra:
                fail("RELEASING.md %s list is out of step: missing %s, stale %s"
                     % (label, missing or "none", extra or "none"))
            else:
                ok("RELEASING.md lists every check to %s" % label)
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
print("PASS")
