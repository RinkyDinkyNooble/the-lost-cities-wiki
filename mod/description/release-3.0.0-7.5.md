# The Lost Cities - DevTool 3.0.0-7.5

Build a Lost Cities pack by building it in Minecraft, and open a pack you already have
by walking around inside it.

**This is 3.0.0 for the 7.5 line of Lost Cities.** Nothing is added and nothing is
removed. If you run 7.4.12, download 3.0.0 instead.

Marked **beta**: 7.5 turns on two road generation systems that did not exist when this
mod's checks were written. All 26 checks pass against 7.5.4, but they have had one run
against this line rather than a release cycle of them.

## Requires

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47+ |
| The Lost Cities | 7.5.1, 7.5.2, 7.5.3 or 7.5.4 |
| Java | 17 or newer |

Forge checks the Lost Cities version at boot and refuses to start rather than loading
the wrong file, so a mismatch is a clear message instead of a strange failure later.

## Which file to download

| Your Lost Cities | Download |
|---|---|
| 7.4.12 | `3.0.0` |
| 7.5.1 to 7.5.4 | `3.0.0-7.5` |

## Why two files instead of one

The DevTool rewrites parts of Lost Cities' own methods so that a generation error names
the building that caused it. That ties it to the shape of those methods.

7.5 added a chunk neighbourhood locking system and moved the body of the chunk
generation method into a helper the lock wrapper calls. The fault reporting and the
sphere crash guard both attach to code that moved with it. Nine of the eleven patch
points are unchanged between the lines; two are not, and those two cannot match both at
once.

The profile key reference the mod ships is generated from the target jar rather than
written by hand, and the two lines do not declare the same keys: 131 on 7.4.12, 161 on
7.5.4.

## What was checked

Every patch point was compared by exact signature, and every rewritten call counted
inside the method it sits in, across 7.4.12, 7.5.1, 7.5.2, 7.5.3 and 7.5.4. 7.4.12 was
the control.

| | 7.5.1 | 7.5.2 | 7.5.3 | 7.5.4 |
|---|---|---|---|---|
| Classes | 327 | 327 | 327 | 330 |
| Profile keys | 160 | 160 | 160 | 161 |
| Datapack keys | 268 | 268 | 268 | 268 |

7.5.1, 7.5.2 and 7.5.3 hold the same classes. 7.5.4 adds three GUI classes and one
profile key, and touches nothing this mod patches.

The full 26 check suite was run against the built jar on a dedicated server running
7.5.4.

## One key exists only on 7.5.4

`railwayLevelOffset` arrived in 7.5.4. The key help and the file check carry it, so on
7.5.1, 7.5.2 or 7.5.3 you can be offered a key your Lost Cities ignores. Leaving it out
would have hidden a real key from everyone on the current version.

## Two things about 7.5 worth knowing

**The street shape bug is still there.** Lost Cities draws a street type from a range
that can only return the first value, so `FULL` streets never generate. The optional
`fixFullStreetShape` still applies on 7.5.4, unchanged.

**Lost Cities still ships one palette file that fails its own format.**
`bricks_desert_redsand.json` uses `minecraft:red_sandstone@2`, a 1.12 metadata suffix
that no longer parses, and the whole palette throws while being built. The DevTool names
the file and line at boot, as it does on 7.4.12. This is upstream content, and the
DevTool changes nothing about it.

## Everything else

Identical to 3.0.0. The workshop, export and import, `.json5` and comments, the load
time file check, the fault reports, the palette pool, licence carrying, and every
`/lcdev` command behave exactly as they do there.

Every command and argument is documented in
[The DevTool Commands](https://rinkydinkynooble.github.io/the-lost-cities-wiki/tooling/lcdev/).

## Credits and licence

The Lost Cities is created by **McJty**. DevTool is an unofficial companion mod and is
**not affiliated with or endorsed by McJty or The Lost Cities.**

Released under [0BSD](https://opensource.org/license/0bsd).
