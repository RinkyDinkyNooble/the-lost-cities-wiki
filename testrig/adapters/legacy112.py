"""Run a claim test on Minecraft 1.12.2, where the mod reads files, not datapacks.

The modern adapter cannot be reused. Three commands it depends on do not exist:

    /forceload              nothing equivalent. Generation follows world spawn
    /execute in <dim> ...   the dimension prefix does not exist
    /data get block         nothing equivalent

`/clone ... filtered` survives and still reports how many blocks it copied, which
is why counting works the same way on both adapters.

Three things this rig needs that no page states, each found the hard way:

  * `level-type=lostcities` in server.properties. The mod registers a world TYPE
    of that name, and `defaultProfile` only picks which profile a Lost Cities
    world uses. Without the world type the overworld is ordinary terrain and the
    profile does nothing visible.
  * Two boots. With no /forceload a headless server generates only the region
    around world spawn, and spawn lands wherever the seed puts it. The first boot
    exists to move spawn onto the pinned city; the second generates it.
  * The scratch area must sit inside the spawn region too, because /clone needs
    its destination loaded and nothing here can force a chunk.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rcon import Rcon  # noqa: E402
from adapters.modern import Error  # noqa: E402

# High in the air, not underground. 1.12's /clone throws a
# ConcurrentModificationException if the destination holds tile entities, and any
# scratch area cut into terrain eventually will once the seed changes. Empty sky
# inside the spawn region cannot.
SCRATCH = (-128, 200, -128)


class Legacy112:
    name = "legacy112"

    def __init__(self, server_dir, java, loader_jar, port=25575,
                 password="lcwiki", log=print):
        self.dir = server_dir
        self.java = java
        self.jar = loader_jar
        self.port = port
        self.password = password
        self.log = log

    def boot(self, timeout=420.0):
        proc = subprocess.Popen(
            [self.java, "-Xmx2G", "-jar", self.jar, "nogui"],
            cwd=self.dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                raise Error("server exited during startup. See logs/latest.log")
            if 'For help, type "help"' in line:
                self.log("server up")
                threading.Thread(target=lambda: [None for _ in
                                                 iter(proc.stdout.readline, "")],
                                 daemon=True).start()
                return proc
        raise Error("server did not finish starting")

    def prepare(self, assets_file, profile_cfg=None):
        """Install a userassets.json, and wipe the world so generation repeats."""
        world = os.path.join(self.dir, "world")
        if os.path.isdir(world):
            shutil.rmtree(world)
        cfg = os.path.join(self.dir, "config", "lostcities")
        os.makedirs(cfg, exist_ok=True)
        if assets_file:
            shutil.copy(assets_file, os.path.join(cfg, "userassets.json"))
        if profile_cfg:
            shutil.copy(profile_cfg, os.path.join(
                cfg, os.path.basename(profile_cfg)))
        logs = os.path.join(self.dir, "logs", "latest.log")
        if os.path.isfile(logs):
            os.remove(logs)

    def _find(self, con, x, z, block, y0=40, y1=140):
        for y in range(y0, y1):
            if "Successfully found" in con.command(
                    f"testforblock {x} {y} {z} {block}"):
                return y
        return None

    def measure(self, con, p):
        kind = p.get("kind", "count")
        if kind == "count":
            # 1.12 boxes are given as a chunk corner plus the block to look for,
            # because the column has to be found before it can be counted.
            cx, cz = p["chunk"]
            x, z = cx * 16, cz * 16
            y = self._find(con, x + 8, z + 8, p["block"])
            if y is None:
                return 0, f"no {p['block']} in column {x + 8},{z + 8}"
            sx, sy, sz = SCRATCH
            cmd = (f"clone {x} {y - 2} {z} {x + 15} {y + 20} {z + 15} "
                   f"{sx} {sy} {sz} filtered normal {p['block']}")
            # 1.12's /clone iterates the world's pending block updates without
            # guarding the map, so it throws ConcurrentModificationException if
            # anything in the region still has a scheduled tick. That is a race in
            # the command, not a wrong answer, so it is worth retrying: a freshly
            # generated chunk drains its pending ticks within a few seconds.
            for attempt in range(4):
                reply = con.command(cmd)
                m = re.search(r"([0-9]+) block", reply)
                if m:
                    n = int(m.group(1))
                    return n, f"first at y={y}, {n} blocks"
                if attempt < 3:
                    self.log(f"{p['id']}: clone refused, letting the region "
                             f"settle ({attempt + 1}/3)")
                    time.sleep(5)
            return 0, f"first at y={y}, 0 blocks  |  " + reply.strip()[:90]
        if kind == "block":
            x, y, z = p["pos"]
            reply = con.command(f"testforblock {x} {y} {z} {p['block']}")
            hit = "Successfully found" in reply
            return hit, ("present" if hit else "absent")
        raise Error(f"probe kind {kind!r} is not available on 1.12")

    def run(self, packs, profile_dir, profile, spec, patch=None,
            keep_config=False):
        assets = spec.get("userassets")
        if assets and packs:
            assets = os.path.join(packs[0], assets)
        self.prepare(assets)

        self.log("first boot: moving world spawn onto the pinned city")
        proc = self.boot()
        try:
            with Rcon(port=self.port, password=self.password) as con:
                sx, sy, sz = spec.get("spawn", [0, 64, 0])
                self.log(con.command(f"setworldspawn {sx} {sy} {sz}").strip())
                con.command("save-all")
                con.command("stop")
        finally:
            try:
                proc.wait(timeout=120)
            except Exception:
                proc.kill()

        self.log("second boot: generating the region around it")
        proc = self.boot()
        rows, err = [], None
        try:
            with Rcon(port=self.port, password=self.password) as con:
                con.command("gamerule doDaylightCycle false")
                time.sleep(spec.get("settle", 10))
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
        return {"probes": rows, "failed_chunks": {}, "error": err}
