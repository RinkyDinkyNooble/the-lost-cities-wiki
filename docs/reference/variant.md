# Variant Reference

!!! tip "TL;DR"
    `variants/<name>.json`. A named, reusable weighted block list. Referenced from a palette entry's `variant` field. Same 128-slot rule as inline `blocks`.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `blocks` | **yes** | List of `{random, block}`. See the [128-slot rule](palette.md#the-128-slot-rule-for-blocks-and-variant). |

## Example

```json title="variants/stonebrick.json (real, shipped with the mod)"
{
  "blocks": [
    { "random": 9, "block": "minecraft:cracked_stone_bricks" },
    { "random": 8, "block": "minecraft:mossy_stone_bricks" },
    { "random": 1000, "block": "minecraft:stone_bricks" }
  ]
}
```

Mostly plain stone bricks, occasionally cracked or mossy. Referenced from a palette like:

```json
{ "char": "θ", "variant": "stonebrick" }
```

## Why use a Variant instead of inline `blocks`?

Reuse. Ten palettes can all reference `stonebrick` instead of copy-pasting the same weighted list ten times. Change the variant once, every palette using it updates.

## See also

[Palette Reference](palette.md)
