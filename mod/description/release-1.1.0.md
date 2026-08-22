# The Lost Cities - DevTool 1.1.0

Build a Lost Cities pack by building it in Minecraft, and open an existing pack by
walking around inside it.

A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities)
that makes datapack mistakes easier to find, and now makes packs easier to write.
It tells you which building caused a generation error, checks your files as they
load and names the file and line, lets you write comments in Lost Cities assets,
and gives you a workshop dimension to build a pack in.

It adds no blocks, items, mobs or structures to your world, and nothing it does
changes world generation unless you switch on one of the two optional fixes.

Every command, every argument and what each one means is documented in
[The DevTool Commands](https://rinkydinkynooble.github.io/the-lost-cities-wiki/tooling/lcdev/).

## Requires

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47+ |
| The Lost Cities | 7.4.12 |
| Java | 17 or newer |

## Where to install it

- **Dedicated server.** Everything that matters runs here: the workshop, export and
  import, reading `.json5` files, checking files as they load, the improved error
  messages, and all `/lcdev` commands.
- **Client.** Only the Lost Cities menu fixes are client-side, so installing it here
  is optional. A client without it can still join a server that has it.
- **Singleplayer.** One install covers both.

## The workshop

A dimension laid out as a catalogue: a plot for every shape a pack can hold, 138
rows of them, each chunk aligned and floor marked in its own colour, including every
multibuilding footprint up to the 10x10 that is as large as one can be. Rows start
at eight plots and grow as far as you want.

Build in the plots. Then `/lcdev export mypack` writes a complete datapack and the
profile that goes with it. A pack made this way generated a city with **10,672 gold
blocks** in it.

It goes the other way too. `/lcdev import lostcities:standard` pastes Lost Cities'
own pack into the workshop: **42 assets on 42 plots, 714,240 blocks**, streets
included, even though nothing in that pack names a street part. Change one building
and compile the whole thing back out.

Every plot has a settings file beside your world, written with the meaning of each
key in a comment above it, so a file you open six months later still says what it
does. Floors, cellars, roof variations, spawn weights, distance windows, city style
membership, and an escape hatch for anything the format has that the settings do not
name yet.

## Finding mistakes

- **Errors name the building**, not whichever neighbouring chunk happened to ask
  about it. On a test pack with three broken buildings, 78 similar-looking failures
  became three named ones.
- **Your files are checked as they load**, reporting floor ranges that leave a level
  with nothing to build, conditions that can never match, invalid block names,
  weighted lists that do not add up, layers that are the wrong size, and two faults
  that otherwise pass silently: a monorail part written as a list, which stops a
  world style loading, and an inline palette written as a bare list, which loads
  perfectly and generates an empty building. Nothing is blocked from loading.
- **Comments and trailing commas** work in Lost Cities files and profiles, and files
  can be named `.json5`.
- **`/lcdev report`** shows what the generator chose for your chunk, including which
  part was used on each level. **`/lcdev key`** says what a profile key means, which
  section it belongs to and what it does. **`/lcdev char`** and **`/lcdev block`**
  look characters and blocks up in both directions.
- **Sphere worlds no longer crash** on a broken file. Measured on the same pack and
  seed: 21 crashes before, none after, with all 338 errors logged instead.

Two optional fixes, **off by default** because they change generation, correct bugs
in Lost Cities itself: `belowpart` checking the part below as its name suggests, and
the `full` street shape being selectable at all.
