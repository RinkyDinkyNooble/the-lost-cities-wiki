# World Style Reference

!!! tip "TL;DR"
    `worldstyles/<name>.json`. Picks which City Styles can appear and how often. A profile points at exactly one of these by name.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `outsidestyle` | **yes** | Name of a [Style](style.md) used for terrain outside cities. |
| `citystyles` | **yes** | List of `{factor, citystyle, biomes?}`. Weighted, optionally biome-limited picks of which [City Style](citystyle.md) to use. |
| `multisettings` | no | Multibuilding placement tuning: `areasize`, `minimum`, `maximum`, `correctstylefactor` (default `0.8`), `attempts` (default `50`). |
| `settings` | no | `railwayavoidance` (`ignore`/`block_railway`), `railpartheight6`, and `vinewest`/`vineeast`/`vinesouth`/`vinenorth` blockstates for ruin decoration. |
| `cityspheres` | no | `centerpart`, `centertype`, `centerpartorigin`, `centerpartoffset`. |
| `scattered` | no | `areasize`, `chance`, `weightnone`, and a `list` of named [Scattered Building](scattered.md) references + weights. |
| `parts` | no | Overrides for default monorail/highway/railway part names. |
| `citybiomemultipliers` | no | List of `{multiplier, biomes}`, per-biome city density multiplier. |

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
