# 3.0.0-7.5

**The same mod, for the 7.5 line of Lost Cities.** No features are added or removed.
If you are on 7.4.12, stay on 3.0.0; this file will not load for you, and that is on
purpose.

Marked **beta** because 7.5 turns on two generation systems that did not exist when
this mod's checks were written. Everything passes, but the checks have had one run
against 7.5 rather than a release cycle of them.

## Which file to download

| Your Lost Cities | Download |
|---|---|
| 7.4.12 | `3.0.0` |
| 7.5.1, 7.5.2, 7.5.3, 7.5.4 | `3.0.0-7.5` |

Forge checks the version and refuses to start rather than loading the wrong one, so a
mismatch is a clear message at boot instead of a confusing failure later.

## Why there are two files

The DevTool rewrites parts of Lost Cities' own methods to report faults with the
building that caused them. That ties it to the shape of those methods.

7.5 added a chunk neighbourhood locking system, and the body of the method that
generates a chunk moved into a helper that the lock wrapper calls. The fault reporting
and the sphere crash guard both attach to code that moved with it. Nine of the eleven
patch points did not change at all; two did, and those two cannot be written to match
both versions at once.

The shipped key reference is also generated from the target jar rather than written by
hand: 7.4.12 declares 131 profile keys and 7.5.4 declares 161.

## What is covered

7.5.1, 7.5.2, 7.5.3 and 7.5.4, checked rather than assumed.

| | 7.5.1 | 7.5.2 | 7.5.3 | 7.5.4 |
|---|---|---|---|---|
| Classes | 327 | 327 | 327 | 330 |
| Profile keys | 160 | 160 | 160 | 161 |
| Datapack keys | 268 | 268 | 268 | 268 |

Every patch point was compared by exact signature, and every rewritten call was counted
inside the method it sits in, across all four versions and against 7.4.12 as a control.
All four agree.

## One key exists only on 7.5.4

`railwayLevelOffset` was added in 7.5.4. The DevTool's key help and validation carry it,
so on 7.5.1, 7.5.2 or 7.5.3 you can be offered a key your Lost Cities ignores. Omitting
it would have hidden a real key from everyone on the current version, which is worse.

## Two things about 7.5 worth knowing

**The street shape bug is still there.** Lost Cities picks a street type from a range
that can only ever return the first one, so `FULL` streets never generate. The optional
`fixFullStreetShape` still applies, unchanged, on 7.5.4.

**Lost Cities still ships one palette file that fails its own format.**
`bricks_desert_redsand.json` uses `minecraft:red_sandstone@2`, a 1.12 metadata suffix
that no longer parses. The DevTool's asset check names it on boot, as it does on 7.4.12.
This is upstream content, not something the DevTool changes.
