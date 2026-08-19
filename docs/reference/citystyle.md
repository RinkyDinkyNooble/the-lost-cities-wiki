---
claims: verified
---

# City Style Reference

!!! tip "TL;DR"
    `citystyles/<name>.json` is the theme layer. It picks a [Style](style.md), sets building, street, park and rail behaviour, and can inherit from another city style. **Inheritance behaves differently for selectors than for everything else.** See [Inheritance](#inheritance).

!!! note "Several keys on this page do not exist on every version"
    More of this page is version-sensitive than any other reference page, because
    the street, park, corridor and general settings all live here.

    | Keys | Need | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
    |---|---|
    | `profile_overrides`, holding only `openLotParkChance` | 7.5.0 |
    | Inside `parkblocks`: `parkchance`, `parkborder`, `parkelevation`, `parkstreetthreshold`, `avoidfoliage` | 7.4.12 |
    | Inside `streetblocks`: `frontchance`, `fountainchance` | 7.4.12 |
    | Inside `corridorblocks`: `corridorchance` | 7.4.12 |
    | Inside `selectors`: `feather`, `minSpawnDistance`, `maxSpawnDistance` | 7.4.12 |
    | `stuff_tags`, and inside `streetblocks` the key `parts` | 6.2.2 |
    | Inside `generalblocks`: `leaves`, `rubbledirt` | present except in 6.0.3 |

    The 7.4.12 rows are also absent in 8.2.2, whose version number reads newer. See
    [Key availability](../versions/key-availability.md). [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Keys

| Key | Required | Meaning | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|
| `inherit` | no | The name of another city style to build on. See [Inheritance](#inheritance). |
| `style` | no | The name of a [Style](style.md), which is the palette combinator. This decides how the city looks. |
| `stuff_tags` | no | A list of tags controlling which [Stuff Objects](stuff.md) can appear. Note the underscore. The tag `"all"` is always included. |
| `explosionchance` | no | Float, 0 to 1. Overrides the [Profile](profile.md)'s `explosionChance`. |
| `generalblocks` | no | Palette characters for `ironbars`, `glowstone`, `leaves` and `rubbledirt`. The damage and ruin passes use them. |
| `buildingsettings` | no | `minfloors`, `maxfloors`, `mincellars`, `maxcellars` and `buildingchance`. Overrides the matching [Profile](profile.md) values, and is in turn narrowed by each [Building](building.md)'s own bounds. |
| `corridorblocks` | no | `corridorchance`, plus the `roof` and `glass` characters. |
| `parkblocks` | no | `parkchance`, `parkstreetthreshold` (a count of surrounding street chunks, 0 to 8), `avoidfoliage`, `parkborder`, `parkelevation`, plus the `elevation` and `grass` characters. |
| `railblocks` | no | The `railmain` character. |
| `sphereblocks` | no | The `inner`, `border` and `glass` characters for city spheres. |
| `streetblocks` | no | `fountainchance` and `frontchance`, the `street`, `border` and `wall` characters, plus a nested `parts` block for [street part-name overrides](../concepts/infrastructure-parts.md). Three more keys parse and do nothing: `width`, `streetbase` and `streetvariant`. A fourth, `parts.full`, parses and is never reached. See the warning below. |
| `selectors` | no | Eight weighted lists: `buildings`, `bridges`, `parks`, `fountains`, `stairs`, `fronts`, `raildungeons` and `multibuildings`. See [Selectors](#selectors-and-distance-gating). |

!!! danger "A city style that inherits nothing must define its own characters"
    The generator reads these characters and dereferences them **without a null
    check**. If the city style does not supply one and nothing it inherits does,
    every chunk that reaches that code fails:

    ```
    java.lang.NullPointerException: Cannot invoke "java.lang.Character.charValue()"
      because "corridorRoofBlock" is null
        at mcjty.lostcities.worldgen.gen.Corridors.generateCorridors
    ```

    The full set, with the values `citystyle_common` uses: [code review](../examples/claim-tests.md#ref-1){.v .v-c}

    | Block group | Characters | `citystyle_common` | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
    |---|---|---|
    | `streetblocks` | `street`, `border`, `wall` | `S`, `y`, `w` |
    | `corridorblocks` | `roof`, `glass` | `x`, `+` |
    | `parkblocks` | `elevation` | `x` |
    | `railblocks` | `railmain` | `y` |
    | `sphereblocks` | `inner`, `border`, `glass` | `b`, `9`, `Z` |

    Almost nobody hits this, because almost every city style inherits
    `citystyle_common`. The mod's own `citystyle_standard` sets **none** of these
    and works only for that reason. <!-- noclaim -->

    A standalone city style, written to empty an inherited selector for example, has
    to set them all itself. Found the hard way: 2 test runs, 1535 then 357 failed
    chunks, each exposing the next missing character in turn. [game test](../examples/claim-tests.md#cty-8){.v .v-g}

    `sphereblocks` only matters in a world with city spheres. The others are reached
    by any ordinary city. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    All 17 character getters are present and unguarded in 7.4.12, 7.5.1, 8.4.1 and
    10.0.1, so this is not version specific. [code review](../examples/claim-tests.md#key-1){.v .v-c}

!!! warning "None of these numbers are validated"
    Nothing validates a number in an asset JSON, exactly as in the [Profile](profile.md). A `buildingchance` of `4.0` loads and simply means always. The ranges this page mentions are the windows the mod is built around, not checks it performs.

!!! warning "Three `streetblocks` keys parse and then do nothing"
    `width`, `streetbase` and `streetvariant` all load, all inherit, and are all readable by a companion mod through `ILostCityCityStyle`. **No generation code reads any of them.**

    | Key | Reaches | Read during generation | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
    |---|---|---|
    | `street` | City style, generator | Yes |
    | `border` | City style, generator | Yes |
    | `wall` | City style, generator | Yes |
    | `width` | City style, public API only | **No** |
    | `streetbase` | City style, public API only | **No** |
    | `streetvariant` | City style, public API only | **No** |

    All three look load-bearing because the mod's own content sets them. `citystyle_config` exists solely to set `width`, and both `citystyle_common` and `citystyle_border` set `streetbase` and `streetvariant`. Setting them changes nothing about how a street generates. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    If you want to change what a street is made of, edit the palette characters the street **part** uses, or point `streetblocks.parts` at your own part. See [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md). <!-- noclaim -->

!!! danger "`streetblocks.parts.full` is a fourth dead key"
    It loads, it inherits, and the street type it belongs to is never assigned. The
    mod picks the street type with `nextInt(0, values().length - 2)`, which on 3
    constants can only return `NORMAL`.

    The other 6 shape keys work. Only `full` is unreachable. Confirmed in game, and
    unreachable in 7.4.12 through 10.0.1. See
    [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md#streets). [game test](../examples/claim-tests.md#cty-4){.v .v-g}

!!! warning "The naming is not consistent"
    Six of these keys use a `...blocks` suffix: `generalblocks`, `corridorblocks`, `parkblocks`, `railblocks`, `sphereblocks` and `streetblocks`. One uses a `...settings` suffix: `buildingsettings`. That is genuinely how the mod names them. Copy the exact key. Do not guess from the pattern.

!!! note "`railmain` resolves once per chunk, not once per block"
    If `railmain` points at a weighted [Palette](palette.md) entry, that is a `variant` or a `blocks` list rather than a fixed `block`, the mod picks one result and reuses it for the whole rail-bed strip in that chunk. It does not re-roll per block.

    On a long straight railway this appears as solid-coloured strips 16 blocks long, because each chunk gets its own independent roll. The mod's own default city style points `railmain` at the `stonebrick` variant, which is mostly plain stone bricks with a small chance of cracked or mossy, so most chunks look identical and occasionally a whole chunk-length strip stands out. [game test](../examples/claim-tests.md#cty-2){.v .v-g}

    This is how the resolution works, not a fault. If you want every rail chunk to look uniform, use a fixed `block` instead of a weighted one. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Selectors and distance gating

All eight selector lists take the same entry shape. Two keys are the common case. Three more exist and are almost unknown. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Required | Limits | Meaning | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|---|
| `factor` | **yes** | float above 0 | The relative weight. |
| `value` | **yes** | | The name of the building, park, bridge and so on. |
| `minSpawnDistance` | no | blocks, 0 or more | The weight is 0 closer to the origin than this. Defaults to `0`. |
| `maxSpawnDistance` | no | blocks, 0 or more | The weight is 0 further out than this. Defaults to unlimited. |
| `feather` | no | blocks, 0 or more | The width of a fade band on both edges. `0`, the default, means a hard cutoff. |

Note the **camelCase** on those three, unlike nearly every other key in the mod. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

```json title="Skyscrapers only in the far city, fading in over 500 blocks"
{
  "selectors": {
    "buildings": [
      { "factor": 1.0, "value": "mypack:house" },
      { "factor": 2.0, "value": "mypack:skyscraper",
        "minSpawnDistance": 3000, "feather": 500 }
    ]
  }
}
```

Inside the allowed band the entry carries its full `factor`. Within `feather` blocks of an edge the mod ramps it linearly between 0 and `factor`. Outside that band the weight is 0. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! warning "Three things the key names do not tell you"
    **Distance is measured from the world origin, not from world spawn.** The mod squares the chunk's own block coordinates, so the centre of the effect is always 0, 0. If your spawn is not near the origin, this does not behave the way the name suggests.

    **It stops working beyond about 46,340 blocks from the origin.** The mod holds the squared distance in a 32-bit integer, which overflows past that radius. The value goes negative and every comparison flips. The same overflow applies to `minSpawnDistance` and `maxSpawnDistance` themselves, because the mod squares those as integers too. Treat the whole feature as usable only within the first 46,000 blocks. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    **If every entry in a list is excluded, the mod picks the first one anyway.** The weighted picker sums the weights to zero and then returns the first element rather than nothing, so a fully gated list falls back silently instead of reporting an error. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### An empty selector list is safe for five of the eight, and fatal for three

Setting a selector to `[]` is not uniformly safe. The weighted picker returns `null` for an empty list, and what happens next depends entirely on which lookup the caller used. [game test](../examples/claim-tests.md#cty-7){.v .v-g}

| Selector | Empty list | What you get | [game test](../examples/claim-tests.md#cty-7){.v .v-g}
|---|---|---|
| `parks` | Safe | No park in that chunk. |
| `fountains` | Safe | No fountain. |
| `stairs` | Safe | No stairs. |
| `fronts` | Safe | No building front. |
| `raildungeons` | Safe | No rail dungeon. |
| `buildings` | **Crashes** | `Invalid building for multibuilding!` |
| `multibuildings` | **Crashes** | `Cannot find multibuilding: null` |
| `bridges` | **Crashes** | `Invalid name given to minecraft:root getOrThrow!` |

The five safe ones go through the mod's warn-and-skip lookup, which returns immediately when the name is `null`. It does not even log, because the null check happens before the registry is consulted. The feature does not appear. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

The three fatal ones reach a lookup that refuses a null name. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! danger "`bridges` must be non-empty even when `bridgeChance` is `0`"
    The mod resolves the bridge part **eagerly**, in the same straight run of code that sets the door block and the stair part, for every city chunk that has a building. No chance value is tested first.

    So `bridgeChance: 0` does **not** protect an empty `bridges` list. Setting the chance to zero and the list to `[]` still fails every building chunk. Confirmed in game: 1842 failed chunks in one session, with `bridgeChance` at `0.0`. [game test](../examples/claim-tests.md#cty-6){.v .v-g}

    If you do not want bridges, leave the list populated and set the chance to `0`. Do not empty the list. <!-- noclaim -->

`fountains` is the opposite case: the mod tests `fountainChance` before it looks anything up, so a zero chance means the selector is never consulted. `parks` is looked up unconditionally, like bridges, but survives it because parks use the safe lookup. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! warning "Remember that inheritance is additive, so `[]` may not mean empty"
    Writing `"buildings": []` in a style that inherits from `citystyle_common` does not give you an empty list. You inherit the parent's 8 entries and add nothing. The crash above only happens when the **merged** list is empty, which means you either inherited nothing or inherited from a style that has none.

## What a building front is

`fronts` is the least self-explanatory selector. <!-- noclaim -->

A front is an extra part that belongs to a **building** but generates in the **adjacent street chunk**, along the edge facing that building. It is the shop awning, porch, step or overhang that makes a building meet the street instead of stopping dead at the chunk line. [game test](../examples/claim-tests.md#frt-1){.v .v-g}

The sequence: <!-- noclaim -->

1. When the mod builds a building's chunk, it rolls once against `frontchance` (or the profile's `buildingFrontChance`). If the roll wins, that building gets a front part, chosen from the `fronts` selector.
2. The front is **not** drawn in the building's own chunk. Nothing happens yet.
3. Later, when a neighbouring **street** chunk generates, it looks at each of its four neighbours in turn. For any neighbour that is a building with a front, it draws that front along the shared edge. [game test](../examples/claim-tests.md#frt-1){.v .v-g}

So one building with a front can have it drawn up to four times, once by each adjacent street chunk, and a street chunk between two buildings draws both. [game test](../examples/claim-tests.md#frt-1){.v .v-g}

!!! note "The front uses the building's palette, not the street's"
    The mod generates the part with the **neighbouring building's** context, so the front resolves its characters against that building's merged palette. This is what makes a front match the building it belongs to rather than the road it sits on.

    Hard air in a front resolves to real air, so a front never fills with water, whatever the sea level. [code review](../examples/claim-tests.md#pipe-3){.v .v-c}

### When a front does not appear

All of these must hold, or the street chunk skips it: [game test](../examples/claim-tests.md#frt-1){.v .v-g}

| Condition | Meaning | [game test](../examples/claim-tests.md#frt-1){.v .v-g}
|---|---|
| The neighbour has a building | Fronts only come from buildings. |
| The neighbour's building rolled a front | The `frontchance` roll happened in the neighbour's chunk. |
| This chunk's street is a normal street | An elevated park section counts as a park, not a street, and gets no fronts. |
| This chunk sits lower than the neighbour's roof | Specifically, this chunk's city level must be below the neighbour's city level plus its floor count. |
| This chunk is not an underground rail station, and not a rail chunk descending from the surface | Those need the space for their own geometry. |

### Front parts are deliberately not 16 by 16

This is the exception to the usual footprint rule, and the mod's own content relies on it. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| Shipped part | `xsize` | `zsize` | Layers | [code review](../examples/claim-tests.md#ref-2){.v .v-c}
|---|---|---|---|
| `building_front1` | 2 | 16 | 4 |
| `building_front2` | 3 | 16 | 4 |
| `building_front3` | 3 | 16 | 4 |

A front is a **strip**, 2 or 3 blocks deep and 16 long, running the full length of the shared edge. The mod places the same strip on each of the four sides using a different rotation, so you author it once, for one edge, and the mod turns it for the other three. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

Write yours the same shape. A 16 by 16 front would cover the entire street chunk. <!-- noclaim -->

## Inheritance

`inherit` names one other city style. Chains work, so a style can inherit from a style that inherits from another, and the whole chain resolves. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

**There are two completely different merge behaviours, depending on the key.** [game test](../examples/claim-tests.md#cty-5){.v .v-g}

| Key group | Behaviour | [game test](../examples/claim-tests.md#cty-5){.v .v-g}
|---|---|
| `selectors`, all eight lists, and `stuff_tags` | **Additive.** The mod appends the parent's entries to yours. You end up with both. |
| Everything else: `style`, all the `...blocks` characters, `buildingsettings`, all the chances | **The child wins, key by key.** Any individual value you do not set is taken from the parent. |
| `streetblocks.parts` | **All or nothing.** See the warning below. |

### Selectors accumulate, they do not replace

This surprises nearly everyone. If a parent lists eight buildings and your child lists three, the resulting pool holds **eleven entries**, not three. There is no way to remove or narrow a parent's selector list. You can only add to it. [game test](../examples/claim-tests.md#cty-5){.v .v-g} The same catches `fronts`: `citystyle_common` ships three, so adding one of yours leaves a one-in-four draw, and three runs out of four look like your front is being ignored. [game test](../examples/claim-tests.md#frt-3){.v .v-g}

If your three entries name buildings the parent also names, those buildings appear **twice** in the pool. Their effective weight is the sum of both factors, not your value. [game test](../examples/claim-tests.md#cty-5){.v .v-g}

```json title="Parent"
{ "selectors": { "buildings": [
  { "factor": 1.0, "value": "house" },
  { "factor": 1.0, "value": "tower" }
] } }
```
```json title="Child, inheriting the above"
{ "inherit": "parent", "selectors": { "buildings": [
  { "factor": 5.0, "value": "house" }
] } }
```

The child's pool is `house` at 5.0, `house` at 1.0, and `tower` at 1.0. So `house` carries an effective weight of 6.0 against `tower`'s 1.0, not 5 to 1. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

**If you need a genuinely different building list, do not inherit from a style that has one.** Inherit from a minimal base, or from nothing, and declare the full list yourself. <!-- noclaim -->

!!! warning "`streetblocks.parts` is the exception, and it is all or nothing"
    Every other nested key merges key by key, so setting `streetblocks.border` alone keeps the parent's `streetblocks.wall`.

    **`streetblocks.parts` does not work that way.** Writing any `parts` block at all, even one holding a single key, discards the parent's entire `parts` block. Every key you did not restate falls back to the mod's built-in default, not to the parent's value. Restate every key you want to keep. [game test](../examples/claim-tests.md#cty-3){.v .v-g}

## How the shipped city styles are organised

The five city styles the mod ships are worth reading before you write your own, because the layering is deliberate. <!-- noclaim -->

```
citystyle_config          only { "streetblocks": { "width": 8 } }
      ^
citystyle_common          all block characters, all eight selectors, stuff_tags
      ^           ^              ^
citystyle_    citystyle_    citystyle_border
standard      desert        (adds buildingsettings and its own selectors)
```

The two most used styles are two lines each. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```json title="citystyle_standard.json, in full"
{
  "style": "standard",
  "inherit": "citystyle_common"
}
```
```json title="citystyle_desert.json, in full"
{
  "style": "desert",
  "inherit": "citystyle_common"
}
```

Three things are worth taking from this. <!-- noclaim -->

**1. A desert city is not made of different buildings.** `citystyle_standard` and `citystyle_desert` differ by exactly one key: which [Style](style.md) they point at. Same buildings, same street rules, same selectors, different palettes. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

A city's visual identity comes from the palette layer, not from authoring a separate set of buildings. If you want a themed city, write a new Style and new palettes first, not new buildings. <!-- noclaim -->

**2. `citystyle_config` exists to be overridden.** It sits at the bottom of the chain and holds one setting, so a modpack can replace one small file through the [`lostcities` namespace](../getting-started/namespaces.md) and have it apply to every city style, without copying anything else. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

The pattern is worth copying: put the settings most likely to be changed in their own small file at the base of the chain. The particular setting this file holds, `streetblocks.width`, does nothing in 7.4.12, so do not read the file as evidence that street width is adjustable. <!-- noclaim -->

**3. `citystyle_border` is what city edges use.** It inherits `citystyle_common` and adds `buildingsettings` with `maxfloors: 1`, `maxcellars: 1` and `buildingchance: 0.2`, which gives low, sparse buildings. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

This is the style to pair with the [`cityStyleThreshold` and `cityStyleAlternative`](profile.md#cities) profile keys to fade a dense downtown out into low outskirts. If you want that effect, copy this working example. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

`citystyle_border` also restates all the block characters it would have inherited anyway. That is harmless duplication. You do not need to imitate it. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### Writing your own

The practical decision is what to inherit from. <!-- noclaim -->

| Goal | Approach | <!-- noclaim -->
|---|---|
| Retheme an existing city, with different materials and the same content | Set `inherit: "citystyle_common"` and point `style` at your own [Style](style.md). Two lines, exactly like `citystyle_desert`. |
| Add a few buildings on top of the defaults | Set `inherit: "citystyle_common"` and list only your additions in `selectors.buildings`. The mod appends them to the built-in ones. |
| Use only your own buildings | **Do not inherit from `citystyle_common`.** Its selectors are merged in, so the built-in buildings continue to generate. Declare everything yourself. |
| Apply one setting across every city style | Override `citystyle_config` in the `lostcities` namespace. The only key it holds, `width`, has no effect, so this is a pattern to copy rather than a working knob. |

## Example: a minimal retheme

```json title="citystyle_wasteland.json"
{
  "inherit": "citystyle_common",
  "style": "mypack:wasteland",
  "buildingsettings": {
    "buildingchance": 0.5
  }
}
```

Everything comes from `citystyle_common` except the Style and the building density. `buildingsettings` merges key by key here, so setting only `buildingchance` leaves the parent's floor and cellar bounds intact. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## See also

- [Style Reference](style.md) for the palette layer that gives a city style its look
- [Profile Reference](profile.md) for the values these keys override
- [Building Reference](building.md) for the bounds that narrow `buildingsettings` further
- [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md) for `streetblocks.parts`
- [Stuff Object Reference](stuff.md) for `stuff_tags`
- [Glossary](../glossary.md) <!-- noclaim -->
