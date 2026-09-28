#!/usr/bin/env python3
"""Phase C: the flags on export and import, which decide what arrives armed.

    python mod/tools/check-cmd-io.py

Needs the wiki's test rig, the same way the other server checks do.

`export` and `import` are covered by checks of their own for what they compile and
what they paste. This is the arguments: the overwrite guard, the listing, the way a
name is resolved, and `run`, which is the one flag on either command that changes
what the world does rather than what a file holds.

What it asserts:

  * **`run` is what arms a pasted command block, and the default disarms it.** A
    palette entry can carry a command with `auto` set, which is how the
    command-block technique works: Lost Cities places the block already carrying its
    command and it fires where it lands. Pasting that into the workshop without
    disarming would run somebody else's commands the moment their pack is imported,
    which is a pack from the internet executing on the importer's server. The
    default has to be off and the flag has to be the only way on.

  * **`export` will not overwrite without being told.** Losing a pack to a repeated
    command is a bad way to learn that the command repeats.

  * **`import` with no argument lists what can be imported**, because a world style
    is a namespaced name nobody can guess, and the alternative to listing is reading
    someone else's files.

  * **An unknown world style is refused by name.** The commonest way to get this
    wrong is a bare name that means `lostcities:` rather than the pack's own
    namespace, which is the format's rule and not this mod's.
"""
import atexit
import io
import json
import os
import re
import shutil
import sys

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from rcon import Rcon  # noqa: E402
import rig  # noqa: E402
from rig import fail, failures  # noqa: E402

SERVER = rig.SERVER
JAR = rig.jar()
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
TOOLDIR = os.path.join(SERVER, "config", "lostcitiesdevtool")
EXPORTS = os.path.join(TOOLDIR, "exports")
BACKUPS = os.path.join(TOOLDIR, "backups")
SENTINEL = os.path.join(BACKUPS, "check-cmd-io", "keep.txt")
# What an export named `..` writes where the exports and backups were, on a build
# without the guard. Removed either way, so a red run leaves the rig as it found it.
STRAYS = [os.path.join(TOOLDIR, n) for n in ("data", "profile", "pack.mcmeta")]
BASE = -63
NS = "iopack"


def tidy():
    for path in STRAYS + [os.path.dirname(SENTINEL)]:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


atexit.register(tidy)


def solid(ch):
    """Six layers, with the command block at the plot's own corner on layer 0."""
    layer = [ch * 16 for _ in range(16)]
    first = ["C" + ch * 15] + [ch * 16 for _ in range(15)]
    return [first] + [layer for _ in range(5)]


def write_pack(root):
    data = os.path.join(root, "data", NS, "lostcities")
    assets = {
        "worldstyles/main": {
            "outsidestyle": NS + ":outside",
            "citystyles": [{"factor": 1.0, "citystyle": NS + ":city"}],
        },
        "citystyles/city": {
            "style": NS + ":main",
            "streetblocks": {"border": "g", "wall": "g", "street": "g",
                             "streetbase": "g", "streetvariant": "g", "width": 8},
            "selectors": {"buildings": [{"factor": 1.0, "value": NS + ":tower"}]},
        },
        "styles/main": {"randompalettes": [[{"factor": 1.0,
                                             "palette": NS + ":main"}]]},
        "styles/outside": {"randompalettes": [[{"factor": 1.0,
                                                "palette": NS + ":main"}]]},
        # `auto` set is the whole point: Lost Cities places the block already
        # carrying its command and it fires where it lands.
        "palettes/main": {"palette": [
            {"char": "g", "block": "minecraft:gold_block"},
            {"char": "C", "block": "minecraft:command_block[conditional=false,"
                                   "facing=north]",
             "tag": {"Command": "/say imported", "auto": 1, "conditionMet": 1}},
        ]},
        "buildings/tower": {
            "refpalette": NS + ":main", "filler": "g",
            "minfloors": 0, "maxfloors": 0, "mincellars": 0, "maxcellars": 0,
            "overrideFloors": True,
            "parts": [{"part": NS + ":floor", "floor": 0}],
        },
        "parts/floor": {"xsize": 16, "zsize": 16, "refpalette": NS + ":main",
                        "slices": solid("g")},
    }
    for name, body in assets.items():
        path = os.path.join(data, *name.split("/")) + ".json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write(
            json.dumps(body, indent=2) + "\n")
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "io flags"}}, indent=2))


def auto_at(con, x, y, z):
    """The `auto` byte on a pasted command block, or None if there is not one.

    The reply is checked for being block data before a number is taken out of it.
    Scraping the last digits of whatever came back would read a coordinate out of
    an error message, and a trailing 0 would then pass the disarmed case while
    there was no command block at that position at all.
    """
    said = con.command("execute in %s run data get block %d %d %d auto"
                       % (WORKSHOP, x, y, z)).strip()
    if "has the following block data" not in said:
        return None
    found = re.search(r"data:\s*([0-9]+)b?\s*$", said)
    return int(found.group(1)) if found else None


def is_command_block(con, x, y, z):
    """Whether the block there is a command block carrying the pack's command."""
    said = con.command("execute in %s run data get block %d %d %d Command"
                       % (WORKSHOP, x, y, z))
    return "imported" in said


for path in (WORLD, EXPORTS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
write_pack(os.path.join(WORLD, "datapacks", "iopack"))
print("fresh world, jar installed, a pack whose palette carries an armed command")
print("using %s\n" % os.path.basename(JAR))

proc, _ = rig.boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
        plot = plots["building/1x1/0"]
        x, z = plot["chunkX"] * 16, plot["chunkZ"] * 16
        con.command("execute in %s run forceload add %d %d %d %d"
                    % (WORKSHOP, x, z, x + 15, z + 15))

        print("=" * 72)
        print("1. import with no argument lists what can be imported")
        said = con.command("lcdev import").rstrip()
        print("  " + said.replace("\n", " ")[:260])
        if "%s:main" % NS not in said:
            fail("the loaded pack's world style is not in the listing, so the only "
                 "way to learn its name is to read somebody else's files")

        print("\n" + "=" * 72)
        print("2. an unknown world style is refused by name")
        said = con.command("lcdev import %s:nosuchstyle" % NS).rstrip()
        print("  " + said.replace("\n", " ")[:230])
        if "nosuchstyle" not in said:
            fail("importing a world style that does not exist did not name it back")

        print("\n" + "=" * 72)
        print("3. by default a pasted command block arrives disarmed")
        con.command("lcdev import %s:main" % NS)
        placed = is_command_block(con, x, BASE, z)
        armed = auto_at(con, x, BASE, z)
        print("  a command block carrying the pack's command is there: %s" % placed)
        print("  auto on the pasted command block: %s" % armed)
        if not placed:
            fail("no command block carrying the pack's command was pasted, so "
                 "neither this case nor the next is testing what it claims")
        if armed is None:
            fail("the block there did not answer with block data, so the value "
                 "below is not the auto byte of anything")
        elif armed != 0:
            fail("a command block imported from somebody else's pack arrived with "
                 "auto=%s. It fires where it lands, so importing a pack off the "
                 "internet would run its commands on the importer's server" % armed)

        print("\n" + "=" * 72)
        print("4. run is the only way to arm it")
        con.command("lcdev import %s:main run" % NS)
        armed = auto_at(con, x, BASE, z)
        print("  auto after importing with run: %s" % armed)
        if armed != 1:
            fail("importing with `run` left auto=%s, so the flag that exists to "
                 "arm a pasted command block does not" % armed)

        print("\n" + "=" * 72)
        print("5. keep leaves conversions as written, the default reverses them")
        # An export turns a placeholder into a real block and an import turns it
        # back, so a placeholder somebody stood in with survives a round trip.
        # `keep` is the way to say leave the real blocks alone. Asserted on the
        # mode the command reports, which is what a person sees; that a conversion
        # really resolves per scope is check-conversions' job.
        default = con.command("lcdev import %s:main" % NS).rstrip()
        kept = con.command("lcdev import %s:main keep" % NS).rstrip()
        print("  default: %s" % re.sub(r"\s+", " ", default)[
            max(0, default.find("conversions")):][:60])
        print("  keep:    %s" % re.sub(r"\s+", " ", kept)[
            max(0, kept.find("conversions")):][:60])
        if "reversed" not in default:
            fail("the default import did not report reversing conversions, so a "
                 "placeholder does not come back as the placeholder")
        if "left as written" not in kept:
            fail("`keep` did not report leaving conversions as written, so the "
                 "flag that exists to keep the real blocks does not reach the "
                 "importer")

        print("\n" + "=" * 72)
        print("6. export will not overwrite without being told")
        first = con.command("lcdev export once").rstrip()
        print("  " + first.replace("\n", " ")[-150:])
        again = con.command("lcdev export once").rstrip()
        print("  " + again.replace("\n", " ")[:200])
        if "already there" not in again:
            fail("exporting over a pack of the same name was allowed without -f, "
                 "so a repeated command loses the pack it wrote first")
        forced = con.command("lcdev export once -f").rstrip()
        print("  " + forced.replace("\n", " ")[-150:])
        if "Exported" not in forced:
            fail("-f did not overwrite, so there is no way to re-export a pack "
                 "under the name it already has")

        print("\n" + "=" * 72)
        print("7. a name cannot climb out of the exports folder")
        # `..` is a legal word to the argument. Resolved as written it names the
        # folder holding every export and every wipe backup, the refusal above says
        # to pass -f, and -f deleted the lot. `.` names the exports folder itself.
        # The damage is asserted before the wording, because it is the one cause.
        tidy()
        os.makedirs(os.path.dirname(SENTINEL), exist_ok=True)
        io.open(SENTINEL, "w", encoding="utf-8").write("a backup somebody needs\n")
        for name in ("..", "."):
            said = con.command("lcdev export %s -f" % name).rstrip()
            print("  %-3s %s" % (name, said.replace("\n", " ")[:170]))
            if not os.path.isfile(SENTINEL):
                fail("an export named %s deleted a wipe backup outside the exports "
                     "folder" % name)
                break
            if not os.path.isdir(os.path.join(EXPORTS, "once")):
                fail("an export named %s deleted the export written in case 6" % name)
                break
            if "cannot name an export" not in said:
                fail("an export named %s was not refused with the rule it broke"
                     % name)

        print("\n" + "=" * 72)
        print("8. a hand-edited value the export cannot read is refused by name")
        # The settings file says it is safe to edit by hand, so a word where a
        # number belongs is the ordinary mistake. Gson threw on it and the command
        # answered "An unexpected error occurred", naming neither plot nor key.
        hand = os.path.join(WORLD, "lostcitiesdevtool", "plots", "building", "1x1",
                            "5.json5")
        os.makedirs(os.path.dirname(hand), exist_ok=True)
        io.open(hand, "w", encoding="utf-8", newline="\n").write(json.dumps({
            "name": "handmade", "citystyles": ["city"], "floors": 1,
            "cellars": 0, "factor": "lots"}))
        said = con.command("lcdev export hand -f").rstrip()
        flat = re.sub(r"\s+", " ", said)
        print("  " + flat[:230])
        if os.path.isdir(os.path.join(EXPORTS, "hand")):
            fail("a pack was written with a factor nobody can read")
        elif "building/1x1/5" not in flat or "factor" not in flat:
            fail("the export did not name the plot and the key it could not read")
        os.remove(hand)
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
print("a pasted command arrives disarmed unless asked for, and an export will not "
      "quietly replace one")
print("all checks passed")
