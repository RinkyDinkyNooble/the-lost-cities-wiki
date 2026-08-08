# Stuff Object Reference

!!! tip "TL;DR"
    `stuff/<name>.json`. Small decorative extras (cobwebs, chains) placed by scanning columns, not baked into a part. Random attempts within a column, gated by tags/blocks/biome.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `column` | **yes** | Identifies a valid vertical placement column. |
| `mincount` / `maxcount` | **yes** | How many to place per successful attempt. |
| `attempts` | **yes** | How many placement attempts to make. |
| `tags` | no | Matched against a [City Style](citystyle.md)'s `stuff_tags`. |
| `minheight` / `maxheight` | no | Height range to search within. |
| `inbuilding` | no | Restrict to inside buildings. |
| `seesky` | no | Restrict to spots that see sky. |
| `biomes` | no | [Matcher](../concepts/matchers.md) for allowed biomes. |
| `blocks` | no | [Matcher](../concepts/matchers.md) for the block required below the spawn point. |
| `upperblocks` | no | Same, for the block required above. |
| `buildings` | no | Restrict to specific buildings by resource location. |

## Example

```json
{
  "column": "minecraft:air",
  "mincount": 1,
  "maxcount": 3,
  "attempts": 10,
  "blocks": { "if_any": ["minecraft:stone_bricks"] },
  "tags": ["ruined"]
}
```

## See also

- [City Style Reference](citystyle.md) for `stuff_tags`
- [Matchers](../concepts/matchers.md)
