#!/usr/bin/env python3
"""Phase C: the plot commands, which are the ones people actually type.

    python mod/tools/check-cmd-plot.py

Needs the wiki's test rig, the same way the other server checks do.

`get`, `keys`, `file` and `resolve` had no check of their own, and `set` was only
ever exercised as a way of setting up some other check. This asks what each of them
promises.

What it asserts, and why each is here rather than assumed:

  * **The schema is per row class, not global.** A building plot offers `floors` and
    a street plot offers `height`, because the codec behind a street stacks nothing
    and the codec behind a building does. Offering every key everywhere would teach
    the format wrong, which is a claim the mod makes in `Settings` and which nothing
    checked. A street offering `floors` would be silently accepted and silently
    ignored by the export.

  * **The four scopes fold most-specific-first.** `resolve` is the only way to see
    what a chunk of a plot at a level actually gets, and the order is what the
    exporter relies on. A wrong order does not fail: it writes a pack that builds
    the wrong thing.

  * **A refusal names the value and what would be valid.** Four of them: a key the
    plot does not have, a value the key cannot take, a chunk outside the plot, and
    standing off a plot entirely. These are the whole reason the command exists
    rather than an instruction to edit the file, so a refusal that does not say what
    would work sends the reader to the file anyway.

  * **`show` and `hide` are inverses.** Markers are drawn on the walkway and rubbed
    out again, so the count cleared has to match the count placed. A `hide` that
    misses some leaves blocks on the walkway that the next export reads as content.

  * **`file` names a path that is really there.** The command exists to be clicked,
    so a path that does not exist after a `set` is worse than no answer.
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

BUILDING = "building/1x1/0"
STREET = "street/all/0"
MULTI = "multibuilding/2x2/0"

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


def settings_of(plot_id):
    path = os.path.join(SETTINGS, *plot_id.split("/")) + ".json5"
    if not os.path.isfile(path):
        return None
    return json.loads(strip_json5(io.open(path, encoding="utf-8").read()))


def number(text, label):
    """One number out of a reply, by the label in front of it."""
    found = re.search(re.escape(label) + r"\D{0,4}([0-9]+)", text)
    return int(found.group(1)) if found else None


def count_before(text, label):
    """One number out of a reply, by the label after it, as a header writes it."""
    found = re.search(r"([0-9]+)\s+" + re.escape(label), text)
    return int(found.group(1)) if found else None


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
shutil.copy(JAR, dest)
print("fresh world, jar installed: %s\n" % os.path.basename(JAR))

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}

        def at(plot_id, rest):
            """Run a plot command standing in the middle of that plot."""
            p = plots[plot_id]
            return con.command(
                "execute in %s positioned %d 10 %d run lcdev plot %s"
                % (WORKSHOP, p["chunkX"] * 16 + 8, p["chunkZ"] * 16 + 8,
                   rest)).rstrip()

        print("=" * 72)
        print("1. the schema a plot offers depends on what the plot is")
        b_keys = at(BUILDING, "keys")
        s_keys = at(STREET, "keys")
        print("  %s: %s keys" % (BUILDING, count_before(b_keys, "keys")))
        print("  %s: %s keys" % (STREET, count_before(s_keys, "keys")))
        if "floors" not in b_keys:
            fail("a building plot does not offer floors, which is the key its "
                 "whole row class exists for")
        if "floors" in s_keys:
            fail("a street plot offers floors. A street is one part and the codec "
                 "behind it stacks nothing, so the export would ignore it and the "
                 "command would have taught the format wrong")
        if "height" not in s_keys:
            fail("a street plot does not offer height, which is how tall it is")
        if "height" in b_keys:
            fail("a building plot offers height, which belongs to a flat shape")

        print("\n" + "=" * 72)
        print("2. what is set is what comes back")
        said = at(BUILDING, "set floors 4")
        print("  " + said.replace("\n", " ")[-120:])
        got = at(BUILDING, "get floors")
        print("  " + got.replace("\n", " ")[-160:])
        if "4" not in got:
            fail("floors was set to 4 and reading it back did not say 4")
        on_disk = settings_of(BUILDING)
        if on_disk is None or on_disk.get("floors") != 4:
            fail("the file the exporter reads does not hold what the command "
                 "reported writing: %s" % on_disk)

        unset = at(BUILDING, "get cellars")
        print("  unset: " + unset.replace("\n", " ")[-140:])
        if "unset" not in unset:
            fail("a key that has never been set did not say so")
        if "the export will use" not in unset:
            fail("a key that is unset did not say what the export would do "
                 "instead, which is the only thing that makes `get` worth running "
                 "on an unset key")

        print("\n" + "=" * 72)
        print("3. the four scopes fold most specific first")
        # A 2x2 plot, because a 1x1 has one chunk and a chunk override cannot then
        # be told apart from a plot-wide one. Four values, one per scope, so each
        # layer is the only thing that could have produced the number it gives.
        at(MULTI, "set floors 4")
        at(MULTI, "setlevel 2 floors 7")
        at(MULTI, "setchunk 0 0 floors 9")
        wanted = [
            ("resolve 1 1 0", 4, "a chunk and level nothing overrides"),
            ("resolve 1 1 2", 7, "the plot's own level 2"),
            ("resolve 0 0 0", 9, "chunk 0,0"),
            ("resolve 0 0 2", 9, "chunk 0,0 against the plot's level 2"),
        ]
        for command, want, what in wanted:
            got = number(at(MULTI, command), "floors")
            print("  %-38s floors %s" % (what, got))
            if got != want:
                fail("%s should resolve floors to %d and gave %s. The order the "
                     "exporter reads is the plot, then its levels, then the "
                     "chunk, then that chunk's levels, and a pack compiled in a "
                     "different order builds the wrong thing"
                     % (what, want, got))

        print("\n" + "=" * 72)
        print("4. clearing a key removes it rather than blanking it")
        at(BUILDING, "clear floors")
        after = settings_of(BUILDING)
        print("  keys left on the plot: %s"
              % sorted(k for k in (after or {}) if k not in ("chunks", "levels")))
        if after is not None and "floors" in after:
            fail("clear left floors in the file, so the export still reads it")

        print("\n" + "=" * 72)
        print("5. a refusal names the value and what would work")
        cases = [
            ("set nosuchkey 1", "Not a key this plot has", "an unknown key"),
            ("set floors banana", "not a valid value", "a value of the wrong type"),
            ("setchunk 5 5 floors 2", "not part of this plot",
             "a chunk outside a 1x1 plot"),
        ]
        for command, want, what in cases:
            said = at(BUILDING, command)
            print("  %-22s %s" % (what, said.replace("\n", " ")[:120]))
            if want not in said:
                fail("%s was not refused with a message naming what would work"
                     % what)

        # Off a plot entirely. The walkway is one chunk wide between plots, so a
        # position on it is on no plot at all.
        p = plots[BUILDING]
        off = con.command("execute in %s positioned %d 10 %d run lcdev plot get"
                          % (WORKSHOP, p["chunkX"] * 16 - 8,
                             p["chunkZ"] * 16 + 8)).rstrip()
        print("  %-22s %s" % ("standing on walkway", off.replace("\n", " ")[:120]))
        if "not standing on a plot" not in off:
            fail("a plot command run off a plot did not say so")

        print("\n" + "=" * 72)
        print("6. show and hide are inverses")
        at(BUILDING, "set floors 3")
        shown = at(BUILDING, "show")
        placed = number(shown, "markers placed")
        hidden = at(BUILDING, "hide")
        cleared = number(hidden, "markers cleared")
        print("  placed %s, cleared %s" % (placed, cleared))
        if not placed:
            fail("show placed no markers, so there is nothing for hide to prove")
        elif cleared != placed:
            fail("show placed %s markers and hide cleared %s. What is left stands "
                 "on the walkway, and the next export reads the walkway as part of "
                 "nothing while the plot boundary preview is still drawn"
                 % (placed, cleared))

        print("\n" + "=" * 72)
        print("7. file names a path that is really there")
        said = at(BUILDING, "file")
        print("  " + said.replace("\n", " ")[-170:])
        if "yes" not in said:
            fail("the settings file was written by every set above and `file` "
                 "says it is not there")
        path = os.path.join(SETTINGS, *BUILDING.split("/")) + ".json5"
        if not os.path.isfile(path):
            fail("`file` reported a written settings file and there is none at %s"
                 % path)

        empty = at(STREET, "file")
        print("  never set: " + empty.replace("\n", " ")[-120:])
        if "not yet" not in empty:
            fail("a plot nothing has been set on did not say its file is not "
                 "written yet")
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
print("the plot commands offer the keys the plot really has, fold the scopes in "
      "the order the export reads them, and refuse with a reason")
print("all checks passed")
