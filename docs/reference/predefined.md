# Predefined City and Sphere Reference

!!! tip "TL;DR"
    A predefined city or sphere pins that feature to an exact dimension and chunk coordinate, instead of letting generation choose. The mod ships no examples of either type, but both are fully supported.

The folder names carry no underscore:

```
data/<namespace>/lostcities/predefinedcities/<name>.json
data/<namespace>/lostcities/predefinedspheres/<name>.json
```

## Predefined City

| Key | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | The dimension ID this applies to. |
| `chunkx` / `chunkz` | **yes** | The centre chunk coordinate. |
| `radius` | **yes** | The radius, in chunks. |
| `citystyle` | **yes** | The city style to use here. |
| `buildings` | no | A list of pinned buildings. See the table below. |
| `streets` | no | A list of pinned streets, each `{chunkx, chunkz}`. |

### A pinned building

| Key | Required | Default | Meaning |
|---|---|---|---|
| `building` | **yes** | | The building name to place. |
| `chunkx` / `chunkz` | **yes** | | The chunk coordinate for this building. |
| `multi` | no | `false` | If `true`, the mod treats the name as a [Multi-Building](multibuilding.md) rather than a single building. |
| `preventruins` | no | `false` | If `true`, the ruin pass skips this building, so a landmark stays intact. |

## Predefined Sphere

| Key | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | The dimension ID. |
| `chunkx` / `chunkz` | **yes** | The chunk coordinate. |
| `centerx` / `centerz` | **yes** | The sphere centre, in blocks. |
| `radius` | **yes** | The sphere radius. |

Every key on a predefined sphere is required. There are no optional keys.

## Example

```json title="A landmark city fixed at the origin"
{
  "dimension": "lostcities:lostcity",
  "chunkx": 0,
  "chunkz": 0,
  "radius": 8,
  "citystyle": "citystyle_standard",
  "buildings": [
    { "building": "town_hall", "chunkx": 0, "chunkz": 0, "preventruins": true }
  ]
}
```

!!! note "`onlyPredefined` turns off random spheres"
    A profile's `cityspheres.onlyPredefined` makes the mod generate predefined spheres and nothing else. Use it when you want a fixed, hand-placed set rather than a random scatter. See [Profile](profile.md#cityspheres).

## See also

- [City Style Reference](citystyle.md)
- [Profile Reference](profile.md) for `spawnCity` and `spawnSphere`, which name these assets
