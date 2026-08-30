#!/usr/bin/env python3
"""Does a config toggle actually change anything?

    python mod/tools/check-config.py

Needs the wiki's test rig, the same way the other server checks do.

**Written because nothing checked this at all.** The audit grepped every one of the
mod's eleven toggle names across all 25 checks and found none of them. Nothing wrote
the mod's config or asserted that a toggle changed a thing. The repairs default off,
so their code had never executed under any check, and coverage agreed: `FaultReport`
and `LastFault` sat at 0% of their lines after a full suite run.

That matters most for the repairs, because `mod/README.md` makes measured claims about
them and a claim no check defends is one that quietly stops being true.

Each case boots the rig twice over the same fixture and the same seed, with one line of
config different, and asserts the difference. A toggle that does nothing fails here.

**The flagship is `fixFullStreetShape`.** Lost Cities picks a street type with
`nextInt(0, values().length - 2)`, and with NORMAL, FULL and PARK that is `nextInt(0,
1)`, so only NORMAL can ever come out. PARK has its own branch, so the subtraction was
meant to exclude it and excludes FULL as well by being one too large. The fixture
points the `full` shape at a part made of one distinctive block, so the question
"is FULL reachable" becomes "is that block anywhere in the world".

What is deliberately not here: `anchorCitiesButton`, `fixCustomizeCrash` and
`rightClickCyclesProfilesBack` are client only and a dedicated server never loads the
classes they patch. `catchSphereFeatureErrors` needs a sphere landscape with a faulting
pack, which is its own fixture.
"""
import atexit
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
CITY = "lostcities:lostcity"
WORLD = os.path.join(SERVER, "world")
LC_CONFIG = os.path.join(SERVER, "config", "lostcities")
KEPT_LC = LC_CONFIG + ".kept"
MOD_CONFIG = os.path.join(SERVER, "config", "lostcities_devtool-common.toml")
KEPT_MOD = MOD_CONFIG + ".kept"
NS = "f1pack"
PACK = "f1pack"

# The block only the `full` street shape can draw. Nothing in Lost Cities' own content
# uses it, so one of them anywhere means FULL was reached.
MARK = "minecraft:gold_block"

# Where the city is looked at. `/clone` refuses more than 32768 blocks, and 16 by 16 by
# 128 is exactly the limit, so a region is counted one chunk at a time.
LOW = 40
HIGH = 167
CHUNKS = range(7, 11)

DEFAULTS = {
    "diagnostics": {
        "catchSphereFeatureErrors": True,
        "detailedFaultReports": True,
        "validateOnLoad": True,
        "acceptCommentsAndTrailingCommas": True,
        "acceptJson5Extension": True,
        "warnOnJson5Override": True,
    },
    "repairs": {
        "fixBelowPart": False,
        "fixFullStreetShape": False,
        "anchorCitiesButton": True,
        "fixCustomizeCrash": True,
        "rightClickCyclesProfilesBack": True,
    },
}

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def write_config(**overrides):
    """The mod's config, at its defaults except for what is named."""
    out = []
    for section, keys in DEFAULTS.items():
        out.append("[%s]" % section)
        for key, value in keys.items():
            on = overrides.get(key, value)
            out.append("\t%s = %s" % (key, "true" if on else "false"))
    io.open(MOD_CONFIG, "w", encoding="utf-8", newline="\n").write(
        "\n".join(out) + "\n")


def boot(must_start=True):
    """Boot, and hand back the log as well as the process.

    `must_start` is False where a refusal is the point. Without
    `acceptCommentsAndTrailingCommas` a commented asset does not merely go unread,
    it stops the server: the registry loader raises and the process exits. That is
    the documented behaviour, so the check has to be able to assert it rather than
    fall over on it.
    """
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
            if not must_start:
                return None, tail
            print("\n".join(tail[-20:]))
            raise SystemExit("server exited during startup")
        tail.append(line.rstrip())
        if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
            threading.Thread(
                target=lambda: [tail.append(ln.rstrip())
                                for ln in iter(proc.stdout.readline, "")],
                daemon=True).start()
            return proc, tail
    if must_start:
        raise SystemExit("server did not start")
    return None, tail


def stop(proc):
    if proc is None:
        return
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("stop")
    except Exception:
        pass
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()


def row(char, n=16):
    return char * n


def part(char, block):
    """A 16 by 16 street part of one block, carrying its own palette.

    An inline palette is an object holding the list, never a bare list: a bare list
    decodes as no palette at all and the part draws air with nothing logged.
    """
    return {
        "xsize": 16,
        "zsize": 16,
        "palette": {"palette": [{"char": char, "block": block}]},
        "slices": [[row(char) for _ in range(16)]],
    }


def write_pack(root):
    """A world style whose only interesting property is which street shape it draws."""
    base = os.path.join(root, "data", NS, "lostcities")
    for folder in ("worldstyles", "citystyles", "parts"):
        os.makedirs(os.path.join(base, folder), exist_ok=True)

    def put(folder, name, doc):
        io.open(os.path.join(base, folder, name + ".json"), "w",
                encoding="utf-8", newline="\n").write(json.dumps(doc, indent=2))

    put("worldstyles", "main", {
        "outsidestyle": "outside",
        "citystyles": [{"factor": 1.0, "citystyle": NS + ":mycity"}],
    })
    # `streetblocks.parts` is all or nothing: writing any `parts` block discards the
    # parent's entire one, so every shape has to be restated even to change a single
    # key. Six point at the mod's own defaults and only `full` is ours.
    put("citystyles", "mycity", {
        "inherit": "citystyle_common",
        "style": "standard",
        "streetblocks": {
            "parts": {
                "none": ["street_none"],
                "straight": ["street_straight"],
                "bend": ["street_bend"],
                "t": ["street_t"],
                "all": ["street_all"],
                "end": ["street_end"],
                "full": [NS + ":street_full_marked"],
            }
        },
    })
    put("parts", "street_full_marked", part("G", MARK))
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15,
                          "description": "config toggle fixture"}}, indent=2))


PROFILE = {
    "cities": {"cityChance": 1.0},
    "lostcity": {
        "buildingChance": 0.0,
        "highwayDistanceMask": 0,
        "railwaysEnabled": False,
        "ruinChance": 0.0,
        "generateLoot": False,
        "worldStyle": NS + ":main",
    },
    "explosions": {"explosionChance": 0.0, "miniExplosionChance": 0.0},
}


def install(style=None):
    """A fresh world with the fixture in it, and the dimension pointed at it.

    `style` names the world style the profile asks for, so a case can point the
    dimension at one written as `.json5` and find out whether Lost Cities loaded it.
    """
    if os.path.isdir(WORLD):
        shutil.rmtree(WORLD)
    write_pack(os.path.join(WORLD, "datapacks", PACK))
    profile = json.loads(json.dumps(PROFILE))
    if style:
        profile["lostcity"]["worldStyle"] = style
    profiles = os.path.join(LC_CONFIG, "profiles")
    os.makedirs(profiles, exist_ok=True)
    io.open(os.path.join(profiles, PACK + ".json"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(profile, indent=2))
    io.open(os.path.join(LC_CONFIG, "common.toml"), "w", encoding="utf-8",
            newline="\n").write(
        '[profiles]\n\tdimensionsWithProfiles = ["%s=%s"]\n' % (CITY, PACK))


def count(con, block):
    """How many of `block` stand in the sampled city, a chunk at a time."""
    total = 0
    for cx in CHUNKS:
        for cz in CHUNKS:
            bx, bz = cx * 16, cz * 16
            reply = con.command(
                "execute in %s run clone %d %d %d %d %d %d 992 %d 992 filtered %s"
                % (CITY, bx, LOW, bz, bx + 15, HIGH, bz + 15, LOW, block))
            m = re.search(r"([0-9]+) block", reply)
            total += int(m.group(1)) if m else 0
    return total


def generated(style=None, block=None, wait=240, **toggles):
    """Boot over a fresh world with these toggles, and count a block in the city.

    `block` defaults to the marked one. `wait` is how long to give generation before
    accepting that nothing came, which a case expecting nothing wants short.
    """
    install(style)
    write_config(**toggles)
    proc, log = boot()
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("execute in %s run forceload add 112 112 175 175" % CITY)
            con.command("execute in %s run forceload add 992 992 1023 1023" % CITY)
            # Generation is asynchronous. Poll on the street base, which every street
            # chunk draws whichever shape is chosen, so this waits for the city rather
            # than for the answer.
            deadline = time.time() + wait
            while time.time() < deadline:
                if count(con, "minecraft:stone_bricks") > 0:
                    break
                time.sleep(5)
            return count(con, block or MARK), log
    finally:
        stop(proc)


# ------------------------------------------------------------------ the rig's own

# Both configs belong to the rig. Registered rather than left at the bottom of the
# file, because the bottom is only reached when nothing raised, and leaving either
# behind hands every later check a dimension whose world style stops resolving.
for live, kept in ((LC_CONFIG, KEPT_LC), (MOD_CONFIG, KEPT_MOD)):
    if os.path.exists(kept):
        shutil.rmtree(kept) if os.path.isdir(kept) else os.remove(kept)
    if os.path.isdir(live):
        shutil.copytree(live, kept)
    elif os.path.isfile(live):
        shutil.copy(live, kept)


def restore():
    jar = globals().get("dest")
    if jar and os.path.isfile(jar):
        os.remove(jar)
    if os.path.isdir(KEPT_LC):
        if os.path.isdir(LC_CONFIG):
            shutil.rmtree(LC_CONFIG)
        shutil.move(KEPT_LC, LC_CONFIG)
    if os.path.isfile(KEPT_MOD):
        shutil.move(KEPT_MOD, MOD_CONFIG)
    print("\nput the rig's own config back")


atexit.register(restore)

dest = rig.install(SERVER, JAR)
print("jar installed: %s" % os.path.basename(JAR))
print("the fixture points the `full` street shape at a part of %s\n" % MARK)

# ------------------------------------------ 1 and 2, the repair that changes generation

print("=" * 72)
print("1. fixFullStreetShape off: the `full` street shape is never reached")
off, _ = generated(fixFullStreetShape=False)
print("  %s in the sampled city: %d" % (MARK.replace("minecraft:", ""), off))
if off != 0:
    fail("the `full` shape drew %d blocks with the repair off, so either the repair "
         "is not what makes it reachable or the fixture is drawing it another way"
         % off)

print("\n" + "=" * 72)
print("2. fixFullStreetShape on: it is reached")
on, _ = generated(fixFullStreetShape=True)
print("  %s in the sampled city: %d" % (MARK.replace("minecraft:", ""), on))
if on == 0:
    fail("the repair changed nothing: the `full` shape still drew nothing. Either "
         "the mixin stopped applying or the street type is chosen somewhere else now")
elif off == on:
    fail("the same count with the repair off and on, so nothing here is measuring "
         "the toggle")

# ------------------------------------------------- 3 and 4, the check that runs at load

BROKEN = {"filler": "#", "parts": [{"part": "p", "inpart": "x"}]}


def with_broken_asset(**toggles):
    """Boot with an asset the check is documented to refuse, and hand back the log."""
    install()
    folder = os.path.join(WORLD, "datapacks", PACK, "data", NS, "lostcities",
                          "buildings")
    os.makedirs(folder, exist_ok=True)
    io.open(os.path.join(folder, "broken.json"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(BROKEN, indent=2))
    write_config(**toggles)
    proc, log = boot()
    stop(proc)
    return "\n".join(log)


print("\n" + "=" * 72)
print("3. validateOnLoad on: a broken asset is reported at load")
said = with_broken_asset(validateOnLoad=True)
found = "Lost Cities asset check" in said
print("  the asset check ran: %s" % found)
if not found:
    fail("validateOnLoad is on and the asset check said nothing about a building "
         "whose part condition can never match")

print("\n" + "=" * 72)
print("4. validateOnLoad off: it says nothing")
said = with_broken_asset(validateOnLoad=False)
quiet = "Lost Cities asset check" not in said
print("  the asset check stayed quiet: %s" % quiet)
if not quiet:
    fail("validateOnLoad is off and the asset check reported anyway, so the toggle "
         "does not turn it off")

# ------------------------------------- 5 to 8, the two that decide what a pack may be

def with_asset(name, text, must_start=True, kind="buildings", **toggles):
    """Boot with one asset written verbatim, and hand back what the mod said."""
    install()
    folder = os.path.join(WORLD, "datapacks", PACK, "data", NS, "lostcities", kind)
    os.makedirs(folder, exist_ok=True)
    io.open(os.path.join(folder, name), "w", encoding="utf-8",
            newline="\n").write(text)
    write_config(**toggles)
    proc, log = boot(must_start)
    if proc is None:
        return None, "\n".join(log)
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            # The mod's own answer, rather than reading the log for an absence. An
            # asset it cannot see is an asset `import` cannot name.
            return con.command("lcdev import").rstrip(), "\n".join(log)
    finally:
        stop(proc)


# A comment and a trailing comma. Strict JSON refuses both, and without the toggle
# this file stops the server rather than loading.
COMMENTED = """// the marker building
{
  "filler": "#",
  "parts": [
    { "part": "p" },
  ],
}
"""

print("\n" + "=" * 72)
print("5. acceptCommentsAndTrailingCommas on: a commented asset loads")
said, log = with_asset("commented.json", COMMENTED,
                       acceptCommentsAndTrailingCommas=True, validateOnLoad=False)
broke = re.search(r"MalformedJson|Expected name at line", log)
print("  the pack loaded without a JSON complaint: %s" % (not broke))
if broke:
    fail("a commented asset was refused with the toggle on")

print("\n" + "=" * 72)
print("6. acceptCommentsAndTrailingCommas off: the same file is refused")
# The refusal is not a quiet one. The registry loader raises and the server exits, so
# the boot is allowed to fail and that failure is the assertion.
said, log = with_asset("commented.json", COMMENTED, must_start=False,
                       acceptCommentsAndTrailingCommas=False, validateOnLoad=False)
refused = said is None and bool(
        re.search(r"MalformedJson|Expected name at line|Failed to load registries",
                  log))
print("  the same file stopped the server starting: %s" % refused)
if not refused:
    fail("a commented asset did not stop the server with the toggle off, so the "
         "toggle does not decide whether comments are accepted")

print("\n" + "=" * 72)
print("7. acceptJson5Extension on: Lost Cities generates from a .json5 world style")
# Asked through generation rather than through `lcdev import`. The first draft listed
# world styles instead, and that case passed with the toggle off: `Assets` reads
# `.json5` unconditionally while the mixin gates it, so the mod's own listing can name
# a world style Lost Cities never registered. Recorded as F16. Generation is the
# question the toggle actually governs.
STYLED = json.dumps({"outsidestyle": "outside",
                     "citystyles": [{"factor": 1.0, "citystyle": NS + ":mycity"}]})


def with_json5_style(**toggles):
    """A world style written as .json5, and whether a city came out of it.

    A world style the mod never registered does not merely generate nothing: asking
    for it throws inside generation and takes the connection with it. So a dropped
    connection counts as "no city", which is the answer the case is asking for, and
    is why the count is wrapped rather than allowed to end the run.
    """
    install(NS + ":styled")
    folder = os.path.join(WORLD, "datapacks", PACK, "data", NS, "lostcities",
                          "worldstyles")
    os.makedirs(folder, exist_ok=True)
    io.open(os.path.join(folder, "styled.json5"), "w", encoding="utf-8",
            newline="\n").write(STYLED)
    write_config(**toggles)
    proc, log = boot()
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("execute in %s run forceload add 112 112 175 175" % CITY)
            con.command("execute in %s run forceload add 992 992 1023 1023" % CITY)
            deadline = time.time() + 90
            found = 0
            while time.time() < deadline:
                found = count(con, "minecraft:stone_bricks")
                if found > 0:
                    break
                time.sleep(5)
            return found
    except Exception as e:
        print("  the world style did not resolve and generation threw (%s)"
              % type(e).__name__)
        return 0
    finally:
        stop(proc)


on7 = with_json5_style(acceptJson5Extension=True, validateOnLoad=False)
print("  street blocks generated: %d" % on7)

print("\n" + "=" * 72)
print("8. acceptJson5Extension off: it does not")
off8 = with_json5_style(acceptJson5Extension=False, validateOnLoad=False)
print("  street blocks generated with the toggle on: %d, with it off: %d"
      % (on7, off8))
if on7 == 0:
    fail("a .json5 world style generated nothing with the toggle on, so either the "
         "extension is not being read or the fixture is wrong")
if off8 != 0:
    fail("a .json5 world style still generated with the toggle off, so the toggle "
         "does not decide whether the extension reaches Lost Cities")

print("\n" + "=" * 72)
print("not checked here, and why")
print("  catchSphereFeatureErrors  needs a sphere landscape with a faulting pack")
print("  detailedFaultReports      needs a pack that faults during generation")
print("  fixBelowPart              needs a building gated on belowpart")
print("  anchorCitiesButton, fixCustomizeCrash, rightClickCyclesProfilesBack")
print("                            client only, a dedicated server never loads them")

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("every toggle checked here changes what the mod does, in both directions")
print("all checks passed")
