# Building Part Reference

!!! tip "TL;DR"
    `parts/<name>.json`. The actual 16×16×N block grid. This is what [main.py](https://github.com/RinkyDinkyNooble/abza3) in this wiki's companion tooling generates from a schematic.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `xsize` / `zsize` | **yes** | Footprint size in blocks. Almost always `16`/`16`. |
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
