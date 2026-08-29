#!/usr/bin/env python3
"""The terms a pack states are found, shown, and carried into what is compiled.

    python mod/tools/check-licence.py

Needs the wiki's test rig, the same way the other server checks do. The text half of
this, where a licence is cut down for a chat line and several are folded into one
notice, is check-licence-text.py and runs in a second without a server.

What it asserts, and why each one is here rather than assumed:

  * a licence at `data/<namespace>/lostcities/license.txt` is found. That is the
    primary path and the only one that works for a pack living inside KubeJS or
    inside a mod jar, neither of which has a root of its own.

  * a licence at the root of a **folder** pack is found. `getRootResource` cannot
    reach it: it validates every path segment against `[-._a-z0-9]+` and throws on
    an uppercase one, so `LICENSE.txt`, the commonest spelling of the commonest
    file, is exactly the case the public API refuses. A zip pack has no such check.
    Two packs are laid out here because one of them cannot prove the other.

  * an oversized licence is capped in three ways at once: the read stops at 64 KB,
    three lines are shown, and each line is cut to the chat width. A licence
    written as one long paragraph satisfies a line count and defeats it.

  * a namespace stating nothing is reported as nothing found, naming both places
    looked. It does **not** assert that the content is all rights reserved and does
    not use the word illegal: a missing file is weak evidence, since plenty of packs
    state their terms on a project page, and a determination printed by a tool is
    one that can be wrong with the author's name on it.

  * the export carries what was found, and `export plot` carries that plot's
    author's terms and nobody else's. A fragment shipping the wrong author's licence
    is a false statement about somebody's work, not an untidy file.
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
import rig  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORKSHOP = "lostcitiesdevtool:workshop"
WORLD = os.path.join(SERVER, "world")
PLOTS = os.path.join(WORLD, "lostcitiesdevtool", "plots.json")
KEPT = os.path.join(WORLD, "lostcitiesdevtool", "licences")
EXPORTS = os.path.join(SERVER, "config", "lostcitiesdevtool", "exports")
BACKUPS = os.path.join(SERVER, "config", "lostcitiesdevtool", "backups")

MIT = ("MIT License\n"
       "\n"
       "Copyright (c) 2024 Pri Author\n"
       "\n"
       "Permission is hereby granted, free of charge, to any person obtaining a "
       "copy\n"
       "of this software.\n")

# Apache's own shape: blank lines, then a centred title. Taking the first three
# lines as written would show two empty ones and a run of spaces.
ROOT_LICENCE = ("\n"
                "\n"
                "                            Root Pack Licence\n"
                "                          Version 1.0, June 2024\n"
                "\n"
                "   Redistribution of the buildings is not permitted.\n")

# Over the 64 KB cap, opening with a line far wider than chat holds.
BIG_FIRST = "x" * 400
BIG = BIG_FIRST + "\n" + "".join("filler line %d\n" % i for i in range(9000))

SHAPES = ("all", "bend", "end", "full", "none", "straight", "t")

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


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def asset(root, namespace, name, body):
    write(os.path.join(root, "data", namespace, "lostcities",
                       *name.split("/")) + ".json",
          json.dumps(body, indent=2) + "\n")


def meta(root, description):
    write(os.path.join(root, "pack.mcmeta"), json.dumps(
        {"pack": {"pack_format": 15, "description": description}}, indent=2))


def solid(ch):
    return [[ch * 16 for _ in range(16)] for _ in range(6)]


def building(root, namespace, palette):
    """One building and its one part, in a namespace of its own."""
    asset(root, namespace, "buildings/tower_" + namespace, {
        "refpalette": palette, "filler": "#",
        "minfloors": 0, "maxfloors": 0, "mincellars": 0, "maxcellars": 0,
        "overrideFloors": True,
        "parts": [{"part": namespace + ":floor_" + namespace, "floor": 0}],
    })
    asset(root, namespace, "parts/floor_" + namespace, {
        "xsize": 16, "zsize": 16, "refpalette": palette, "slices": solid("#"),
    })


def city(root, namespace, buildings, street_namespace):
    """A world style whose city style names its own street parts.

    Naming them matters to this check rather than being decoration. A city style
    that says nothing about street parts falls back to the seven `StreetParts`
    defaults, which live in `lostcities`, and that namespace would then join every
    set of namespaces here and make the counts below say nothing about the packs
    this check actually wrote.
    """
    palette = namespace + ":main"
    asset(root, namespace, "worldstyles/main", {
        "outsidestyle": namespace + ":outside",
        "citystyles": [{"factor": 1.0, "citystyle": namespace + ":city"}],
    })
    asset(root, namespace, "citystyles/city", {
        "style": palette.split(":")[0] + ":main",
        "streetblocks": {
            "border": "#", "wall": "#", "street": "#", "streetbase": "#",
            "streetvariant": "#", "width": 8,
            # One part per shape. Seven shapes naming one part is seven plots
            # compiling to one file, which the export refuses and rightly.
            "parts": {shape: street_namespace + ":road_" + shape
                      for shape in SHAPES},
        },
        "selectors": {"buildings": [{"factor": 1.0, "value": b}
                                    for b in buildings]},
    })
    asset(root, namespace, "styles/main",
          {"randompalettes": [[{"factor": 1.0, "palette": palette}]]})
    asset(root, namespace, "styles/outside",
          {"randompalettes": [[{"factor": 1.0, "palette": palette}]]})
    asset(root, namespace, "palettes/main",
          {"palette": [{"char": "#", "block": "minecraft:gold_block"}]})
    for shape in SHAPES:
        asset(root, street_namespace, "parts/road_" + shape, {
            "xsize": 16, "zsize": 16, "refpalette": palette,
            "slices": solid("#"),
        })


def packs():
    """Two folder packs, because one of them cannot prove the other."""
    main = os.path.join(WORLD, "datapacks", "licpack")
    # licmain owns the world style, the city style, the palette and the road.
    # licpri, licbig and licnone each own one building, so the namespaces the
    # import reports are exactly the ones written here.
    city(main, "licmain", ["licpri:tower_licpri", "licroot:tower_licroot",
                           "licbig:tower_licbig", "licnone:tower_licnone"],
         "licmain")
    for namespace in ("licpri", "licbig", "licnone"):
        building(main, namespace, "licmain:main")
    write(os.path.join(main, "data", "licpri", "lostcities", "license.txt"), MIT)
    write(os.path.join(main, "data", "licbig", "lostcities", "license.txt"), BIG)
    meta(main, "licence primary")

    # A second pack, whose licence is only at its root and spelled the way a
    # repository spells it. Nothing under data/licroot/ states anything.
    root = os.path.join(WORLD, "datapacks", "licrootpack")
    building(root, "licroot", "licmain:main")
    write(os.path.join(root, "LICENSE.txt"), ROOT_LICENCE)
    meta(root, "licence at the root")

    # One namespace, stating nothing, reached by a world style of its own. The
    # message for a single namespace names its path in full rather than a
    # template, and that branch is only reachable this way.
    solo = os.path.join(WORLD, "datapacks", "licsolopack")
    city(solo, "licsolo", ["licsolo:tower_licsolo"], "licsolo")
    building(solo, "licsolo", "licsolo:main")
    meta(solo, "licence absent")


def carried(export):
    """The notice an exported pack carries, or None."""
    found = glob.glob(os.path.join(EXPORTS, export, "data", "*", "lostcities",
                                   "license.txt"))
    if not found:
        return None
    return io.open(found[0], encoding="utf-8").read()


def blocks(notice):
    """The namespaces a notice names."""
    return sorted(re.findall(r"^===== (\S+) =====$", notice or "", re.M))


for path in (WORLD, EXPORTS, BACKUPS):
    if os.path.isdir(path):
        shutil.rmtree(path)
dest = rig.install(SERVER, JAR)
packs()
print("fresh world, jar installed, three packs: primary, root only, none\n")

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")

        print("=" * 72)
        print("1. an import says what the authors of what it took said")
        said = con.command("lcdev import licmain:main").rstrip()
        print(said[said.find("Licence"):][:1400] if "Licence" in said
              else said[-600:])

        if "MIT License" not in said:
            fail("the licence at the primary path was not found, and it is the "
                 "only path that works for a pack inside KubeJS or a mod jar")
        if "Copyright (c) 2024 Pri Author" not in said:
            fail("only the first line was shown, so a licence that names itself "
                 "and then its holder gives away neither")
        if "data/licpri/lostcities/license.txt" not in said:
            fail("the file it read was not named, so nobody can go and read the "
                 "rest of it")

        print("\n" + "=" * 72)
        print("2. a licence only at the root of a folder pack")
        if "Root Pack Licence" not in said:
            fail("the LICENSE.txt at a folder pack's root was not found. "
                 "getRootResource refuses an uppercase path segment, so this is "
                 "the case the public API cannot reach")
        if "Version 1.0, June 2024" not in said:
            fail("the blank lines and the centring were not stripped, so a licence "
                 "laid out the way Apache lays one out shows nothing")
        # Named as well as read. Without this the case above would pass on a
        # licence found at the primary path, which is the case it exists to rule
        # out rather than the one it is testing.
        if "licrootpack/LICENSE.txt" not in said:
            fail("the terms were shown and the root file was not named, so this "
                 "does not show where they were found")

        print("\n" + "=" * 72)
        print("3. an oversized licence is capped three ways")
        if BIG_FIRST in said:
            fail("a 400 character first line reached chat whole, so the line cap "
                 "does nothing and one paragraph defeats the line count")
        if "64 KB" not in said:
            fail("a licence over the read cap was reported as though the whole of "
                 "it had been read")
        # Three lines, and the fourth is the one that proves it. Asserting only
        # that the first three are present would pass on a summary that showed
        # nine thousand.
        if "filler line 2" in said:
            fail("a fourth line of a nine thousand line licence reached chat, so "
                 "the line count is not the count")
        # Printed rather than asserted on: the count is what tells a reader a
        # permissive licence from a whole GPL, and a wrong one is worth seeing
        # even when the assertions above pass.
        for line in said.splitlines():
            if "more line" in line:
                print("  " + line.strip())
        if "1 more lines" in said:
            fail("the remainder is counted and then reported as \"1 more lines\"")

        print("\n" + "=" * 72)
        print("4. a namespace stating nothing")
        if "none found" not in said:
            fail("a namespace with no licence anywhere was not reported at all")
        if "licnone" not in said:
            fail("the namespace with nothing was not named")
        if "and the pack root" not in said:
            fail("only one of the two places looked in was named, so somebody "
                 "whose licence is not being found cannot tell why")
        if "Treat it as all rights reserved" not in said:
            fail("nothing was said about how to proceed")
        # Pointed at where terms actually live, because a namespace says nothing
        # about who wrote what is in it: a datapack can override any namespace,
        # so even the mod's own may hold somebody else's content under their own
        # terms. Naming a namespace's usual licence would be a guess dressed as
        # a fact, so the message sends the reader to the source instead.
        if "official sources" not in said:
            fail("the message did not point at where terms actually live, so a "
                 "reader with no file to read is left with only the caution")
        for word in ("illegal", "is all rights reserved", "you may not"):
            if word in said:
                fail("the output states %r, which is a determination about "
                     "somebody's work rather than advice about how to proceed"
                     % word)
        print("  kept in the world: %s"
              % sorted(os.listdir(KEPT) if os.path.isdir(KEPT) else []))

        print("\n" + "=" * 72)
        print("5. the export carries what was found")
        print(con.command("lcdev export whole").rstrip()[-320:])
        notice = carried("whole")
        print("  namespaces the pack carries: %s" % blocks(notice))
        if notice is None:
            fail("the pack was compiled out of three licensed namespaces and "
                 "shipped no statement at all")
        else:
            for namespace in ("licpri", "licroot", "licbig"):
                if namespace not in blocks(notice):
                    fail("%s stated terms and the pack does not carry them"
                         % namespace)
            if "licnone" in blocks(notice):
                fail("licnone states nothing, so a block naming it claims "
                     "something that was never written")
            if "Copyright (c) 2024 Pri Author" not in notice:
                fail("the statement was named and not reproduced, and a licence "
                     "summarised is no longer the licence")
            if len(notice) > 128 * 1024:
                fail("the notice is %d bytes, so the read cap is not reaching the "
                     "file that is written" % len(notice))

        print("\n" + "=" * 72)
        print("6. one plot carries its own author's terms and nobody else's")
        plots = {p["id"]: p for p in
                 json.load(io.open(PLOTS, encoding="utf-8"))["plots"]}
        # Which plot holds which building is decided by the order the selector
        # was walked, so it is read back rather than assumed.
        target = None
        for index in range(4):
            path = os.path.join(WORLD, "lostcitiesdevtool", "plots", "building",
                                "1x1", "%d.json5" % index)
            if os.path.isfile(path) and "licpri" in io.open(
                    path, encoding="utf-8").read():
                target = "building/1x1/%d" % index
                break
        if target is None:
            fail("no plot says it came from licpri, so the export has nothing to "
                 "read and this case is not being tested")
        else:
            plot = plots[target]
            x, z = plot["chunkX"] * 16 + 8, plot["chunkZ"] * 16 + 8
            print("  standing on %s" % target)
            print(con.command("execute in %s positioned %d 10 %d run lcdev export "
                              "one plot" % (WORKSHOP, x, z)).rstrip()[-260:])
            one = carried("one")
            print("  namespaces the fragment carries: %s" % blocks(one))
            if one is None:
                fail("a fragment lifted out of somebody's pack carries no "
                     "statement, which is exactly when attribution should follow")
            elif blocks(one) != ["licpri"]:
                fail("the fragment carries %s, and it holds one building from "
                     "licpri. Terms of an author whose work is not in the file "
                     "are a false statement about it" % blocks(one))

        print("\n" + "=" * 72)
        print("7. one namespace with nothing names its path in full")
        said = con.command("lcdev import licsolo:main").rstrip()
        print(said[said.find("Licence"):][:500] if "Licence" in said
              else said[-400:])
        if "data/licsolo/lostcities/license.txt" not in said:
            fail("with one namespace to name, the message showed a template "
                 "instead of the path that namespace would use")

        print("\n" + "=" * 72)
        print("8. a kept licence that cannot be deleted does not fail the wipe")
        # A wipe drops the kept statements after it has emptied every plot,
        # deleted their settings and reset the grown rows, and before it repaints.
        # Anything thrown there leaves the workshop half done and reports the
        # whole clear as failed. Windows refuses to delete a file another process
        # holds open, so holding one is the trigger, and it is the trigger a
        # locked file or a read-only folder would produce on a real machine.
        kept = sorted(glob.glob(os.path.join(KEPT, "*.txt")))
        print("  kept: %s" % [os.path.basename(k) for k in kept])
        if not kept:
            fail("nothing is kept, so this case cannot hold one open and is not "
                 "testing what it claims")
        else:
            # Windows refuses to delete a file another process holds open, so an
            # open handle is the trigger a locked file or a read-only folder
            # would produce on a real machine.
            held = io.open(kept[0], "r", encoding="utf-8")
            try:
                done = con.command("lcdev workshop clear confirm").rstrip()
                print("  " + done.replace("\n", " ")[-300:])
                # Proof the trigger fired, taken while the handle is still open.
                # If the delete succeeded anyway then the platform did not refuse
                # it, nothing was thrown, and everything below passes without
                # having tested anything.
                blocked = os.path.isfile(kept[0])
            finally:
                held.close()
            print("  the held file survived the wipe: %s" % blocked)
            if not blocked:
                fail("the held file was deleted anyway, so nothing refused the "
                     "delete and this case proves nothing about a wipe that "
                     "meets one that cannot be dropped")
            if "could not be cleared" in done:
                fail("a kept licence that could not be deleted failed the whole "
                     "wipe, after every plot had already been emptied")
            if "Cleared" not in done:
                fail("the clear did not report clearing anything: %s"
                     % done.replace("\n", " ")[-160:])
            # Asserted through the interface rather than through the folder. What
            # somebody clearing the workshop cares about is that the plots are
            # gone, and the workshop saying so is how they see it.
            again = con.command("lcdev workshop clear").rstrip()
            print("  " + again.replace("\n", " ")[-200:])
            if "already empty" not in again:
                fail("the workshop does not report itself empty after a clear "
                     "that ran with a kept licence held open, so the wipe "
                     "stopped part way through")
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
print("what a pack's author said is found, shown, and carried into what is "
      "compiled out of it")
print("all checks passed")
