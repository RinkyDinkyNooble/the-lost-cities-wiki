# Building Part Reference

!!! tip "TL;DR"
    `parts/<name>.json`. The actual 16×16×N block grid. This is what [main.py](https://github.com/RinkyDinkyNooble/abza3) in this wiki's companion tooling generates from a schematic.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `xsize` / `zsize` | **yes** | Footprint size in blocks. Should be `16`/`16`, see the warning below. |
| `slices` | **yes** | List of layers (bottom to top), each a list of row strings. |
| `refpalette` | no | Shared palette name. |
| `palette` | no | Embedded palette instead. |
| `meta` | no | List of typed key/value pairs. **Key is `meta`, not `metadata`.** |

## `slices` shape

One entry per Y layer. Each layer is `zsize` strings, each string `xsize` characters long. Every character is a palette lookup, space (`" "`) always means air.

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

!!! warning "Sizes other than 16×16 are accepted but not safe"
    A part declaring e.g. `xsize: 32` loads without complaint, then generates wrong. Rotation math assumes a 16-wide footprint, and writes past column 15 wrap back into the same chunk rather than continuing into the next one, so an oversized part silently overwrites its own first columns. There's no error and nothing in the log.

    Parts are meant to fill exactly one chunk footprint. To cover a larger area, use a [Multi-Building](multibuilding.md), which is the supported way to span several chunks. Smaller-than-16 parts have the same rotation problem and are equally unsupported.

## Slices, floors, and height

Each floor of a building occupies **6 blocks** of vertical space, and parts are stacked at 6-block intervals. A part with more than 6 slices will have its upper slices overwritten by the floor above; one with fewer leaves a gap. Match your slice count to 6 unless you know exactly what you're doing.

## `meta`

```json
{
  "meta": [
    { "key": "loot_tier", "string": "rare" }
  ]
}
```

Each entry is a `key` plus exactly one typed value: `boolean`, `char`, `string`, `integer`, or `float`. What actually reads these values is still unconfirmed, a full read of the generation code and its supporting packages turned up no consumer of `meta` anywhere. The field itself is real, parses fine, and is safe to set, it just doesn't appear to do anything in 7.4.12 as far as this wiki has traced. Worth retesting against a future mod version before assuming that's permanent.

## Rotation

A part isn't always placed the way it's authored. Buildings reuse one part on multiple sides of the same structure, and streets/highways/rails reuse a small set of shapes in whatever orientation an intersection needs, so the same part JSON commonly gets placed rotated or mirrored. Most blocks don't reorient when that happens, only stairs and rails do by default. See [Palette Reference: Rotation and the `lostcities:rotatable` tag](palette.md#rotation-and-the-lostcitiesrotatable-tag) if a part uses doors, furnaces, or any other block whose facing matters.

## See also

- [Building Reference](building.md) for how parts get selected
- [Palette Reference](palette.md) for what the characters resolve to, and for the rotation tag
