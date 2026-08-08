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

Each entry is a `key` plus exactly one typed value: `boolean`, `char`, `string`, `integer`, or `float`. What actually reads these values isn't confirmed yet, it's flagged for the deeper "how generation behaves" pass, but the field itself is real and safe to set.

## See also

- [Building Reference](building.md) for how parts get selected
- [Palette Reference](palette.md) for what the characters resolve to
