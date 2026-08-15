# The Lost Cities - DevTool

**A helper mod for people creating datapacks for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities).**

Find mistakes faster, understand why your cities generate the way they do, and make
your Lost Cities files easier to work with.

---

## What does it do?

Creating custom cities for Lost Cities can involve a lot of files, and when something
goes wrong, the error messages often don't tell you which file caused the problem.

**DevTool makes those problems much easier to find.**

It can:

- Tell you which building caused a generation error, and where it is
- Check your Lost Cities files for common mistakes before you create a world
- Let you use comments and trailing commas in your JSON files
- Show you exactly which building, part, and floor Lost Cities is using
- Help you look up palette characters and blocks
- Keep certain Lost Cities world types from crashing when generation encounters an error

It does **not** add blocks, items, mobs, structures, or anything else to your world.

## Use comments in your files

Normally, JSON does not allow comments. DevTool lets you use them:

```json5
// The tower at the centre of the city
{
  "filler": "#",
  "parts": [
    { "part": "mypack:origin" }, // Used on every level
  ],
}
```

Trailing commas are supported too.

You can use either `.json` or `.json5` files. If both versions of the same file exist,
the `.json5` version is used, and you are told which file was ignored.

This works in your datapacks and in your Lost Cities profiles.

## Find out what went wrong

When something is wrong with a building, Lost Cities can produce a large number of
errors from different chunks. It can be difficult to tell what the original problem
actually was.

DevTool gives you the useful information directly:

```
Misconfiguration! Floor were generated for a building where no part condition matches!
  [building mypack:tower at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]
```

Instead of searching through dozens of similar errors, you can immediately see **which
building is broken and where it came from**.

It also provides additional information for things such as missing palette characters,
including the character's code and name when the character cannot be displayed
normally.

## Check your files before creating a world

DevTool checks your Lost Cities files as they are loaded and reports common mistakes
with the file name and line number.

For example:

```
Lost Cities asset check: 2 errors, 1 warning
  ERROR  mypack:lostcities/buildings/tower.json:10  levels [3] match no part
         Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building
  ERROR  mypack:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
         looks like an ID, but 'loot' names a Condition
  WARN   mypack:lostcities/buildings/tower.json:13  range "0,2,9" has more than two numbers
         The mod reads the first two and discards the rest, silently
```

This can catch problems such as invalid blocks, incorrect floor ranges, conditions
that can never match, invalid weighted lists, and incorrectly sized layers.

**These checks do not prevent your pack from loading.** They simply tell you about
problems so you can fix them.

## See why a building generated the way it did

The `/lcdev report` command shows you what Lost Cities selected for a particular chunk.

It can show:

- Your profile
- The world style
- The city style
- The building
- Which part was selected on each level

This is especially useful when you're trying to figure out **why a particular
condition did or did not work**.

You can also look up individual palette characters or blocks:

```
/lcdev report
/lcdev char G
/lcdev block minecraft:gold_block
/lcdev in mypack:mystyle char G
```

The `in` command lets you inspect a specific file without having to find a generated
city first.

Characters can also be entered as `U+0047`, for the ones you cannot easily type into
chat.

## Works with your existing datapacks

You can keep your Lost Cities files where you already have them, including:

- Your world's `datapacks` folder
- Global datapack loaders
- `kubejs/data`

**Everyone loading a pack that uses DevTool's features needs the mod installed.**

Without DevTool, Lost Cities cannot read a `.json5` file at all, and a `.json` file
containing comments or trailing commas fails to load.

## Optional fixes

DevTool also includes two optional fixes for problems in Lost Cities itself.

They are **disabled by default** because they can change world generation.

They are:

- A `belowpart` condition that actually checks the part below it
- A `streetblocks.parts.full` option that can actually be selected

Each fix can be enabled separately in `config/lostcities_devtool-common.toml`.

There are also a few fixes enabled by default that only affect the Lost Cities menus
and do not change world generation.

## Prevent crashes in certain world types

Some Lost Cities world types can crash the server when a chunk fails to generate.

DevTool prevents those errors from crashing the server. This is on by default, and can
be turned off.

The broken chunk still fails to generate, and **the underlying problem is not hidden
or changed**. Instead, the error is recorded and generation continues.

This is available for `spheres`, `cavernspheres`, and `space`.

## Want to try it first?

Three example datapacks are available
[in the wiki repository](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test).

They demonstrate the same basic city using different setups, so you can see how the
files work before creating your own.

## More information

The [Lost Cities Wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/)
contains more detailed information about creating Lost Cities cities, including
explanations and examples for the features covered by DevTool.

## Credits and licence

The Lost Cities is created by **McJty**. The Lost Cities Discord also helped answer
questions that were not covered by the available documentation.

DevTool is an unofficial companion mod and is **not affiliated with or endorsed by
McJty or The Lost Cities.**

Released under [0BSD](https://opensource.org/license/0bsd).
