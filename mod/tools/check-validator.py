#!/usr/bin/env python3
"""The asset checker's own rules, checked. No server, no world, under a second.

    python mod/tools/check-validator.py

The other four checks each boot a real Minecraft server and take about a minute
and a half. This one does not need to: `AssetValidator` imports nothing but Gson,
so it compiles and runs in a plain JVM against `ValidatorProbe.java` beside it.

That matters because the validator is the part of this mod that reads files
somebody else wrote by hand. It has to say the right thing about a broken asset,
say nothing about a sound one, and above all never throw: it runs as a datapack
load listener, and a throw there means the file is logged as "could not check"
with every one of its real faults unreported.

Needs a JDK. It looks for one where the test rig keeps its own, then falls back to
JAVA_HOME and then to whatever `javac` is on the path.
"""
import glob
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "mod", "tools")
SRC = os.path.join(REPO, "mod", "src", "main", "java")
OUT = os.path.join(REPO, "mod", "build", "validator-probe")

SOURCES = [
    os.path.join(SRC, "com", "rinkynooble", "lostcitiesdevtool", "validate",
                 "AssetValidator.java"),
    os.path.join(SRC, "com", "rinkynooble", "lostcitiesdevtool", "validate",
                 "Finding.java"),
    os.path.join(TOOLS, "ValidatorProbe.java"),
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
    for base in (r"C:\Program Files\Eclipse Adoptium",
                 r"C:\Program Files\Java"):
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
])

os.makedirs(OUT, exist_ok=True)
compiled = subprocess.run([jdk("javac"), "-nowarn", "-cp", classpath,
                           "-d", OUT] + SOURCES,
                          capture_output=True, text=True)
if compiled.returncode != 0:
    print(compiled.stdout + compiled.stderr)
    raise SystemExit("the validator did not compile")

run = subprocess.run([jdk("java"), "-cp", OUT + os.pathsep + classpath,
                      "ValidatorProbe"],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace")
print(run.stdout + run.stderr, end="")

if run.returncode != 0:
    raise SystemExit("\nFAILURES: see above")
print("\nall checks passed")
