---
claims: verified
---

# Stuff Object Reference

!!! tip "TL;DR"
    `stuff/<name>.json` places small decorative extras such as cobwebs and chains. The mod scans columns and makes random attempts inside them rather than baking the decoration into a part. Tags, blocks and biome gate where it happens. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! warning "This asset type does not exist before 6.2.2"
    Every key on this page arrived in 6.2.2. On 5.3.29, 6.0.3, 6.1.6 or 6.2.3 the mod does not know the stuff object at all. See [Key availability](../versions/key-availability.md). [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! info "None of this has been placed in a world"
    Stuff objects are documented from their codec and have never been generated on the rig. The arithmetic below follows from the bytecode; the visual result does not. [unverified](../examples/claim-tests.md#ref-3){.v .v-u}

## Keys

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Limits | Meaning |
|---|---|---|---|
| `column` | **yes** | | Identifies a valid vertical placement column |
| `mincount` / `maxcount` | **yes** | `maxcount` must be **greater than** `mincount` | How many objects to place per successful attempt |
| `attempts` | **yes** | 1 or more | How many placement attempts to make. `0` places nothing, silently |
| `tags` | no | | Matched against a [City Style](citystyle.md)'s `stuff_tags` |
| `minheight` / `maxheight` | no | `maxheight` must be **greater than** `minheight` | The height range to search within. See the defaults below |
| `inbuilding` | no | | `true` restricts placement to inside buildings |
| `seesky` | no | | `true` restricts placement to spots that can see the sky |
| `biomes` | no | | A [Matcher](../concepts/matchers.md) for allowed biomes |
| `blocks` | no | | A [Matcher](../concepts/matchers.md) for the block required below the spawn point |
| `upperblocks` | no | | The same, for the block required above it |
| `buildings` | no | | Restricts placement to specific buildings. A resource-location matcher, which does **not** take `if_all`. See [Matchers](../concepts/matchers.md#not-every-matcher-takes-all-three-keys) |

!!! danger "Equal `mincount` and `maxcount` crash world generation"
    The count is `random(maxcount - mincount) + mincount`, and the random call needs a **positive** bound. `"mincount": 2, "maxcount": 2` therefore does not mean "always place 2": it throws `bound must be positive` during generation. Write `"mincount": 2, "maxcount": 3` for that. Reversed values throw for the same reason. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    The count is computed before any attempt runs, so a high `attempts` value is no protection. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    `minheight` and `maxheight` work the same way, because the Y coordinate is `random(maxheight - minheight) + minheight`. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### What `minheight` and `maxheight` default to

Leaving **both** unset is always safe. The risk is setting one of the pair and landing on a range of zero. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| Key | Outside a building | Inside a building |
|---|---|---|
| `minheight` | The chunk's ground level | The bottom of the cellars, that is city ground level minus `cellars * 6` |
| `maxheight` | `minheight + 20` | City ground level plus `floors * 6`, plus 10 |
[code review](../examples/claim-tests.md#ref-2){.v .v-c}

The inside-a-building defaults apply only when `inbuilding` is set and the chunk actually holds a building. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

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
- [Error Messages](../troubleshooting/errors.md) for `bound must be positive` <!-- noclaim -->
