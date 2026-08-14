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
| A weighted list that misses or overruns its 128 slots | `Not enough blocks in the random list`, or entries that never appear |
| A `slices` layer that is not `xsize * zsize` characters | `String index out of range`, or a silent shift |

Nothing is prevented from loading. The check reports and steps aside.

A building does not have to declare floor bounds. Conditions written as `top: true`
and `top: false` cover every level at any height, which is what the mod's own content
does, so where bounds are absent the check tests every height the profile could roll
rather than demanding a declaration.

## Commands

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

The mod ships `/lostcities debug`, which covers some of the same ground and writes
only to the server console, so on a dedicated server the person asking cannot read
the answer. This writes to the caller.

If the chunk itself cannot be described, because its selection stage is what throws,
the command says that too. It is the answer to the question.

## Building

```bash
./gradlew build
```

The jar lands in `build/libs/`. `libs/lostcities-1.20-7.4.12.jar` is compile-only
and is not bundled.

## Testing

Acceptance tests run on the wiki's headless server rig, which boots a real server,
force loads a grid and reads the world back over RCON.

```bash
cd ../research/server-1.20.1-7.4.12
python harness.py --pack ../../docs/examples/wiki-test8 --profile wteight \
    --probes probes/wt8ruins.json \
    --profile-patch '{"lostcity":{"landscapeType":"spheres","ruinChance":1.0}}'
```

Every feature in [PLAN.md](PLAN.md) names the test that proves it.

## Licence

[0BSD](LICENSE.txt). No rights reserved, no attribution required.

Not affiliated with or endorsed by McJty.
