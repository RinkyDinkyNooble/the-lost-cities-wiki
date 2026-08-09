# Stuff Object Reference

!!! tip "TL;DR"
    `stuff/<name>.json`. Small decorative extras (cobwebs, chains) placed by scanning columns, not baked into a part. Random attempts within a column, gated by tags/blocks/biome.

## Fields

| Key | Required | Limits | Meaning |
|---|---|---|---|
| `column` | **yes** | | Identifies a valid vertical placement column. |
| `mincount` / `maxcount` | **yes** | `maxcount` **>** `mincount` | How many to place per successful attempt. |
| `attempts` | **yes** | ≥ 1 | How many placement attempts to make. `0` places nothing, silently. |
| `tags` | no | | Matched against a [City Style](citystyle.md)'s `stuff_tags`. |
| `minheight` / `maxheight` | no | `maxheight` **>** `minheight` | Height range to search within. |
| `inbuilding` | no | | Restrict to inside buildings. |
| `seesky` | no | | Restrict to spots that see sky. |
| `biomes` | no | | [Matcher](../concepts/matchers.md) for allowed biomes. |
| `blocks` | no | | [Matcher](../concepts/matchers.md) for the block required below the spawn point. |
| `upperblocks` | no | | Same, for the block required above. |
| `buildings` | no | | Restrict to specific buildings by resource location. |

!!! danger "Equal min/max counts crash chunk generation"
    Both count pairs are used as `random(max - min) + min`, and the random call requires a **positive** bound. So `"mincount": 2, "maxcount": 2` is not "always place 2", it throws during generation. Use `mincount: 2, maxcount: 3` for that. Reversed values (max below min) throw for the same reason.

    The same applies to `minheight`/`maxheight`. Leaving **both** unset is always safe: `minheight` defaults to the chunk's ground level and `maxheight` to `minheight + 20` (or the top of the building plus 10 when inside one). The risk comes from setting only one of the pair and landing on a range of zero.

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
