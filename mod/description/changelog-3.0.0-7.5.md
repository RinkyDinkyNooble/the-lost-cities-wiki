# 3.0.0-7.5

The same mod as 3.0.0, built against the 7.5 line of Lost Cities. No features are
added or removed. If you run 7.4.12, stay on 3.0.0.

It is beta because 7.5 turns on two road generation systems that did not exist when
this mod's checks were written. Everything passes, but the checks have had one run
against 7.5 rather than a release cycle of them.

## Which file to download

| Your Lost Cities | Download |
|---|---|
| 7.4.12 | `3.0.0` |
| 7.5.1, 7.5.2, 7.5.3, 7.5.4 | `3.0.0-7.5` |

## Why there are two files

The DevTool rewrites parts of Lost Cities' own methods so that a generation error
names the building that caused it. That ties it to the shape of those methods.

7.5 added a chunk neighbourhood locking system, and the body of the method that
generates a chunk moved into a helper the lock wrapper calls. The fault reporting and
the sphere crash guard both attach to code that moved with it. Nine of the eleven
patch points are unchanged between the lines. Two are not, and no single annotation
matches both shapes.

The key reference the mod ships is generated from the target jar, and the two lines
declare different keys: 131 profile keys on 7.4.12, 161 on 7.5.4.

## What is covered

| | 7.5.1 | 7.5.2 | 7.5.3 | 7.5.4 |
|---|---|---|---|---|
| Classes | 327 | 327 | 327 | 330 |
| Profile keys | 160 | 160 | 160 | 161 |
| Datapack keys | 268 | 268 | 268 | 268 |

Every patch point was compared by exact signature, and every rewritten call counted
inside the method it sits in, across all four versions with 7.4.12 as a control.

## One key exists only on 7.5.4

`railwayLevelOffset` arrived in 7.5.4. The key help and the file check carry it, so on
7.5.1, 7.5.2 or 7.5.3 you can be offered a key your Lost Cities ignores.

## Two things about 7.5 worth knowing

Lost Cities still picks a street type from a range that can only return the first
value, so `FULL` streets never generate. The optional `fixFullStreetShape` still
applies on 7.5.4, unchanged.

Lost Cities also still ships one palette file that fails its own format.
`bricks_desert_redsand.json` uses `minecraft:red_sandstone@2`, a 1.12 metadata suffix
that no longer parses, and the whole palette throws while being built. The DevTool's
asset check names the file and line at boot, as it does on 7.4.12. This is upstream
content and the DevTool changes nothing about it.
