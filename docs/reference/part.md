---
claims: verified
---

# Building Part Reference

!!! tip "TL;DR"
    `parts/<name>.json` holds the block grid itself: one chunk footprint, one floor level, 16 by 16 by 6. This is the file a schematic converter produces. See [Editing and Tooling](../tooling/editing.md) for ways to generate one without typing it, and [Examples](../examples/index.md) for a complete working part.

## Keys

| Key | Required | Meaning | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|
| `xsize` / `zsize` | **yes** | The footprint size in blocks. Use `16` and `16`. See the warning below. |
| `slices` | **yes** | The list of layers, bottom to top. Each layer is a list of row strings. |
| `refpalette` | no | The name of a shared palette. |
| `palette` | no | An embedded palette, used instead of `refpalette`. |
| `meta` | no | A list of typed key and value pairs. **The key is `meta`, not `metadata`.** |

## The shape of `slices`

`slices` holds one entry per Y layer. Each layer holds `zsize` strings, and each string is `xsize` characters long. Every character is a [palette](palette.md) lookup. A space means air in practice, because the shipped `common` palette defines it that way. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

```json
{
  "xsize": 4,
  "zsize": 4,
  "slices": [
    [
      "αααα",
      "α  α",
      "α  α",
      "αααα"
    ]
  ]
}
```

That is one layer: a hollow 4 by 4 box made of whatever block `α` maps to. <!-- noclaim -->

!!! warning "A wrong row length produces a diagonal smear, not an error"
    The mod concatenates the rows of a layer into one flat string at load, then indexes them as `row * xsize + column`. Nothing verifies that a row is `xsize` characters long, or that a layer has `zsize` rows.

    A row one character short pulls the next row's first character into its last slot. It shifts **everything after it in that layer** by one, which looks like a generation bug rather than a typo. If the whole layer ends up shorter than `xsize * zsize`, you get a string index crash during chunk generation instead. [game test](../examples/claim-tests.md#prt-2){.v .v-g}

    The lookup is `slices[y].charAt(z * xsize + x)`, so **row breaks in the JSON are formatting only**. A layer is one 256-character sequence, and a wrong length anywhere in it moves every character after that point. [game test](../examples/claim-tests.md#prt-1){.v .v-g}

    Confirmed in game on 7.4.12, both directions: [game test](../examples/claim-tests.md#prt-1){.v .v-g}

    | Layer total | Result | [game test](../examples/claim-tests.md#prt-2){.v .v-g}
    |---|---|
    | 257 characters, one row written 17 long | No error. A marker at the extra position **was** placed, one column further on, and the character at index 256 was never read. |
    | 255 characters, one row written 15 long | The chunk fails with `String index out of range: 255`, which is the last position of a 16 by 16 layer. |

    So too long is silent and too short is loud, and neither is caught by anything at load. [game test](../examples/claim-tests.md#prt-3){.v .v-g}

    Count in **UTF-16 code units**, not characters. An emoji counts as two. See [Palette: what counts as a valid character](palette.md#what-counts-as-a-valid-character). [game test](../examples/claim-tests.md#pal-7){.v .v-g}

!!! warning "A footprint larger than 16 loads, then generates wrong"
    A part declaring `xsize: 32` loads without complaint and then generates incorrectly. A write past column 15 wraps back into the same chunk instead of continuing into the next one, so an oversized part silently overwrites its own first columns. There is no error and nothing in the log.

    To cover a larger area use a [Multi-Building](multibuilding.md), which is the supported way to span several chunks. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! note "Smaller than 16 is legal, and the mod relies on it"
    The mod iterates each part over its **own** `xsize`, `zsize` and slice count, so a part smaller than the chunk simply writes a smaller area. It is not corrupted, and it is not unsupported.

    The mod's own [building fronts](citystyle.md#front-parts-are-deliberately-not-16-by-16) are 2 by 16 and 3 by 16 strips, placed along one edge of a street chunk and rotated for each of the four sides. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    The rule that matters is: **never exceed 16**, and match the footprint to the job. A part used where a full chunk is expected, such as a building floor or a street, should be 16 by 16, or it will cover only part of the chunk and leave the rest as it was. [game test](../examples/claim-tests.md#prt-2){.v .v-g}

## Slices, floors and height

Each floor of a building occupies **6 blocks** of vertical space, and the mod stacks parts at 6-block intervals. A part with more than 6 slices has its upper slices overwritten by the floor above. A part with fewer leaves a gap. Match your slice count to 6. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## `meta`

Each entry is a `key` plus exactly one typed value: `boolean`, `char`, `string`, `integer` or `float`. The mod accepts an unknown key and ignores it, but **five keys are real and read during generation**. Two of them are mandatory for certain kinds of part, so `meta` is not optional decoration. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Type | Applies to | Effect | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|---|---|
| `support` | char | Highway and bridge parts | The palette character used for the support pillars underneath. |
| `z1` / `z2` | integer | Stair parts | The Z range along the part's edge that the staircase occupies. |
| `dontconnect` | boolean | Building floor parts | If `true`, the mod generates no doorways between this part and the neighbouring chunk. |
| `nowater` | boolean | Any part | If `true`, hard air stays dry below sea level instead of flooding. |

### `support`

```json title="highway_bridge.json, as shipped"
{ "meta": [ { "key": "support", "char": "v" } ] }
```

Where a highway or bridge crosses open space, the mod drops pillars of this character downward. It stops at the first non-empty block, or after 40 blocks, whichever comes first. The profile's `highwaySupports` and `bridgeSupports` suppress the pillars entirely. All 8 shipped highway and bridge parts use `v`. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! danger "An undefined `support` character fails the chunk"
    The mod throws `Cannot find support block '<char>' for highway part '<name>'!` when `support` names a character no palette in scope defines. Define the character, or remove the `support` meta. Omitting `support` is safe, and gives you a highway with nothing holding it up.

### `z1` and `z2`

```json title="stairsnormal.json, as shipped"
{ "meta": [ { "key": "z1", "integer": 5 }, { "key": "z2", "integer": 10 } ] }
```

These mark where the staircase meets the chunk edge, so the street border in the **adjacent** chunk leaves a gap there instead of walling the stairs off. Both are Z coordinates from 0 to 15. The 4 shipped stair parts use 0 and 2, 13 and 15, 4 and 11, and 5 and 10. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! danger "A stair part without `z1` and `z2` fails the chunk"
    The mod throws `NullPointerException` when the neighbouring chunk works out its border. It reads both values into `Integer` and passes them straight into an `int` parameter, with no null check, so an absent key unboxes a null.

    Any part you put in a city style's `stairs` selector **must** define both keys. [game test](../examples/claim-tests.md#cty-8){.v .v-g}

### `dontconnect`

```json
{ "meta": [ { "key": "dontconnect", "boolean": true } ] }
```

Set this on a floor part to suppress doorways between it and the neighbouring chunks, in both directions. All 14 shipped `shopping*` parts use it. They are interior mall sections, and they should connect only through their own openings rather than have generic doorways punched through them. [game test](../examples/claim-tests.md#bld-6){.v .v-g}

### `nowater`

```json
{ "meta": [ { "key": "nowater", "boolean": true } ] }
```

Hard air below the water level normally fills with water. `nowater` keeps it dry. All 3 shipped `monorails_*` parts use it, so a monorail crossing an ocean stays an open tube. [code review](../examples/claim-tests.md#pipe-3){.v .v-c}

This is the per-part equivalent of the profile's `avoidFoliage`, without the cost to trees and flowers. See [Profile](profile.md). [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### Any other key

Any other key parses, is stored, and nothing in 7.4.12 reads it. A companion mod can read it, so it is a reasonable place to keep your own data. Do not expect the mod to act on it. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! note "Two of the five value types are never read either"
    The codec accepts `boolean`, `char`, `string`, `integer` and `float`, but the mod only ever reads three of them. The five real keys use `char` (`support`), `integer` (`z1`, `z2`) and `boolean` (`dontconnect`, `nowater`).

    Nothing in the mod calls the `string` or `float` accessors at all. Those two types exist for a reader that does not currently exist, so a `string` or `float` meta value is storage and nothing more. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Rotation

The mod does not always place a part the way you authored it. A building reuses one part on several sides of the same structure, and streets, highways and rails reuse a small set of shapes in whatever orientation an intersection needs. So the same part JSON is commonly placed rotated or mirrored. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

Most blocks do not reorient when that happens. Only stairs and rails do by default. See [Palette: rotation and the `lostcities:rotatable` tag](palette.md#rotation-and-the-lostcitiesrotatable-tag) if your part uses doors, furnaces, or any other block whose facing matters. [game test](../examples/claim-tests.md#prt-4){.v .v-g}

## See also

- [Building Reference](building.md) for how the mod selects parts
- [Palette Reference](palette.md) for what the characters resolve to, and for the rotation tag
- [Editing and Tooling](../tooling/editing.md) for ways to produce these files without typing them
- [Error Messages](../troubleshooting/errors.md) if a part is crashing generation <!-- noclaim -->
