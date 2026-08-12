# World Style Reference

!!! tip "TL;DR"
    `worldstyles/<name>.json` picks which City Styles can appear, and how often. A profile points at exactly one world style by name.

## Keys

| Key | Required | Meaning |
|---|---|---|
| `outsidestyle` | **yes** | The name of a [Style](style.md) used for terrain outside cities. |
| `citystyles` | **yes** | A list of `{factor, citystyle, biomes}` entries. Weighted, optionally biome-limited picks of which [City Style](citystyle.md) to use. |
| `multisettings` | no | Multi-building placement tuning. See [below](#multisettings). |
| `settings` | no | `railwayavoidance`, `railpartheight6`, and the four vine block states. See [below](#settings). |
| `cityspheres` | no | Defines a special part placed at the exact centre chunk of every city sphere, such as a landmark or a reactor. `centerpart` names the part, `centertype` selects the variety, and `centerpartorigin` and `centerpartoffset` position it vertically. The mod looks this up only for a chunk that is a sphere centre, and skips it silently if the part name does not resolve. |
| `scattered` | no | Where wilderness structures go. See [below](#scattered). |
| `parts` | no | Overrides for the default monorail, highway and railway part names. See [Streets, Highways, Rails and Monorails](../concepts/infrastructure-parts.md). |
| `citybiomemultipliers` | no | A list of `{multiplier, biomes}` entries giving a per-biome city density multiplier. A `multiplier` below 1 makes cities rarer in those biomes, and above 1 makes them denser. The shipped world style uses `0.1` for oceans and `0.3` for rivers. |

## `settings`

| Key | Default | Meaning |
|---|---|---|
| `railwayavoidance` | *(required)* | `ignore` lets buildings generate over railways. `block_railway` suppresses the railway instead. These are the only two accepted values. |
| `railpartheight6` | `1` | The height, in 6-block floor units, that a railway part occupies. |
| `vinewest` / `vineeast` / `vinesouth` / `vinenorth` | the matching vanilla vine state | The block state used for vine decoration on each face. |

The shipped `standard` world style sets only `railwayavoidance: "ignore"` and `railpartheight6: 1`.

## `multisettings`

This controls how [Multi-Buildings](multibuilding.md) are placed. The mod tiles the world into square areas of `areasize` by `areasize` chunks, and each area gets its own independent roll.

| Key | Default | Limits | Meaning |
|---|---|---|---|
| `areasize` | *(required)* | 1 or more, and at least as large as every multi-building's `dimx` and `dimz` | The side of the placement area, in chunks. The shipped world style uses `10`. |
| `minimum` | *(required)* | 0 or more, and no greater than `maximum` | The fewest multi-buildings attempted per area. Shipped value `1`. |
| `maximum` | *(required)* | at least `minimum` | The most attempted per area. Shipped value `5`. |
| `correctstylefactor` | `0.8` | 0 to 1 | The fraction of a multi-building's chunks that must share the dominant city style, or the mod refuses the placement. |
| `attempts` | `50` | 1 or more | The number of random positions tried per multi-building before the mod gives up. `0` places nothing, silently. |

!!! warning "`areasize` has to fit your largest multi-building"
    Placement uses `random(areasize - dimx + 1)`, so a multi-building wider than the area makes that bound zero or negative and the mod throws. See [Multi-Building](multibuilding.md).

!!! note "A multi-building does not cross a style boundary well"
    The mod draws the multi-building from whichever city style covers the most chunks in the area, then `correctstylefactor` requires that fraction of the building's own footprint to share that style.

    Raising the value toward 1 forces multi-buildings to sit fully inside one style. Lowering it toward 0 lets them straddle a boundary. A value above 1 can never be satisfied, so nothing is placed.

## `scattered`

This controls [Scattered Buildings](scattered.md), the structures out in the wilderness. It uses the same area-tiling idea with its own settings.

| Key | Default | Limits | Meaning |
|---|---|---|---|
| `areasize` | *(required)* | 1 or more, and at least as large as any referenced multi-building's `dimx` and `dimz` | The side of the area, in chunks. Shipped value `8`. |
| `chance` | *(required)* | 0 to 1 | The chance **per area**, not per chunk. The mod multiplies it by the profile's `scatteredChanceMultiplier` before rolling, so `0` on either side disables scattered buildings entirely. Shipped value `0.7`. |
| `weightnone` | *(required)* | 0 or more | The weight of the "place nothing" outcome, drawn against the entries in `list`. Shipped value `30`. |
| `list` | *(required)* | | Weighted references. See [Scattered Building Reference](scattered.md#where-placement-is-actually-controlled). |

At most **one** structure spawns per area, at a random offset inside it, from a roll seeded by the area's coordinates. So `areasize` sets the spacing and `chance` sets how many of those slots are filled.

!!! example "Reading the shipped numbers"
    The shipped world style uses `areasize: 8`, `chance: 0.7` and `weightnone: 30`, with `radiotower` at 15, `cabin` at 10 and `oilrig` at 4.

    That is roughly one slot per 8 by 8 chunks, filled 70% of the time. When a slot is filled, the draw is 30 in 59 for nothing, 15 in 59 for a radio tower, 10 in 59 for a cabin and 4 in 59 for an oil rig. The biome and terrain filters then reject most of what is left. The oil rig, for example, is limited to deep ocean.

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

In a desert biome both entries match, so the mod picks `citystyle_desert` twice as often as `citystyle_standard`. Everywhere else only `citystyle_standard` is eligible.

The shipped `standard` world style uses a much steeper split: `citystyle_standard` at 0.5 against `citystyle_desert` at 9.0 in desert and badlands.

## See also

- [The Content Model](../getting-started/content-model.md)
- [Matchers](../concepts/matchers.md) for how `biomes`, `if_any` and `excluding` work
- [Scattered Building Reference](scattered.md) for the `scattered` section
- [Glossary](../glossary.md)
