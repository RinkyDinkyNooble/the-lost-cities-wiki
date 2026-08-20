---
claims: verified
---

# Building Reference

!!! tip "TL;DR"
    `buildings/<name>.json` describes a vertical stack: cellars, ground floor, upper floors, top. Each level picks from a list of candidate parts, filtered by [conditions](condition.md). **Every level that can generate must have at least one matching part, or that chunk fails to generate.** See [Floor coverage](#floor-coverage-the-most-common-failure).

!!! note "Some keys here do not exist on every version"
    `overrideFloors` and the part reference key `belowpart` were added in 7.4.12,
    and are absent in 8.2.2. `allowDoors` and `allowFillers` are absent in 6.0.3
    only. See [Key availability](../versions/key-availability.md).

## Keys

| Key | Required | Default | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `filler` | **yes** | | One palette character. The mod uses it to seat the building into the terrain. See [Filler](#filler-what-it-is-and-why-it-is-required). |
| `rubble` | no | | One palette character, used for rubble when this building is ruined. If the character is not defined in the palette, the mod uses `filler` instead. |
| `refpalette` | no | | Name of a shared palette. |
| `palette` | no | | An embedded palette, used instead of `refpalette`. It is a whole palette asset, so the entry list nests under a second `palette` key, exactly as on a [Part](part.md#the-shape-of-slices). Written as a bare list it decodes to nothing and is not an error. |
| `minfloors` / `maxfloors` | no | `-1` | Bounds on the number of floors above ground. By default these only narrow the count the profile already chose. They do not replace it. See [Floor counts](#how-floor-and-cellar-counts-are-decided). |
| `mincellars` / `maxcellars` | no | `-1` | The same, for levels below ground. |
| `allowDoors` | no | `true` | If `true`, the mod cuts doorways through this building's walls to adjacent city chunks. If `false`, the walls are left exactly as the part draws them and the building is sealed. The top floor never gets doors either way. Measured on 7.4.12: the same three-storey part placed 2240 wall blocks with doors allowed and 2256 with `allowDoors: false`. |
| `allowFillers` | no | `true` | If `true`, the mod generates the filler skirt around a building **that has cellars**. If `false`, it does not. On a building with no cellars this key changes nothing. See [Filler](#filler-what-it-is-and-why-it-is-required). |
| `overrideFloors` | no | `false` | If `false`, this building's floor bounds clamp the profile's count. If `true`, they replace it. See [Floor counts](#how-floor-and-cellar-counts-are-decided). |
| `preferslonely` | no | `0` | The chance, from 0 to 1, that this building type suppresses a building in each neighbouring chunk. `0` disables it. See [preferslonely](#preferslonely). |
| `parts` | **yes** | | The list of part references, one entry per candidate part. |
| `parts2` | no | | A second, independent list, generated as an overlay. See [parts2](#parts2). |

!!! note "Unset is `-1`, not `0`"
    The four floor and cellar bounds default to `-1`, and `-1` is the value the mod checks for "not set". So `"minfloors": 0` is **not** the same as omitting `minfloors`. `0` is a real bound that takes part in the clamping. Omitting the key lets the profile's value pass through untouched.

!!! warning "No bound is enforced on these numbers"
    `minfloors`, `maxfloors`, `mincellars` and `maxcellars` are plain integers in the codec. Nothing rejects a negative, an absurd value, or a minimum above its maximum.

    The `0` to `60` floor range and `0` to `20` cellar range you may have seen belong to the **profile**, not to a building, and even there they only drive the config screen's sliders. `Configuration.getInt` returns the stored value without clamping it, so a hand-edited profile is not validated either. See [Profile](profile.md). [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! warning "The casing is not consistent"
    `allowDoors`, `allowFillers` and `overrideFloors` are camelCase. `filler`, `rubble`, `preferslonely`, `minfloors`, `maxfloors`, `mincellars` and `maxcellars` are lowercase, in the same file. That is how the mod names them. Copy the exact key. Do not guess from the pattern.

!!! tip "Building your first one?"
    [Your First Custom City](../getting-started/first-city.md) walks through a complete working building and palette, and links to the finished files.

## Filler: what it is, and why it is required

`filler` is one palette character. With `parts`, it is one of only two required keys. It is not part of your building's design. It is what makes the building sit correctly in the ground. The mod uses it in two places. [game test](../examples/claim-tests.md#bld-7){.v .v-g}

**1. The foundation slab.** The mod clears space before a building generates. At the building's lowest level, any column that would otherwise be open air gets the filler block. Natural terrain is uneven, so without this a building on a slope generates with holes in its lowest floor where the ground falls away. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

**2. The skirt around cellars.** On a building with one or more cellars, the mod fills the outermost ring of the chunk with the filler block. The skirt runs from the building's bottom up to the ground level of whichever is lower, this chunk or the neighbour on that side. This hides the exposed outside face of the cellars, so the building reads as buried rather than as a box in a pit. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

`allowFillers: false` disables step 2 only. On a building with no cellars it changes nothing. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```json
{ "filler": "#" }
```

Choose something structural that matches the building's walls, such as stone bricks or concrete. The filler is visible. It is the underside and the buried exterior. <!-- noclaim -->

!!! danger "`filler` and `rubble` resolve against the building's palette, not the part's"
    The building's palette is the [Style](style.md)'s palettes, plus this building's own `refpalette` or `palette`. **A `refpalette` on a part is not included.**

    So a building whose `filler` character is defined only in a palette that its parts reference will pass every load check, generate its parts correctly, and then throw as soon as the mod places a door: [game test](../examples/claim-tests.md#bld-7){.v .v-g}

    ```
    java.lang.NullPointerException: Cannot invoke "...BlockState.m_60734_()" because "state" is null
        at mcjty.lostcities.worldgen.ChunkDriver.correct(ChunkDriver.java:253)
        at mcjty.lostcities.worldgen.gen.Doors.generateDoors(Doors.java:60)
    ```

    Give the **building** a `refpalette` as well as the parts. See [Error Messages](../troubleshooting/errors.md#nullpointerexception-in-chunkdrivercorrect). [game test](../examples/claim-tests.md#bld-7){.v .v-g}

    The building palette is built the same way in 7.4.12, 7.5.1 and 10.0.1. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## How floor and cellar counts are decided

**Your building does not decide how tall it is.** The [Profile](profile.md) rolls a
number, and the bounds then pull it up or down. [game test](../examples/claim-tests.md#bld-3){.v .v-g}

The mod rolls the count first: [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```
floors = buildingMinFloors
       + random( buildingMinFloorsChance
                 + (cityFactor + 0.1) x (buildingMaxFloorsChance - buildingMinFloorsChance) )
       + 1
```

The trailing `+ 1` is in the mod and is easy to miss. It is applied before either
bound, so it cannot push a building past `maxfloors`, but it does mean the roll
never produces `buildingMinFloors` exactly. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

`cityFactor` is how strong the city is at that point, so buildings are taller near
the centre. See [How a Chunk Becomes a City](../under-the-hood/city-generation.md). [code review](../examples/claim-tests.md#city-3){.v .v-c}

Then it applies the two bounds, **in this order**: [game test](../examples/claim-tests.md#bld-3){.v .v-g}

1. `if floors > maximum: floors = maximum`
2. `if floors < minimum: floors = minimum` [game test](../examples/claim-tests.md#bld-3){.v .v-g}

Each bound is resolved from three sources: [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| Bound | `overrideFloors: false` (default) | `overrideFloors: true` [game test](../examples/claim-tests.md#bld-2){.v .v-g} |
|---|---|---|
| maximum | The smallest of the profile's `buildingMaxFloors`, the building's `maxfloors`, and the city style's `maxfloors` | The building's `maxfloors`, alone |
| minimum | The largest of the profile's `buildingMinFloors`, the building's `minfloors`, and the city style's `minfloors` | The building's `minfloors`, alone |

!!! danger "`minfloors` is applied last, so it can push a building past every maximum"
    The minimum is a `max()`, and it runs **after** the maximum has already been
    applied. A building with `minfloors: 6` gets 6 floors even when the profile,
    the city style and its own `maxfloors` all say 3.

    This happens with `overrideFloors` absent. The key is not required to exceed
    the profile, and setting it changes nothing in that case, because the building's
    own value was already going to win the `max()`. [game test](../examples/claim-tests.md#bld-3){.v .v-g}

    Tested in game on 7.4.12: two buildings both declaring `minfloors: 6` and
    `maxfloors: 6`, one with `overrideFloors` and one without, generate at the same
    height under a profile allowing 2 to 3 floors. Both are 6. [game test](../examples/claim-tests.md#bld-3){.v .v-g}

    The minimum is a `max()` in 7.4.12, 7.5.1 and 10.0.1 alike. [code review](../examples/claim-tests.md#key-1){.v .v-c}

**So what is `overrideFloors` actually for?** Making a building **shorter or looser**
than the profile permits, which is the case the `min` and `max` cannot express: [game test](../examples/claim-tests.md#bld-2){.v .v-g}

| Goal | What to write [game test](../examples/claim-tests.md#bld-2){.v .v-g} |
|---|---|
| Never taller than 2, whatever the profile says | `maxfloors: 2`. No override needed, `min()` already wins. |
| Never shorter than 6, whatever the profile says | `minfloors: 6`. No override needed, `max()` already wins. |
| Exactly 2, in a profile whose `buildingMinFloors` is 4 | `minfloors: 2`, `maxfloors: 2`, **and** `overrideFloors: true`. Without it the profile's minimum of 4 wins the `max()`. |

Cellar counts work the same way, with one addition. The mod adds the chunk's city level to the profile's cellar maximum, so a building on higher terrain is allowed deeper cellars. [code review](../examples/claim-tests.md#ref-2){.v .v-c} [game test](../examples/claim-tests.md#bhv-1){.v .v-g}

!!! warning "`buildingMaxCellars: 0` does not mean no cellars"
    The maximum is a **base**, not a cap. Because the chunk's city level is added
    to it, a profile set to `0` still builds cellars on every chunk above level 0.
    Measured: `0` produced 2352 cellar blocks over sixteen chunks, and the same
    profile with every chunk pinned to level 0 produced none. [game test](../examples/claim-tests.md#bhv-1){.v .v-g}

## Floor coverage: the most common failure

Floor numbering: <!-- noclaim -->

| Level | Index [game test](../examples/claim-tests.md#bld-1){.v .v-g} |
|---|---|
| Deepest cellar | `-cellars` |
| Ground floor | `0` |
| Top floor | `floors` |

!!! important "`maxfloors: 3` is a four-storey building"
    The count is the **top index**, not the number of levels. Levels run from `-cellars` up to `floors` inclusive, and `0` is the ground floor. So `floors: 3` gives indices 0, 1, 2 and 3, which is the ground floor plus three above it. Cellars work the same way. `maxcellars: 1` adds one level, at index `-1`.

    `top: true` does not add a level. It is a test that passes on whichever index is currently highest. With `floors: 3` it matches index 3, the same level `"floor": 3` matches. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    That has a consequence. If you write both a `"floor": 3` part and a `top: true` part, **both match at index 3**, and the mod picks one at random with equal probability. If you want the top part to win there, either remove the `"floor": 3` entry or narrow it to `"floor": 3, "top": false`. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    You can combine `top` with a number. The mod chains tests with AND, so `{"part": "roof", "top": true, "floor": 3}` means "the top level, but only when the building is exactly four storeys tall". That is useful for a roof that suits only one height. [game test](../examples/claim-tests.md#cnd-1){.v .v-g}

The mod fills every level from `-cellars` up to and including `floors` in one pass. For each level it collects every entry in `parts` whose conditions match, then picks one at random. **If nothing matches, the mod throws:** [game test](../examples/claim-tests.md#bld-1){.v .v-g}

```
Misconfiguration! Floor were generated for a building where no part condition matches!
```

The wording, including the missing word, is the mod's own. This kills the chunk that was generating. [game test](../examples/claim-tests.md#bld-4){.v .v-g}

**The real rule is coverage, not `minfloors` and `maxfloors`.** You do not have to declare bounds. You have to guarantee that every level that can generate has a matching part. Declaring bounds is the most direct way to make that guarantee, because otherwise the profile decides the height and will eventually roll higher than the parts you wrote. [game test](../examples/claim-tests.md#bld-4){.v .v-g}

This is why writing `"floor": 0`, `"floor": 1` and `"floor": 2` and nothing else crashes. As soon as the profile rolls a four-floor building, level 3 has no match. [game test](../examples/claim-tests.md#bld-4){.v .v-g}

There are two ways to fix it. <!-- noclaim -->

=== "Bound the height (explicit)"

    ```json
    {
      "filler": "#",
      "minfloors": 0,
      "maxfloors": 2,
      "overrideFloors": true,
      "parts": [
        { "part": "shop_ground", "floor": 0 },
        { "part": "shop_mid",    "floor": 1 },
        { "part": "shop_top",    "floor": 2 }
      ]
    }
    ```
    `overrideFloors: true` matters here. Without it, a city style with a higher minimum can still push this building past floor 2. [game test](../examples/claim-tests.md#bld-2){.v .v-g}

=== "Add a catch-all"

    ```json
    {
      "filler": "#",
      "parts": [
        { "part": "shop_ground", "floor": 0 },
        { "part": "shop_top",    "top": true },
        { "part": "shop_generic" }
      ]
    }
    ```
    The last entry has no conditions, so it matches every level. The building can now be any height without crashing, and specific levels still get their own parts. [game test](../examples/claim-tests.md#bld-4){.v .v-g}

Use the catch-all as your default, especially if your building may be used under a profile you did not write. <!-- noclaim -->

The same rule applies below ground. If cellars generate and no part matches a negative index, you get the same crash. [game test](../examples/claim-tests.md#bld-4){.v .v-g}

!!! tip "`parts2` never crashes"
    Only `parts` has to match. If nothing in `parts2` matches a level, that level simply gets no overlay.

!!! note "`parts2` sits on the same level, it does not stack above it"
    For each level the mod places the `parts` entry, then places the `parts2` entry
    **at the same origin** if one matched. So the overlay writes into the space the
    main part just filled, and anything it sets replaces what is already there.
    Leave the positions you want kept as air in the overlay part.

    Confirmed in game on 7.4.12: a base part of 1504 blocks with an 8-block overlay
    generated all 1504 and all 8. [game test](../examples/claim-tests.md#bld-5){.v .v-g}

## Part references

Each entry in `parts` is a part name plus any of **13** optional test keys. They are the same set a [Condition](condition.md) entry uses, so anything valid there is valid here. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Type | Matches when [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|
| `part` | string | **Required.** Not a test. It names the [Building Part](part.md) this entry places when every test below passes. An entry without it fails to load. |
| `floor` | int | The level index equals this number. `0` is ground, negatives are cellars. |
| `range` | string | The level index falls between two comma-separated integers, including both ends. |
| `top` | bool | If `true`, this is the building's topmost level. If `false`, it is any other level. |
| `ground` | bool | If `true`, the level index is `0`. If `false`, it is any other level. |
| `cellar` | bool | If `true`, the level index is below `0`. If `false`, it is `0` or above. |
| `isbuilding` | bool | If `true`, a building stands in this chunk. If `false`, none does. |
| `issphere` | bool | If `true`, this chunk is inside a city sphere. If `false`, it is outside one. |
| `chunkx` / `chunkz` | int | The absolute chunk coordinate equals this number. |
| `inpart` | string or list | The current part name is in this set. |
| `belowpart` | string or list | The part directly below is in this set. |
| `inbuilding` | string or list | The current building name is in this set. |
| `inbiome` | string | The current biome is in this set. **Avoid it here on Minecraft 1.21 and later**, see below. |

!!! danger "`inbiome` on a part reference fails every chunk on 1.21 and later"
    Reading a biome here means reading it out of a neighbouring chunk while that chunk is still generating, which Minecraft 1.21 refuses. Measured on 8.2.2: one part reference carrying `inbiome` failed **335** chunks with `Exception generating new chunk`. The same pack runs clean on 7.4.12 and 7.5.1. [game test](../examples/claim-tests.md#ek-5){.v .v-g}

    The same key on a [Condition](condition.md) is safe on every version, because a condition is evaluated later. Put the biome test there instead. [game test](../examples/claim-tests.md#ek-5){.v .v-g}

    The accepted shape also moved. 7.5.1 takes a list or a string, 8.2.2 takes only a string, and 7.4.12 accepted an object and quietly did nothing with it. A bare string is the only form every version accepts. [game test](../examples/claim-tests.md#ek-5){.v .v-g}

```json
{ "part": "apartment_floor", "floor": 2 }
{ "part": "apartment_mid",   "range": "9,12" }
```

When several test keys are set on one entry, **all of them must pass**. The mod chains them with AND, never with OR. An entry with no test keys matches every level, which is what makes the catch-all pattern work. [game test](../examples/claim-tests.md#cnd-1){.v .v-g}

Among all matching entries the mod picks one at random with equal probability. There is no `factor` key here, unlike a [Condition](condition.md) entry. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### `range`, for a run of identical floors

`range` is the compact way to say "floors 9 through 12 all use this part" instead of writing four separate `floor` entries. [game test](../examples/claim-tests.md#cnd-2){.v .v-g}

```json title="Two candidates across floors 9 to 12, picked at random per floor"
{
  "filler": "~",
  "parts": [
    { "part": "building001_floor4", "range": "9,12" },
    { "part": "building001_floor5", "range": "9,12" },
    { "part": "building001_top", "top": true }
  ]
}
```

| | [game test](../examples/claim-tests.md#cnd-3){.v .v-g} |
|---|---|
| **Format** | A string holding two integers separated by a comma. Write `"9,12"`, not `[9,12]` and not `9,12`. |
| **Bounds** | Inclusive at both ends. `"9,12"` matches 9, 10, 11 and 12. |
| **Negatives** | Work normally. `range` tests the same index `floor` does, so `"-2,-1"` matches the two deepest cellars. |

!!! warning "A third number is accepted and silently ignored"
    The mod splits the string on commas and reads only the first two pieces. `"1,2,3"` does **not** throw. It produces the range 1 to 2 and discards the 3, with no error and no log line.

    These forms do throw `Bad range specification: <l1>,<l2>!`: [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    | You write | Why it throws [code review](../examples/claim-tests.md#ref-2){.v .v-c} |
    |---|---|
    | `"9"` | There is no second number. |
    | `"9, 12"` | The space makes `" 12"` a non-number. |
    | `"abc,def"` | Neither piece is a number. |

!!! note "`range` does not require `minfloors` or `maxfloors`"
    `range` filters the level index and does nothing else. It shares the [coverage rule](#floor-coverage-the-most-common-failure) with `floor`: every level that can generate still needs something to match it.

    Declaring `minfloors` and `maxfloors` is one way to keep the generated range inside what your parts cover, and it is a reasonable habit. Remember that those bounds only clamp the profile unless you also set `overrideFloors: true`. Under a profile whose `buildingMaxFloors` is 8, `maxfloors: 13` gives you 8, not 13. A `top: true` entry is what safely caps the stack however tall it ends up. [game test](../examples/claim-tests.md#bld-3){.v .v-g}

### Example: two candidates for the same floor

```json
{
  "filler": "#",
  "parts": [
    { "part": "apartment_floor_a", "floor": 2 },
    { "part": "apartment_floor_b", "floor": 2 }
  ]
}
```

Floor 2 becomes `apartment_floor_a` or `apartment_floor_b`, with equal probability. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## parts2

`parts2` is a second, independent pass over the same levels. The mod checks it separately for each level. If something matches, it generates that part on top of the one from `parts`, at the same height. [game test](../examples/claim-tests.md#bld-5){.v .v-g}

Use it for decoration or variation layered over a structural base. Put one plain floor shell in `parts`, and an optional furniture, damage or signage overlay in `parts2`. That avoids authoring every combination as its own part. <!-- noclaim -->

## preferslonely

`preferslonely` is a probability from 0 to 1, default 0, which disables it. It does not affect the building it is set on. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

When the mod decides whether a chunk gets a building, it looks at the building type of the four orthogonally adjacent chunks, west, east, north and south. It rolls once against each neighbour's `preferslonely`. If any roll succeeds, this chunk gets no building. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

So `preferslonely: 0.8` on a cathedral means chunks next to a cathedral are usually left empty, which gives the cathedral open space. This applies only to normal single-chunk buildings. A [multi-building](multibuilding.md) ignores it. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

`1.0` does **not** empty every neighbour. In a city whose only building type carries `1.0`, about a quarter of the buildings a `0.0` control builds still generate: 4560 blocks against 18028 over the same sixteen chunks. The effect is large and it is not total, and the reason for the surviving quarter has not been traced. Treat the value as a strong preference rather than a guarantee. [game test](../examples/claim-tests.md#bhv-2){.v .v-g}

## See also

- [Building Part Reference](part.md) for what a part contains
- [Condition Reference](condition.md) for the full test key table
- [City Style Reference](citystyle.md) for the settings that override yours
- [Profile Reference](profile.md) for where floor counts come from <!-- noclaim -->
