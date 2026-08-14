# Predefined City and Sphere Reference

!!! tip "TL;DR"
    A predefined city or sphere pins that feature to an exact dimension and chunk coordinate, instead of letting generation choose. The mod ships no examples of either type, but both are fully supported.

!!! note "The sphere keys are absent in 6.0.3"
    `centerx`, `centerz`, `chunkx`, `chunkz`, `dimension` and `radius` exist in
    5.3.29 and again from 6.1.6 onward, but not in 6.0.3. See
    [Key availability](../versions/key-availability.md).

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
| `chunkx` / `chunkz` | **yes** | | An offset **from the city centre**, in chunks, not a world chunk coordinate. `0, 0` is the centre chunk itself, and `2, -1` is two chunks east and one north of it. |
| `multi` | no | `false` | If `true`, the mod treats the name as a [Multi-Building](multibuilding.md) rather than a single building. |
| `preventruins` | no | `false` | If `true`, the ruin pass skips this building, so a landmark stays intact. |

!!! warning "Both coordinate pairs are named `chunkx` and `chunkz` and they do not mean the same thing"
    On the city itself they are absolute world chunk coordinates. On a pinned
    building or street they are **relative to that city**. The mod adds the two
    together, so a city at `chunkx: 8` holding a building at `chunkx: 2` places
    that building at world chunk 10, which is block 160.

    Writing a world coordinate on a pinned building therefore lands it that many
    chunks past where you meant, and if the result falls outside `radius` it
    simply never appears. Nothing is logged either way.

### A pinned street

| Key | Required | Meaning |
|---|---|---|
| `chunkx` / `chunkz` | **yes** | An offset from the city centre, exactly as above. That chunk becomes a street instead of rolling `buildingchance`. |

## What a predefined city overrides

Pinning a city is not a hint. The chunk you name becomes a city centre outright:

| Normally decided by | Inside a predefined city |
|---|---|
| `cityChance` | Ignored. The centre chunk is a city centre even at `cityChance: 0.0`, which is the cleanest way to get exactly one city in a world. |
| The city radius roll | Fixed to `radius`. |
| The [World Style](worldstyle.md)'s weighted city style pick | Fixed to `citystyle`. |
| `buildingchance`, per chunk | Ignored on any chunk holding a pinned building or a pinned street. |

## Predefined Sphere

| Key | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | The dimension ID. |
| `chunkx` / `chunkz` | **yes** | The chunk coordinate. |
| `centerx` / `centerz` | **yes** | The sphere centre, in blocks. |
| `radius` | **yes** | The sphere radius. |

Every key on a predefined sphere is required. There are no optional keys.

## Example

```json title="A landmark city centred on world chunk 8, 8"
{
  "dimension": "lostcities:lostcity",
  "chunkx": 8,
  "chunkz": 8,
  "radius": 8,
  "citystyle": "citystyle_standard",
  "buildings": [
    { "building": "town_hall", "chunkx": 0, "chunkz": 0, "preventruins": true },
    { "building": "office", "chunkx": 2, "chunkz": 0 }
  ],
  "streets": [
    { "chunkx": 1, "chunkz": 0 }
  ]
}
```

The city covers world chunks 0 to 16 on both axes. `town_hall` lands on chunk
8, 8, that is block 128, 128. `office` lands on chunk 10, 8, that is block 160,
128. The street sits between them on chunk 9, 8.

!!! note "`onlyPredefined` turns off random spheres"
    A profile's `cityspheres.onlyPredefined` makes the mod generate predefined spheres and nothing else. Use it when you want a fixed, hand-placed set rather than a random scatter. See [Profile](profile.md#cityspheres).

## See also

- [City Style Reference](citystyle.md)
- [Profile Reference](profile.md) for `spawnCity` and `spawnSphere`, which name these assets
