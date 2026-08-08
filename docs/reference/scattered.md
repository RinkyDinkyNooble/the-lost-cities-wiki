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

This asset only defines the *structure*. Where and how often it spawns is controlled separately, from a [World Style](worldstyle.md)'s `scattered` settings (`areasize`, `chance`, `weightnone`, and a weighted list of these by name).

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
