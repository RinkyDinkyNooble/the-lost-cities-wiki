# Building Reference

!!! tip "TL;DR"
    `buildings/<name>.json` describes a vertical stack: cellars, ground floor, upper floors, top. Each level picks from a list of candidate parts, filtered by [conditions](condition.md). **Every level that can generate must have at least one matching part, or the mod crashes world generation.** See [Floor coverage](#floor-coverage-the-most-common-crash).

## Keys

| Key | Required | Default | Meaning |
|---|---|---|---|
| `filler` | **yes** | | One palette character. The mod uses it to seat the building into the terrain. See [Filler](#filler-what-it-is-and-why-it-is-required). |
| `rubble` | no | | One palette character, used for rubble when this building is ruined. If the character is not defined in the palette, the mod uses `filler` instead. |
| `refpalette` | no | | Name of a shared palette. |
| `palette` | no | | An embedded palette, used instead of `refpalette`. |
| `minfloors` / `maxfloors` | no | `-1` | Bounds on the number of floors above ground. By default these only narrow the count the profile already chose. They do not replace it. See [Floor counts](#how-floor-and-cellar-counts-are-decided). |
| `mincellars` / `maxcellars` | no | `-1` | The same, for levels below ground. |
| `allowDoors` | no | `true` | If `true`, the mod generates doorways to adjacent city chunks on this building's floors. If `false`, the building is sealed and has no side connections. The top floor never gets doors either way. |
| `allowFillers` | no | `true` | If `true`, the mod generates the filler skirt around a building **that has cellars**. If `false`, it does not. On a building with no cellars this key changes nothing. See [Filler](#filler-what-it-is-and-why-it-is-required). |
| `overrideFloors` | no | `false` | If `false`, this building's floor bounds clamp the profile's count. If `true`, they replace it. See [Floor counts](#how-floor-and-cellar-counts-are-decided). |
| `preferslonely` | no | `0` | The chance, from 0 to 1, that this building type suppresses a building in each neighbouring chunk. `0` disables it. See [preferslonely](#preferslonely). |
| `parts` | **yes** | | The list of part references, one entry per candidate part. |
| `parts2` | no | | A second, independent list, generated as an overlay. See [parts2](#parts2). |

!!! note "Unset is `-1`, not `0`"
    The four floor and cellar bounds default to `-1`, and `-1` is the value the mod checks for "not set". So `"minfloors": 0` is **not** the same as omitting `minfloors`. `0` is a real bound that takes part in the clamping. Omitting the key lets the profile's value pass through untouched.

!!! warning "No bound is enforced on these numbers"
    `minfloors`, `maxfloors`, `mincellars` and `maxcellars` are plain integers in the codec. Nothing rejects a negative, an absurd value, or a minimum above its maximum.

    The `0` to `60` floor range and `0` to `20` cellar range you may have seen belong to the **profile**, not to a building, and even there they only drive the config screen's sliders. `Configuration.getInt` returns the stored value without clamping it, so a hand-edited profile is not validated either. See [Profile](profile.md).

!!! warning "The casing is not consistent"
    `allowDoors`, `allowFillers` and `overrideFloors` are camelCase. `filler`, `rubble`, `preferslonely`, `minfloors`, `maxfloors`, `mincellars` and `maxcellars` are lowercase, in the same file. That is how the mod names them. Copy the exact key. Do not guess from the pattern.

!!! tip "Building your first one?"
    [Your First Custom City](../getting-started/first-city.md) walks through a complete working building and palette, and links to the finished files.

## Filler: what it is, and why it is required

`filler` is one palette character. With `parts`, it is one of only two required keys. It is not part of your building's design. It is what makes the building sit correctly in the ground. The mod uses it in two places.

**1. The foundation slab.** The mod clears space before a building generates. At the building's lowest level, any column that would otherwise be open air gets the filler block. Natural terrain is uneven, so without this a building on a slope generates with holes in its lowest floor where the ground falls away.

**2. The skirt around cellars.** On a building with one or more cellars, the mod fills the outermost ring of the chunk with the filler block. The skirt runs from the building's bottom up to the ground level of whichever is lower, this chunk or the neighbour on that side. This hides the exposed outside face of the cellars, so the building reads as buried rather than as a box in a pit.

`allowFillers: false` disables step 2 only. On a building with no cellars it changes nothing.

```json
{ "filler": "#" }
```

Choose something structural that matches the building's walls, such as stone bricks or concrete. The filler is visible. It is the underside and the buried exterior.

!!! note "The character must exist in the effective palette"
    The mod resolves `filler` against the same merged palette the building's parts use. A character that is not defined there cannot resolve to a block.

## How floor and cellar counts are decided

**Your building does not decide how tall it is.** The count comes from the [Profile](profile.md), the terrain adjusts it, and your building's `minfloors` and `maxfloors` only narrow the result.

In order:

1. The profile rolls a floor count from `buildingMinFloors`, `buildingMaxFloors` and the two `...FloorsChance` values, scaled by how strong the city is at that point. See [How a Chunk Becomes a City](../under-the-hood/city-generation.md).
2. The [City Style](citystyle.md)'s `buildingsettings` clamps that count.
3. Your building's `minfloors` and `maxfloors` clamp it further.
4. The mod caps the result so the building cannot pass the world height limit.

**`overrideFloors` changes step 3 from a clamp into a replacement.**

| `overrideFloors` | Effect of the building's own `minfloors` and `maxfloors` |
|---|---|
| `false` (default) | The mod combines them with the profile and city style values, and the most restrictive wins. Your building can only make itself shorter than the profile allows, never taller. |
| `true` | The mod uses your value directly and ignores the profile and city style for that bound. |

So if a profile allows up to 8 floors and you want a building that is always exactly 2 floors, `maxfloors: 2` alone does not guarantee it. That caps the top while the minimum still floats. Set the bounds you want **and** `overrideFloors: true`.

Cellar counts work the same way, with one addition. The mod adds the chunk's city level to the profile's cellar maximum, so a building on higher terrain is allowed deeper cellars.

## Floor coverage: the most common crash

Floor numbering:

| Level | Index |
|---|---|
| Deepest cellar | `-cellars` |
| Ground floor | `0` |
| Top floor | `floors` |

!!! important "`maxfloors: 3` is a four-storey building"
    The count is the **top index**, not the number of levels. Levels run from `-cellars` up to `floors` inclusive, and `0` is the ground floor. So `floors: 3` gives indices 0, 1, 2 and 3, which is the ground floor plus three above it. Cellars work the same way. `maxcellars: 1` adds one level, at index `-1`.

    `top: true` does not add a level. It is a test that passes on whichever index is currently highest. With `floors: 3` it matches index 3, the same level `"floor": 3` matches.

    That has a consequence. If you write both a `"floor": 3` part and a `top: true` part, **both match at index 3**, and the mod picks one at random with equal probability. If you want the top part to win there, either remove the `"floor": 3` entry or narrow it to `"floor": 3, "top": false`.

    You can combine `top` with a number. The mod chains tests with AND, so `{"part": "roof", "top": true, "floor": 3}` means "the top level, but only when the building is exactly four storeys tall". That is useful for a roof that suits only one height.

The mod fills every level from `-cellars` up to and including `floors` in one pass. For each level it collects every entry in `parts` whose conditions match, then picks one at random. **If nothing matches, the mod throws:**

```
Misconfiguration! Floor were generated for a building where no part condition matches!
```

The wording, including the missing word, is the mod's own. This kills the chunk that was generating.

**The real rule is coverage, not `minfloors` and `maxfloors`.** You do not have to declare bounds. You have to guarantee that every level that can generate has a matching part. Declaring bounds is the most direct way to make that guarantee, because otherwise the profile decides the height and will eventually roll higher than the parts you wrote.

This is why writing `"floor": 0`, `"floor": 1` and `"floor": 2` and nothing else crashes. As soon as the profile rolls a four-floor building, level 3 has no match.

There are two ways to fix it.

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
    `overrideFloors: true` matters here. Without it, a city style with a higher minimum can still push this building past floor 2.

=== "Add a catch-all (robust)"

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
    The last entry has no conditions, so it matches every level. The building can now be any height without crashing, and specific levels still get their own parts.

Use the catch-all as your default, especially if your building may be used under a profile you did not write.

The same rule applies below ground. If cellars generate and no part matches a negative index, you get the same crash.

!!! tip "`parts2` never crashes"
    Only `parts` has to match. If nothing in `parts2` matches a level, that level simply gets no overlay.

## Part references

Each entry in `parts` is a part name plus any of **13** optional test keys. They are the same set a [Condition](condition.md) entry uses, so anything valid there is valid here.

| Key | Type | Matches when |
|---|---|---|
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
| `inbiome` | string or list | The current biome is in this set. |

```json
{ "part": "apartment_floor", "floor": 2 }
{ "part": "apartment_mid",   "range": "9,12" }
```

When several test keys are set on one entry, **all of them must pass**. The mod chains them with AND, never with OR. An entry with no test keys matches every level, which is what makes the catch-all pattern work.

Among all matching entries the mod picks one at random with equal probability. There is no `factor` key here, unlike a [Condition](condition.md) entry.

### `range`, for a run of identical floors

`range` is the compact way to say "floors 9 through 12 all use this part" instead of writing four separate `floor` entries.

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

| | |
|---|---|
| **Format** | A string holding two integers separated by a comma. Write `"9,12"`, not `[9,12]` and not `9,12`. |
| **Bounds** | Inclusive at both ends. `"9,12"` matches 9, 10, 11 and 12. |
| **Negatives** | Work normally. `range` tests the same index `floor` does, so `"-2,-1"` matches the two deepest cellars. |

!!! warning "A third number is accepted and silently ignored"
    The mod splits the string on commas and reads only the first two pieces. `"1,2,3"` does **not** throw. It produces the range 1 to 2 and discards the 3, with no error and no log line.

    These forms do throw `Bad range specification: <l1>,<l2>!`:

    | You write | Why it throws |
    |---|---|
    | `"9"` | There is no second number. |
    | `"9, 12"` | The space makes `" 12"` a non-number. |
    | `"abc,def"` | Neither piece is a number. |

!!! note "`range` does not require `minfloors` or `maxfloors`"
    `range` filters the level index and does nothing else. It shares the [coverage rule](#floor-coverage-the-most-common-crash) with `floor`: every level that can generate still needs something to match it.

    Declaring `minfloors` and `maxfloors` is one way to keep the generated range inside what your parts cover, and it is a reasonable habit. Remember that those bounds only clamp the profile unless you also set `overrideFloors: true`. Under a profile whose `buildingMaxFloors` is 8, `maxfloors: 13` gives you 8, not 13. A `top: true` entry is what safely caps the stack however tall it ends up.

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

Floor 2 becomes `apartment_floor_a` or `apartment_floor_b`, with equal probability.

## parts2

`parts2` is a second, independent pass over the same levels. The mod checks it separately for each level. If something matches, it generates that part on top of the one from `parts`, at the same height.

Use it for decoration or variation layered over a structural base. Put one plain floor shell in `parts`, and an optional furniture, damage or signage overlay in `parts2`. That avoids authoring every combination as its own part.

## preferslonely

`preferslonely` is a probability from 0 to 1, default 0, which disables it. It does not affect the building it is set on.

When the mod decides whether a chunk gets a building, it looks at the building type of the four orthogonally adjacent chunks, west, east, north and south. It rolls once against each neighbour's `preferslonely`. If any roll succeeds, this chunk gets no building.

So `preferslonely: 0.8` on a cathedral means chunks next to a cathedral are usually left empty, which gives the cathedral open space. `1.0` always leaves them empty. This applies only to normal single-chunk buildings. A [multi-building](multibuilding.md) ignores it.

## See also

- [Building Part Reference](part.md) for what a part contains
- [Condition Reference](condition.md) for the full test key table
- [City Style Reference](citystyle.md) for the settings that override yours
- [Profile Reference](profile.md) for where floor counts come from
