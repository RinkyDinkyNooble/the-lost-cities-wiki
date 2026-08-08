# Predefined City & Sphere Reference

!!! tip "TL;DR"
    Pin an entire city (or city sphere) to an exact dimension and chunk coordinate, instead of letting generation choose. Neither type ships any examples with the mod, both are fully supported.

## Predefined City

| Key | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | Dimension ID this applies to. |
| `chunkx` / `chunkz` | **yes** | Center chunk coordinate. |
| `radius` | **yes** | Radius in chunks. |
| `citystyle` | **yes** | City style to use here. |
| `buildings` | no | List of pinned buildings, each `{building, chunkx, chunkz, multi?, preventruins?}` at a relative offset. |
| `streets` | no | List of pinned streets, each `{chunkx, chunkz}`. |

## Predefined Sphere

| Key | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | Dimension ID. |
| `chunkx` / `chunkz` | **yes** | Chunk coordinate. |
| `centerx` / `centerz` | **yes** | Sphere center, in blocks. |
| `radius` | **yes** | Sphere radius. |

## Example

```json title="A landmark city fixed at spawn"
{
  "dimension": "lostcities:lostcity",
  "chunkx": 0,
  "chunkz": 0,
  "radius": 8,
  "citystyle": "citystyle_standard",
  "buildings": [
    { "building": "town_hall", "chunkx": 0, "chunkz": 0 }
  ]
}
```

## See also

[City Style Reference](citystyle.md)
