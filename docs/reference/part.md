# Building Part Reference

!!! tip "TL;DR"
    `parts/<name>.json`. The actual 16×16×6 block grid, one chunk footprint and one floor level. This is the file a schematic converter produces. See [Editing & Tooling](../tooling/editing.md) for ways to generate one without typing it by hand, and [Examples](../examples/index.md) for a complete working part.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `xsize` / `zsize` | **yes** | Footprint size in blocks. Should be `16`/`16`, see the warning below. |
| `slices` | **yes** | List of layers (bottom to top), each a list of row strings. |
| `refpalette` | no | Shared palette name. |
| `palette` | no | Embedded palette instead. |
| `meta` | no | List of typed key/value pairs. **Key is `meta`, not `metadata`.** |

## `slices` shape

One entry per Y layer. Each layer is `zsize` strings, each string `xsize` characters long. Every character is a [palette](palette.md) lookup, and space (`" "`) means air in practice because the shipped `common` palette defines it that way.

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

One layer, a 4×4 hollow box made of whatever block character `α` maps to in the palette.

!!! warning "Row lengths are never checked"
    The rows of a layer are **concatenated into one flat string** at load, then indexed as `row * xsize + column`. Nothing verifies that a row is `xsize` long or that a layer has `zsize` rows.

    A row that is one character short does not error, it pulls the next row's first character into its last slot and shifts **everything after it in that layer** by one. The result is a diagonal smear that looks like a generation bug rather than a typo. If the layer ends up shorter than `xsize × zsize` in total, you get a string index crash during chunk generation instead.

    Count in **UTF-16 code units**, not characters. An emoji counts as two, which is the same off-by-one from a source your editor will not show you. See [Palette: what counts as a valid character](palette.md#what-counts-as-a-valid-character).

!!! warning "Sizes other than 16×16 are accepted but not safe"
    A part declaring e.g. `xsize: 32` loads without complaint, then generates wrong. Rotation math assumes a 16-wide footprint, and writes past column 15 wrap back into the same chunk rather than continuing into the next one, so an oversized part silently overwrites its own first columns. There is no error and nothing in the log.

    Parts are meant to fill exactly one chunk footprint. To cover a larger area, use a [Multi-Building](multibuilding.md), which is the supported way to span several chunks. Smaller-than-16 parts have the same rotation problem and are equally unsupported.

## Slices, floors, and height

Each floor of a building occupies **6 blocks** of vertical space, and parts are stacked at 6-block intervals. A part with more than 6 slices will have its upper slices overwritten by the floor above; one with fewer leaves a gap. Match your slice count to 6 unless you know exactly what you are doing.

## `meta`

Each entry is a `key` plus exactly one typed value: `boolean`, `char`, `string`, `integer`, or `float`. Unknown keys are accepted and ignored, but **five keys are real and read by the generator.** Two of them are mandatory for certain kinds of part, so this is not optional decoration.

| Key | Type | Applies to | Effect |
|---|---|---|---|
| `support` | char | Highway and bridge parts | Palette character for the support pillars underneath. |
| `z1` / `z2` | integer | Stair parts | The Z range along the part's edge that the staircase occupies. |
| `dontconnect` | boolean | Building floor parts | `true` blocks doorways to the neighbouring chunk. |
| `nowater` | boolean | Any part | `true` keeps "hard air" dry below sea level instead of flooding. |

### `support`

```json title="highway_bridge.json, as shipped"
{ "meta": [ { "key": "support", "char": "v" } ] }
```

Where the highway or bridge crosses open space, the generator drops pillars of this character downward until it hits something solid (up to 40 blocks). Suppressed by the profile's `highwaySupports` / `bridgeSupports`. All eight shipped highway and bridge parts use `v`.

!!! danger "An undefined `support` character crashes chunk generation"
    `Cannot find support block 'v' for highway part '<name>'!` Omitting `support` entirely is safe, you just get a highway with nothing holding it up.

### `z1` / `z2`

```json title="stairsnormal.json, as shipped"
{ "meta": [ { "key": "z1", "integer": 5 }, { "key": "z2", "integer": 10 } ] }
```

Marks where the staircase meets the chunk edge, so the street border in the **adjacent** chunk leaves a gap there instead of walling the stairs off. Both are Z coordinates in the 0–15 range. The four shipped stair parts use `0/2`, `13/15`, `4/11`, and `5/10`.

!!! danger "A stair part without `z1` and `z2` crashes chunk generation"
    The neighbouring chunk reads both values with no null check while deciding its border. Any part you put in a city style's `stairs` selector **must** define both.

### `dontconnect`

```json
{ "meta": [ { "key": "dontconnect", "boolean": true } ] }
```

Set on a floor part to suppress doorways between it and neighbouring chunks, in both directions. All 14 shipped `shopping*` parts use it: they are interior mall sections that should connect only through their own openings, not have generic doorways punched through.

### `nowater`

```json
{ "meta": [ { "key": "nowater", "boolean": true } ] }
```

"Hard air" below the water level normally fills with water. `nowater` keeps it dry. All three shipped `monorails_*` parts use it, so a monorail crossing an ocean stays an open tube.

### Any other key

Parses, is stored, and nothing in 7.4.12 reads it. Companion mods can read it through the API, so it is a reasonable place to hang your own data. Just do not expect Lost Cities to act on it.

## Rotation

A part is not always placed the way it is authored. Buildings reuse one part on multiple sides of the same structure, and streets/highways/rails reuse a small set of shapes in whatever orientation an intersection needs, so the same part JSON commonly gets placed rotated or mirrored. Most blocks do not reorient when that happens, only stairs and rails do by default. See [Palette Reference: Rotation and the `lostcities:rotatable` tag](palette.md#rotation-and-the-lostcitiesrotatable-tag) if a part uses doors, furnaces, or any other block whose facing matters.

## See also

- [Building Reference](building.md) for how parts get selected
- [Palette Reference](palette.md) for what the characters resolve to, and for the rotation tag
- [Editing & Tooling](../tooling/editing.md) for ways to produce these files without hand-typing them
- [Error Messages](../troubleshooting/errors.md) if a part is crashing generation
