#!/usr/bin/env python3
"""The rig itself: its command line answers, and a check boots its own Lost Cities.

    python mod/tools/check-rig.py

No server. Reports through a failure list of its own rather than `rig.fail`,
because the file under test cannot also be the thing that says whether it works.

What it asserts:

  * **`testrig/rig.py` is a command line as well as the checks' library.** It was
    once replaced by a helper for the checks alone, and `doctor`, `list`, `install`,
    `run` and `matrix` then printed nothing and exited 0, while four documents told
    people to run them.

  * **The checks' target comes from `versions.json`.** `"checks"` names a version
    the manifest knows, on a server that is installed, which is what makes moving
    the checks one line.

  * **`rig.install` puts the checks' Lost Cities jar in place.** The claim tests
    share the server and leave their own version in its mods folder. Planted here as
    another Lost Cities jar; after an install the mods folder has to hold the one
    `"checks"` names and no other.
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

sys.path.insert(0, "testrig")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rig  # noqa: E402

MANIFEST = json.load(io.open("testrig/versions.json", encoding="utf-8"))

failures = []


def fail(msg):
    failures.append(msg)
    print("  FAIL " + msg)


def cli(*args):
    run = subprocess.run([sys.executable, "testrig/rig.py", *args],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    return run.returncode, run.stdout + run.stderr


# -------------------------------------------------------------------- 1. the CLI

print("1. the command line answers")
code, out = cli("list")
rows = [ln for ln in out.splitlines()
        if re.match(r"^[ *](\d+\.\d+\.\d+)\s", ln)]
print("  list: exit %d, %d version rows, %d in the manifest"
      % (code, len(rows), len(MANIFEST["versions"])))
if code != 0 or len(rows) != len(MANIFEST["versions"]):
    fail("`rig.py list` gave %d rows for %d versions, exit %d"
         % (len(rows), len(MANIFEST["versions"]), code))

checks = MANIFEST.get("checks")
code, out = cli("doctor", str(checks))
print("  doctor %s: exit %d, %s" % (checks, code,
                                    out.strip().splitlines()[-1] if out.strip()
                                    else "no output"))
if code != 0 or "versions ready" not in out:
    fail("`rig.py doctor %s` did not report readiness" % checks)

# ------------------------------------------------------------------ 2. the target

print("\n2. the checks' target comes from versions.json")
if checks not in MANIFEST["versions"]:
    fail("versions.json names %r under checks, which is not a version it knows"
         % checks)
else:
    key = MANIFEST["versions"][checks]["server"]
    args = os.path.join(getattr(rig, "SERVER", ""), "libraries",
                        MANIFEST["servers"][key]["loader_dir"], "win_args.txt")
    print("  checks %s on %s, SERVER %s" % (checks, key, getattr(rig, "SERVER", None)))
    if getattr(rig, "SERVER", None) != "testrig/servers/" + key:
        fail("rig.SERVER is %r, not the server of the checks' version"
             % getattr(rig, "SERVER", None))
    elif not os.path.isfile(args):
        fail("the checks' server is not installed: no %s" % args)

# ------------------------------------------------------- 3. its own Lost Cities

print("\n3. an install puts the checks' Lost Cities jar in place")
SERVER = "testrig/servers/" + MANIFEST["versions"][checks]["server"]
MODS = os.path.join(SERVER, "mods")
WANT = MANIFEST["versions"][checks]["mod_jar"]
OTHER = next((v["mod_jar"] for name, v in MANIFEST["versions"].items()
              if name != checks and v["server"] == MANIFEST["versions"][checks]["server"]
              and os.path.isfile(os.path.join("testrig", "downloads", v["mod_jar"]))),
             None)
before = sorted(os.listdir(MODS)) if os.path.isdir(MODS) else []
AWAY = os.path.join("testrig", ".rigcache", "check-rig")


def restore():
    """Leave the mods folder as it was found, whatever the install did."""
    if not os.path.isdir(MODS):
        return
    for entry in os.listdir(MODS):
        if entry not in before:
            os.remove(os.path.join(MODS, entry))
    for entry in before:
        if not os.path.isfile(os.path.join(MODS, entry)) \
                and os.path.isfile(os.path.join(AWAY, entry)):
            shutil.copy(os.path.join(AWAY, entry), os.path.join(MODS, entry))
    if os.path.isdir(AWAY):
        shutil.rmtree(AWAY)


atexit.register(restore)

if OTHER is None:
    fail("no second Lost Cities jar for the checks' server in testrig/downloads, "
         "so the swap cannot be planted")
else:
    os.makedirs(AWAY, exist_ok=True)
    for entry in before:
        shutil.copy(os.path.join(MODS, entry), os.path.join(AWAY, entry))
        if re.match(r"(?i)lostcities-", entry):
            os.remove(os.path.join(MODS, entry))
    shutil.copy(os.path.join("testrig", "downloads", OTHER), os.path.join(MODS, OTHER))
    print("  planted %s where %s belongs" % (OTHER, WANT))

    jar = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
    rig.install(SERVER, jar)
    lost = sorted(e for e in os.listdir(MODS) if re.match(r"(?i)lostcities-", e))
    print("  after an install: %s, and the DevTool %s"
          % (", ".join(lost) or "none",
             "present" if os.path.isfile(os.path.join(MODS, os.path.basename(jar)))
             else "ABSENT"))
    if lost != [WANT]:
        fail("after an install the mods folder holds %s, not %s alone"
             % (lost or "no Lost Cities jar", WANT))
    if not os.path.isfile(os.path.join(MODS, os.path.basename(jar))):
        fail("the install did not put the DevTool jar in place")

if failures:
    print("FAILED (%d)" % len(failures))
    for f in failures:
        print("  " + f)
    raise SystemExit(1)
print("the rig answers on its command line, names the checks' version once, and "
      "gives a check that version's Lost Cities")
print("all checks passed")
