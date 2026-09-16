#!/usr/bin/env python3
"""Acceptance test for the city style a profile names and no world style does.

    python mod/tools/check-import-profile.py

Needs the wiki's test rig, the same way the other server checks do.

Generation starts from a profile, not from a world style. The profile picks the
world style and may also name a `cityStyleAlternative` that no world style
mentions, entered whenever a city's factor falls below `cityStyleThreshold`. An
import that walked only `world.citystyles` never visited that second style, so
every asset living under it stayed out of the workshop and the pack came in
looking smaller than it is. Reported from the field against ChaosZPack, whose
world style lists only `standard` while its profile names `citystyle_border1`.

The fixture is that report in miniature: one world style listing exactly one city
style, a second city style it does not mention, and a profile joining them. Each
style holds one building made of one distinctive block, so "did it arrive" is a
block count rather than a judgement.

What it asserts, in two boots:

  case A, threshold 0.3, the style is reachable in game
  * the building under the world style's own city style still imports, which is
    the control: the fix must not cost the path that already worked
  * the building under the profile's alternative style imports at all, which is
    the bug
  * both really landed as blocks, not just as settings files
  * the import recorded the profile keys an export needs to write back
  * an export keeps the alternative out of the world style's `citystyles` list,
    because listing it would weight it against the others and roll it for
    ordinary cities, which is a pack that generates differently from the one
    that was read
  * the alternative's own asset is still written, and the exported profile points
    at it under the new namespace rather than at `lostcities:`

  case B, threshold left at the -1.0 default, so no city factor falls below it
  * the import says the alternative is unreachable, and imports it anyway

The world is wiped first, the profile removed afterwards and the jar removed with
it, so the rig's baseline stays what the wiki's published results were produced
on.
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
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
SETTINGS = os.path.join(WORLD, "lostcitiesdevtool", "plots")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
PROFILES = os.path.join(SERVER, "config", "lostcities", "profiles")
PROFILE = os.path.join(PROFILES, "devtoolprofilecheck.json")
WORKSHOP = "lostcitiesdevtool:workshop"

NS = "prof"
# One block per style, so a count answers which style was walked. Neither is used
# by anything the mod or Lost Cities ships, so a non-zero count can only have come
# from this pack.
PRIMARY_BLOCK = "minecraft:gold_block"
ALT_BLOCK = "minecraft:emerald_block"

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def ok(msg):
    print("  ok   " + msg)


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


def solid(ch):
    """One part: six layers of one character."""
    return [[ch * 16 for _ in range(16)] for _ in range(6)]


def house(block_char):
    return {"refpalette": NS + ":main", "filler": block_char,
            "minfloors": 1, "maxfloors": 1, "mincellars": 0, "maxcellars": 0,
            "parts": [{"part": NS + ":p" + block_char, "ground": True,
                       "top": True}]}


def write_pack(root):
    data = os.path.join(root, "data", NS, "lostcities")
    assets = {
        # Exactly one city style, which is the whole point: `alt` is defined,
        # is referenced by the profile, and is not named here.
        "worldstyles/main": {
            "outsidestyle": NS + ":outside",
            "citystyles": [{"factor": 1.0, "citystyle": NS + ":primary"}],
        },
        "citystyles/primary": {
            "style": NS + ":main",
            "streetblocks": {"border": "y", "wall": "w", "street": "S",
                             "streetbase": "b", "streetvariant": "B",
                             "width": 8},
            "selectors": {"buildings": [{"factor": 1.0,
                                         "value": NS + ":primhouse"}]},
        },
        "citystyles/alt": {
            "style": NS + ":main",
            "streetblocks": {"border": "y", "wall": "w", "street": "S",
                             "streetbase": "b", "streetvariant": "B",
                             "width": 8},
            "selectors": {"buildings": [{"factor": 1.0,
                                         "value": NS + ":althouse"}]},
        },
        "styles/main": {"randompalettes": [[{"factor": 1.0,
                                             "palette": NS + ":main"}]]},
        "styles/outside": {"randompalettes": [[{"factor": 1.0,
                                                "palette": NS + ":main"}]]},
        "palettes/main": {"palette": [
            {"char": "g", "block": PRIMARY_BLOCK},
            {"char": "e", "block": ALT_BLOCK},
            {"char": "y", "block": "minecraft:stone"},
            {"char": "w", "block": "minecraft:stone"},
            {"char": "S", "block": "minecraft:stone"},
            {"char": "b", "block": "minecraft:stone"},
            {"char": "B", "block": "minecraft:stone"},
        ]},
        "buildings/primhouse": house("g"),
        "buildings/althouse": house("e"),
        "parts/pg": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                     "slices": solid("g")},
        "parts/pe": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                     "slices": solid("e")},
    }
    for name, body in assets.items():
        path = os.path.join(data, *name.split("/")) + ".json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write(
            json.dumps(body, indent=2) + "\n")
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "profile"}}))


def write_profile(threshold):
    """The join between config and datapack, in the sections the mod reads.

    A key in the wrong section is not an error and is not reported: it is simply
    never read. `worldStyle` is `lostcity` and both city style keys are `cities`,
    which is what the shipped profiles do.
    """
    os.makedirs(PROFILES, exist_ok=True)
    io.open(PROFILE, "w", encoding="utf-8", newline="\n").write(json.dumps({
        "lostcity": {"worldStyle": NS + ":main"},
        "cities": {"cityStyleAlternative": NS + ":alt",
                   "cityStyleThreshold": threshold},
    }, indent=2) + "\n")


# Removed however this exits. A profile left behind names a world style that only
# this check's datapack defines, and every later check would boot into a profile
# whose world style does not resolve.
def cleanup():
    if os.path.isfile(PROFILE):
        os.remove(PROFILE)


atexit.register(cleanup)


# The whole column a plot can hold, rather than the layers a building was
# expected to occupy. Where the paste starts is the workshop's business and it is
# not where the floor is: guessing at it gave an all-air region and two failures
# that looked like a palette which had not resolved. 16 by 16 by 25 is 6400
# blocks, well inside the 32768 `/clone` refuses, and a region over that limit
# counts nothing rather than erroring.
COLUMN_BOTTOM = -64
COLUMN_TOP = -40


def blocks_at(con, plot, block):
    """How many of one block stand anywhere on a plot's column."""
    x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
    # Both ends. Leaving the source unloaded returns zero rather than an error,
    # which reads exactly like a building that never pasted.
    con.command("execute in %s run forceload add %d %d %d %d"
                % (WORKSHOP, x, z, x + 15, z + 15))
    con.command("execute in %s run forceload add 3990 3990 4031 4031" % WORKSHOP)
    reply = con.command("execute in %s run clone %d %d %d %d %d %d 4000 %d 4000 "
                        "filtered %s"
                        % (WORKSHOP, x, COLUMN_BOTTOM, z, x + 15, COLUMN_TOP,
                           z + 15, COLUMN_BOTTOM, block))
    found = re.search(r"([0-9]+) block", reply)
    if not found:
        # A clone that refused says so, and a check that swallowed the reply
        # would report the refusal as an empty plot.
        print("    clone gave: %s" % reply.strip()[:160])
    return int(found.group(1)) if found else 0


def run_case(label, threshold, assertions):
    print("\n" + "=" * 72)
    print(label)
    print("=" * 72)
    for path in (WORLD, EXPORTS):
        if os.path.isdir(path):
            shutil.rmtree(path)
    rig.install(SERVER, JAR)
    write_pack(os.path.join(WORLD, "datapacks", "profpack"))
    write_profile(threshold)
    proc = boot()
    try:
        with Rcon(port=25575, password="lcwiki") as con:
            con.command("lcdev workshop build")
            # The clone destination has to be loaded too, or every count comes
            # back zero and the comparison silently measures nothing.
            con.command("execute in %s run forceload add 3990 3990 4030 4030"
                        % WORKSHOP)
            output = con.command("lcdev import %s:main" % NS)
            print(output.rstrip()[-1200:])
            assertions(con, output)
    finally:
        try:
            with Rcon(port=25575, password="lcwiki") as con:
                con.command("stop")
        except Exception:
            proc.kill()
        proc.wait(timeout=120)


# --------------------------------------------------------------- case A

def case_a(con, output):
    plots = {p["id"]: p for p in
             json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}

    # Which plot holds which building. The import names plots after the asset, so
    # the settings are what say where each one landed.
    placed = {}
    for pid in plots:
        if not pid.startswith("building/1x1/"):
            continue
        s = settings_of(pid)
        if s and s.get("name"):
            placed[s["name"]] = (pid, s)

    print("\nbuildings that got a plot: %s" % sorted(placed))

    if "primhouse" in placed:
        ok("the world style's own city style still imports (control)")
    else:
        fail("primhouse did not import, so the path that already worked broke")

    if "althouse" in placed:
        ok("the profile's alternative city style imports")
    else:
        fail("althouse did not import: the profile's cityStyleAlternative was "
             "not walked, which is the bug this check exists for")

    # Settings files are not the claim. Blocks are.
    #
    # Each building is one floor of six 16x16 layers of its own block, so a plot
    # that pasted holds about 1536 of it. "Greater than zero" would wave through a
    # plot where the palette resolved to nothing and a dozen blocks landed, and
    # counting the other pack's block on the same plot is what catches the two
    # buildings arriving on each other's plots.
    for name, mine, theirs in (("primhouse", PRIMARY_BLOCK, ALT_BLOCK),
                               ("althouse", ALT_BLOCK, PRIMARY_BLOCK)):
        if name not in placed:
            continue
        pid, _ = placed[name]
        count = blocks_at(con, plots[pid], mine)
        other = blocks_at(con, plots[pid], theirs)
        print("  %s on %s: %d of %s, %d of %s"
              % (name, pid, count, mine, other, theirs))
        if count < 500:
            fail("only %d of %s pasted for %s, so the palette did not resolve"
                 % (count, mine, name))
        elif other > 0:
            fail("%s's plot also holds %d of %s, so the two buildings did not "
                 "land on their own plots" % (name, other, theirs))
        else:
            ok("%s really landed as blocks, and only its own" % name)

    if "althouse" in placed:
        styles = placed["althouse"][1].get("citystyles") or []
        if "alt" in styles:
            ok("althouse's plot names the alternative style: %s" % styles)
        else:
            fail("althouse's plot names %s, not alt, so an export would write "
                 "it into the wrong city style" % styles)

    core = settings_of("core") or {}
    profile = core.get("profile") or {}
    if profile.get("cityStyleAlternative") == "alt":
        ok("the import recorded cityStyleAlternative for the export")
    else:
        fail("core settings hold profile=%r, so an export cannot put the style "
             "back where it came from" % (profile,))
    if abs(float(profile.get("cityStyleThreshold", 0)) - 0.3) < 1e-6:
        ok("the import recorded cityStyleThreshold")
    else:
        fail("cityStyleThreshold came back as %r, not 0.3"
             % (profile.get("cityStyleThreshold"),))

    # ------------------------------------------------------------- the export
    print("\n" + "-" * 72)
    print(con.command("lcdev export profout -f").rstrip()[-600:])
    root = os.path.join(EXPORTS, "profout")
    ns = (settings_of("core") or {}).get("namespace", "mypack")
    data = os.path.join(root, "data", ns, "lostcities")

    world_path = os.path.join(data, "worldstyles", "main.json")
    if not os.path.isfile(world_path):
        fail("no world style was exported at %s" % world_path)
        return
    world = json.load(io.open(world_path, encoding="utf-8"))
    listed = [e.get("citystyle") for e in world.get("citystyles", [])]
    print("  exported world style lists: %s" % listed)
    if any(str(c).endswith(":primary") for c in listed):
        ok("the primary style is listed on the world style")
    else:
        fail("the primary style is missing from the exported world style")
    if any(str(c).endswith(":alt") for c in listed):
        fail("the alternative style was promoted into the world style's "
             "citystyles list, so it would be rolled for ordinary cities and "
             "the pack generates differently from the one that was imported")
    else:
        ok("the alternative style is kept out of the world style's list")

    alt_asset = os.path.join(data, "citystyles", "alt.json")
    if os.path.isfile(alt_asset):
        ok("the alternative style's own asset is still written")
    else:
        fail("no citystyles/alt.json was written, so the style was dropped "
             "rather than moved")

    written = os.path.join(root, "profile", "profout.json")
    if not os.path.isfile(written):
        fail("no profile was written beside the pack at %s" % written)
        return
    got = json.load(io.open(written, encoding="utf-8"))
    alt = (got.get("cities") or {}).get("cityStyleAlternative")
    print("  exported profile cities.cityStyleAlternative = %r" % alt)
    if alt == ns + ":alt":
        ok("the exported profile points at the pack's own alternative style")
    elif alt and ":" not in str(alt):
        fail("the exported profile names %r unqualified, which Lost Cities "
             "reads as lostcities:%s and is the wrong pack" % (alt, alt))
    else:
        fail("the exported profile names %r, not %s:alt" % (alt, ns))


# --------------------------------------------------------------- case B

def case_b(con, output):
    plots = {p["id"]: p for p in
             json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
    names = set()
    for pid in plots:
        if pid.startswith("building/1x1/"):
            s = settings_of(pid)
            if s and s.get("name"):
                names.add(s["name"])

    if "althouse" in names:
        ok("an unreachable alternative is imported anyway")
    else:
        fail("althouse was dropped when the threshold made it unreachable; it "
             "should import and warn")

    said = "never reaches it" in output or "cityStyleThreshold" in output
    if said:
        ok("the import says the alternative is never reached")
    else:
        fail("the import said nothing about cityStyleThreshold being -1.0, so "
             "a pack whose alternative style can never generate looks correct")


print("check-import-profile: a city style only a profile names")
print("jar: %s" % os.path.basename(JAR))

run_case("case A: cityStyleThreshold 0.3, the alternative is reachable",
         0.3, case_a)
run_case("case B: cityStyleThreshold -1.0, the default, nothing falls below it",
         -1.0, case_b)

print("\n" + "=" * 72)
if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("PASS")
