# Scattered Building Reference

!!! tip "TL;DR"
    `scattered/<name>.json` describes a standalone structure placed out in the wilderness, entirely outside cities. Cabins, oil rigs and radio towers are the shipped examples.

## Keys

| Key | Required | Meaning |
|---|---|---|
| `buildings` | one of these two | A list of building names. The mod picks one at random. |
| `multibuilding` | | A single multi-building name, used instead of `buildings`. |
| `rotatable` | no | If `true`, the mod may place the structure at a random rotation. |
| `terrainheight` | **yes** | One of `lowest`, `average`, `highest`, `ocean`. Decides which terrain height the structure is seated at. |
| `terrainfix` | **yes** | One of `none`, `clear`, `repeatslice`. Decides what the mod does to the terrain around the structure. |
| `heightoffset` | no | A vertical offset in blocks. Defaults to `0`. |

!!! warning "A scattered asset with neither `buildings` nor `multibuilding` throws"
    Both keys are optional in the codec, so a file with neither loads. The mod then throws `Missing buildings for scattered '<name>'!` when it tries to place the structure.

## Where placement is actually controlled

This asset defines only the **structure**. Where and how often it spawns lives in a [World Style](worldstyle.md)'s [`scattered`](worldstyle.md#scattered) block, and the per-structure filters live on each entry of its `list`, not here.

| Key | Required | Limits | Meaning |
|---|---|---|---|
| `name` | **yes** | | The scattered asset to place. |
| `weight` | **yes** | 0 or more | The weight in the draw, against the other entries **and** against `weightnone`. |
| `nearhighway` | no | | If `true`, the mod places the structure only when one of the four neighbouring chunks has a highway. |
| `allowvoid` | no | | If `true`, the mod allows placement where the terrain is at or near world bottom. It consults this only on the `floating`, `space` and `spheres` landscapes, and ignores it on `default` and `cavern`. |
| `maxheightdiff` | no | blocks, 0 or more | Rejects the spot when the highest terrain minus the lowest terrain across the **whole footprint** exceeds this. This is the flatness filter. |
| `biomes` | no | | A standard [Matcher](../concepts/matchers.md). |

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
    `maxheightdiff` does most of the work here. The cabin needs near-flat ground at 2, the radio tower tolerates a little slope at 3, and the oil rig sits on open water where 100 is effectively unlimited.

!!! warning "A multi-building here must fit the scattered `areasize`"
    If you set `multibuilding`, its `dimx` and `dimz` must not exceed the world style's `scattered.areasize`, whose shipped default is 8. Otherwise the mod throws during generation. See [Multi-Building](multibuilding.md).

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

- [World Style Reference](worldstyle.md) for the settings that place these
- [Multi-Building Reference](multibuilding.md)
- [Matchers](../concepts/matchers.md)
