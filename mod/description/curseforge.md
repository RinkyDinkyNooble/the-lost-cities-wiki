# The Lost Cities - DevTool

**A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities).**
Build a pack by building it in Minecraft, open a pack you already have by walking
around inside it, and find the mistake in the one you are writing.

It adds no blocks, items, mobs or structures to your world, and nothing it does changes
world generation unless you switch on one of the optional fixes.

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47+ |
| The Lost Cities | 7.4.12, required |
| Java | 17 or newer |
| Licence | [0BSD](https://opensource.org/license/0bsd) |

---

## What it does

A custom city is a lot of small files, and when one of them is wrong, Lost Cities
usually tells you in a way that does not name the file.

- Builds a whole pack out of what you build in game, and opens a pack you already have
- Names the building that caused a generation error, and where it is
- Checks your files as they load and reports the file and line number
- Lets you write comments and trailing commas in your JSON
- Shows which building, part and floor the generator picked for a chunk
- Looks up palette characters and blocks, in both directions
- Carries a pack's licence with the pack, so credit is not lost in a rebuild
- Keeps a broken file from crashing sphere worlds

## Build a pack by building it

The workshop is a dimension laid out as a catalogue, with a plot for every shape a pack
can hold: 138 rows covering streets, highways, railways, monorails, parks, fountains,
bridges, stairs, fronts, rail dungeons, buildings, and every multibuilding footprint up
to the 10x10 that is as wide as one can be. Each plot sits on chunk boundaries and is
floor marked in its own colour. Rows start at eight plots and grow as far as you want.

```
/lcdev workshop build     lay the catalogue out
/lcdev workshop go        travel there
/lcdev workshop leave     go back where you came from
/lcdev workshop here      what the plot you are standing on compiles into
/lcdev workshop rows      every row, each one a place to click
```

Build in the plots with whatever you normally build with. Then compile the lot:

```
/lcdev export mypack
```

That writes a complete datapack and the profile that goes with it, ready to drop into a
world. A pack made this way generated a city with **10,672 gold blocks** in it.

`/lcdev export mypack plot` writes just the plot you are standing on, as a fragment
with no world style, for sharing one building rather than a city.

## Open a pack you already have

Point it at a pack that is loaded and it pastes that pack into the workshop, so you can
walk around it and edit it:

```
/lcdev import lostcities:standard
```

The Lost Cities default pack comes in as **42 assets on 42 plots, 714,240 blocks**,
streets included, even though nothing in that pack names a street part. Change one
building and compile the whole thing back out.

A building that names several parts for the same level comes in showing all of them
rather than the first one repeated. A palette entry's `tag` is carried both ways, so
command blocks keep their commands, chests keep their loot tables and spawners keep
their mobs. Command blocks arrive unable to fire, because forty spawn commands going
off while you are looking at a building is not useful. `/lcdev import mypack:main run`
pastes them live instead.

`tagkeys` decides which of a block's NBT reaches the pack, so a chest you opened while
building does not ship its contents, and a loot chest does not ship a seed that pins
one roll into every copy.

Importing a second city leaves the first one's plots alone, since an import only fills
what its own pack needs. It says how many it left behind, and `/lcdev workshop clear`
empties the workshop when you want to start again, writing a full backup pack first.

Every plot has a settings file beside your world, with the meaning of each key in a
comment above it, so a file you open six months later still says what it does. Edit it
in game or in a text editor: values are read from the file every time, so both stay in
step without syncing anything.

## A pack's licence travels with the pack

Import a pack and DevTool shows what its author said about reuse, reading
`license.txt` from the pack itself. Export, and those statements are carried into what
you build, one heading per namespace, so a pack compiled out of somebody else's content
does not ship with the credit stripped out.

A namespace that states nothing is reported as **nothing found**, which is not the same
as nothing being reserved. Copyright is automatic, so the mod says so rather than
guessing on the author's behalf.

## Find out what actually went wrong

One broken building makes Lost Cities produce errors from every chunk that asked about
it, and none of them say which building it was. DevTool says it directly:

<pre>
<span style="color:#ed3d3d">Misconfiguration!</span> Floor were generated for a building where no part condition matches!
  <span style="color:#7f7f7f">[building mypack:tower at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]</span>
</pre>

On a test pack with three broken buildings, 78 similar looking failures became **three
named ones**. Missing palette characters are reported the same way, with the
character's code and name when it cannot be printed.

## Your files are checked as they load

<pre>
Lost Cities asset check: <span style="color:#ed3d3d">2 errors</span>, <span style="color:#a5783a">1 warning</span>
  <span style="color:#ed3d3d">ERROR</span>  mypack:lostcities/buildings/tower.json:10  levels [3] match no part
         <span style="color:#7f7f7f">Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building</span>
  <span style="color:#ed3d3d">ERROR</span>  mypack:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
         <span style="color:#7f7f7f">looks like an ID, but 'loot' names a Condition</span>
  <span style="color:#a5783a">WARN</span>   mypack:lostcities/buildings/tower.json:13  range "0,2,9" has more than two numbers
         <span style="color:#7f7f7f">The mod reads the first two and discards the rest, silently</span>
</pre>

It catches floor ranges that leave a level with nothing to build, conditions that can
never match, invalid block names, weighted lists that do not add up, layers that are the
wrong size, Condition entries whose weight is missing or unreadable, and two faults that
otherwise pass in silence: a monorail part written as a list, which stops a world style
loading, and an inline palette written as a bare list, which loads perfectly and
generates an empty building.

**Nothing is blocked from loading.** The check tells you what is wrong and lets the pack
run.

## Ask why a chunk generated the way it did

```
/lcdev report                     profile, world style, city style, building, and the part on each level
/lcdev key name                   what a profile key means, its section, type, range and default
/lcdev char G                     what a palette character resolves to here
/lcdev block minecraft:gold_block which characters produce that block here
/lcdev in mypack:mystyle char G   the same lookup inside one named asset
/lcdev conditions                 every Condition loaded
/lcdev condition chestloot        its entries, each one's share, and the test that places it
```

`in` lets you inspect a named file without finding a generated city first, which is the
difference between testing a condition and waiting to see whether it worked.

`condition` matters more than it looks: `loot` and `mob` in a palette name a Condition
rather than a loot table or an entity, and until now there was no way to see what one
contained without opening somebody else's pack.

Tab completion does not read every loaded file on every keystroke. On a server holding
911 Lost Cities assets that cost **99 ms a character**, close to two seconds to type one
name; it is **0.1 ms** now.

## Palettes as large as your build

Every distinct block state in a pack needs its own palette character. The pool the
exporter draws from holds about **40,000** of them, against the roughly 26,000 block
states Minecraft ships, so a detailed build does not run out.

Characters are chosen to survive being written to a file and read back: nothing blank,
nothing that reorders the text around it, nothing a normaliser would rewrite, and
nothing above `U+FFFF`, which Lost Cities would read as two cells and shift the rest of
the row.

## Comments in your files

JSON does not allow comments. DevTool does:

```
// The tower at the centre of the city
{
  "filler": "#",
  "parts": [
    { "part": "mypack:origin" }, // used on every level
  ],
}
```

Trailing commas work too. Files can be named `.json` or `.json5`, and where both exist
the `.json5` one wins. This applies to your datapacks and to your Lost Cities profiles.

## Where it goes, and where your files can live

Your Lost Cities files can stay where you already keep them: the world's `datapacks`
folder, a global datapack loader, or `kubejs/data`.

Everything that matters runs on the server. The workshop, export and import, reading
`.json5`, the load-time check, the better error messages and every `/lcdev` command all
live there. Only the Lost Cities menu fixes are client side, so a client install is
optional and a client without the mod can still join a server that has it. In single
player, one install covers both.

**The machine loading the pack does need it.** Without DevTool, Lost Cities cannot read
a `.json5` file at all, and a `.json` file with comments or trailing commas fails to
load.

Every `/lcdev` command needs permission level 2, which means `op` on a server and cheats
enabled in single player. It teleports between dimensions, writes tens of thousands of
blocks and writes files beside your world, so it is a tool for building a pack rather
than a feature for players.

## Optional fixes

Two fixes correct bugs in Lost Cities itself. Both are **off by default**, because
turning one on changes what a seed generates, and each is switched separately in
`config/lostcities_devtool-common.toml`.

- A `belowpart` condition that checks the part below it, as its name says
- A `streetblocks.parts.full` option that can actually be selected. Measured on the same
  pack and seed: the `full` shape draws **nothing** with the fix off and **1,504
  blocks** with it on

Three more are on by default and touch only the Lost Cities menus, so they cannot change
a world. Pressing Customize after having played a world no longer crashes the game.
Right-clicking the profile button walks back through the list, so overshooting the
profile you wanted no longer means cycling all the way around. The Cities button stays
where it is when you resize the window.

## Sphere worlds do not crash on a broken file

Some Lost Cities world types take the server down when a chunk fails to generate.
Measured on the same pack and seed: **21 crashes** before, **none** after, with all 338
errors logged instead. The broken chunk still fails, and nothing about the fault is
hidden or changed. This is on by default, can be turned off, and covers `spheres`,
`cavernspheres` and `space`.

## Try it before you write anything

Three example datapacks are
[in the wiki repository](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test).
They build the same small city three different ways, so you can see how the files fit
together before starting your own.

Every command, argument and flag is written up in
[The DevTool Commands](https://rinkydinkynooble.github.io/the-lost-cities-wiki/tooling/lcdev/),
and the rest of the
[Lost Cities Wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/) covers the
format itself with examples.

## Credits and licence

The Lost Cities is created by **McJty**. The Lost Cities Discord answered questions that
no documentation covered.

DevTool is an unofficial companion mod and is **not affiliated with or endorsed by McJty
or The Lost Cities.**

Released under [0BSD](https://opensource.org/license/0bsd).
