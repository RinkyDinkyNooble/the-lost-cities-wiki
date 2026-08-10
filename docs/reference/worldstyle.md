# World Style Reference

!!! tip "TL;DR"
    `worldstyles/<name>.json`. Picks which City Styles can appear and how often. A profile points at exactly one of these by name.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `outsidestyle` | **yes** | Name of a [Style](style.md) used for terrain outside cities. |
| `citystyles` | **yes** | List of `{factor, citystyle, biomes?}`. Weighted, optionally biome-limited picks of which [City Style](citystyle.md) to use. |
| `multisettings` | no | Multibuilding placement tuning. See [below](#multisettings). |
| `settings` | no | `railwayavoidance` (`ignore`/`block_railway`), `railpartheight6`, and `vinewest`/`vineeast`/`vinesouth`/`vinenorth` blockstates for ruin decoration. |
| `cityspheres` | no | `centerpart`, `centertype`, `centerpartorigin`, `centerpartoffset`. |
| `scattered` | no | Where wilderness structures go. See [below](#scattered). |
| `parts` | no | Overrides for default monorail/highway/railway part names. See [Streets, Highways, Rails & Monorails](../concepts/infrastructure-parts.md). |
| `citybiomemultipliers` | no | List of `{multiplier, biomes}`, per-biome city density multiplier. `multiplier` is a float: below 1 makes cities rarer in those biomes, above 1 makes them denser. The shipped world style uses `0.1` for oceans and `0.3` for rivers. |

## `multisettings`

Controls how [Multi-Buildings](multibuilding.md) are placed. The world is tiled into square areas of `areasize` × `areasize` chunks, and each area gets its own independent roll.

| Key | Default | Limits | Meaning |
|---|---|---|---|
| `areasize` | *(required)* | ≥ 1, and ≥ every multi-building's `dimx`/`dimz` | Side of the placement area, in chunks. Shipped world style uses `10`. |
| `minimum` | *(required)* | ≥ 0, ≤ `maximum` | Fewest multi-buildings attempted per area. |
| `maximum` | *(required)* | ≥ `minimum` | Most attempted per area. Shipped: `1` to `5`. |
| `correctstylefactor` | `0.8` | 0 – 1 | Fraction of a multi-building's chunks that must share the dominant city style, or placement is refused. |
| `attempts` | `50` | ≥ 1 | Random positions tried per multi-building before giving up. `0` silently places nothing. |

!!! warning "`areasize` has to fit your largest multi-building"
    Placement uses `random(areasize - dimx + 1)`, so a multi-building wider than the area throws during chunk generation. See [Multi-Building Reference](multibuilding.md).

!!! note "Multi-buildings do not cross style boundaries well"
    The multi-building is drawn from whichever city style covers the most chunks in the area, then `correctstylefactor` requires that much of its own footprint to share that style. Raising it toward `1` forces multi-buildings fully inside one style; lowering it toward `0` lets them straddle. Above `1` makes placement impossible.

## `scattered`

Controls [Scattered Buildings](scattered.md), the structures out in the wilderness. Same area-tiling idea, separate settings.

| Key | Default | Limits | Meaning |
|---|---|---|---|
| `areasize` | *(required)* | ≥ 1, and ≥ any referenced multi-building's `dimx`/`dimz` | Side of the area in chunks. Shipped: `8`. |
| `chance` | *(required)* | 0 – 1 | Chance **per area**, not per chunk. Multiplied by the profile's `scatteredChanceMultiplier` before the roll, so `0` on either side disables everything. Shipped: `0.7`. |
| `weightnone` | *(required)* | ≥ 0 | Weight of the "place nothing" outcome, drawn against the entries in `list`. Shipped: `30`. |
| `list` | *(required)* | | Weighted references, see [Scattered Building Reference](scattered.md#where-placement-is-actually-controlled). |

At most **one** structure spawns per area, at a random offset inside it, chosen from a roll seeded by the area's coordinates. So `areasize` sets the spacing and `chance` sets how many of those slots are filled.

!!! example "Reading the shipped numbers"
    `areasize: 8`, `chance: 0.7`, `weightnone: 30`, with `radiotower` at 15, `cabin` at 10, `oilrig` at 4. That means: roughly one slot per 8×8 chunks, filled 70% of the time, and when filled the draw is 30/59 nothing, 15/59 radio tower, 10/59 cabin, 4/59 oil rig. Biome and terrain filters then reject most of the remainder.

## Example: picking a city style by biome

```json
{
  "outsidestyle": "standard",
  "citystyles": [
    { "factor": 1.0, "citystyle": "citystyle_standard" },
    { "factor": 2.0, "citystyle": "citystyle_desert", "biomes": { "if_any": ["minecraft:desert"] } }
  ]
}
```

In a desert biome, `citystyle_desert` is picked twice as often as `citystyle_standard`. Everywhere else, only `citystyle_standard` is eligible.

## See also

- [The Content Model](../getting-started/content-model.md)
- [Matchers](../concepts/matchers.md) for how `biomes`/`if_any`/`excluding` work
- [Scattered Building Reference](scattered.md) for the `scattered` section
- [Glossary](../glossary.md)
