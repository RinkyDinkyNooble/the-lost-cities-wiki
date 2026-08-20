"""Run a claim-test pack on Minecraft 1.18 or later.

Wipes the world, installs the pack and its profile, boots the server headless,
force loads the test grid so generation happens with no player present, then asks
the world what it actually built.

This adapter measures. It does not judge: every probe returns the raw number or
string the world gave back, and rig.py decides whether that is a pass. Keeping the
two apart is what lets one probe carry a different expected value per version
without the adapter knowing anything about versions.

Traps encoded here, each of which cost a test round to find:

  * /forceload takes BLOCK coordinates, not chunk coordinates. Passing chunk
    numbers silently loads only the chunk containing them, so every probe reads an
    empty world.
  * /clone needs its destination loaded, so the scratch area is force loaded too.
  * /clone caps at 32768 blocks, which is exactly one chunk footprint 128 tall.
    A count box larger than that returns nothing rather than a partial answer.
  * /clone also needs the whole destination extent loaded, not just its corner. A
    box wider than the scratch area fails even when it is well under the cap.
  * The Lost Cities config section is [profiles]. Under any other name Forge
    rewrites the file to defaults with no error, which points the dimension at
    'biosphere' and makes a config typo look like a generation bug.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rcon import Rcon  # noqa: E402

DIM = "lostcities:lostcity"
SCRATCH = (992, 40, 992)
# 32 by 32, not 16 by 16. /clone writes the source box's full extent starting at
# the destination corner, so the destination has to be at least as wide and as deep
# as the source. A single chunk footprint only ever fits a box one chunk wide, and a
# probe that has to span four chunks to be sure of catching a building then fails
# with "That position is not loaded" rather than returning a count. 32 by 32 fits
# any box within the 32768 block cap that is at least 32 levels tall.
SCRATCH_BOX = (992, 992, 1023, 1023)


class Error(Exception):
    """The run could not complete. Distinct from a probe returning the wrong number."""


class Modern:
    name = "modern"

    def __init__(self, server_dir, java, loader_dir, port=25575,
                 password="lcwiki", log=print):
        self.dir = server_dir
        self.java = java
        self.loader_dir = loader_dir
        self.port = port
        self.password = password
        self.log = log

    # ---------------------------------------------------------------- booting

    def args_file(self):
        """Every installer writes both. Which one to use is the whole of the
        cross-platform story for booting a modded server."""
        name = "win_args.txt" if os.name == "nt" else "unix_args.txt"
        path = os.path.join(self.dir, "libraries", self.loader_dir, name)
        if not os.path.isfile(path):
            raise Error(f"no {name} under libraries/{self.loader_dir}. "
                        "The loader install did not complete.")
        return "@" + os.path.join("libraries", self.loader_dir, name)

    def boot(self, timeout=420.0):
        proc = subprocess.Popen(
            [self.java, "@user_jvm_args.txt", self.args_file(), "nogui"],
            cwd=self.dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                raise Error("server exited during startup. See logs/latest.log")
            if 'For help, type "help"' in line or re.search(r"Done \(.*\)!", line):
                self.log("server up")
                threading.Thread(target=lambda: [None for _ in
                                                 iter(proc.stdout.readline, "")],
                                 daemon=True).start()
                return proc
        raise Error("server did not finish starting")

    # ---------------------------------------------------------------- setting up

    def prepare(self, packs, profile_dir, profile, patch=None, keep_config=False):
        """Install packs and profiles, and wire the dimension to the profile.

        Hermetic by default. State left behind by a previous mod version is how
        the 8.4.1 upgrade crash was found, so carrying it over is opt in.
        """
        world = os.path.join(self.dir, "world")
        if os.path.isdir(world):
            shutil.rmtree(world)

        for src in packs:
            dest = os.path.join(world, "datapacks", os.path.basename(src))
            shutil.copytree(os.path.join(src, "data"), os.path.join(dest, "data"))
            shutil.copy(os.path.join(src, "pack.mcmeta"), dest)

        cfg = os.path.join(self.dir, "config", "lostcities")
        if not keep_config:
            # The whole mod config, not just the profiles. An 8.2.2 config left in
            # place stops 8.4.1 booting at all, because selectedProfile carries a
            # sentinel 8.4.1 no longer understands.
            if os.path.isdir(cfg):
                shutil.rmtree(cfg)
            for stale in ("lostcities-server.toml", "lostcities-common.toml"):
                p = os.path.join(self.dir, "config", stale)
                if os.path.isfile(p):
                    os.remove(p)
        profiles = os.path.join(cfg, "profiles")
        if os.path.isdir(profiles):
            shutil.rmtree(profiles)
        os.makedirs(profiles, exist_ok=True)

        if profile_dir and os.path.isdir(profile_dir):
            for name in sorted(os.listdir(profile_dir)):
                shutil.copy(os.path.join(profile_dir, name),
                            os.path.join(profiles, name))
        if patch:
            src = os.path.join(profile_dir, profile + ".json")
            if not os.path.isfile(src):
                raise Error(f"--profile-patch needs {profile}.json in the pack")
            data = json.loads(io.open(src, encoding="utf-8").read())
            for section, keys in patch.items():
                data.setdefault(section, {}).update(keys)
            io.open(os.path.join(profiles, profile + ".json"), "w",
                    encoding="utf-8").write(json.dumps(data, indent=2))
            self.log(f"profile patched with {patch}")

        with io.open(os.path.join(cfg, "common.toml"), "w",
                     encoding="utf-8") as f:
            f.write("[profiles]\n\tdimensionsWithProfiles = "
                    f'["{DIM}={profile}"]\n')

        logs = os.path.join(self.dir, "logs", "latest.log")
        if os.path.isfile(logs):
            os.remove(logs)

    # ---------------------------------------------------------------- generating

    def generate(self, con, grid, anchor, settle=20.0):
        boxes = [(grid["x0"] * 16, grid["z0"] * 16,
                  grid["x1"] * 16 + 15, grid["z1"] * 16 + 15), SCRATCH_BOX]
        for a, b, c, d in boxes:
            reply = con.command(
                f"execute in {DIM} run forceload add {a} {b} {c} {d}")
            self.log(f"forceload {a},{b} to {c},{d}: {reply}")
        # Wait until the anchor stops being air, which means the chunk generated.
        # NOT `#minecraft:air`: there is no such block tag, so that form errors on
        # every call, never matches, and silently burns the whole timeout on every
        # single run. It cost five minutes a run for as long as it was there.
        ax, ay, az = anchor
        deadline = time.time() + 180
        first = True
        while time.time() < deadline:
            reply = con.command(
                f"execute in {DIM} if block {ax} {ay} {az} minecraft:air")
            if first:
                self.log(f"anchor check: {reply.strip()[:90]}")
                first = False
            if "Test failed" in reply:      # not air, so something generated
                break
            time.sleep(3)
        else:
            self.log("WARNING: anchor still air after 180s. Probing anyway, "
                     "which is fine if the anchor sits above the terrain.")
        time.sleep(settle)

    # ---------------------------------------------------------------- measuring

    def count_box(self, con, probe_id, block, corner_a, corner_b):
        (x0, y0, z0), (x1, y1, z1) = corner_a, corner_b
        sx, sy, sz = SCRATCH
        reply = con.command(
            f"execute in {DIM} run clone {x0} {y0} {z0} {x1} {y1} {z1} "
            f"{sx} {sy} {sz} filtered {block}")
        if "not loaded" in reply:
            raise Error(f"{probe_id}: scratch area not loaded. " + reply)
        found = re.search(r"([0-9]+) block", reply)
        return int(found.group(1)) if found else 0

    def measure(self, con, p):
        """Return (raw, detail). raw is a count, a bool, or NBT text."""
        kind = p.get("kind", "count")
        if kind == "count":
            # `boxes` sums several boxes into one number. The cap is per /clone,
            # so anything that spreads over an area rather than sitting in a known
            # chunk has to be counted a chunk at a time and added up. A single box
            # can only ever answer "is it here", and for a building, a highway or a
            # sphere, where it lands is not something the pack decides.
            boxes = p.get("boxes") or [[p["from"], p["to"]]]
            n = sum(self.count_box(con, p["id"], p["block"], a, b)
                    for a, b in boxes)
            unit = "blocks" if len(boxes) == 1 else f"blocks over {len(boxes)} boxes"
            return n, f"{n} {unit}"
        if kind == "block":
            x, y, z = p["pos"]
            reply = con.command(
                f"execute in {DIM} if block {x} {y} {z} {p['block']}")
            hit = "Test passed" in reply
            return hit, ("present" if hit else "absent")
        if kind == "data":
            if "scan" in p:
                s = p["scan"]
                y = self._find(con, s["x"], s["z"], s["block"],
                               s.get("y0", 40), s.get("y1", 168))
                if y is None:
                    return "", f"no {s['block']} in column {s['x']},{s['z']}"
                y += s.get("dy", 0)
                x, z = s["x"], s["z"]
            else:
                x, y, z = p["pos"]
            reply = con.command(f"execute in {DIM} run data get block {x} {y} {z}")
            return reply, f"y={y} {reply[:120]}"
        raise Error(f"unknown probe kind {kind!r}")

    def _find(self, con, x, z, block, y0, y1):
        for y in range(y0, y1):
            if "Test passed" in con.command(
                    f"execute in {DIM} if block {x} {y} {z} {block}"):
                return y
        return None

    # ---------------------------------------------------------------- the run

    def run(self, packs, profile_dir, profile, spec, patch=None,
            keep_config=False):
        self.prepare(packs, profile_dir, profile, patch, keep_config)
        rows, err = [], None
        try:
            proc = self.boot()
        except Exception as exc:
            # A server that will not start is a result about that
            # version, not a reason to abandon the other nine.
            return {"probes": [], "failed_chunks": self.failed_chunks(),
                    "error": "%s: %s" % (type(exc).__name__, exc)}
        try:
            with Rcon(port=self.port, password=self.password) as con:
                self.generate(con, spec["grid"], spec["anchor"])
                for cmd in spec.get("commands", []):
                    self.log("$ " + cmd)
                    self.log("    " + con.command(cmd).replace("\n", "\n    "))
                for p in spec["probes"]:
                    raw, detail = self.measure(con, p)
                    rows.append({"id": p["id"], "raw": raw, "detail": detail})
                con.command("stop")
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                proc.wait(timeout=120)
            except Exception:
                proc.kill()
        return {"probes": rows, "failed_chunks": self.failed_chunks(),
                "error": err}

    def failed_chunks(self):
        path = os.path.join(self.dir, "logs", "latest.log")
        if not os.path.isfile(path):
            return {}
        text = io.open(path, encoding="utf-8", errors="replace").read()
        out = {}
        for coord, msg in re.findall(
                r"Error generating chunk (-?\d+,-?\d+): (.+)", text):
            out.setdefault("caught: " + msg.strip(), []).append(coord)
        uncaught = len(re.findall(r"ReportedException: Feature placement", text))
        if uncaught:
            out["UNCAUGHT ReportedException: Feature placement"] = ["x%d" % uncaught]
        return out
