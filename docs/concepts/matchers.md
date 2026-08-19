---
claims: verified
---

# Matchers

!!! tip "TL;DR"
    A matcher is a small filter object built from `if_all`, `if_any` and `excluding`. Biome and block matchers take all three. The resource-location matcher takes only two. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! note "`if_any` and `excluding` need 6.2.2"
    Both keys arrived in 6.2.2, on the block matcher and on the resource location matcher. Before that only `if_all` exists. See [Key availability](../versions/key-availability.md). [code review](../examples/claim-tests.md#ref-1){.v .v-c}

Several unrelated keys share this filter shape rather than each inventing one: a world style's `biomes`, a stuff object's `blocks`, a scattered entry's `biomes`, and others. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## The shape

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Meaning |
|---|---|
| `if_all` | Every entry in this list must match |
| `if_any` | At least one entry in this list must match |
| `excluding` | None of these may match |

Every key is optional, and a matcher with nothing set matches anything. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

## Not every matcher takes all three keys

The mod has three matcher types and they do not share a key set. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Matcher | Used by | `if_all` | `if_any` | `excluding` |
|---|---|---|---|---|
| Biome matcher | `biomes`, everywhere it appears | yes | yes | yes |
| Block matcher | a Stuff Object's `blocks` and `upperblocks` | yes | yes | yes |
| Resource-location matcher | a Stuff Object's `buildings` | **no** | yes | yes |
[code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! warning "`if_all` in a `buildings` matcher fails to load"
    The resource-location matcher's codec declares `if_any` and `excluding` and nothing else, so a `buildings` matcher using `if_all` does not parse and the whole [Stuff Object](../reference/stuff.md) fails with it. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

    It would mean nothing there anyway. A chunk holds one building, and one name cannot equal several names at once. <!-- noclaim -->

## Example: a biome matcher

```json
{
  "biomes": {
    "if_any": ["minecraft:desert", "minecraft:badlands"],
    "excluding": ["minecraft:eroded_badlands"]
  }
}
```

That matches desert and badlands, but not eroded badlands. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

## Tags work in place of an exact ID

Block matchers and biome matchers both take a `#namespace:tag` entry instead of an exact ID. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

```json
{ "blocks": { "if_any": ["#minecraft:planks"] } }
```

That matches any block in the `minecraft:planks` tag rather than one plank type. The shipped world style does the same for biomes, with entries such as `#minecraft:is_ocean` and `#minecraft:is_deep_ocean`. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## See also

- [Stuff Object Reference](../reference/stuff.md)
- [World Style Reference](../reference/worldstyle.md)
- [Glossary](../glossary.md) <!-- noclaim -->
