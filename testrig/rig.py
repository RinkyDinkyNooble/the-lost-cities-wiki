#!/usr/bin/env python3
"""Run the Lost Cities wiki's claim tests against a real server.

    python testrig/rig.py doctor
    python testrig/rig.py install 7.4.12 --accept-eula
    python testrig/rig.py run 7.4.12 wiki-test10
    python testrig/rig.py matrix wiki-test10

Start with `doctor`. It names every file you still need and where to get it, and
never downloads anything itself.

Everything that differs between versions lives in versions.json. This file holds
no version knowledge at all.
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOWNLOADS = os.path.join(HERE, "downloads")
SERVERS = os.path.join(HERE, "servers")
JAVA_DIR = os.path.join(HERE, "java")
PACKS = os.path.join(REPO, "docs", "examples")

sys.path.insert(0, HERE)

OK, MISSING = "ok", "MISSING"
# Class file major version to the Java release that introduced it. Used to catch a
# wrong download before it becomes an UnsupportedClassVersionError mid-boot.
CLASSFILE = {52: "8", 53: "9", 55: "11", 60: "16", 61: "17", 65: "21", 69: "25"}


def load_manifest():
    with io.open(os.path.join(HERE, "versions.json"), encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------- finding

def find_download(name):
    """Locate a user-supplied jar, forgivingly.

    Case is ignored because the mod's own filenames are inconsistent
    (`lostcities-1.20-7.4.12.jar` but `LostCities-1.21.11-9.5.1.jar`), and a `.zip`
    with the right stem is accepted because that is what some browsers save.
    """
    if not os.path.isdir(DOWNLOADS):
        return None
    stem = os.path.splitext(name)[0].lower()
    for entry in sorted(os.listdir(DOWNLOADS)):
        base, ext = os.path.splitext(entry)
        if base.lower() == stem and ext.lower() in (".jar", ".zip"):
            return os.path.join(DOWNLOADS, entry)
    return None


def java_binary(root):
    exe = "java.exe" if os.name == "nt" else "java"
    direct = os.path.join(root, "bin", exe)
    if os.path.isfile(direct):
        return direct
    # Unzipping a Temurin archive leaves one nested folder. Descending saves every
    # user the same small annoyance.
    if os.path.isdir(root):
        for entry in sorted(os.listdir(root)):
            nested = os.path.join(root, entry, "bin", exe)
            if os.path.isfile(nested):
                return nested
    return None


def find_java(major):
    """Env var, then testrig/java/<major>/, then whatever is on PATH if it fits."""
    env = os.environ.get("LCRIG_JAVA_" + str(major))
    if env and os.path.isfile(env):
        return env
    found = java_binary(os.path.join(JAVA_DIR, str(major)))
    if found:
        return found
    onpath = shutil.which("java")
    if onpath and java_major(onpath) == str(major):
        return onpath
    return None


def java_major(binary):
    try:
        out = subprocess.run([binary, "-version"], capture_output=True,
                             text=True, timeout=30)
    except Exception:
        return None
    text = (out.stderr or "") + (out.stdout or "")
    m = re.search(r'version "(\d+)(?:\.(\d+))?', text)
    if not m:
        return None
    major, minor = m.group(1), m.group(2)
    return minor if major == "1" else major


def jar_java_major(path):
    """Which Java a jar was compiled for, from its first class file."""
    try:
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.endswith(".class"):
                    return CLASSFILE.get(int.from_bytes(z.read(n)[6:8], "big"))
    except Exception:
        return None
    return None


def server_dir(key):
    return os.path.join(SERVERS, key)


def is_installed(server, key):
    root = server_dir(key)
    if server.get("launch") == "jar":
        return os.path.isfile(os.path.join(root, server["server_jar"]))
    return os.path.isdir(os.path.join(root, "libraries", server["loader_dir"]))


# ---------------------------------------------------------------------- doctor

def check(manifest, version):
    """Everything one version needs, and whether it is there."""
    v = manifest["versions"][version]
    server = manifest["servers"][v["server"]]
    rows = []

    java = find_java(server["java"])
    rows.append(("java " + server["java"], OK if java else MISSING,
                 java or os.path.join("testrig", "java", server["java"]),
                 manifest["javas"][server["java"]].get("url")))

    inst = find_download(server["installer"])
    rows.append(("loader installer", OK if inst else MISSING,
                 inst or os.path.join("testrig", "downloads", server["installer"]),
                 server.get("url")))

    rows.append(("server installed",
                 OK if is_installed(server, v["server"]) else MISSING,
                 os.path.join("testrig", "servers", v["server"]),
                 None))

    jar = find_download(v["mod_jar"])
    rows.append(("mod jar", OK if jar else MISSING,
                 jar or os.path.join("testrig", "downloads", v["mod_jar"]),
                 manifest.get("mod_url")))

    warn = None
    if jar:
        want, got = server["java"], jar_java_major(jar)
        if got and got != want:
            warn = (f"{os.path.basename(jar)} is compiled for Java {got}, but this "
                    f"version needs Java {want}. That is probably the wrong download.")
    return rows, warn


def cmd_doctor(manifest, args):
    ready = 0
    only = args.version
    for version, v in manifest["versions"].items():
        if only and version != only:
            continue
        server = manifest["servers"][v["server"]]
        rows, warn = check(manifest, version)
        good = all(s == OK for _, s, _, _ in rows)
        ready += good
        head = (f"{version:<8} {server['loader']} {v['server'].split('-', 1)[1]}, "
                f"Minecraft {server['minecraft']}, Java {server['java']}")
        print(("\n" if not args.quiet else "") + head)
        for label, state, where, url in rows:
            if state == OK and args.quiet:
                continue
            print(f"  [{state:^7}] {label:<18} {where}")
            if state == MISSING and url:
                print(f"{'':<12}get it from {url}")
        if warn:
            print(f"  [{'warn':^7}] {warn}")
        if good:
            print(f"  ready:  python testrig/rig.py run {version} wiki-test10")
        elif all(s == OK for l, s, _, _ in rows if l != "server installed"):
            print(f"  next:   python testrig/rig.py install {version} --accept-eula")

    total = len([v for v in manifest["versions"] if not only or v == only])
    print(f"\n{ready} of {total} versions ready.")
    if ready < total:
        print("Put downloaded jars in testrig/downloads/ and unzip a JDK into "
              "testrig/java/<major>/.")
    return 0


def cmd_list(manifest, args):
    print(f"{'version':<9} {'minecraft':<10} {'loader':<10} {'ready':<6} note")
    for version, v in manifest["versions"].items():
        s = manifest["servers"][v["server"]]
        rows, _ = check(manifest, version)
        good = "yes" if all(st == OK for _, st, _, _ in rows) else "no"
        star = "*" if v.get("baseline") else " "
        print(f"{star}{version:<8} {s['minecraft']:<10} {s['loader']:<10} "
              f"{good:<6} {v.get('note', '')[:60]}")
    print("\n* baseline: the version the wiki's expectations are written against.")
    return 0


# --------------------------------------------------------------------- install

PROPERTIES = """\
enable-rcon=true
rcon.password={password}
rcon.port={port}
broadcast-rcon-to-ops=false
level-name=world
level-seed=lostcitieswiki
level-type={level_type}
generate-structures=false
online-mode=false
spawn-protection=0
max-tick-time=-1
sync-chunk-writes=false
view-distance=4
op-permission-level=4
function-permission-level=2
difficulty=easy
gamemode=survival
"""


def write_properties(root, manifest, server):
    """Pin everything that decides whether two runs agree.

    level-seed is the important one: without it every machine generates a
    different world and no count is comparable. generate-structures=false keeps a
    village out of a test chunk, and max-tick-time=-1 stops the watchdog killing
    slow generation and reporting it as a crash.
    """
    rc = manifest["rcon"]
    io.open(os.path.join(root, "server.properties"), "w",
            encoding="utf-8", newline="\n").write(PROPERTIES.format(
                password=rc["password"], port=rc["port"],
                level_type=server.get("level_type", "minecraft\\:normal")))


def cmd_install(manifest, args):
    version = args.version
    if version not in manifest["versions"]:
        print(f"unknown version {version}. Try: python testrig/rig.py list")
        return 2
    v = manifest["versions"][version]
    key = v["server"]
    server = manifest["servers"][key]
    root = server_dir(key)

    java = find_java(server["java"])
    inst = find_download(server["installer"])
    if not java or not inst:
        print("Not ready to install. What is missing:\n")
        args.quiet = True
        cmd_doctor(manifest, args)
        return 1

    os.makedirs(root, exist_ok=True)
    if not is_installed(server, key):
        print(f"installing {key} (this downloads Minecraft and takes a few minutes)")
        r = subprocess.run([java, "-jar", os.path.abspath(inst), "--installServer"],
                           cwd=root)
        if r.returncode != 0 or not is_installed(server, key):
            print("the loader installer did not finish. Its own log is in "
                  f"{root}")
            return 1
    else:
        print(f"{key} already installed, reusing it")

    write_properties(root, manifest, server)

    eula = os.path.join(root, "eula.txt")
    if args.accept_eula:
        io.open(eula, "w", encoding="utf-8", newline="\n").write("eula=true\n")
    elif not os.path.isfile(eula):
        print("\nThe server will not start until you accept Mojang's EULA.")
        print("Read it at https://aka.ms/MinecraftEULA, then re-run with "
              "--accept-eula.")
        return 1

    sync_mod(manifest, version, root)
    print(f"\n{version} ready:  python testrig/rig.py run {version} wiki-test10")
    return 0


def sync_mod(manifest, version, root):
    """One mod jar in mods/, and only one.

    Server installs are shared between mod versions, so the jar left by the last
    run has to go. Two Lost Cities jars in one mods folder is not a supported
    state and fails in confusing ways.
    """
    v = manifest["versions"][version]
    mods = os.path.join(root, "mods")
    os.makedirs(mods, exist_ok=True)
    for entry in os.listdir(mods):
        if entry.lower().endswith((".jar", ".zip")):
            os.remove(os.path.join(mods, entry))
    jar = find_download(v["mod_jar"])
    if not jar:
        raise SystemExit(f"missing {v['mod_jar']} in testrig/downloads/")
    shutil.copy(jar, os.path.join(mods, v["mod_jar"]))


# ------------------------------------------------------------------- the packs

def resolve_spec(name):
    for cand in (name, os.path.join(HERE, "probes", name),
                 os.path.join(HERE, "probes", name + ".json")):
        if os.path.isfile(cand):
            return cand
    raise SystemExit(f"no probe file for {name!r}. Looked in testrig/probes/")


def resolve_pack(name):
    for cand in (name, os.path.join(PACKS, name)):
        if os.path.isdir(cand):
            return cand
    raise SystemExit(f"no pack {name!r}. Looked in docs/examples/")


def adapt_pack(pack, v, workdir):
    """Copy the pack and rename the predefined city folder for this version.

    This is the ONLY thing the rig changes in a pack. The folder spelling differs
    between versions and a folder the version did not compile in is never scanned,
    so the pack silently looks empty. Everything else, including keys a version
    does not declare, is left exactly as written, because that is what the tests
    are measuring.
    """
    dest = os.path.join(workdir, os.path.basename(pack))
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(pack, dest)
    want = (v.get("registries") or {}).get("predefined_city")
    if not want:
        return dest, None
    for root, dirs, _ in os.walk(dest):
        for d in list(dirs):
            if d.startswith("predefinedcit") and d != want:
                os.rename(os.path.join(root, d), os.path.join(root, want))
                return dest, f"{d} -> {want}"
    return dest, None


# ----------------------------------------------------------------- judging

def expectation(probe, version):
    exp = dict(probe)
    override = (probe.get("expect") or {}).get(version)
    if override:
        exp.update(override)
    return exp


def judge(probe, version, raw, capabilities):
    need = set(probe.get("requires") or [])
    if not need <= set(capabilities):
        return "n/a", "needs " + ", ".join(sorted(need - set(capabilities)))
    exp = expectation(probe, version)
    why = exp.get("why", "")
    kind = probe.get("kind", "count")
    if kind == "count":
        lo, hi = exp.get("min", 0), exp.get("max")
        ok = raw >= lo and (hi is None or raw <= hi)
        want = f"{lo}" if hi == lo else f"{lo}..{hi if hi is not None else ''}"
        return ("pass" if ok else "fail"), (why if ok else f"expected {want}")
    if kind == "block":
        ok = bool(raw) == bool(exp.get("present", True))
        return ("pass" if ok else "fail"), why
    if kind == "data":
        want = exp.get("contains")
        ok = (want in raw) if want else True
        return ("pass" if ok else "fail"), (why if ok else f"expected {want!r}")
    return "fail", "unknown probe kind"


# ---------------------------------------------------------------------- run

def build_adapter(manifest, version, port):
    from adapters.modern import Modern
    from adapters.legacy112 import Legacy112
    v = manifest["versions"][version]
    server = manifest["servers"][v["server"]]
    root = server_dir(v["server"])
    java = find_java(server["java"])
    if not java:
        raise SystemExit(f"no Java {server['java']}. Run doctor.")
    if not is_installed(server, v["server"]):
        raise SystemExit(f"{v['server']} is not installed. Run: "
                         f"python testrig/rig.py install {version} --accept-eula")
    log = lambda m: print("  . " + str(m), flush=True)
    if v["adapter"] == "legacy112":
        return Legacy112(root, java, server["server_jar"], port,
                         manifest["rcon"]["password"], log), root
    return Modern(root, java, server["loader_dir"], port,
                  manifest["rcon"]["password"], log), root


def applicable(manifest, version, spec):
    """Whether running this spec on this version could tell us anything.

    Two ways it cannot. A datapack spec on a file-era version is meaningless,
    because those builds never read a datapack at all. And if every probe needs a
    capability the version lacks, the answer is n/a before the server boots, so
    booting it wastes a minute to learn nothing.
    """
    v = manifest["versions"][version]
    if v.get("asset_system", "datapack") != spec.get("asset_system", "datapack"):
        return False, "different asset system"
    caps = set(v.get("capabilities", []))
    if all(not set(p.get("requires") or []) <= caps for p in spec["probes"]):
        missing = sorted({r for p in spec["probes"]
                          for r in (p.get("requires") or []) if r not in caps})
        return False, "no probe applies: needs " + ", ".join(missing)
    return True, ""


def skipped(version, spec, why):
    return {"version": version, "skipped": why, "failed_chunks": {}, "error": None,
            "rows": [("n/a", p["id"], why, "", p.get("claim", ""))
                     for p in spec["probes"]]}


def run_one(manifest, version, spec_path, args):
    v = manifest["versions"][version]
    spec = json.load(io.open(spec_path, encoding="utf-8"))
    ok, why = applicable(manifest, version, spec)
    if ok is False and not args.force:
        return skipped(version, spec, why)
    pack = resolve_pack(args.pack or spec["pack"])
    profile = args.profile or spec.get("profile")
    port = args.port or manifest["rcon"]["port"]

    adapter, root = build_adapter(manifest, version, port)
    sync_mod(manifest, version, root)

    work = os.path.join(HERE, ".rigcache")
    os.makedirs(work, exist_ok=True)
    adapted, renamed = adapt_pack(pack, v, work)
    if renamed:
        print(f"  . pack adapted for {version}: {renamed}")
    extra = [resolve_pack(p) for p in (args.also_pack or [])]
    extra = [adapt_pack(p, v, work)[0] for p in extra]

    patch = json.loads(args.profile_patch) if args.profile_patch else None
    result = adapter.run([adapted] + extra,
                         os.path.join(adapted, "profile"), profile, spec,
                         patch, args.keep_config)

    caps = v.get("capabilities", [])
    by_id = {p["id"]: p for p in spec["probes"]}
    rows = []
    for got in result["probes"]:
        probe = by_id[got["id"]]
        state, note = judge(probe, version, got["raw"], caps)
        rows.append((state, got["id"], got["detail"], note,
                     probe.get("claim", "")))
    for pid, probe in by_id.items():
        if pid not in {r[1] for r in rows}:
            need = set(probe.get("requires") or [])
            state = "n/a" if not need <= set(caps) else "error"
            rows.append((state, pid, "not measured", "", probe.get("claim", "")))
    return {"version": version, "rows": rows, "skipped": None,
            "failed_chunks": result["failed_chunks"], "error": result["error"]}


def report(res, spec_name):
    print(f"\n{res['version']}  {spec_name}")
    print()
    width = max([len(r[1]) for r in res["rows"]] + [4])
    for state, pid, detail, note, claim in res["rows"]:
        short = detail if len(detail) <= 21 else detail[:20] + "…"
        print(f"  {state:<5} {pid:<{width}}  {short:<22}{claim[:52]}")
        # Anything that did not pass gets its full detail and reason on their own
        # lines. Truncating exactly when something went wrong is the wrong choice.
        if state != "pass":
            if len(detail) > 21:
                print(f"  {'':<5} {'':<{width}}  {detail}")
            if note:
                print(f"  {'':<5} {'':<{width}}  {note}")
        elif note:
            print(f"  {'':<5} {'':<{width}}  {note}")
    tally = {}
    for state, *_ in res["rows"]:
        tally[state] = tally.get(state, 0) + 1
    print("\n  " + "   ".join(f"{n} {s}" for s, n in sorted(tally.items())))
    if res["error"]:
        print(f"  run error: {res['error']}")
    if res["failed_chunks"]:
        print("  failed chunks:")
        for msg, coords in sorted(res["failed_chunks"].items()):
            print(f"    {len(coords):>4}x  {msg}")
    return 0 if tally.get("fail", 0) == 0 and not res["error"] else 1


def cmd_run(manifest, args):
    spec_path = resolve_spec(args.pack_or_spec)
    res = run_one(manifest, args.version, spec_path, args)
    return report(res, os.path.basename(spec_path))


def cmd_matrix(manifest, args):
    spec_path = resolve_spec(args.pack_or_spec)
    targets = []
    for version in manifest["versions"]:
        if args.only and version not in args.only:
            continue
        rows, _ = check(manifest, version)
        if all(s == OK for _, s, _, _ in rows):
            targets.append(version)
    if not targets:
        print("no versions are ready. Run: python testrig/rig.py doctor")
        return 1
    print(f"running {os.path.basename(spec_path)} on: {', '.join(targets)}")
    print("expect roughly a minute per version.\n")

    results = []
    for version in targets:
        try:
            res = run_one(manifest, version, spec_path, args)
        except Exception as exc:
            # The point of a matrix is the comparison. Losing one column is worth
            # far less than losing the other nine to one bad server.
            spec = json.load(io.open(spec_path, encoding="utf-8"))
            res = skipped(version, spec, "%s: %s" % (type(exc).__name__, exc))
            res["rows"] = [("error", p["id"], "run did not complete", "",
                            p.get("claim", "")) for p in spec["probes"]]
        report(res, os.path.basename(spec_path))
        results.append(res)

    ids = [r[1] for r in results[0]["rows"]]
    print("\n" + "=" * 78)
    if args.md:
        print("| Probe | " + " | ".join(targets) + " |")
        print("|---" * (len(targets) + 1) + "|")
    else:
        print(f"{'probe':<28}" + "".join(f"{v:<12}" for v in targets))
    for pid in ids:
        cells = []
        for res in results:
            row = next((r for r in res["rows"] if r[1] == pid), None)
            cells.append("-" if row is None else
                         (row[2] if row[0] != "n/a" else "n/a"))
        if args.md:
            print(f"| {pid} | " + " | ".join(cells) + " |")
        else:
            print(f"{pid:<28}" + "".join(f"{c:<12}" for c in cells))
    return 0


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Run the Lost Cities wiki's claim tests against a real server.")
    sub = ap.add_subparsers(dest="cmd")

    d = sub.add_parser("doctor", help="what is installed, what is missing")
    d.add_argument("version", nargs="?")
    d.add_argument("--quiet", action="store_true", help="only show problems")

    sub.add_parser("list", help="every version the manifest knows")

    i = sub.add_parser("install", help="install a loader and wire a version to it")
    i.add_argument("version")
    i.add_argument("--accept-eula", action="store_true",
                   help="you accept https://aka.ms/MinecraftEULA")
    i.add_argument("--quiet", action="store_true")

    for name, helptext in (("run", "run one pack on one version"),
                           ("matrix", "run one pack on every ready version")):
        p = sub.add_parser(name, help=helptext)
        if name == "run":
            p.add_argument("version")
        p.add_argument("pack_or_spec")
        p.add_argument("--pack", help="override the pack the probe file names")
        p.add_argument("--profile", help="override the profile")
        p.add_argument("--profile-patch", help="JSON merged into the profile")
        p.add_argument("--also-pack", action="append", default=[],
                       help="install another pack beside the first")
        p.add_argument("--keep-config", action="store_true",
                       help="skip the config wipe, to reproduce upgrade bugs")
        p.add_argument("--port", type=int, help="RCON port, if 25575 is taken")
        p.add_argument("--force", action="store_true",
                       help="run even where no probe applies")
        if name == "matrix":
            p.add_argument("--only", nargs="*", help="limit to these versions")
            p.add_argument("--md", action="store_true",
                           help="emit a markdown table")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 0
    manifest = load_manifest()
    return {"doctor": cmd_doctor, "list": cmd_list, "install": cmd_install,
            "run": cmd_run, "matrix": cmd_matrix}[args.cmd](manifest, args)


if __name__ == "__main__":
    raise SystemExit(main())
