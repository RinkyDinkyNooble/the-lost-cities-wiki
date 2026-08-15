# The Lost Cities - DevTool 1.0.1

First release.

A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities)
that makes datapack mistakes easier to find. It tells you which building caused a
generation error, checks your files as they load and names the file and line, and lets
you write comments in Lost Cities assets.

It adds no blocks, items, mobs or structures, and nothing it does changes world
generation unless you switch on one of the two optional fixes.

## Requires

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47+ |
| The Lost Cities | 7.4.12 |
| Java | 17 or newer |

## Where to install it

- **Dedicated server.** Everything that matters runs here: reading `.json5` files,
  checking files as they load, the improved error messages, and all `/lcdev` commands.
- **Client.** Only the Lost Cities menu fixes are client-side, so installing it here
  is optional. A client without it can still join a server that has it.
- **Singleplayer.** One install covers both.

## What it does

- **Errors name the building**, not whichever neighbouring chunk happened to ask about
  it. On a test pack with three broken buildings, 78 similar-looking failures became
  three named ones.
- **Nine checks run as your files load**, reporting floor ranges that leave a level
  with nothing to build, conditions that can never match, invalid block names,
  weighted lists that do not add up, and layers that are the wrong size. Nothing is
  blocked from loading.
- **Comments and trailing commas** work in Lost Cities files and profiles, and files
  can be named `.json5`.
- **`/lcdev report`** shows what the generator chose for your chunk, including which
  part was used on each level. **`/lcdev char`** and **`/lcdev block`** look characters
  and blocks up in both directions, in your chunk and across every loaded asset.
- **Sphere worlds no longer crash** on a broken file. Measured on the same pack and
  seed: 21 crashes before, none after, with all 338 errors logged instead.

Two optional fixes, **off by default** because they change generation, correct bugs in
Lost Cities itself: `belowpart` checking the part below as its name suggests, and the
`full` street shape being selectable at all.

## Try it without writing anything

[Three example datapacks](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test)
build the same three towers using different setups. One of them needs no mod at all,
so you can see a working baseline first.

## Documentation

[The Lost Cities Wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/) is
what this mod implements the findings of, and the
[mod README](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/blob/main/mod/README.md)
covers every setting with the evidence behind it.

## Known issue in Lost Cities itself

`lostcities:bricks_desert_redsand` contains `minecraft:red_sandstone@2`, a block name
from before the 1.13 flattening. The whole palette fails to load, not just that entry.
Nothing in 7.4.12 uses it, so it only matters if you point at it yourself. The file
check reports it with the file name and line.

## Credits and licence

The Lost Cities is by **McJty**, and the Lost Cities Discord answered questions no
documentation covers. Unofficial, and not affiliated with or endorsed by either.

[0BSD](https://opensource.org/license/0bsd).
