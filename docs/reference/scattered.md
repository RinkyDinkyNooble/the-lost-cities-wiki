# Scattered Building Reference

!!! tip "TL;DR"
    `scattered/<name>.json`. Standalone structures placed out in the wilderness, outside cities entirely. Cabins, oil rigs, radio towers, that sort of thing.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `buildings` | one of these two | List of building names, randomly picked. |
| `multibuilding` | | A single multi-building name instead. |
| `rotatable` | no | Allow random rotation. |
| `terrainheight` | **yes** | One of `lowest`, `average`, `highest`, `ocean`. |
| `terrainfix` | **yes** | One of `none`, `clear`, `repeatslice`. |
| `heightoffset` | no | Vertical offset in blocks, default `0`. |

## Where placement is actually controlled

This asset only defines the *structure*. Where and how often it spawns lives in a [World Style](worldstyle.md)'s [`scattered`](worldstyle.md#scattered) block, and the per-structure filters live on each entry of its `list`, not here:

| Key | Required | Limits | Meaning |
|---|---|---|---|
| `name` | **yes** | | The scattered asset to place. |
| `weight` | **yes** | ≥ 0 | Weight in the draw, against the other entries **and** against `weightnone`. |
| `nearhighway` | no | | If `true`, only places when one of the four neighbouring chunks has a highway. |
| `allowvoid` | no | | If `true`, allows placement where the terrain is at or near world bottom. Only consulted on `floating`/`space`/`spheres` landscapes, ignored on `default` and `cavern`. |
| `maxheightdiff` | no | ≥ 0, blocks | Rejects the spot if (highest - lowest) terrain across the **whole footprint** exceeds this. The flatness filter. |
| `biomes` | no | | Standard [Matcher](../concepts/matchers.md). |

!!! example "The shipped list, which is a good template"
    ```json title="worldstyles/standard.json, scattered.list"
    [
      { "name": "radiotower", "weight": 15, "maxheightdiff": 3,
        "biomes": { "excluding": ["#minecraft:is_ocean", "#minecraft:is_river", "#minecraft:is_beach"] } },
      { "name": "oilrig", "weight": 4, "maxheightdiff": 100,
        "biomes": { "if_any": ["#minecraft:is_deep_ocean"] } },
      { "name": "cabin", "weight": 10, "maxheightdiff": 2,
        "biomes": { "excluding": ["#minecraft:is_ocean", "#minecraft:is_river", "#minecraft:is_beach"] } }
    ]
    ```
    `maxheightdiff` is doing most of the work: the cabin needs near-flat ground (`2`), the radio tower tolerates a little slope (`3`), and the oil rig sits on open water where the value is effectively unlimited (`100`).

!!! warning "A multi-building here must fit the scattered `areasize`"
    If `multibuilding` is set, its `dimx`/`dimz` must not exceed the world style's `scattered.areasize` (shipped default `8`), or generation throws. See [Multi-Building Reference](multibuilding.md).

## Example

```json
{
  "buildings": ["cabin"],
  "terrainheight": "average",
  "terrainfix": "clear",
  "heightoffset": 0
}
```

## See also

[World Style Reference](worldstyle.md)
