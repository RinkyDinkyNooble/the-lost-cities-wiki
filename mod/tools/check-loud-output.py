#!/usr/bin/env python3
"""A command that answers about every asset must not answer with all of them.

    python mod/tools/check-loud-output.py

Needs the wiki's test rig, the same way the other server checks do.

`/lcdev block` and `/lcdev char` search every palette, part and building the server
has loaded. On a small pack that is a handful of lines. On a modpack it is not, and
neither the list of matches nor the list of assets that could not be built has any
limit on it, so the answer arrives as hundreds of lines of chat.

That is worse than untidy. This check first hit it by accident: 600 assets that
could not be built dropped the RCON connection outright, so the reply was large
enough to break the transport carrying it.

The pack here is deliberately broken. Every part points at a palette that does not
exist, which is what a modpack looks like when one file is wrong and everything
referencing it stops resolving.
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
from rcon import Rcon, RconError  # noqa: E402
import rig  # noqa: E402

SERVER = "testrig/servers/forge-1.20.1-47.4.10"
JAR = sorted(glob.glob("mod/build/libs/lostcities_devtool-*.jar"))[-1]
JAVA = os.path.abspath("testrig/java/17/bin/java.exe")
LOADER = "net/minecraftforge/forge/1.20.1-47.4.10"
WORLD = os.path.join(SERVER, "world")

BROKEN = 600
# What a person can read in chat before it stops being an answer. The mod's own
# reports run to a dozen lines or so.
MAX_LINES = 60

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


def write_broken(root, parts):
    """Parts pointing at a palette that is not there, so none of them build."""
    data = os.path.join(root, "data", "broke", "lostcities", "parts")
    os.makedirs(data, exist_ok=True)
    layer = ["#" * 16 for _ in range(16)]
    text = json.dumps({"xsize": 16, "zsize": 16, "refpalette": "broke:missing",
                       "slices": [layer for _ in range(6)]}) + "\n"
    for i in range(parts):
        io.open(os.path.join(data, "p%04d.json" % i), "w", encoding="utf-8",
                newline="\n").write(text)
    io.open(os.path.join(root, "pack.mcmeta"), "w", encoding="utf-8",
            newline="\n").write(json.dumps(
                {"pack": {"pack_format": 15, "description": "broke"}}))


if os.path.isdir(WORLD):
    shutil.rmtree(WORLD)
dest = rig.install(SERVER, JAR)
write_broken(os.path.join(WORLD, "datapacks", "brokepack"), BROKEN)
print("fresh world, jar installed, %d parts that cannot be built\n" % BROKEN)

proc = boot()
print("server up\n")
try:
    with Rcon(port=25575, password="lcwiki") as con:
        con.command("lcdev workshop build")

        print("=" * 72)
        print("how much a lookup says when everything is broken")
        for command in ("lcdev block minecraft:gold_block", "lcdev char #"):
            try:
                reply = con.command(command)
            except RconError as e:
                fail("`%s` broke the connection carrying its own answer: %s"
                     % (command, e))
                break
            lines = [l for l in reply.splitlines() if l.strip()]
            print("  %-34s %d lines" % (command, len(lines)))
            if len(lines) > MAX_LINES:
                fail("`%s` answered with %d lines, which is chat nobody can read"
                     % (command, len(lines)))
            elif len(lines) > 3:
                print("      last: %s" % lines[-1][:90])

        con.command("stop")
finally:
    try:
        proc.wait(timeout=180)
    except Exception:
        proc.kill()

if os.path.isfile(dest):
    os.remove(dest)
print("\nremoved the jar, rig baseline is clean again")
print("\n" + ("FAILURES:\n  " + "\n  ".join(failures)) if failures
      else "\nall checks passed")
