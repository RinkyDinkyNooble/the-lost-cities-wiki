"""Every mixin actually applied to a running server, not just to a jar.

`check-mixin-targets.py` reads the jars and says an injection point exists.
This says the mixin reached it. The two fail in different ways and neither
substitutes for the other:

- A target that moved is caught by `check-mixin-targets`, before a build.
- A mixin whose config never loads it, whose target class is never transformed,
  or which is refused for a reason a descriptor comparison cannot show, gets
  through `check-mixin-targets` green and is caught only here.

**Why this check exists.** `check-config` covers eight of the eleven toggles and
says plainly that it cannot cover `catchSphereFeatureErrors`, which needs a
sphere landscape with a faulting pack, or `detailedFaultReports`, which needs a
pack that faults during generation. Those two are exactly the mixins the 7.5
port had to retarget, so the port would otherwise have shipped its only two
source changes with no runtime assertion behind them.

**How it gets a positive answer, and one way that does not work.**
`-Dmixin.debug=true` was tried first and is not enough: it names a mixin only
when that mixin has a synthetic method to rename, so three of the nine were
named for having lambdas and the rest were invisible. A missing name proved
nothing either way.

`-Dmixin.debug.export=true` writes every class Mixin transforms to
`.mixin.out/class/`, so the presence of a target class there is direct evidence
that it was transformed. That is what this asserts, per target class. A
`@Redirect` that cannot find its injection point throws
`InvalidInjectionException` while the class is being transformed, so a class
that is exported was patched successfully rather than merely attempted.

**Two worlds, and a forceload, because none of it happens on its own.** A
`spheres` landscape is the only way `LostCitySphereFeature` is touched at all, so
one run uses it and a second uses a city profile. Booting is not enough for
either: a registered `Feature` class loads when the registries bootstrap, which
is why the two feature classes appear from a boot alone, while
`LostCityTerrainFeature` is a plain helper that loads only when a chunk is really
generated. The Lost Cities dimension is not the overworld and nothing enters it
by itself, so each run forceloads a 64 by 64 block area in it over RCON.

Getting that wrong is how this check was written: three earlier versions passed
eight of nine rows while the ninth was a fixture that never loaded the class, and
one row failed because the target's package had been guessed rather than read.
Both are the kind of miss the check exists to prevent, so they are recorded here
rather than tidied away.

    python mod/tools/check-mixin-applied.py
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from rcon import Rcon  # noqa: E402
import rig  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORLD = os.path.join(SERVER, "world")
EXPORT = os.path.join(SERVER, ".mixin.out", "class")
CITY = "lostcities:lostcity"

# Mixin, and the class it patches. The target is what gets exported, so the
# pairing is what makes a failure name the mixin rather than a file path.
TARGETS = [
    ("BuildingInfoMixin", "mcjty/lostcities/worldgen/lost/BuildingInfo"),
    ("ConditionContextAccessor",
     "mcjty/lostcities/worldgen/lost/cityassets/ConditionContext"),
    ("ConditionContextMixin",
     "mcjty/lostcities/worldgen/lost/cityassets/ConditionContext"),
    ("FileToIdConverterMixin", "net/minecraft/resources/FileToIdConverter"),
    ("LostCityFeatureMixin", "mcjty/lostcities/worldgen/LostCityFeature"),
    ("LostCitySphereFeatureMixin", "mcjty/lostcities/worldgen/LostCitySphereFeature"),
    ("LostCityTerrainFeatureMixin", "mcjty/lostcities/worldgen/LostCityTerrainFeature"),
    ("PathPackResourcesAccessor", "net/minecraft/server/packs/PathPackResources"),
    ("ProfileSetupMixin", "mcjty/lostcities/config/ProfileSetup"),
]

# The two in the mixin config's "client" list. A dedicated server never loads
# GuiLCConfig or LostCitySetup, so these cannot appear and their absence is not a
# failure. They are named rather than left out, so that a mixin moved from the
# common list to the client list is visible rather than silently unchecked.
CLIENT_ONLY = ["GuiLCConfigAccessor", "LostCitySetupMixin"]

# spheres reaches LostCitySphereFeature, which nothing else does. The second
# reaches LostCityTerrainFeature, which spheres did not.
#
# The second is written rather than named: `default` was tried and its city
# chance is low enough that spawn chunks came back with no city at all, so
# LostCityFeature loaded and LostCityTerrainFeature never did. A partial profile
# inherits everything it does not state, so this is one key.
PROFILES = ["spheres", "devtoolcheck"]
WRITTEN = {"devtoolcheck": {"cityChance": 1.0}}

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def write_profile(name):
    """Point the Lost Cities dimension at one profile, writing it if it is ours."""
    cfg = os.path.join(SERVER, "config", "lostcities")
    os.makedirs(cfg, exist_ok=True)
    if name in WRITTEN:
        profiles = os.path.join(cfg, "profiles")
        os.makedirs(profiles, exist_ok=True)
        open(os.path.join(profiles, name + ".json"), "w",
             encoding="utf-8", newline="\n").write(
                 json.dumps(WRITTEN[name], indent=2) + "\n")
    common = os.path.join(cfg, "common.toml")
    text = ""
    if os.path.isfile(common):
        text = open(common, encoding="utf-8").read()
    line = 'dimensionsWithProfiles = ["lostcities:lostcity=%s"]' % name
    if "dimensionsWithProfiles" in text:
        text = re.sub(r'dimensionsWithProfiles\s*=\s*\[[^\]]*\]', line, text)
    else:
        text += "\n[profiles]\n    " + line + "\n"
    open(common, "w", encoding="utf-8", newline="\n").write(text)


def boot():
    """Boot over a fresh world with class export on, then stop. Returns the log.

    The world is deleted first so that spawn chunks are generated rather than
    read back, which is what loads the generation classes at all.
    """
    if os.path.isdir(WORLD):
        shutil.rmtree(WORLD)
    args = "@" + os.path.join("libraries", LOADER, "win_args.txt")
    proc = subprocess.Popen(
        [JAVA, "-Dmixin.debug.export=true", "@user_jvm_args.txt", args, "nogui"],
        cwd=SERVER, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    seen = []
    deadline = time.time() + 300
    up = False
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        seen.append(line)
        if 'For help, type "help"' in line:
            up = True
            break
    if not up:
        proc.kill()
        raise SystemExit("server did not start\n" + "".join(seen[-30:]))

    # Booting is not enough. Registered Feature classes load when the registries
    # bootstrap, which is why LostCityFeature and LostCitySphereFeature appear
    # from a boot alone, but LostCityTerrainFeature is a plain helper that only
    # loads when a chunk is really generated in the Lost Cities dimension. That
    # dimension is not the overworld, so nothing enters it on its own.
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("execute in %s run forceload add 0 0 63 63" % CITY)
            time.sleep(20)
            con.command("execute in %s run forceload remove all" % CITY)
    except Exception as e:
        print("    rcon: %s" % e)

    try:
        proc.stdin.write("stop\n")
        proc.stdin.flush()
    except Exception:
        pass
    end = time.time() + 120
    while time.time() < end:
        line = proc.stdout.readline()
        if not line:
            break
        seen.append(line)
    try:
        proc.wait(timeout=60)
    except Exception:
        proc.kill()
    return "".join(seen)


print("=" * 72)
print("mixins applied on a running server")

installed = rig.install(SERVER, JAR)
try:
    # Stale exports from an earlier run would make every row pass.
    if os.path.isdir(os.path.dirname(EXPORT)):
        shutil.rmtree(os.path.dirname(EXPORT))

    log = []
    for name in PROFILES:
        print("\n  world: %s" % name)
        write_profile(name)
        log.append(boot())
    text = "\n".join(log)

    print()
    for mixin, target in TARGETS:
        path = os.path.join(EXPORT, target.replace("/", os.sep) + ".class")
        if os.path.isfile(path):
            print("  applied  %-28s into %s" % (mixin, target))
        else:
            fail("%s did not apply: %s was never transformed. Either the mixin "
                 "config does not list it, or no world in this fixture loads "
                 "that class" % (mixin, target))

    for name in CLIENT_ONLY:
        print("  skipped  %-28s client only" % name)

    # Mixin says so loudly when it refuses one. These would mean a mixin was
    # found and then rejected, which the export check alone could miss.
    for bad in ("InvalidInjectionException", "Mixin apply failed",
                "was not found in", "Critical injection failure"):
        for line in text.splitlines():
            if bad in line:
                fail("mixin error in the log: " + line.strip())
                break
finally:
    if os.path.isfile(installed):
        os.remove(installed)
    print("\nremoved the jar")

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    raise SystemExit(1)
print("all %d server side mixins applied to their targets" % len(TARGETS))
