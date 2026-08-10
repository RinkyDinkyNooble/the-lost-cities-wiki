# Variant Reference

!!! tip "TL;DR"
    `variants/<name>.json` is a named, reusable weighted block list. A palette entry references it through its `variant` key. The same 128-slot rule applies as for an inline `blocks` list.

## Keys

| Key | Required | Meaning |
|---|---|---|
| `blocks` | **yes** | A list of `{random, block}` entries. See the [128-slot rule](palette.md#the-128-slot-rule-for-blocks-and-variant). |

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

That gives mostly plain stone bricks, and occasionally cracked or mossy ones. A palette references it like this:

```json
{ "char": "θ", "variant": "stonebrick" }
```

## Why use a Variant instead of an inline `blocks` list

Reuse. Ten palettes can reference `stonebrick` instead of repeating the same weighted list ten times. Change the variant once and every palette that uses it changes with it.

!!! warning "A `variant` name that does not resolve throws"
    The mod throws `Invalid palette entry for '<char>'!` when the named variant does not exist. Check the namespace as well as the spelling. See [Namespaces](../getting-started/namespaces.md).

## See also

- [Palette Reference](palette.md)
- [Error Messages](../troubleshooting/errors.md)
