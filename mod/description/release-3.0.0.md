# The Lost Cities - DevTool 3.0.0

Build a Lost Cities pack by building it in Minecraft, and open a pack you already have
by walking around inside it.

A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities)
that makes datapack mistakes easier to find, and makes packs easier to write. It tells
you which building caused a generation error, checks your files as they load and names
the file and line, lets you write comments in Lost Cities assets, and gives you a
workshop dimension to build a pack in.

It adds no blocks, items, mobs or structures to your world, and nothing it does changes
world generation unless you switch on one of the two optional fixes.

Every command and argument is documented in
[The DevTool Commands](https://rinkydinkynooble.github.io/the-lost-cities-wiki/tooling/lcdev/).

**Upgrading from 1.x: export your workshop first.** An existing workshop's coordinates
change in this release. See the end.

## Requires

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47+ |
| The Lost Cities | 7.4.12 |
| Java | 17 or newer |

## Where to install it

Everything that matters runs on the server: the workshop, export and import, reading
`.json5` files, checking files as they load, the improved error messages, and all
`/lcdev` commands. Only the Lost Cities menu fixes are client side, so installing it on
a client is optional, and a client without it can still join a server that has it. In
single player, one install covers both.

## The workshop

A dimension laid out as a catalogue, with a plot for every shape a pack can hold: 138
rows, including every multibuilding footprint up to the 10x10 that is as wide as one can
be. Each plot sits on chunk boundaries and is floor marked in its own colour. Rows start
at eight plots and grow as far as you want.

Build in the plots. Then `/lcdev export mypack` writes a complete datapack and the
profile that goes with it. A pack made this way generated a city with **10,672 gold
blocks** in it. `/lcdev export mypack plot` writes just the plot you are standing on, as
a fragment with no world style, for sharing one building rather than a city.

It works the other way too. `/lcdev import lostcities:standard` pastes Lost Cities' own
pack into the workshop: **42 assets on 42 plots, 714,240 blocks**, streets included,
even though nothing in that pack names a street part. Change one building and compile
the whole thing back out.

`/lcdev workshop go` takes you there and `/lcdev workshop leave` brings you back to
where you ran `go`.

Every plot has a settings file beside your world, with the meaning of each key in a
comment above it. Edit it in game or in a text editor: values are read from the file
every time, so both stay in step without syncing anything. `/lcdev workshop sync` is for
the one case that needs it, a file describing a plot the catalogue does not have, and it
reports a mistyped key at any depth while it is there.

Every `/lcdev` command needs permission level 2, which means `op` on a server and cheats
enabled in single player.

## Palettes as large as your build

Every distinct block state needs its own palette character, and the pool holds about
**40,000** of them against the roughly 26,000 block states Minecraft ships, so a
detailed build does not run out. A pack of 1,174 distinct block states was exported,
loaded and generated to check it.

Characters are chosen to survive being written to a file and read back: nothing blank,
nothing that reorders the text around it, nothing a normaliser would rewrite, and
nothing above `U+FFFF`, which Lost Cities reads as two cells.

## Licences travel with the pack

An import shows what a pack's author said about reuse, read from `license.txt` in the
pack itself. An export carries those statements into what you build, one heading per
namespace, so a pack compiled out of somebody else's content does not ship with the
credit stripped out.

A namespace that states nothing is reported as **nothing found**, which is not the same
as nothing being reserved.

## Choosing what reaches the pack

`tagkeys` decides which of a block's NBT is exported, so a chest you opened while
building does not ship its contents and a loot chest does not ship a seed that pins one
roll into every copy. A conversion belongs to a scope, so a placeholder block can mean
different things on different plots, chunks and levels.

## Finding mistakes

Errors name the building rather than whichever neighbouring chunk happened to ask about
it. On a test pack with three broken buildings, 78 similar looking failures became three
named ones.

Your files are checked as they load. The check reports floor ranges that leave a level
with nothing to build, conditions that can never match, invalid block names, weighted
lists that do not add up, layers that are the wrong size, Condition entries whose weight
is missing or unreadable, and two faults that otherwise pass silently: a monorail part
written as a list, which stops a world style loading, and an inline palette written as a
bare list, which loads perfectly and generates an empty building. Nothing is blocked
from loading.

Comments and trailing commas work in Lost Cities files and profiles, and files can be
named `.json5`.

`/lcdev report` shows what the generator chose for your chunk, including which part was
used on each level. `/lcdev key` says what a profile key means. `/lcdev char` and
`/lcdev block` look characters and blocks up in both directions. `/lcdev conditions` and
`/lcdev condition <name>` show what a Condition holds, which matters because `loot` and
`mob` in a palette name one of those rather than a loot table or an entity.

Tab completion does not read every loaded file on every keystroke. On a server holding
911 Lost Cities assets that cost 99 ms a character, close to two seconds to type one
name; it is 0.1 ms now.

Sphere worlds no longer crash on a broken file. Measured on the same pack and seed: 21
crashes before, none after, with all 338 errors logged instead.

Two optional fixes correct bugs in Lost Cities itself, and both are off by default
because they change generation: `belowpart` checking the part below as its name
suggests, and the `full` street shape being selectable at all. The second is measured:
the shape draws nothing with the fix off and 1,504 blocks with it on.

## Upgrading from 1.x

**An existing workshop's coordinates change.** Rows used to take no room until they held
plots, so growing one pushed every row after it, and anything already built was left at
coordinates that now belong to a different plot. Rows keep their band now whether or not
they hold plots, which is what stops it happening again.

**Export before upgrading, import after.** The export is the only record of what was on
a plot that survives the move.
