# Multi-Building Reference

!!! tip "TL;DR"
    `multibuildings/<name>.json`. A grid of building names. Occupies multiple city chunks at once instead of one.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `dimx` / `dimz` | **yes** | Grid size, in chunks. |
| `buildings` | **yes** | 2D list of building names, `dimx` rows of `dimz` entries each. |

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
