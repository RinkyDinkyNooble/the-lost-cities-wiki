# Scattered Building Reference

!!! tip "TL;DR"
    `scattered/<name>.json` describes a standalone structure placed out in the wilderness, entirely outside cities. Cabins, oil rigs and radio towers are the shipped examples.

!!! note "Some keys here do not exist on every version"
    `rotatable`, `nearhighway`, `feather`, `minSpawnDistance` and
    `maxSpawnDistance` were added in 7.4.12, and are absent in 8.2.2. `allowvoid`
    was added in 7.4.12 and is present in 8.2.2. `supportpart` and
    `clearhighwayrailing` need 7.5.1. See
    [Key availability](../versions/key-availability.md).

## Keys

| Key | Required | Meaning |
|---|---|---|
| `buildings` | one of these two | A list of building names. The mod picks one at random. |
| `multibuilding` | | A single multi-building name, used instead of `buildings`. |
| `rotatable` | no | **Does nothing in 7.4.12.** See the warning below. |
| `terrainheight` | **yes** | One of `lowest`, `average`, `highest`, `ocean`. Decides which terrain height the structure is seated at. |
| `terrainfix` | **yes** | One of `none`, `clear`, `repeatslice`. Decides what the mod does to the terrain around the structure. |
| `heightoffset` | no | A vertical offset in blocks. Defaults to `0`. |

!!! warning "`rotatable` is dropped before generation ever sees it"
    This one is deader than the inert city style keys. Those at least reach the city style object and the public API. `rotatable` is parsed into the codec record and then **never copied into the `ScatteredBuilding` the generator uses**. The asset class has no field for it, and no API method exposes it.

    Setting `"rotatable": true` has no effect and no way to have an effect. A scattered structure generates in the orientation you authored it.

!!! warning "A scattered asset with neither `buildings` nor `multibuilding` throws"
    Both keys are optional in the codec, so a file with neither loads. The mod then throws `Missing buildings for scattered '<name>'!` when it tries to place the structure.

## Where placement is controlled

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
