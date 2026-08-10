# Matchers

!!! tip "TL;DR"
    A matcher is a small filter object built from `if_all`, `if_any` and `excluding`. Biome and block matchers accept all three. The resource-location matcher accepts only two.

Several unrelated keys use this same filter shape rather than each inventing their own: a world style's `biomes`, a stuff object's `blocks`, a scattered entry's `biomes`, and others.

## The shape

| Key | Meaning |
|---|---|
| `if_all` | Every entry in this list must match. |
| `if_any` | At least one entry in this list must match. |
| `excluding` | None of these may match. |

Every key is optional. A matcher with nothing set matches anything.

## Not every matcher accepts all three keys

There are three matcher types in the mod, and they do not share a key set.

| Matcher | Used by | `if_all` | `if_any` | `excluding` |
|---|---|---|---|---|
| Biome matcher | `biomes`, everywhere it appears | yes | yes | yes |
| Block matcher | a Stuff Object's `blocks` and `upperblocks` | yes | yes | yes |
| Resource-location matcher | a Stuff Object's `buildings` | **no** | yes | yes |

!!! warning "`if_all` in a `buildings` matcher fails to load"
    The resource-location matcher's codec declares only `if_any` and `excluding`. A `buildings` matcher that uses `if_all` does not parse, so the whole [Stuff Object](../reference/stuff.md) fails to load.

    `if_all` would be meaningless there anyway. A chunk has one building, and one name cannot equal several names at once.

## Example: a biome matcher

```json
{
  "biomes": {
    "if_any": ["minecraft:desert", "minecraft:badlands"],
    "excluding": ["minecraft:eroded_badlands"]
  }
}
```

This matches desert and badlands, but not eroded badlands.

## Tags work in place of an exact ID

A block matcher and a biome matcher both accept a `#namespace:tag` entry instead of an exact ID.

```json
{ "blocks": { "if_any": ["#minecraft:planks"] } }
```

This matches any block in the `minecraft:planks` tag, not one specific plank type. The shipped world style uses the same technique for biomes, with entries such as `#minecraft:is_ocean` and `#minecraft:is_deep_ocean`.

## See also

- [Stuff Object Reference](../reference/stuff.md)
- [World Style Reference](../reference/worldstyle.md)
- [Glossary](../glossary.md)
