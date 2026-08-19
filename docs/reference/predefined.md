---
claims: verified
---

# Predefined City and Sphere Reference

!!! tip "TL;DR"
    A predefined city or sphere pins that feature to an exact dimension and chunk coordinate instead of letting generation choose. The mod ships no examples of either type, and both work. [game test](../examples/claim-tests.md#pre-2){.v .v-g}

!!! note "The sphere keys are absent in 6.0.3"
    `centerx`, `centerz`, `chunkx`, `chunkz`, `dimension` and `radius` exist in 5.3.29 and again from 6.1.6 onward, but not in 6.0.3. See [Key availability](../versions/key-availability.md). [code review](../examples/claim-tests.md#ref-1){.v .v-c}

The folder names carry no underscore: <!-- noclaim -->

```
data/<namespace>/lostcities/predefinedcities/<name>.json
data/<namespace>/lostcities/predefinedspheres/<name>.json
```

## Predefined City

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | The dimension ID this applies to |
| `chunkx` / `chunkz` | **yes** | The centre chunk coordinate |
| `radius` | **yes** | The radius, in chunks |
| `citystyle` | **yes** | The city style to use here |
| `buildings` | no | A list of pinned buildings. See the table below |
| `streets` | no | A list of pinned streets, each `{chunkx, chunkz}` |

### A pinned building

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Default | Meaning |
|---|---|---|---|
| `building` | **yes** | | The building name to place |
| `chunkx` / `chunkz` | **yes** | | An offset **from the city centre**, in chunks, not a world chunk coordinate. `0, 0` is the centre chunk itself and `2, -1` is two chunks east and one north of it [game test](../examples/claim-tests.md#pre-1){.v .v-g} |
| `multi` | no | `false` | `true` treats the name as a [Multi-Building](multibuilding.md) rather than a single building |
| `preventruins` | no | `false` | `true` makes the ruin pass skip this building, so a landmark stays intact [game test](../examples/claim-tests.md#pre-3){.v .v-g} |

!!! warning "Both coordinate pairs are named `chunkx` and `chunkz` and they do not mean the same thing"
    On the city itself they are absolute world chunk coordinates. On a pinned building or street they are **relative to that city**. The mod adds the two together, so a city at `chunkx: 8` holding a building at `chunkx: 2` places that building at world chunk 10, which is block 160. [game test](../examples/claim-tests.md#pre-1){.v .v-g}

    Writing a world coordinate on a pinned building therefore lands it that many chunks past where you meant, and a result outside `radius` never appears. Nothing is logged either way. [game test](../examples/claim-tests.md#pre-1){.v .v-g}

### A pinned street

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Meaning |
|---|---|---|
| `chunkx` / `chunkz` | **yes** | An offset from the city centre, exactly as above. That chunk becomes a street instead of rolling `buildingchance` |

## What a predefined city overrides

Pinning a city is not a hint. The chunk you name becomes a city centre outright. [game test](../examples/claim-tests.md#pre-2){.v .v-g}

| Normally decided by | Inside a predefined city |
|---|---|
| `cityChance` | Ignored. The centre chunk is a city centre even at `cityChance: 0.0`, which is the cleanest way to get exactly one city in a world [game test](../examples/claim-tests.md#pre-2){.v .v-g} |
| The city radius roll | Fixed to `radius` [code review](../examples/claim-tests.md#ref-2){.v .v-c} |
| The [World Style](worldstyle.md)'s weighted city style pick | Fixed to `citystyle` [code review](../examples/claim-tests.md#ref-2){.v .v-c} |
| `buildingchance`, per chunk | Ignored on any chunk holding a pinned building or a pinned street [game test](../examples/claim-tests.md#pre-1){.v .v-g} |

!!! danger "At `cityChance: 0.0`, an unpinned chunk inside the radius is not a city chunk"
    The radius bounds the city, and on its own it does not make the chunks inside it part of one. With `cityChance` at `0.0` and nothing else pinned, the chunk beside a pinned building reported `is city: false` and generated as open ground, so the building had no street next to it and no [front](citystyle.md#what-a-building-front-is) was ever drawn. [game test](../examples/claim-tests.md#frt-2){.v .v-g}

    Pin the streets you want, as the `streets` list above does, and those chunks become city. This is worth ruling out first when a feature that needs a street neighbour appears to do nothing. [game test](../examples/claim-tests.md#frt-2){.v .v-g}

## Predefined Sphere

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Meaning |
|---|---|---|
| `dimension` | **yes** | The dimension ID |
| `chunkx` / `chunkz` | **yes** | The chunk coordinate |
| `centerx` / `centerz` | **yes** | The sphere centre, in blocks |
| `radius` | **yes** | The sphere radius |

Every key on a predefined sphere is required, and there are no optional ones. The sphere half of this page has never been generated, unlike the city half. [code review](../examples/claim-tests.md#ref-1){.v .v-c} [unverified](../examples/claim-tests.md#ref-3){.v .v-u}

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

The city covers world chunks 0 to 16 on both axes. `town_hall` lands on chunk 8, 8, that is block 128, 128. `office` lands on chunk 10, 8, that is block 160, 128. The street sits between them on chunk 9, 8. [game test](../examples/claim-tests.md#pre-1){.v .v-g}

!!! danger "Pin to the dimension the profile is actually driving"
    Choosing a profile with the **Cities** button makes the **overworld** the Lost Cities world, while `dimensionsWithProfiles` wires `lostcities:lostcity`. A city pinned to the wrong one of those appears not to generate at all, with nothing logged. The shipped example packs pin to both. [game test](../examples/claim-tests.md#cfg-5){.v .v-g}

!!! note "`onlyPredefined` turns off random spheres"
    A profile's `cityspheres.onlyPredefined` makes the mod generate predefined spheres and nothing else, for a fixed hand-placed set rather than a random scatter. See [Profile](profile.md#cityspheres). [code review](../examples/claim-tests.md#ref-1){.v .v-c}

## See also

- [City Style Reference](citystyle.md)
- [Configuration](config.md) for wiring a profile to a dimension
- [Profile Reference](profile.md) for `spawnCity` and `spawnSphere`, which name these assets <!-- noclaim -->
