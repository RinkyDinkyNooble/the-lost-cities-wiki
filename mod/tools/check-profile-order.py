#!/usr/bin/env python3
"""The Cities screen's profile cycle, both directions. No server, under a second.

    python mod/tools/check-profile-order.py

The right click that steps back through profiles and the Customize repair both run
on the client only, and a dedicated server never loads the classes they patch, so
the rig cannot press either button. What can be checked without one is checked
here, and what cannot is said.

  * **The order and its inverse.** `ProfileOrder` holds the order `toggleProfile`
    sorts into and the step back through it, with no Lost Cities type in it, so
    `ProfileOrderProbe` runs it in a plain JVM: `default` first, code point order
    after, and a step back that undoes a step forward from every state.
  * **One builder for both lists.** The Customize repair used to build the profile
    list itself, unsorted. `toggleProfile` sorts only a list it built, so after the
    repair fired the left click cycled in hash order and the right click in sorted
    order. The sources are read to show the repair builds through `Profiles`, and
    the right click steps through the screen's own live list.

Not checked, because only a person at a client can: that the buttons really do
this on screen.
"""
import glob
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "testrig"))
import rig  # noqa: E402
TOOLS = os.path.join(REPO, "mod", "tools")
SRC = os.path.join(REPO, "mod", "src", "main", "java", "com", "rinkynooble",
                   "lostcitiesdevtool")
OUT = os.path.join(REPO, "mod", "build", "profile-order-probe")
SOURCES = [os.path.join(SRC, "core", "ProfileOrder.java"),
           os.path.join(TOOLS, "ProfileOrderProbe.java")]

failures = []


def jar(*fragments):
    cache = os.path.join(os.path.expanduser("~"), ".gradle", "caches",
                         "modules-2", "files-2.1")
    found = [p for p in glob.glob(os.path.join(cache, *fragments))
             if "sources" not in p]
    if not found:
        raise SystemExit("could not find %s in the Gradle cache. Build the mod "
                         "once first: cd mod && ./gradlew build" % fragments[-1])
    return sorted(found)[-1]


print("=" * 72)
print("1. the order, and a step back that undoes a step forward")
classpath = jar("com.google.code.findbugs", "jsr305", "*", "*", "jsr305-*.jar")
os.makedirs(OUT, exist_ok=True)
compiled = subprocess.run([rig.jdk("javac"), "-nowarn", "-cp", classpath, "-d", OUT]
                          + SOURCES, capture_output=True, text=True)
if compiled.returncode != 0:
    print(compiled.stdout + compiled.stderr)
    failures.append("ProfileOrder did not compile")
else:
    run = subprocess.run([rig.jdk("java"), "-cp", OUT + os.pathsep + classpath,
                          "ProfileOrderProbe"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    print(run.stdout + run.stderr, end="")
    if run.returncode != 0:
        failures.append("the probe failed")

print("\n" + "=" * 72)
print("2. both lists come out of one builder")


def source(*parts):
    path = os.path.join(SRC, *parts)
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


wiring = [
    ("client/Profiles.java", "ProfileOrder.sorted(",
     "the screen's list is sorted by ProfileOrder"),
    ("mixin/LostCitySetupMixin.java", "Profiles.selectable()",
     "the Customize repair builds its list through Profiles"),
    ("mixin/LostCitySetupMixin.java", "implements ProfileListAccess",
     "the repair hands the live list to the right click"),
    ("platform/ClientEvents.java", "lostcitiesdevtool$profiles()",
     "the right click steps through the live list"),
]
for where, needle, what in wiring:
    held = needle in source(*where.split("/"))
    print("  %-6s %s" % ("ok" if held else "FAIL", what))
    if not held:
        failures.append("%s: %s no longer holds" % (where, what))

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("both directions of the cycle use one order, and the right click undoes the "
      "left from every state")
print("all checks passed")
