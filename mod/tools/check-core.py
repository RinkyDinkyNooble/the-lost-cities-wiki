#!/usr/bin/env python3
"""The core package compiles with no Minecraft, no loader and no Lost Cities.

    python mod/tools/check-core.py

No server. Compiles every class in `core/` on its own, against Gson, jsr305 and
slf4j-api only, the same jars the other plain-JVM checks take from the Gradle cache.

What it protects: `core/` is the half of the mod a port to another loader or
Minecraft version moves unchanged (see `mod/PORTING.md`). One import of a game,
loader or Lost Cities class, or of a class in another package of this mod, would
tie it back to the version it was written against, and the mod's own build would
not notice, because the game is on its classpath there.
"""
import glob
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "testrig"))
import rig  # noqa: E402
CORE = os.path.join(REPO, "mod", "src", "main", "java", "com", "rinkynooble",
                    "lostcitiesdevtool", "core")
OUT = os.path.join(REPO, "mod", "build", "core-alone")

# The classes the restructure put there. Fewer means a file moved out or the glob
# found nothing, and an empty compile would pass.
EXPECTED = 11


def jar(*fragments):
    """One dependency out of the Gradle cache, by path fragment."""
    cache = os.path.join(os.path.expanduser("~"), ".gradle", "caches",
                         "modules-2", "files-2.1")
    pattern = os.path.join(cache, *fragments)
    found = [p for p in glob.glob(pattern) if "sources" not in p]
    if not found:
        raise SystemExit("could not find %s in the Gradle cache. Build the mod "
                         "once first: cd mod && ./gradlew build" % pattern)
    return sorted(found)[-1]


sources = sorted(glob.glob(os.path.join(CORE, "*.java")))
print("  %d classes in core/" % len(sources))
if len(sources) < EXPECTED:
    raise SystemExit("FAIL: expected at least %d classes in core/, found %d"
                     % (EXPECTED, len(sources)))

classpath = os.pathsep.join([
    jar("com.google.code.gson", "gson", "*", "*", "gson-*.jar"),
    jar("com.google.code.findbugs", "jsr305", "*", "*", "jsr305-*.jar"),
    jar("org.slf4j", "slf4j-api", "*", "*", "slf4j-api-*.jar"),
])

os.makedirs(OUT, exist_ok=True)
compiled = subprocess.run([rig.jdk("javac"), "-nowarn", "-cp", classpath,
                           "-d", OUT] + sources,
                          capture_output=True, text=True)
if compiled.returncode != 0:
    print(compiled.stdout + compiled.stderr)
    raise SystemExit("FAIL: core/ does not compile on its own; the errors above "
                     "name the import that ties it to something outside")
print("\nall checks passed: core/ compiles with Gson, jsr305 and slf4j only")
