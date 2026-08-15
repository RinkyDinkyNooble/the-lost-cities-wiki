# The Lost Cities - DevTool

A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities),
for people writing datapacks for it.

Lost Cities assembles a city from a chain of assets: a profile picks a world style,
which picks a city style, which picks buildings, which pick parts, which read
palettes. When something in that chain is wrong, the message you get names the chunk
that was being generated rather than the file that is broken, and you get one per
affected chunk. This mod reports the file instead, checks what it can before the world
loads, and lets asset files carry comments.

It adds no blocks, no items and no generation of its own. Removing it leaves every
world it touched loadable by vanilla Lost Cities.

## Requirements

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47+ |
| The Lost Cities | 7.4.12, a hard dependency |

The version range is deliberately narrow. This mod patches Lost Cities with mixins,
and a mixin is bound to the shape of the code it patches, so each target version needs
its own verification pass rather than a range bump.

## Comments in asset files

```json5
// the marker tower at the city centre
{
  "filler": "#",
  "parts": [
    { "part": "mypack:origin" },  // one part, no condition, covers every level
  ],
}
```

Comments and trailing commas, and files may be named `.json5` so your editor stops
underlining them. Both work for datapack assets under
`data/<namespace>/lostcities/` and for profiles in `config/lostcities/profiles/`.

Where both `foo.json` and `foo.json5` exist the `.json5` wins, and the shadowed file
is named in the log and once in chat, because two files that look interchangeable in
an editor and are not is a bad afternoon.

This is a subset of JSON5, not all of it. Unquoted keys and single quotes are not
accepted: they change what a valid file looks like without solving a problem an author
actually has.

**A pack written this way will not load for anyone without this mod.**

## Faults reported against the file, not the chunk

A fault raised while a chunk's information is built spreads to every neighbour that
queries it, and those queries chain. So one broken building produces a wall of
failures with coordinates that all point somewhere other than the problem.

The message is enriched where the building is still known:

```
Misconfiguration! Floor were generated for a building where no part condition matches!
  [building mypack:tower at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]
```

On a test pack with three broken buildings, that turned 78 undifferentiated failures
across a 13 by 10 chunk area into three named faults.

For an unresolved palette character the report gives the code point and Unicode name,
which a console cannot render, and the four places to look for it.

## Checked before the world loads

Every asset file is read when datapacks load, and what will fail is reported once,
with a file name and a line number:

```
Lost Cities asset check: 2 errors, 1 warning
  ERROR  mypack:lostcities/buildings/tower.json:10  levels [3] match no part
         Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building
  ERROR  mypack:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
         looks like an ID, but 'loot' names a Condition
  WARN   mypack:lostcities/buildings/tower.json:13  range "0,2,9" has more than two numbers
         The mod reads the first two and discards the rest, silently
```

Checked: level coverage, `inpart` and `belowpart` where neither can ever match, a
`range` that does not parse or carries a third number, `loot` and `mob` holding an ID
rather than a Condition name, a `char` that is not one code unit, a block id that is
not a legal resource location, a weighted list that misses or overruns its 128 slots,
and a `slices` layer that is not `xsize` by `zsize` characters.

Nothing is prevented from loading. The check reports and steps aside.

## Commands

```
/lcdev report                                  what the generator decided for this chunk
/lcdev char G                                  a character, here and in every asset
/lcdev char U+0047                             the same, by code point
/lcdev block minecraft:gold_block              which characters produce this block
/lcdev in mypack:mystyle char G                one named asset, from anywhere
/lcdev in mypack:mystyle block minecraft:gold_block
```

`/lcdev report` names the profile, world style, city style, building, and **the part
chosen for each level**, which is the direct answer to any question about which
condition won. None of the mod's own commands report that, and unlike
`/lostcities debug` this writes to whoever asked rather than to the server console.

The `in <asset>` forms tab complete over every palette, part and building that carries
a palette, and work from anywhere: outside a city, or in a dimension with no Lost
Cities profile at all. That is the state you are in while actually editing a file.

## Optional repairs

Off by default, one toggle each, in `config/lostcities_devtool-common.toml`. Each
changes what generates, so a world made with one enabled will not come out the same
without it.

| Repair | Measured, same seed, only the toggle changed |
|---|---|
| `belowpart` tests the part below, as its name says | off: gold on both levels. on: gold on level 0, diamond on level 1 |
| `streetblocks.parts.full` becomes reachable | off: 0 blocks placed, every chunk reports `NORMAL`. on: 256 blocks, chunks report `FULL` |

Both are off-by-one or wrong-field mistakes in compiled code that no datapack can
reach. The wiki traces each one to the line.

Two client fixes default to **on**, because they change nothing about generation:
the Cities button keeps its position when the window is resized, and pressing
Customize after having played a world no longer crashes the game. Right-click on the
profile button also cycles backwards, which it previously could not do at all.

## Sphere worlds survive a broken datapack

`LostCityFeature` wraps generation in a catch, which is what makes a datapack mistake
survivable: the chunk fails, a line is logged, generation continues.
`LostCitySphereFeature` has no such catch anywhere in the class, so on
`landscapeType` `spheres`, `cavernspheres` or `space` the same fault escapes instead.

Measured on the same pack, profile and seed, with only that toggle changed:

| Toggle | Faults escaping | Faults logged | Server |
|---|---|---|---|
| off | 21 | 0 | connection dropped mid-run |
| on | 0 | 338 | ran to completion |

Nothing about what generates changes. A chunk that would have failed still fails and
is left in the same state. Only the survivability changes.

## Try it without writing anything

Three datapacks and two profiles, generated from one definition so they cannot drift
apart, are in the wiki repository under
[`docs/examples/json5-test`](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test).
All three build the same three towers, and one of them needs no mod at all so you can
see the control first.

## More detail

Everything above is traced and tested on
[the Lost Cities Wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/),
which is what this mod implements the findings of. The
[mod's own README](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/blob/main/mod/README.md)
covers every setting and the evidence behind it.

## Credits and licence

The Lost Cities is by **McJty**, and the Lost Cities Discord answered questions no
documentation covers. This is an unofficial companion mod, not affiliated with or
endorsed by either.

Released under [0BSD](https://opensource.org/license/0bsd). No rights reserved, no
attribution required. Take any of it.
