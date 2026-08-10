# Multi-Building Reference

!!! tip "TL;DR"
    `multibuildings/<name>.json`. A grid of building names. Occupies multiple city chunks at once instead of one.

## Fields

| Key | Required | Limits | Meaning |
|---|---|---|---|
| `dimx` / `dimz` | **yes** | ≥ 1, and **≤ the `areasize` it is placed with** | Grid size, in chunks. |
| `buildings` | **yes** | | 2D list of building names, `dimx` rows of `dimz` entries each. |

!!! danger "A multi-building larger than its placement area crashes generation"
    Placement picks a random offset inside a square area of chunks, using `random(areasize - dimx + 1)`. If `dimx` or `dimz` exceeds `areasize`, that bound goes to zero or negative and generation throws.

    Two different `areasize` values apply, depending on how the multi-building is reached:

    | Reached via | Setting | Shipped default |
    |---|---|---|
    | A city style's `multibuildings` selector | [World Style](worldstyle.md) `multisettings.areasize` | `10` |
    | A [Scattered Building](scattered.md)'s `multibuilding` | [World Style](worldstyle.md) `scattered.areasize` | `8` |

    A multi-building used both ways has to fit the smaller of the two. Nothing checks this at load, only at the moment a chunk in that area generates.

## Example

```json
{
  "dimx": 2,
  "dimz": 2,
  "buildings": [
    ["mall_nw", "mall_ne"],
    ["mall_sw", "mall_se"]
  ]
}
```

A 2×2 chunk footprint, four separate building definitions tiled together into one structure. Each entry is a normal [Building](building.md) name, referenced the usual [namespaced](../getting-started/namespaces.md) way.

## See also

[Building Reference](building.md)
