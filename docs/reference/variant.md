---
claims: verified
---

# Variant Reference

!!! tip "TL;DR"
    `variants/<name>.json` is a named, reusable weighted block list. A palette entry reaches it through its `variant` key. The same 128-slot rule applies as for an inline `blocks` list. [code review](../examples/claim-tests.md#ref-2){.v .v-c} [game test](../examples/claim-tests.md#pal-3){.v .v-g}

## Keys

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Meaning |
|---|---|---|
| `blocks` | **yes** | A list of `{random, block}` entries. See the [128-slot rule](palette.md#the-128-slot-rule-for-blocks-and-variant) |

## Example

```json title="variants/stonebrick.json, shipped with the mod"
{
  "blocks": [
    { "random": 9, "block": "minecraft:cracked_stone_bricks" },
    { "random": 8, "block": "minecraft:mossy_stone_bricks" },
    { "random": 1000, "block": "minecraft:stone_bricks" }
  ]
}
```

That gives mostly plain stone bricks, with the occasional cracked or mossy one. A palette reaches it like this: <!-- noclaim -->

```json
{ "char": "θ", "variant": "stonebrick" }
```

## Why a variant beats an inline `blocks` list

Reuse. Ten palettes can name `stonebrick` instead of repeating the same weighted list ten times, and changing the variant changes all ten. <!-- noclaim -->

!!! warning "A `variant` name that does not resolve throws"
    `CompiledPalette` throws `Invalid palette entry for '<char>'!` when the named variant is missing. The character, not the variant, is what the message names, so the file to look at is the palette rather than the variant. Check the namespace as well as the spelling. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! danger "The weights are slots, not odds"
    A variant's `random` numbers fill a 128-entry table. Once the table is full the remaining entries are unreachable, and nothing is logged. The 1000 above is not a probability, it is "take every slot the first two did not". [game test](../examples/claim-tests.md#pal-3){.v .v-g}

## See also

- [Palette Reference](palette.md)
- [Error Messages](../troubleshooting/errors.md) <!-- noclaim -->
