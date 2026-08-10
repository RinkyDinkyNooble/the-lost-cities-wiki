# Stuff Object Reference

!!! tip "TL;DR"
    `stuff/<name>.json` places small decorative extras such as cobwebs and chains. The mod scans columns and makes random attempts inside them, rather than baking the decoration into a part. Tags, blocks and biome gate where it happens.

## Keys

| Key | Required | Limits | Meaning |
|---|---|---|---|
| `column` | **yes** | | Identifies a valid vertical placement column. |
| `mincount` / `maxcount` | **yes** | `maxcount` must be **greater than** `mincount` | How many objects to place per successful attempt. |
| `attempts` | **yes** | 1 or more | How many placement attempts to make. `0` places nothing, silently. |
| `tags` | no | | Matched against a [City Style](citystyle.md)'s `stuff_tags`. |
| `minheight` / `maxheight` | no | `maxheight` must be **greater than** `minheight` | The height range to search within. See the defaults below. |
| `inbuilding` | no | | If `true`, restricts placement to inside buildings. |
| `seesky` | no | | If `true`, restricts placement to spots that can see the sky. |
| `biomes` | no | | A [Matcher](../concepts/matchers.md) for allowed biomes. |
| `blocks` | no | | A [Matcher](../concepts/matchers.md) for the block required below the spawn point. |
| `upperblocks` | no | | The same, for the block required above it. |
| `buildings` | no | | Restricts placement to specific buildings. This one is a resource-location matcher, which does **not** accept `if_all`. See [Matchers](../concepts/matchers.md#not-every-matcher-accepts-all-three-keys). |

!!! danger "Equal `mincount` and `maxcount` crash world generation"
    The mod computes the count as `random(maxcount - mincount) + mincount`, and the random call requires a **positive** bound. So `"mincount": 2, "maxcount": 2` does not mean "always place 2". It throws `bound must be positive` during generation. Write `"mincount": 2, "maxcount": 3` for that. Reversed values, with `maxcount` below `mincount`, throw for the same reason.

    The mod computes the count before it runs any attempt, so a high `attempts` value does not protect you.

    The same rule applies to `minheight` and `maxheight`, because the Y coordinate uses `random(maxheight - minheight) + minheight`.

### What `minheight` and `maxheight` default to

Leaving **both** unset is always safe. The risk comes from setting only one of the pair and landing on a range of zero.

| Key | Outside a building | Inside a building |
|---|---|---|
| `minheight` | The chunk's ground level. | The bottom of the cellars, that is the city ground level minus `cellars * 6`. |
| `maxheight` | `minheight + 20`. | The city ground level plus `floors * 6`, plus 10. |

The inside-a-building defaults apply only when `inbuilding` is set and the chunk actually has a building.

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
- [Error Messages](../troubleshooting/errors.md) for `bound must be positive`
