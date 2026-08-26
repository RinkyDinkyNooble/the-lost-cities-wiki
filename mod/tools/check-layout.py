#!/usr/bin/env python3
"""Where the plots are, and that they stay there.

    python mod/tools/check-layout.py

No server. The layout is arithmetic over the catalogue and, since the floor colours
moved to Workshop, it holds no Minecraft type at all, so this runs in a plain JVM
and finishes in about a second.

What it protects: a plot's position is written into the world the moment anything is
pasted onto it, and never written down again. If growing one row moves another row's
plots, every build on them is stranded at coordinates that now belong to a different
plot. Reported against 1.3.0 as buildings standing beside their own floors.

Compiles against the sources directly, taking Gson and slf4j from the Gradle cache,
so it needs the mod to have been built once but does not need it built now.
"""
import glob
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "mod", "tools")
SRC = os.path.join(REPO, "mod", "src", "main", "java")
OUT = os.path.join(REPO, "mod", "build", "layout-probe")
RES = os.path.join(REPO, "mod", "src", "main", "resources")

SOURCES = [
    os.path.join(SRC, "com", "rinkynooble", "lostcitiesdevtool", "workshop",
                 "Catalogue.java"),
    os.path.join(SRC, "com", "rinkynooble", "lostcitiesdevtool", "workshop",
                 "Layout.java"),
    os.path.join(TOOLS, "LayoutProbe.java"),
]


def jdk(tool):
    """A JDK, from the rig, then JAVA_HOME, then the path."""
    rig = os.path.join(REPO, "testrig", "java", "17", "bin", tool + ".exe")
    if os.path.isfile(rig):
        return rig
    home = os.environ.get("JAVA_HOME")
    if home:
        for name in (tool + ".exe", tool):
            candidate = os.path.join(home, "bin", name)
            if os.path.isfile(candidate):
                return candidate
    for base in (r"C:\Program Files\Eclipse Adoptium", r"C:\Program Files\Java"):
        for candidate in sorted(glob.glob(os.path.join(base, "*", "bin",
                                                       tool + ".exe"))):
            return candidate
    return tool


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


classpath = os.pathsep.join([
    jar("com.google.code.gson", "gson", "*", "*", "gson-*.jar"),
    jar("com.google.code.findbugs", "jsr305", "*", "*", "jsr305-*.jar"),
    jar("org.slf4j", "slf4j-api", "*", "*", "slf4j-api-*.jar"),
])

os.makedirs(OUT, exist_ok=True)
compiled = subprocess.run([jdk("javac"), "-nowarn", "-cp", classpath,
                           "-d", OUT] + SOURCES,
                          capture_output=True, text=True)
if compiled.returncode != 0:
    print(compiled.stdout + compiled.stderr)
    raise SystemExit("the layout did not compile")

# The catalogue is read off the classpath, so the resources directory joins it.
run = subprocess.run([jdk("java"), "-cp",
                      os.pathsep.join([OUT, RES, classpath]), "LayoutProbe"],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace")
# slf4j has no provider in a plain JVM and says so on stderr. That is
# expected here and is not the check talking.
for line in (run.stdout + run.stderr).splitlines():
    if not line.startswith("SLF4J"):
        print(line)

if run.returncode != 0:
    raise SystemExit("\nFAILURES: see above")
print("\nall checks passed")
