<h1 align="center">The Lost Cities - DevTool</h1>

<p align="center">
  <b>A helper mod for people creating datapacks for <a href="https://www.curseforge.com/minecraft/mc-mods/the-lost-cities">The Lost Cities</a>.</b>
</p>

<p align="center">
  Find mistakes faster, understand why your cities generate the way they do, and make your Lost Cities files easier to work with.
</p>

---

<h2>What does it do?</h2>

Creating custom cities for Lost Cities can involve a lot of files, and when something goes wrong, the error messages often don't tell you which file caused the problem.

**DevTool makes those problems much easier to find.**

It can:

- Tell you which building caused a generation error, and where it is
- Check your Lost Cities files for common mistakes before you create a world
- Let you use comments and trailing commas in your JSON files
- Show you exactly which building, part, and floor Lost Cities is using
- Help you look up palette characters and blocks
- Keep certain Lost Cities world types from crashing when generation encounters an error

It does **not** add blocks, items, mobs, structures, or anything else to your world.

<h2>Use comments in your files</h2>

Normally, JSON does not allow comments. DevTool lets you use them:

    // The tower at the centre of the city
    {
      "filler": "#",
      "parts": [
        { "part": "mypack:origin" }, // Used on every level
      ],
    }

Trailing commas are supported too.

You can use either `.json` or `.json5` files. If both versions of the same file exist, the `.json5` version is used.

This works in your datapacks and in your Lost Cities profiles.

<h2>Find out what went wrong</h2>

When something is wrong with a building, Lost Cities can produce a large number of errors from different chunks. It can be difficult to tell what the original problem actually was.

DevTool gives you the useful information directly:

    Misconfiguration! Floor were generated for a building where no part condition matches!
      [building mypack:tower at chunk 10,8, levels 0 to 6 inclusive.
       Every chunk that queries this one fails the same way]

Instead of searching through dozens of similar errors, you can immediately see **which building is broken and where it came from**.

It also provides additional information for things such as missing palette characters, including the character's code and name when the character cannot be displayed normally.

<h2>Check your files before creating a world</h2>

DevTool checks your Lost Cities files as they are loaded and reports common mistakes with the file name and line number.

For example:

    Lost Cities asset check: 2 errors, 1 warning
      ERROR  mypack:lostcities/buildings/tower.json:10  levels [3] match no part
             Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building
      ERROR  mypack:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
             looks like an ID, but 'loot' names a Condition
      WARN   mypack:lostcities/buildings/tower.json:13  range "0,2,9" has more than two numbers
             The mod reads the first two and discards the rest, silently

This can catch problems such as invalid blocks, incorrect floor ranges, conditions that can never match, invalid weighted lists, and incorrectly sized layers.

**These checks do not prevent your pack from loading.** They simply tell you about problems so you can fix them.

<h2>See why a building generated the way it did</h2>

The `/lcdev report` command shows you what Lost Cities selected for a particular chunk.

It can show:

- Your profile
- The world style
- The city style
- The building
- Which part was selected on each level

This is especially useful when you're trying to figure out **why a particular condition did or did not work**.

You can also look up individual palette characters or blocks:

    /lcdev report
    /lcdev char G
    /lcdev block minecraft:gold_block
    /lcdev in mypack:mystyle char G

The `in` command lets you inspect a specific file without having to find a generated city first.

<h2>Works with your existing datapacks</h2>

You can keep your Lost Cities files where you already have them, including:

- Your world's `datapacks` folder
- Global datapack loaders
- `kubejs/data`

<p><b>Everyone loading a pack that uses DevTool's features needs the mod installed.</b></p>

Without DevTool, Lost Cities cannot read a `.json5` file at all, and a `.json` file
containing comments or trailing commas fails to load.

<h2>Optional fixes</h2>

DevTool also includes two optional fixes for problems in Lost Cities itself.

They are **disabled by default** because they can change world generation.

They are:

- A `belowpart` condition that actually checks the part below it
- A `streetblocks.parts.full` option that can actually be selected

Each fix can be enabled separately in `config/lostcities_devtool-common.toml`.

There are also a few fixes enabled by default that only affect the Lost Cities menus and do not change world generation:

- **Right-click the profile button to go back a profile.** Left-click still moves
  forward, so if you overshoot the one you wanted you no longer have to cycle all the
  way around the list.
- The Cities button stays in place when you resize the window.
- Pressing Customize after playing a world no longer crashes the game.

<h2>Prevent crashes in certain world types</h2>

Some Lost Cities world types can crash the server when a chunk fails to generate.

DevTool prevents those errors from crashing the server. This is on by default, and can
be turned off.

The broken chunk still fails to generate — **the underlying problem is not hidden or changed**. Instead, the error is recorded and generation continues.

This is available for `spheres`, `cavernspheres`, and `space`.

<h2>Want to try it first?</h2>

Three example datapacks are available
<a href="https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test">in the wiki repository</a>.

They demonstrate the same basic city using different setups, so you can see how the files work before creating your own.

<h2>More information</h2>

The <a href="https://rinkydinkynooble.github.io/the-lost-cities-wiki/">Lost Cities Wiki</a> contains more detailed information about creating Lost Cities cities, including explanations and examples for the features covered by DevTool.

<h2>Credits and licence</h2>

The Lost Cities is created by <b>McJty</b>. The Lost Cities Discord also helped answer questions that were not covered by the available documentation.

DevTool is an unofficial companion mod and is <b>not affiliated with or endorsed by McJty or The Lost Cities.</b>

Released under <a href="https://opensource.org/license/0bsd">0BSD</a>.