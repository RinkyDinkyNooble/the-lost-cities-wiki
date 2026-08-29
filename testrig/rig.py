"""Putting the mod's jar into the rig, and taking the last one out first.

Every check does this, and it was 22 copies of two lines until a version bump
proved why that matters. Lives beside `rcon.py` because `testrig` is already on
`sys.path` in every check that talks to a server.
"""
import glob
import os
import shutil


def install(server, jar):
    """Copy `jar` into the rig's mods folder, removing older builds of it first.

    **The removal is the point.** A check that only copies leaves the previous
    version's jar behind the moment the version changes, and Forge refuses to start
    at all with two jars declaring one mod id. That turns a version bump into every
    server check failing to boot, with a message about duplicate mods rather than
    about anything the check was testing.

    Only builds of this same mod are removed. The prefix is the part of the file name
    before the first hyphen, so `lostcities_devtool-1.20.1-3.0.0-dev.jar` clears
    `lostcities_devtool-*.jar` and leaves Lost Cities' own `lostcities-1.20-7.4.12.jar`
    alone, which the rig needs and which this must never touch.

    Returns the path it wrote, which callers remove again when they are done.
    """
    mods = os.path.join(server, "mods")
    os.makedirs(mods, exist_ok=True)
    prefix = os.path.basename(jar).split("-")[0]
    dest = os.path.join(mods, os.path.basename(jar))
    for stale in glob.glob(os.path.join(mods, prefix + "-*.jar")):
        if os.path.abspath(stale) != os.path.abspath(dest):
            os.remove(stale)
    shutil.copy(jar, dest)
    return dest
