#!/usr/bin/env python3
"""Rebuild docs/examples/mod-keys.json from the mod jars.

    python testrig/extract-keys.py            # report, change nothing
    python testrig/extract-keys.py --write     # merge into mod-keys.json

`mod-keys.json` is the ground truth the wiki is checked against: `validate.py`
fails a reference table that documents a key no version declares, and
`key-coverage.py` measures the example packs against it. It was originally built by
hand, one jar at a time, which is why it covered two versions and had three codec
types missing.

This reads it out of the jars instead, so adding a version is a download rather than
an afternoon.

Two sources, because the mod has two key systems:

  Codec keys    Every `fieldOf`, `optionalFieldOf` and `Tools.listOrStringList`
                call in the `regassets` classes. The last of those is easy to miss:
                three types register their fields only that way, and an extractor
                looking for `fieldOf` alone walks straight past them.

  Profile keys  Every `Configuration.get*` call in `LostCityProfile`, which carries
                the key, its config section, its type, and for numbers its minimum
                and maximum. Defaults are not literals there, they are field loads,
                so they come from the `default.json` the mod itself writes if a
                server has been booted.

Jars are read from testrig/downloads/, the same place the rig looks. Nothing is
downloaded.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOWNLOADS = os.path.join(HERE, "downloads")
SERVERS = os.path.join(HERE, "servers")
KEYS = os.path.join(REPO, "docs", "examples", "mod-keys.json")

PROFILE_CLASS = "mcjty/lostcities/config/LostCityProfile.class"
# A key is an identifier. This rejects comment text, validation messages, and the
# lone "#" that BlockMatcher pushes as a tag prefix just before a fieldOf call.
IDENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")
GETTER = re.compile(r"Configuration\.get(Boolean|Int|Float|Double|String|StringList)")
TYPE_NAME = {"Boolean": "Boolean", "Int": "Int", "Float": "Float",
             "Double": "Double", "String": "String", "StringList": "StringList"}


def javap():
    for cand in (os.environ.get("LCRIG_JAVAP"),
                 "javap",
                 r"C:/Program Files/Eclipse Adoptium/jdk-17.0.19.10-hotspot/bin/javap.exe"):
        if not cand:
            continue
        try:
            subprocess.run([cand, "-version"], capture_output=True, timeout=20)
            return cand
        except Exception:
            continue
    raise SystemExit("no javap found. Set LCRIG_JAVAP to one, or put a JDK on PATH.")


JAVAP = javap()


def disassemble(blob):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "X.class")
        io.open(p, "wb").write(blob)
        return subprocess.run([JAVAP, "-p", "-c", "-constants", p],
                              capture_output=True, text=True).stdout


def codec_keys(jar):
    """{TypeName: {key: required|optional}} for every regasset class in the jar."""
    out = {}
    with zipfile.ZipFile(jar) as z:
        for name in z.namelist():
            if not (name.endswith(".class") and "regassets" in name
                    and "$" not in name):
                continue
            text = disassemble(z.read(name))
            cls = name.split("/")[-1][:-6]
            pending, found = [], {}
            for line in text.splitlines():
                m = re.search(r"//\s+String\s+(\S+)", line)
                if m:
                    if IDENT.match(m.group(1)):
                        pending.append(m.group(1))
                    continue
                if "listOrStringList" in line:
                    # key first, default second. Having a default makes it optional.
                    if pending:
                        found[pending[0]] = "optional"
                    pending = []
                elif "optionalFieldOf" in line:
                    if pending:
                        found[pending[0]] = "optional"
                    pending = []
                elif "fieldOf" in line:
                    if pending:
                        found[pending[0]] = "required"
                    pending = []
            if found:
                out[cls] = dict(sorted(found.items()))
    return dict(sorted(out.items()))


NUM = re.compile(r"^\s*\d+:\s+(?:ldc\w*|bipush|sipush|iconst_|fconst_|dconst_|"
                 r"lconst_)\S*\s+(?:#\d+\s+//\s+(?:float|double|int|long)\s+)?"
                 r"(-?[\d.]+)")


def profile_keys(jar):
    """{key: {section, type, min, max}} from LostCityProfile's own registrations."""
    with zipfile.ZipFile(jar) as z:
        if PROFILE_CLASS not in z.namelist():
            return {}
        text = disassemble(z.read(PROFILE_CLASS))

    out, strings, numbers = {}, [], []
    for line in text.splitlines():
        m = re.search(r"//\s+String\s+(.*?)\s*$", line)
        if m:
            strings.append(m.group(1))
            continue
        n = NUM.match(line)
        if n:
            numbers.append(n.group(1))
            continue
        if re.search(r"iconst_(-?\d)", line):
            numbers.append(re.search(r"iconst_(-?\d)", line).group(1))
            continue
        g = GETTER.search(line)
        if g:
            kind = TYPE_NAME[g.group(1)]
            # Count from the END of the pushed strings, not the start. Each getter
            # takes its key, its section and its comment, and getString takes a
            # default between them. Reading forwards instead picks up whatever
            # string the previous statement happened to leave behind, which is how
            # comment text ends up recorded as a key.
            want = 4 if kind == "String" else 3
            window = strings[-want:] if len(strings) >= want else strings
            if len(window) >= 2 and IDENT.match(window[0]) and IDENT.match(window[1]):
                key, section = window[0], window[1]
                entry = {"section": section, "type": kind}
                if kind in ("Int", "Float", "Double") and len(numbers) >= 2:
                    lo, hi = numbers[-2], numbers[-1]
                    cast = float if kind != "Int" else int
                    try:
                        entry["min"], entry["max"] = cast(lo), cast(hi)
                    except ValueError:
                        pass
                out[key] = entry
            strings, numbers = [], []
    return dict(sorted(out.items()))


def defaults_from_servers():
    """The mod writes default.json on boot. That is the only literal source."""
    found = {}
    for server in sorted(os.listdir(SERVERS)) if os.path.isdir(SERVERS) else []:
        p = os.path.join(SERVERS, server, "config", "lostcities", "profiles",
                         "default.json")
        if not os.path.isfile(p):
            continue
        try:
            doc = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        flat = {}
        for section, body in doc.items():
            if isinstance(body, dict):
                flat.update(body)
        found[server] = flat
    return found


def version_of(jar_name):
    m = re.search(r"-(\d+\.\d+\.\d+)\.(?:jar|zip)$", jar_name, re.I)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="merge the result into docs/examples/mod-keys.json")
    ap.add_argument("--only", nargs="*", help="limit to these mod versions")
    ap.add_argument("--defaults-from-server", action="store_true",
                    help="also read defaults from a booted server's default.json. "
                         "Only safe when that server last ran this exact version")
    args = ap.parse_args()

    data = json.load(io.open(KEYS, encoding="utf-8"))
    manifest = json.load(io.open(os.path.join(HERE, "versions.json"),
                                 encoding="utf-8"))
    server_defaults = defaults_from_servers()

    # Every Lost Cities jar in downloads/, not only the ones the rig runs. The
    # wiki publishes key counts for versions there is no server for, and those
    # numbers should come from the jar rather than from an earlier reading.
    targets = dict(manifest["versions"])
    for name in sorted(os.listdir(DOWNLOADS)) if os.path.isdir(DOWNLOADS) else []:
        if not re.match(r"lostcities-", name, re.I):
            continue
        ver = version_of(name)
        if ver and ver not in targets:
            targets[ver] = {"mod_jar": name, "server": None}

    rows, changed = [], 0
    for version, v in sorted(targets.items(),
                             key=lambda kv: [int(x) for x in kv[0].split(".")]):
        if args.only and version not in args.only:
            continue
        jar = os.path.join(DOWNLOADS, v["mod_jar"])
        if not os.path.isfile(jar):
            rows.append((version, "?", "?", "jar not in testrig/downloads/"))
            continue

        codec = codec_keys(jar)
        if not codec:
            # No regasset classes means the file-asset era, whose keys live in a
            # .cfg and are documented separately.
            rows.append((version, "-", "-", "file-asset era, a different system"))
            continue
        prof = profile_keys(jar)

        # Defaults are NOT taken from a booted server unless asked for. A server
        # install is shared between mod versions, so the default.json sitting in
        # it belongs to whichever version ran last, and importing it silently
        # would stamp one version's defaults onto another. The stored defaults
        # for 7.4.12 and 7.5.1 were checked by hand; they are preserved below.
        if args.defaults_from_server:
            defaults = server_defaults.get(v.get("server"), {})
            for key, meta in prof.items():
                if key in defaults:
                    meta["default"] = defaults[key]

        known = data["versions"].get(version)
        note = ""
        if known:
            old_c = sum(len(x) for x in known["codec"].values())
            new_c = sum(len(x) for x in codec.values())
            if old_c != new_c or len(known["profile"]) != len(prof):
                note = "differs from stored: codec %d->%d, profile %d->%d" % (
                    old_c, new_c, len(known["profile"]), len(prof))
            else:
                note = "matches stored"
        else:
            note = "new"
            changed += 1
        rows.append((version, sum(len(x) for x in codec.values()), len(prof), note))

        if args.write:
            entry = data["versions"].setdefault(version, {})
            # Never overwrite a hand-checked entry's defaults with nothing.
            if known:
                for key, meta in prof.items():
                    old = known["profile"].get(key, {})
                    if "default" not in meta and "default" in old:
                        meta["default"] = old["default"]
            entry["codec"] = codec
            entry["profile"] = prof

    w = max(len(str(r[0])) for r in rows)
    print("%-*s  %-6s %-8s %s" % (w, "version", "codec", "profile", "status"))
    for version, c, p, note in rows:
        print("%-*s  %-6s %-8s %s" % (w, version, c, p, note))

    if args.write:
        order = sorted(data["versions"],
                       key=lambda s: [int(x) for x in s.split(".")])
        data["versions"] = {k: data["versions"][k] for k in order}
        io.open(KEYS, "w", encoding="utf-8", newline="\n").write(
            json.dumps(data, indent=1) + "\n")
        print("\nwritten to docs/examples/mod-keys.json")
    else:
        print("\nnothing written. Pass --write to merge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
