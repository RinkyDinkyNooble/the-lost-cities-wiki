# The Lost Cities - DevTool

A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities),
for people authoring content for it. It reports faults earlier and more accurately,
and can optionally repair behaviour traced to a bug.

It adds no blocks, no items and no generation of its own. Removing it leaves every
world it touched loadable by vanilla Lost Cities.

The build plan, including everything not yet written, is in [PLAN.md](PLAN.md).

## Requirements

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| The Lost Cities | 7.4.12, a hard dependency |

The Lost Cities version range is deliberately narrow. A mixin is bound to the shape
of the code it patches, so each target version needs its own verification pass.

## Configuration

`config/lostcities_devtool-common.toml`, in two groups.

| Group | Default | Rule |
|---|---|---|
| `diagnostics` | on | Only changes what is reported. Cannot alter block placement. |
| `repairs` | off | Changes what generates. A world made with one enabled will not come out the same without it. |

## What it does today

### `catchSphereFeatureErrors`

`LostCityFeature` wraps its generation call in a `catch (Exception)`, which is what
makes a mistake in a datapack survivable: the chunk fails, a line is logged, and
generation continues.

`LostCitySphereFeature` has no `try` anywhere in the class, and it reaches the same
`BuildingInfo` work through `Spheres.generateSpheres`. On `landscapeType` spheres,
cavernspheres or space, a fault that would normally be logged per chunk escapes to
vanilla's feature placer instead.

Measured on Lost Cities 7.4.12, same pack, same profile, same seed, with only the
toggle changed:

| Toggle | Faults escaping | Faults logged | Server |
|---|---|---|---|
| off | 21 | 0 | connection dropped mid-run |
| on | **0** | 338 | ran to completion |

Nothing about what generates changes. A chunk that would have failed still fails and
is left in the same partial state. Only the survivability changes.

### `detailedFaultReports`

The mod logs `Error generating chunk <x>,<z>: <message>`. Those coordinates are the
chunk being generated, which for a whole class of faults is not the chunk at fault:
a fault raised while a chunk's `BuildingInfo` is built spreads to every neighbour
that queries it, and those queries chain.

Two things are added, and nothing the mod logs is suppressed.

**The misconfiguration message is enriched at the throw**, where the building and
its chunk are known exactly:

```
Misconfiguration! Floor were generated for a building where no part condition matches!
  [building wt5:rangetest at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]
```

On a pack with three broken buildings, that turned 78 undifferentiated failures
across a 13 by 10 chunk area into three named faults.

**A fuller report is logged beside each caught fault**, naming the profile, world
style, city style, building, floor and cellar counts, and the whole cause chain. For
an unresolved palette character it gives the code point and Unicode name, which a
console cannot render:

```
Lost Cities generation fault
    chunk 8,14
    fault: RuntimeException: Could not find entry '?' in the palette for part 'wt7:ct_box'!
    undefined character: '?'  U+0470  CYRILLIC CAPITAL LETTER PSI
    used by part: wt7:ct_box
    the message names the part, but the fault is in a palette. Check, in this order:
      1. the part's own 'palette' or 'refpalette'
      ...
```

### `validateOnLoad`

Every Lost Cities asset file is checked when datapacks load, and what will fail is
reported once, with a file name and a line number:

```
Lost Cities asset check: 6 errors, 2 warnings
  ERROR  wt5:lostcities/buildings/prectest.json:10  levels [3] match no part
         Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building.
         Generation throws 'Misconfiguration! ...', and every chunk that queries
         this one fails the same way
  ERROR  wt5:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
         looks like an ID, but 'loot' names a Condition
  WARN   wt5:lostcities/buildings/rangetest.json:13  range "0,2,9" has more than two numbers
         The mod reads the first two and discards the rest, silently
```

The mod finds these during generation instead, one chunk at a time, often thousands
of times over and with the coordinates of a chunk that merely asked about the one at
fault.

Checked, all decidable from a single file:

| Rule | Otherwise found as |
|---|---|
| Level coverage against the declared bounds, or against every height the profile could roll | `Misconfiguration! Floor were generated...` on every affected chunk |
| `inpart` and `belowpart` in a building's `parts` | Silence. Neither key can ever match there |
| A `range` that does not parse, or carries a third number | A throw, or a floor range that is not the one written |
| `loot` or `mob` holding an ID rather than a Condition name | `Error getting resource ...`, after placement, leaving invisible chests |
| A `char` longer than one code unit, or starting above U+FFFF | Silence, or a smeared layer |
| A `block` value that is not a legal block id, such as a 1.12 `@meta` suffix | The whole palette throws while being built, so every character in the file stops resolving. Lost Cities 7.4.12 ships one |
| A weighted list that misses or overruns its 128 slots | `Not enough blocks in the random list`, or entries that never appear |
| A `slices` layer that is not `xsize * zsize` characters | `String index out of range`, or a silent shift |

Nothing is prevented from loading. The check reports and steps aside.

A building does not have to declare floor bounds. Conditions written as `top: true`
and `top: false` cover every level at any height, which is what the mod's own content
does, so where bounds are absent the check tests every height the profile could roll
rather than demanding a declaration.

### `acceptCommentsAndTrailingCommas`

Lost Cities asset files may carry comments and trailing commas:

```json
// the marker tower at the city centre
/* pinned at relative 0,0 so it lands on the city's own chunk */
{
  "filler": "#",
  "parts": [
    { "part": "wt7:origin" },
  ],
}
```

Without this, the same file stops the server starting with
`MalformedJsonException: Expected name at line 17 column 2`.

This is a **subset of JSON5**, not the whole of it. Unquoted keys and single quotes
are not accepted, because they change what a valid file looks like without solving a
problem an author has.

**Scoped by path.** Only files under `data/<namespace>/lostcities/` are affected. The
hook is the one place where a datapack registry's files are listed together with the
location each came from, so Lost Cities assets can be told apart from everything
else. No other mod's files, and none of Minecraft's own, are touched.

Comments and trailing commas are replaced with spaces rather than deleted, so every
remaining character keeps its original offset. Line numbers reported by the asset
check, and by any parse error, still point at the right line of the file as written.

!!! note
    A pack that uses comments will not load for anyone without this mod.

### `acceptJson5Extension`

A Lost Cities asset or profile may be named `.json5`, which is what makes an editor
stop underlining it.

Nothing in Minecraft or in Lost Cities reads such a file. Datapack assets are listed
with a filter on `.json` and their id is then derived by stripping exactly five
characters, so `buildings/tower.json5` is either invisible or registered as
`buildings/tower.j`, which is a legal resource path and therefore does not even throw.
Profiles are filtered on `.json` too, by `File.listFiles`.

So the file is presented to both loaders under its `.json` name, and read with
comments and trailing commas allowed whatever `acceptCommentsAndTrailingCommas` says.
Nothing else needs patching, because the id is then derived from a name that is
already correct.

| Covered | Not covered |
|---|---|
| `data/<namespace>/lostcities/**` | `pack.mcmeta`, which vanilla reads before any of this |
| `config/lostcities/profiles/*` | Every other mod's files, and Minecraft's own |

**Where both names exist the `.json5` wins.** Lost Cities rewrites every profile it
ships as `.json` on each launch, so the opposite rule would make overriding one
impossible.

### `warnOnJson5Override`

A shadowed file is reported at load and once in chat to any operator joining:

```
Lost Cities JSON5: 1 file is shadowing a .json of the same name
  wt9:lostcities/buildings/shadowed.json5  wins over  wt9:lostcities/buildings/shadowed.json
  The .json is not read. Delete it, or delete the .json5, so an edit lands where you expect.
```

The two files sit next to each other in an editor looking interchangeable, and only
one is read, so an edit to the wrong one changes nothing and gives no sign of why. It
is not an error and nothing is prevented. Set this to `false` if you keep both on
purpose.

Measured on `wiki-test9`, same seed, same pack, with only the toggle changed:

| `acceptJson5Extension` | `.json5`-only building | Shadowed pair | `.json` part reference into a `.json5` |
|---|---|---|---|
| on | 512 blocks | diamond, 512 blocks, no emerald | 512 blocks |
| off | 0 | 0 of either | 0, and 533 chunks log `Error getting resource` |

## Repairs

Every setting under `repairs` changes what generates and defaults to **off**. A world
made with one enabled will not come out the same without it.

### `fixBelowPart`

`belowpart` is compiled into a predicate that reads the **current** part, which is
byte for byte what `inpart` compiles to, so the two keys are the same test. The value
it needs is already passed in and stored in a field with no accessor, so only the
read is wrong.

| Repair | A two-level building gated on `belowpart` |
|---|---|
| off | gold on both levels, 1504 blocks, no diamond |
| on | gold on level 0, diamond on level 1, 752 blocks each |

A building gated on `belowpart` currently fails every chunk it stands in and takes
its neighbours with it, so this can only turn a failing building into a working one.
`inpart` is left alone: it reads the current part, which is what its name says.

### `fixFullStreetShape`

The street type is picked with `nextInt(0, StreetType.values().length - 2)`. The
bound is exclusive and the enum holds NORMAL, FULL and PARK, so the expression is
`nextInt(0, 1)` and only NORMAL is ever chosen. PARK has its own branch, so the
subtraction was meant to exclude PARK and removes FULL as well by being one too
large.

The same expression appears twice, in `BuildingInfo` and in
`LostCityTerrainFeature.generateStreet`. The second re-rolls and overwrites the
stored value before switching on it, so both are patched.

Verified on the same seed and the same chunk, with the toggle as the only change:

| Repair | A custom `full` street part |
|---|---|
| off | 0 blocks placed, and every chunk reports `street type: NORMAL` |
| on | 256 blocks, one full layer, and chunks report `street type: FULL` |

### `rightClickCyclesProfilesBack`

Right-click on the profile button on the Cities screen steps **backwards**.

Left-click cycles forward and wraps, so reaching the entry just before the current
one means clicking through the whole list. The button is a plain vanilla `Button`,
and `AbstractButton.mouseClicked` accepts button 0 only, so a right-click on it
currently does nothing at all.

The order is the forward cycle's own, read from `LostCitySetup.toggleProfile`:

| | |
|---|---|
| Which profiles appear | every entry of `STANDARD_PROFILES` whose `isPublic()` is true, which is the default unless a profile's own JSON sets `"public": false` |
| The order | `default` pinned first, then `String.compareTo` on the key. Code point order, so a digit sorts before an uppercase letter and an uppercase letter before a lowercase one |
| The disabled state | sits between the last profile and the first, so going back from disabled reaches the last profile |

Client only, changes no generation, on by default.

## Commands

### `/lcdev in <asset> char <c>` and `/lcdev in <asset> block <id>`

The same two questions, asked of a **named** palette, part or building instead of
the chunk underfoot.

```
/lcdev in j5:demo char G
character 'G'  U+0047 in j5:demo
palette: Block{minecraft:gold_block}
```

`<asset>` tab completes over every palette, part and building that carries one. It
works from anywhere: outside a city, in a dimension with no Lost Cities profile, or
before a single chunk of the pack has generated. That is the state an author is
actually in while editing, and it is the one state the chunk based forms cannot
answer from.

The asset comes **before** the character in the command, not after, so the greedy
argument is the last node of every branch and no literal can be swallowed.

A part or building appears here whether it carries a palette inline or points at one
with `refpalette`, because what is wanted is the palette that part actually sees.

### `/lcdev report block <block id>`

The reverse lookup: which palette characters produce this block, here.

```
characters mapping to minecraft:gold_block in chunk 10,8
'G'  U+0047: always
'y'  U+0079: one of 3 in a weighted list
```

Reading a palette forwards answers "what is this character". Standing in front of a
block and asking which character placed it is the question an author actually has,
and no forward reading answers it, because the merged palette is assembled in memory
from up to three sources. More than one character can map to the same block, and a
weighted list can hold it among others, so every match is reported.

### `/lcdev report [character]`

Reports what the generator decided for the chunk the caller is standing in, and
optionally what a palette character resolves to there.

```
chunk 10,8   block 160,128
profile: wtseven
world style: wt7:test
is city: true
city level: 4
city style: wt7:test
building: wt7:rangetest
floors: 6, cellars 0   levels 0 to 6 inclusive
level 0: wt7:rt_gold
level 1: wt7:rt_gold
level 2: wt7:rt_gold
level 3: wt7:rt_diamond
level 4: wt7:rt_diamond
level 5: wt7:rt_diamond
level 6: wt7:rt_diamond
character 'G'  U+0047
resolves to: Block{minecraft:gold_block}
```

Both the bare `char` and the bare `block` form report the chunk **and** every named
asset that defines the character:

```
character 'D'  U+0044
here: Block{minecraft:dirt}
building j5:gold: Block{minecraft:diamond_block}
palette j5:demo: Block{minecraft:diamond_block}
palette lostcities:common: Block{minecraft:dirt}
part j5:p_diamond: Block{minecraft:diamond_block}
incomplete: 1 asset could not be built and were not searched
  palette lostcities:bricks_desert_redsand: RuntimeException: Error getting resource
```

The chunk is one answer out of many, and where no city generated it is not an answer
at all. Reporting only the chunk is how `D` reads as dirt while the author's own
palette says diamond.

**An answer assembled from part of the assets is named as such.** Every asset is
built on its own rather than through `AssetRegistries.loadAll`, which has no guard
and stops at the first asset that throws, leaving every asset after it unbuilt. One
unreadable file therefore costs its own line rather than the whole answer.

Two things there are not available any other way.

**The part chosen for each level.** That is the direct answer to a coverage
question, and to any question about which condition won. The listing above shows
`range: "0,2,9"` covering levels 0 to 2, which is the third number being discarded.

**What a character resolves to after the merge.** A palette is merged from the
style, then the building, then the part, and the result is written nowhere. For an
unresolved character the report says so, rather than waiting for the chunk to fail:

```
character 'Ѱ'  U+0470
resolves to: NOTHING. Generation would fail this chunk with 'Could not find entry'
check: the part's palette, then the building's, then the style's, and whether it
is a frompalette alias in a cycle
```

### How this differs from the mod's own commands

| Command | Needs `editMode` | Output | Answers |
|---|---|---|---|
| `/lostcities debug` | no | server console only | The generator's decisions for a chunk: profile, building, floor and cellar counts, city level, street type, ruin height, highway and rail data |
| `/lostcities listparts` | **yes** | chat | Which parts exist in the editor session |
| `/lostcities locatepart` | **yes** | chat | Where a named part was placed |
| `/lcdev report` | no | chat | The above, plus the part chosen for **each level**, plus what a character resolves to after the palette merge, plus the reverse lookup |

Two practical differences. `listparts` and `locatepart` need a world created with
`editMode: true`, so they are unavailable in any world not set up for the editor,
including one that is merely misbehaving. And `debug` writes to the server console,
so on a dedicated server the person asking cannot read the answer.

What no existing command reports at all is the part chosen per level, and the merged
palette. Those are the two things assembled in memory and written nowhere.

If the chunk itself cannot be described, because its selection stage is what throws,
the command says that too. It is the answer to the question.

## Building

```bash
./gradlew build
```

The jar lands in `build/libs/` as `lostcities_devtool-<minecraft>-<version>.jar`.
`libs/lostcities-1.20-7.4.12.jar` is compile-only and is not bundled; check with
`unzip -l`, which should list no `mcjty/` entries.

**This cannot be built by CI.** Every mixin targets a Lost Cities class, so the build
needs McJty's jar on the compile classpath, and that jar is not ours to redistribute.
It is gitignored, so a runner checking out this repository does not have it. Releases
are therefore built locally.

[CurseMaven](https://cursemaven.com) resolves CurseForge files as Gradle dependencies
by project and file id. Declaring the dependency that way redistributes nothing, lets
CI build the mod, and removes the manual step from a fresh clone.

## Testing

Acceptance tests run on the wiki's headless server rig, which boots a real server,
force loads a grid and reads the world back over RCON. Each one wipes the world
first and removes the jar afterwards, so the rig's baseline stays what the wiki's
published results were produced on.

| Check | What has to hold |
|---|---|
| `mod/tools/check-validator.py` | Every asset-check rule says the right thing, says nothing about a sound asset, and never throws on a malformed one. No server, under a second |
| `mod/tools/check-workshop.py` | The dimension exists, the catalogue lays out without two touching plots sharing a colour, and every plot's settings file round trips through `/lcdev plot` |
| `mod/tools/check-export.py` | The compiler writes a pack, and that pack, installed as a datapack, generates a city with the workshop's blocks in it |
| `mod/tools/check-import.py` | Lost Cities' own pack imports: 42 assets onto 42 plots, and what lands has the settings to export again |
| `mod/tools/check-roundtrip.py` | Export, import, export again is **byte for byte the same pack**, and every plot holds the blocks it held before the export. Over every row class, both orientations of a multibuilding, block states with properties, both non-default palette placements, json5 output, the raw escape hatch, and two plots asking for one asset name |

```bash
python mod/tools/check-roundtrip.py
```

The round trip is the one that stops the two halves drifting apart. The other three
can each pass while the exporter and the importer disagree about the format, because
both were written from the same reading of it.

Every feature in [PLAN.md](PLAN.md) names the test that proves it.

## Licence

[0BSD](LICENSE.txt). No rights reserved, no attribution required.

Not affiliated with or endorsed by McJty.
