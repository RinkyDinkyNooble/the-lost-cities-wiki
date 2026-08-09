# Building Reference

!!! tip "TL;DR"
    `buildings/<name>.json`. A vertical stack: cellars, ground floor, floors, top. Each slot picks from a list of candidate parts, optionally filtered by [conditions](condition.md). **Every floor level that can generate must have at least one matching part, or chunk generation crashes.** See [Floor coverage](#floor-coverage-the-most-common-crash).

## Fields

| Key | Required | Default | Meaning |
|---|---|---|---|
| `filler` | **yes** | | Single palette character used to seat the building into the terrain. See [Filler](#filler-what-it-is-and-why-its-required). |
| `rubble` | no | | Single palette character used for rubble when this building is ruined. If the character isn't defined in the palette, `filler` is used instead. |
| `refpalette` | no | | Shared palette name. |
| `palette` | no | | Embedded palette, instead of `refpalette`. |
| `minfloors` / `maxfloors` | no | unset | Bounds on floors above ground, `0`–`60`. **By default these only narrow the range the profile already computed, they don't replace it.** See [Floor counts](#how-floor-and-cellar-counts-are-decided). |
| `mincellars` / `maxcellars` | no | unset | Same, for levels below ground, `0`–`20`. |
| `allowDoors` | no | `true` | Whether doorways to adjacent city chunks are generated on this building's floors. `false` produces a sealed building with no side connections. Doors are never generated on the top floor regardless. |
| `allowFillers` | no | `true` | Whether the outer filler skirt is generated around a building **that has cellars**. See [Filler](#filler-what-it-is-and-why-its-required). No effect on a building with zero cellars. |
| `overrideFloors` | no | `false` | Changes how this building's own floor/cellar bounds are applied: `false` clamps, `true` replaces outright. See [Floor counts](#how-floor-and-cellar-counts-are-decided). |
| `preferslonely` | no | `0` | Chance (0–1) that this building suppresses buildings in each **neighbouring** chunk. See [preferslonely](#preferslonely). |
| `parts` | **yes** | | List of part references, one entry per candidate part. |
| `parts2` | no | | A second, independent list. Optional overlay, see [parts2](#parts2). |

!!! note "Unset is `-1`, not `0`"
    Internally the four floor/cellar bounds default to `-1`, and `-1` is what the code checks for "not set." So `"minfloors": 0` is **not** the same as leaving `minfloors` out: `0` is a real bound that participates in the clamping, omitting it means the profile's value passes through untouched. Same for the other three.

!!! warning "Casing isn't consistent here"
    `allowDoors`, `allowFillers`, `overrideFloors` are camelCase. `filler`, `rubble`, `preferslonely`, `minfloors`, `maxfloors`, `mincellars`, `maxcellars` are all lowercase, in the same file. That's genuinely how the mod names them. Copy the exact key, don't guess by pattern.

!!! tip "Building your first one?"
    [Your First Custom City](../getting-started/first-city.md) walks through a complete working building, palette and all, and links to the finished files.

## Filler: what it is, and why it's required

`filler` is one palette character, and it's the only required field besides `parts`. It isn't part of your building's design, it's what makes the building sit in the ground correctly. It gets used in two distinct places:

**1. The foundation slab.** Before a building generates, the mod clears space for it. At the building's very bottom level, any column that would otherwise be open air gets the filler block. Natural terrain is uneven, so without this a building on a slope would generate with holes in its lowest floor where the ground fell away.

**2. The skirt around cellars.** For a building with **one or more cellars**, the outermost ring of the chunk is filled with the filler block, from the building's bottom up to the ground level of whichever is lower, this chunk or the neighbour on that side. This hides the exposed outside face of your cellars, so the building reads as buried rather than as a box sitting in a pit.

Step 2 is the only thing `allowFillers: false` disables. On a building with no cellars it changes nothing at all.

```json
{ "filler": "#" }
```

Pick something structural that matches the building's walls, stone bricks, concrete, whatever the building is made of. It's visible: it's the underside and the buried exterior.

!!! note "The character must exist in the effective palette"
    Filler is resolved against the same merged palette the building's parts use. A character that isn't defined there can't resolve to a block.

## How floor and cellar counts are decided

This is the part that surprises people: **your building does not decide how tall it is.** The count comes from the [Profile](profile.md), gets adjusted by terrain, and your building's `minfloors`/`maxfloors` only *narrow* the result.

Roughly, in order:

1. The profile rolls a floor count from `buildingMinFloors`, `buildingMaxFloors`, and the two `...FloorsChance` values, scaled by how strong the city is at that spot (see [How a Chunk Becomes a City](../under-the-hood/city-generation.md)).
2. The [City Style](citystyle.md)'s `buildingsettings` clamps that.
3. Your building's `minfloors`/`maxfloors` clamp it further.
4. It's capped so the building can't punch through the world height limit.

**`overrideFloors` changes step 3 from a clamp into a replacement.**

| `overrideFloors` | Effect of the building's own `minfloors`/`maxfloors` |
|---|---|
| `false` (default) | Combined with the profile and city style values, whichever is more restrictive wins. Your building can only make itself *shorter* than the profile allows, never taller. |
| `true` | Your value is used directly and the profile and city style are ignored for that bound. |

So if a profile allows up to 8 floors and you want a building that is **always exactly 2 floors**, `maxfloors: 2` alone is not enough to guarantee it (it caps the top but the minimum still floats). Set the bounds you want *and* `overrideFloors: true`.

Cellar counts work the same way, with one extra wrinkle: the profile's cellar maximum has the chunk's city level added to it, so buildings on higher terrain are allowed deeper basements.

## Floor coverage: the most common crash

Floor numbering:

| Level | Index |
|---|---|
| Deepest cellar | `-cellars` |
| Ground floor | `0` |
| Top floor | `floors` |

Every level from `-cellars` up to and including `floors` is filled in one pass. For each one, the mod collects every entry in `parts` whose conditions match that level and picks one at random. **If nothing matches, generation throws:**

```
Misconfiguration! Floor were generated for a building where no part condition matches!
```

(the wording is the mod's own). This kills the chunk that was generating.

**The real rule is coverage, not min/max.** You don't strictly have to declare `minfloors`/`maxfloors`. What you have to guarantee is that *every level that can actually be generated* has a matching part. Declaring bounds is simply the most direct way to make that guarantee, because otherwise the profile decides the height and it will eventually roll higher than the parts you wrote.

This is why writing `"floor": 0`, `"floor": 1`, `"floor": 2` on three parts and nothing else crashes: as soon as the profile rolls a 4-floor building, level 3 has no match.

Two ways to fix it:

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
    `overrideFloors: true` matters here. Without it, a city style with a higher minimum could still push this past floor 2.

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
    The last entry has no conditions, so it matches every level. The building can now be any height without crashing, and specific levels still get their special parts.

The catch-all approach is the safer default, especially if your building might be used under a profile you didn't write.

The same applies below ground: if cellars generate and no part matches a negative index, it's the same crash. Your hypothesis there is correct, and it's the same underlying mechanism.

!!! tip "`parts2` never crashes"
    Only `parts` is required to match. If nothing in `parts2` matches a level, that level simply gets no overlay.

## Part references

Each entry in `parts` is a part name plus the full [condition test field set](condition.md#the-shared-test-fields):

```json
{ "part": "apartment_floor", "floor": 2 }
```

When several test fields are set on one entry, **all of them must pass** (they're AND-ed, not OR-ed). An entry with no test fields matches every level, which is what makes the catch-all pattern above work.

Among all matching entries, one is picked at random with **equal probability**. There's no `factor` field here, unlike [Condition](condition.md) assets, which are weighted.

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

Floor 2 randomly becomes `apartment_floor_a` or `apartment_floor_b`, 50/50.

## parts2

A second, independent pass over the same levels. Each level checks `parts2` separately and, if something matches, that part is generated **on top of** the one from `parts`, at the same height.

The practical use is decoration or variation layered over a structural base: one plain floor shell in `parts`, and an optional furniture/damage/signage overlay in `parts2`, without having to author every combination as its own part.

## preferslonely

A probability from 0 to 1, default 0 (off). It doesn't affect the building it's set on. Instead, when the mod decides whether a **neighbouring** chunk gets a building, it rolls against the `preferslonely` of each of the four orthogonally adjacent chunks' building types. If any of those rolls hits, that neighbour gets no building.

So `preferslonely: 0.8` on a cathedral means chunks next to a cathedral are usually left empty, giving it open space. `1.0` means always empty. It applies only to normal single-chunk buildings, [multi-buildings](multibuilding.md) ignore it.

## See also

- [Building Part Reference](part.md) for what a part actually contains
- [Condition Reference](condition.md) for the full test field table
- [City Style Reference](citystyle.md) for the settings that override yours
- [Profile Reference](profile.md) for where floor counts really come from
