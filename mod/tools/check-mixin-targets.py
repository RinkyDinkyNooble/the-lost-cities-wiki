"""Every mixin injection point still exists, in every supported Lost Cities version.

A mixin is bound to the compiled shape of the code it patches, and that shape moves
between versions without any warning a compiler can give. This is the check that says
whether a version range is honest, and it needs no server: it reads the jars.

**Presence is not enough, so this counts.** Two of the injections are `@ModifyArg` on
"the only nextInt(int, int) call in this method". A version that added a second call
would leave the injection point present and the fix silently attached to the wrong
argument. Every redirected call is therefore counted inside the method it lives in,
and any count other than the expected one is a failure.

**7.4.12 is the control column.** The 7.4.12 build is known to work, so a row that
does not come back green under 7.4.12 is a bug in this file rather than a finding.
That is not a nicety: three rows came back red on the first run of this sweep, and all
three were parser faults rather than real breakage.

What this found on the 7.5 port, which is the reason it exists: 7.5 added a chunk
neighbourhood locking system, and the bodies of `LostCityFeature.place` and
`LostCitySphereFeature.place` moved into `lambda$place$0`. Both fault-report redirects
and the sphere crash guard went with them. Nine of the eleven mixins needed nothing.

Run it before widening `lostcities_version_range`, and before starting any port.

    python mod/tools/check-mixin-targets.py

Exit code 0 means every injection point in TARGETS resolves identically across every
version in JARS. Read the exit code, not the tail of the output.
"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
REPO = os.path.dirname(MOD)
# The rig's download folder, where every check finds the Lost Cities jars.
MODS = os.path.join(REPO, "testrig", "downloads")

# The control comes first. Everything is compared against it.
JARS = [("7.4.12", "lostcities-1.20-7.4.12.jar"),
        ("7.5.1", "lostcities-1.20-7.5.1.jar"),
        ("7.5.2", "lostcities-1.20-7.5.2.jar"),
        ("7.5.3", "lostcities-1.20-7.5.3.jar"),
        ("7.5.4", "lostcities-1.20-7.5.4.jar"),
        ("7.5.5", "lostcities-1.20-7.5.5.jar"),
        ("7.5.6", "lostcities-1.20-7.5.6.jar")]

# 7.4.12 is the only version where the two place mixins target `place` itself. The
# 7.5 line moved both bodies into a lambda, so the expected shape differs by line and
# this records both rather than pretending one covers the other.
PLACE_7412 = "m_142674_ (Lnet/minecraft/world/level/levelgen/feature/FeaturePlaceContext;)Z"
FEATURE_75 = ("lambda$place$0 (Lnet/minecraft/server/level/WorldGenRegion;"
              "Lmcjty/lostcities/worldgen/IDimensionInfo;)Z")
SPHERE_75 = ("lambda$place$0 (Lnet/minecraft/server/level/WorldGenRegion;"
             "Lnet/minecraft/world/level/WorldGenLevel;"
             "Lmcjty/lostcities/worldgen/IDimensionInfo;)Z")

CC = "mcjty/lostcities/worldgen/lost/cityassets/ConditionContext"

# class, a row label that stays the same across versions, then either one
# "name descriptor" or {version: "name descriptor"} when a version moved the code,
# then [(label, the javap rendering of the call, how many times it must appear)]
TARGETS = [
    ("mcjty.lostcities.worldgen.lost.BuildingInfo", "the constructor",
     "BuildingInfo (Lmcjty/lostcities/varia/ChunkCoord;"
     "Lmcjty/lostcities/worldgen/IDimensionInfo;)V",
     [("Random.nextInt(II)", "java/util/Random.nextInt:(II)I", 1),
      ("new RuntimeException",
       'java/lang/RuntimeException."<init>":(Ljava/lang/String;)V', 1)]),

    ("mcjty.lostcities.worldgen.lost.cityassets.ConditionContext",
     "lambda$parseTest$7", "lambda$parseTest$7 (Ljava/util/Set;L" + CC + ";)Z",
     [("getPart()", "Method getPart:()Ljava/lang/String;", 1)]),

    ("mcjty.lostcities.worldgen.LostCityTerrainFeature", "generateStreet",
     "generateStreet (Lmcjty/lostcities/worldgen/lost/BuildingInfo;"
     "Lmcjty/lostcities/worldgen/ChunkHeightmap;)V",
     [("Random.nextInt(II)", "java/util/Random.nextInt:(II)I", 1)]),

    ("mcjty.lostcities.worldgen.LostCityFeature", "the fault report site",
     {"7.4.12": PLACE_7412, "*": FEATURE_75},
     [("printStackTrace", "printStackTrace:()V", 1),
      ("logChunkInfo",
       "ErrorLogger.logChunkInfo:(IILmcjty/lostcities/worldgen/IDimensionInfo;)V", 1)]),

    ("mcjty.lostcities.worldgen.LostCitySphereFeature", "the crash guard site",
     {"7.4.12": PLACE_7412, "*": SPHERE_75},
     [("generateSpheres",
       "Spheres.generateSpheres:(Lmcjty/lostcities/worldgen/LostCityTerrainFeature;"
       "Lnet/minecraft/server/level/WorldGenRegion;"
       "Lnet/minecraft/world/level/chunk/ChunkAccess;)V", 1)]),

    ("mcjty.lostcities.gui.LostCitySetup", "customize", "customize ()V", []),

    ("mcjty.lostcities.config.ProfileSetup", "readProfiles",
     "readProfiles (Ljava/nio/file/Path;)V",
     [("File.listFiles",
       "java/io/File.listFiles:(Ljava/io/FilenameFilter;)[Ljava/io/File;", 1),
      ("readFileToString", "FileUtils.readFileToString:", 1)]),

    ("mcjty.lostcities.gui.GuiLCConfig", "updateValues", "updateValues ()V", []),
]

# Reached by @Accessor rather than by injection. Exactly one member, by that name.
FIELDS = [("mcjty.lostcities.worldgen.lost.cityassets.ConditionContext", "belowPart"),
          ("mcjty.lostcities.gui.GuiLCConfig", "profileButton")]

# A member's own line in javap output: two spaces, then a declaration.
SIG = re.compile(r"^  \S.*[;{]\s*$")


def javap():
    for cand in (os.environ.get("LCRIG_JAVAP"), "javap",
                 r"C:/Program Files/Eclipse Adoptium/jdk-17.0.19.10-hotspot/bin/javap.exe"):
        if not cand:
            continue
        try:
            subprocess.run([cand, "-version"], capture_output=True, timeout=20)
            return cand
        except Exception:
            continue
    raise SystemExit("no javap found. Set LCRIG_JAVAP or put a JDK on PATH.")


def members(text):
    """javap -p -c -s output into [(declaration, descriptor, bytecode)]."""
    out, sig, desc, buf = [], None, None, []
    for line in text.splitlines():
        if SIG.match(line):
            if sig is not None:
                out.append((sig, desc, "\n".join(buf)))
            sig, desc, buf = line.strip(), None, []
            continue
        stripped = line.strip()
        if stripped.startswith("descriptor: ") and desc is None:
            desc = stripped[len("descriptor: "):]
            continue
        buf.append(line)
    if sig is not None:
        out.append((sig, desc, "\n".join(buf)))
    return out


def name_of(declaration):
    """'public void generateStreet(a, b);' into 'generateStreet'."""
    head = declaration.split("(")[0].strip()
    parts = head.split()
    # A constructor prints as its fully qualified class name, so take the last
    # dotted segment rather than the last whitespace-separated token.
    return parts[-1].split(".")[-1] if parts else head


def wanted(spec, version):
    if isinstance(spec, dict):
        return spec.get(version, spec.get("*"))
    return spec


def main():
    tool = javap()
    dumps = {}

    def dump(version, jar, cls):
        key = (version, cls)
        if key not in dumps:
            done = subprocess.run([tool, "-p", "-c", "-s", "-cp", jar, cls],
                                  capture_output=True, text=True)
            dumps[key] = done.stdout
        return dumps[key]

    rows = {}
    order = []

    def record(tag, label, version, verdict):
        if (tag, label) not in order:
            order.append((tag, label))
        rows[(tag, label, version)] = verdict

    for version, jarname in JARS:
        jar = os.path.join(MODS, jarname)
        if not os.path.isfile(jar):
            raise SystemExit("no %s. The Lost Cities jars are not ours to ship; "
                             "download each from CurseForge into testrig/downloads/."
                             % jar)

        for cls, row_label, spec, invokes in TARGETS:
            short = cls.split(".")[-1]
            want = wanted(spec, version)
            tag = short + " " + row_label
            text = dump(version, jar, cls)
            if not text.strip() or "Error:" in text:
                record(tag, "signature", version, "NOCLASS")
                continue
            name, desc = want.split(" ", 1)
            hits = [m for m in members(text)
                    if name_of(m[0]) == name and m[1] == desc]
            if len(hits) != 1:
                record(tag, "signature", version,
                       "MISSING" if not hits else "AMBIG x%d" % len(hits))
                continue
            record(tag, "signature", version, "ok")
            body = hits[0][2]
            for label, call, expected in invokes:
                seen = body.count(call)
                record(tag, label, version,
                       "ok" if seen == expected else "n=%d" % seen)

        for cls, field in FIELDS:
            text = dump(version, jar, cls)
            hits = [m for m in members(text)
                    if "(" not in m[0] and re.search(r"\b%s\b" % field, m[0])]
            record(cls.split(".")[-1] + "." + field, "field", version,
                   "ok" if len(hits) == 1 else "n=%d" % len(hits))

    versions = [v for v, _ in JARS]
    control = versions[0]
    print("%-56s" % "target / injection point"
          + "".join("%9s" % v for v in versions))

    failures = []
    for tag, label in order:
        row = [rows.get((tag, label, v), "?") for v in versions]
        note = ""
        if row[0] != "ok":
            note = "  <<< control not ok, this file is wrong"
            failures.append("%s / %s is not ok under the control %s"
                            % (tag, label, control))
        elif any(r != "ok" for r in row):
            broken = [v for v, r in zip(versions, row) if r != "ok"]
            note = "  <<< " + ", ".join(broken)
            failures.append("%s / %s does not resolve on %s"
                            % (tag, label, ", ".join(broken)))
        print("%-56s" % (tag + " / " + label)
              + "".join("%9s" % r for r in row) + note)

    print()
    if failures:
        print("%d injection points do not hold:" % len(failures))
        for line in failures:
            print("  FAIL " + line)
        return 1
    print("every injection point holds across %s" % ", ".join(versions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
