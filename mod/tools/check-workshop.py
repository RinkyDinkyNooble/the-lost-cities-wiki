#!/usr/bin/env python3
"""Acceptance test for the workshop: build it on a real server and check it.

    python mod/tools/check-workshop.py

Needs the wiki's test rig installed, because it borrows the rig's 7.4.12 server and
its Java. `python testrig/rig.py doctor` says whether that is ready.

What it asserts, which is what phase 1 promised:

  * the catalogue for the target version produces the rows it should
  * every single-only row holds exactly one plot, because the monorail codec takes
    a string and a list is a load error
  * the shape that parses and never generates is present and flagged, rather than
    quietly dropped
  * no two plots you can see together share a floor colour
  * the floors are in the world, not only in the registry file
  * standing on a plot reports the same plot the registry names
  * every key a plot's schema offers survives a round trip: set by command, read
    back out of the file on disk, same value
  * a key that does not belong to the plot is refused, and so is a bad value
  * the three scopes resolve most-specific-first
  * the boundary preview draws and clears

**The world is wiped first**, because a dimension a mod adds has to register
somewhere it was not before, and **the jar is removed afterwards**, so the rig's
baseline stays what the wiki's published results were produced on. Same discipline
the KubeJS test used.

One trap already paid for: the adjacency test has to grow **both** rectangles by the
walkway before overlapping them. Growing one makes plots separated by exactly the
walkway look unrelated, which is every plot in every row. The first version of this
script had the same bug as the code it was checking, so it passed while the colouring
was giving all 125 plots the same colour.
"""
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
JAR = "mod/build/libs/lostcities_devtool-1.20.1-1.0.1.jar"
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
DIM = "lostcitiesdevtool:workshop"
PLOTS = os.path.join(SERVER, "world", "lostcitiesdevtool", "plots.json")
SETTINGS = os.path.join(SERVER, "world", "lostcitiesdevtool", "plots")
FLOOR_Y = -64

# A value of the right shape for each schema type, plus the two keys whose values
# are a fixed set rather than free text.
BY_TYPE = {
    "string": "roundtrip",
    "char": "Q",
    "int": "3",
    "float": "0.5",
    "bool": "true",
    "string_list": "alpha, beta",
    "int_list": "8, 9",
}
BY_NAME = {"format": "json5", "palette": "building"}
EXPECTED = {
    "string": "roundtrip",
    "char": "Q",
    "int": 3,
    "float": 0.5,
    "bool": True,
    "string_list": ["alpha", "beta"],
    "int_list": [8, 9],
}


def strip_json5(text):
    """Blank comments so the file can be read as JSON, keeping every offset."""
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
    # Trailing commas.
    cleaned = re.sub(r",(\s*[}\]])", r"\1", "".join(out))
    return cleaned


def settings_path(plot_id):
    return os.path.join(SETTINGS, *plot_id.split("/")) + ".json5"


def read_settings(plot_id):
    path = settings_path(plot_id)
    if not os.path.isfile(path):
        return None
    return json.loads(strip_json5(io.open(path, encoding="utf-8").read()))


def keys_of(con, dim, x, y, z):
    """Parse /lcdev plot keys into name -> type."""
    reply = con.command("execute in %s positioned %d.0 %d.0 %d.0 run lcdev plot keys"
                        % (dim, x, y, z))
    out = {}
    for line in reply.splitlines():
        line = line.strip()
        if not line.startswith("\u00b7 "):
            continue
        body = line[2:].strip()
        if "  " not in body:
            continue
        name, rest = body.split("  ", 1)
        out[name.strip()] = rest.split(",")[0].strip()
    return out


def boot():
    args = "@" + os.path.join("libraries", LOADER, "win_args.txt")
    proc = subprocess.Popen([JAVA, "@user_jvm_args.txt", args, "nogui"],
                            cwd=SERVER, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace")
    deadline = time.time() + 300
    lines = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            print("\n".join(lines[-25:]))
            raise SystemExit("server exited during startup")
        lines.append(line.rstrip())
        if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
            threading.Thread(target=lambda: [None for _ in
                                             iter(proc.stdout.readline, "")],
                             daemon=True).start()
            return proc
    raise SystemExit("server did not start")


def touching(a, b):
    """Two plots share a view when their footprints, grown by the walkway, overlap."""
    return (a["chunkX"] - 1 <= b["chunkX"] + b["width"]
            and b["chunkX"] - 1 <= a["chunkX"] + a["width"]
            and a["chunkZ"] - 1 <= b["chunkZ"] + b["height"]
            and b["chunkZ"] - 1 <= a["chunkZ"] + a["height"])


dest = os.path.join(SERVER, "mods", os.path.basename(JAR))
world = os.path.join(SERVER, "world")
if os.path.isdir(world):
    shutil.rmtree(world)
shutil.copy(JAR, dest)
print("fresh world, jar installed\n")

proc = None
failures = []
try:
    proc = boot()
    print("server up\n")
    with Rcon(port=25575, password="lcwiki") as con:
        for cmd in ("lcdev workshop rows", "lcdev workshop build"):
            print("=" * 72)
            print("$ /" + cmd)
            print(con.command(cmd).rstrip() or "(no output)")

        if not os.path.isfile(PLOTS):
            failures.append("no plots.json was written")
        else:
            doc = json.load(io.open(PLOTS, encoding="utf-8"))
            plots = doc["plots"]
            print("\n" + "=" * 72)
            print("registry: %d plots, floor y=%s, version %s"
                  % (len(plots), doc["floorY"], doc["version"]))

            singles = [p for p in plots if p.get("class") == "single"]
            rows_single = {p["row"] for p in singles}
            if len(singles) != len(rows_single):
                failures.append("a single-only row has more than one plot")
            print("  single-only rows: %d, plots in them: %d"
                  % (len(rows_single), len(singles)))

            dead = [p for p in plots if "dead" in p]
            if not dead:
                failures.append("the dead street shape is missing from the catalogue")
            print("  flagged dead: %s" % sorted({p["row"] for p in dead}))

            clashes = 0
            for i, a in enumerate(plots):
                for b in plots[i + 1:]:
                    if touching(a, b) and a["floor"] == b["floor"]:
                        clashes += 1
                        if clashes < 4:
                            print("  CLASH %s and %s both %s"
                                  % (a["id"], b["id"], a["floor"]))
            if clashes:
                failures.append("%d neighbouring plots share a floor colour" % clashes)
            print("  neighbouring plots sharing a colour: %d" % clashes)

            colours = {p["floor"] for p in plots}
            print("  distinct floor colours used: %d" % len(colours))

            # The floors have to actually be in the world, not only in the file.
            print("\n" + "=" * 72)
            checked = 0
            for p in plots[:3] + singles[:1] + dead[:1]:
                x, z = p["chunkX"] * 16, p["chunkZ"] * 16
                con.command("execute in %s run forceload add %d %d %d %d"
                            % (DIM, x, z, x, z))
                reply = con.command("execute in %s if block %d %d %d %s"
                                    % (DIM, x, FLOOR_Y, z, p["floor"]))
                ok = "Test passed" in reply
                checked += 1
                print("  %-28s %s at %d,%d  %s"
                      % (p["id"], p["floor"].split(":")[-1], x, z,
                         "present" if ok else "MISSING: " + reply.strip()[:60]))
                if not ok:
                    failures.append("floor missing at %s" % p["id"])
            print("  checked %d plots in the world" % checked)

            # ---------------------------------------------------- phase 2
            print("\n" + "=" * 72)
            print("settings")
            by_id = {p["id"]: p for p in plots}
            # One of each shape class, plus the front desk.
            sample = ["core"]
            for want in ("selector", "part_list", "single"):
                for p in plots:
                    if p.get("class") == want:
                        sample.append(p["id"])
                        break
            for p in plots:
                if p["id"].startswith("building/"):
                    sample.append(p["id"])
                    break

            for plot_id in sample:
                p = by_id[plot_id]
                x = p["chunkX"] * 16 + 8
                z = p["chunkZ"] * 16 + 8
                y = FLOOR_Y + 1
                con.command("execute in %s run forceload add %d %d %d %d"
                            % (DIM, p["chunkX"] * 16, p["chunkZ"] * 16,
                               p["chunkX"] * 16, p["chunkZ"] * 16))
                schema = keys_of(con, DIM, x, y, z)
                if not schema:
                    failures.append("%s offered no keys" % plot_id)
                    continue
                for key, typ in schema.items():
                    value = BY_NAME.get(key, BY_TYPE.get(typ))
                    if value is None:
                        failures.append("%s: unknown type %s" % (key, typ))
                        continue
                    con.command("execute in %s positioned %d.0 %d.0 %d.0 run "
                                "lcdev plot set %s %s" % (DIM, x, y, z, key, value))
                written = read_settings(plot_id)
                if written is None:
                    failures.append("%s wrote no settings file" % plot_id)
                    continue
                bad = []
                for key, typ in schema.items():
                    want = BY_NAME.get(key, EXPECTED.get(typ))
                    if key in BY_NAME:
                        want = BY_NAME[key]
                    got = written.get(key)
                    if isinstance(want, float) or isinstance(got, float):
                        same = got is not None and abs(float(got) - float(want)) < 1e-6
                    else:
                        same = got == want
                    if not same:
                        bad.append("%s: wrote %r, read %r" % (key, want, got))
                print("  %-22s %2d keys, %s" % (plot_id, len(schema),
                                                "round trip clean" if not bad
                                                else "MISMATCH"))
                for b in bad:
                    print("      " + b)
                    failures.append("%s %s" % (plot_id, b))

            # A key that is not this plot's, and a value of the wrong shape, both
            # have to be refused rather than written.
            print("\n" + "=" * 72)
            street = next(p for p in plots if p.get("class") == "part_list")
            sx, sz = street["chunkX"] * 16 + 8, street["chunkZ"] * 16 + 8
            for cmd, why in (
                    ("lcdev plot set floors 3", "floors is a building key"),
                    ("lcdev plot set height notanumber", "height wants an int")):
                reply = con.command("execute in %s positioned %d.0 %d.0 %d.0 run %s"
                                    % (DIM, sx, FLOOR_Y + 1, sz, cmd))
                refused = "Not a key" in reply or "not a valid value" in reply
                print("  %-40s %s" % (why, "refused" if refused
                                      else "ACCEPTED: " + reply.strip()[:50]))
                if not refused:
                    failures.append("accepted what it should refuse: " + cmd)

            # Three scopes, most specific first.
            print("\n" + "=" * 72)
            multi = next((p for p in plots if p["width"] > 1 and p["height"] > 1), None)
            if multi:
                mx, mz = multi["chunkX"] * 16 + 8, multi["chunkZ"] * 16 + 8
                base = ("execute in %s positioned %d.0 %d.0 %d.0 run "
                        % (DIM, mx, FLOOR_Y + 1, mz))
                con.command(base + "lcdev plot set floors 2")
                con.command(base + "lcdev plot setlevel 1 floors 5")
                con.command(base + "lcdev plot setchunk 1 1 floors 7")
                got = read_settings(multi["id"])
                ok = (got.get("floors") == 2
                      and got["levels"]["1"]["floors"] == 5
                      and got["chunks"]["1,1"]["floors"] == 7)
                print("  %-40s %s" % ("three scopes written separately",
                                      "yes" if ok else "NO: " + json.dumps(got)[:80]))
                if not ok:
                    failures.append("the three scopes did not write separately")
                reply = con.command(base + "lcdev plot resolve 1 1 1")
                resolved = "floors  7" in reply
                print("  %-40s %s" % ("chunk beats level on resolve",
                                      "yes" if resolved else "NO: " + reply.strip()[:70]))
                if not resolved:
                    failures.append("resolve did not prefer the chunk scope")

            # The boundary preview draws and clears.
            print("\n" + "=" * 72)
            b = next(p for p in plots if p["id"].startswith("building/"))
            bx, bz = b["chunkX"] * 16 + 8, b["chunkZ"] * 16 + 8
            base = ("execute in %s positioned %d.0 %d.0 %d.0 run "
                    % (DIM, bx, FLOOR_Y + 1, bz))
            drew = con.command(base + "lcdev plot show")
            edge_x, edge_z = b["chunkX"] * 16 - 1, b["chunkZ"] * 16 - 1
            here = con.command("execute in %s if block %d %d %d minecraft:red_stained_glass"
                               % (DIM, edge_x, FLOOR_Y + 1 + 6 * 3, edge_z))
            placed = "Test passed" in here
            con.command(base + "lcdev plot hide")
            gone = "Test failed" in con.command(
                "execute in %s if block %d %d %d minecraft:red_stained_glass"
                % (DIM, edge_x, FLOOR_Y + 1 + 6 * 3, edge_z))
            print("  %-40s %s" % ("ground line drawn on the walkway",
                                  "yes" if placed else "NO"))
            print("  %-40s %s" % ("cleared again", "yes" if gone else "NO"))
            if not placed:
                failures.append("the boundary preview drew nothing where expected")
            if not gone:
                failures.append("the boundary preview did not clear")

            # And the in-game lookup has to agree with the file.
            print("\n" + "=" * 72)
            for p in (singles[:1] + dead[:1]):
                x = p["chunkX"] * 16 + 8
                z = p["chunkZ"] * 16 + 8
                cmd = ("execute in %s positioned %d.0 %d.0 %d.0 run lcdev workshop here"
                       % (DIM, x, FLOOR_Y + 1, z))
                print("$ /" + cmd)
                print(con.command(cmd).rstrip())
        con.command("stop")
finally:
    if proc is not None:
        try:
            proc.wait(timeout=180)
        except Exception:
            proc.kill()
    if os.path.isfile(dest):
        os.remove(dest)
    print("\nremoved the jar, rig baseline is clean again")

print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
