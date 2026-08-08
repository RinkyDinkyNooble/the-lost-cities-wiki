# Palette Reference

!!! tip "TL;DR"
    `palettes/<name>.json`. Maps single characters to blocks. Each entry is `char` plus **exactly one** of `block`, `variant`, `blocks`, or `frompalette`.

## File shape

```json
{
  "palette": [
    { "char": "α", "block": "minecraft:stone_bricks" }
  ]
}
```

## Entry fields

| Key | Required | Meaning |
|---|---|---|
| `char` | **yes** | Single character. Must be unique within the merged palette set it's used in. |
| `block` | one of these four | A fixed block state string. |
| `variant` | | Name of a [Variant](variant.md), a shared weighted block list. |
| `blocks` | | Inline weighted list, same shape as a Variant but not reusable elsewhere. |
| `frompalette` | | Alias to another character's resolved value. See [Namespaces](../getting-started/namespaces.md#the-default-namespace-trap) for the same "bare name" gotcha applying here. |
| `damaged` | no | Block this maps to when ruined/damaged. Independent of the four above. |
| `mob` | no | Spawns this mob here. |
| `loot` | no | Loot table to use here. |
| `torch` | no | Boolean, special-cased light-level handling. |
| `tag` | no | Raw NBT compound. This is the mechanism behind command-block palette tricks. |

!!! note "frompalette is an alias, not inheritance"
    It copies the *entire* resolved value (one block, or a whole weighted list) from another character, wholesale. There's no partial override, you can't inherit the block but change the loot. Only the first character of the string is used as the lookup, and it resolves once when palettes are merged, not per-placement. `tag`/`mob`/`loot`/`torch`/`damaged` on a `frompalette` entry are still independent, they don't come from the aliased character.

## The 128-slot rule for `blocks` and `variant`

Weighted lists (`blocks` here, or inside a [Variant](variant.md)) fill a **fixed 128-slot array**, in list order.

- Total weight **under 128** → hard crash at palette load (`"Not enough blocks in the random list"`).
- Total weight **over 128** → the entry that fills the last slot gets cut short, and **every entry listed after it gets nothing at all**. Order matters, not just the sum.
- Total weight **exactly 128** → everyone gets their exact stated share.

!!! example "Real example from the mod's own shipped content"
    ```json title="variants/stonebrick.json"
    {
      "blocks": [
        { "random": 9, "block": "minecraft:cracked_stone_bricks" },
        { "random": 8, "block": "minecraft:mossy_stone_bricks" },
        { "random": 1000, "block": "minecraft:stone_bricks" }
      ]
    }
    ```
    Total is 1017, not 128. In practice: 9/128 cracked, 8/128 mossy, and the remaining 111/128 slots go to stone bricks (the `1000` gets clipped down to whatever's left). This is the mod author's own idiom: give rare options small honest numbers, then a big catch-all number **last** to soak up the remainder. Put that catch-all anywhere but last, and everything after it becomes unreachable.

## Stairs, fences, and walls auto-correct on placement

Every block placed through a part goes through a neighbor-aware correction pass before it lands, the same logic vanilla Minecraft uses when a player places these blocks by hand:

- **Stairs** (`minecraft:*_stairs`): the `shape` property is always recalculated from whatever ends up next to it (matching stairs on the facing side or its opposite produce an outer/inner corner, anything else is `straight`). **Whatever `shape=` you write in a `block` string is discarded and replaced.** This isn't occasional, it happens on every stair placement. If a corner comes out wrong, it's because the recalculated shape doesn't match what the surrounding part geometry produces, not because the palette entry was ignored.
- **Fences, walls, and similar connecting blocks**: connections to neighbors are recalculated the same way, this is expected and rarely surprising.
- **Structure void blocks**: silently placed as nothing.

!!! warning "Forcing an exact stair shape"
    If you need a specific corner shape the auto-correction won't produce, the only reliable workaround is placing it *after* generation finishes, since the correction pass only runs during the terrain-generation call itself. The [Command Blocks](../advanced/command-blocks.md) page shows the pattern: a palette entry that places an auto-firing command block whose command forces the exact block state, bypassing the normal palette-to-block path entirely.

## See also

- [Variant Reference](variant.md)
- [Style Reference](style.md) for how multiple palettes combine
- [Namespaces](../getting-started/namespaces.md)
