# Matchers

!!! tip "TL;DR"
    Same shape everywhere: `if_all`, `if_any`, `excluding`. Used for biomes, blocks, resource locations. Learn it once.

Several unrelated fields (a world style's `biomes`, a stuff object's `blocks`, and more) all use this exact same filter shape instead of each inventing their own.

## The shape

| Key | Meaning |
|---|---|
| `if_all` | Every entry in this list must match. |
| `if_any` | At least one entry in this list must match. |
| `excluding` | None of these may match. |

All three are optional. Omit everything and it matches anything.

## Example: biome matcher

```json
{
  "biomes": {
    "if_any": ["minecraft:desert", "minecraft:badlands"],
    "excluding": ["minecraft:eroded_badlands"]
  }
}
```

Matches desert or badlands, except eroded badlands specifically.

## Block matcher: tags too

A block matcher accepts a `#namespace:tag` entry instead of an exact block ID:

```json
{ "blocks": { "if_any": ["#minecraft:planks"] } }
```

Matches any block in the `minecraft:planks` tag, not just one specific plank type.

## See also

[Glossary](../glossary.md)
