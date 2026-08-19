---
claims: verified
---

# The Content Model

!!! tip "TL;DR"
    `WorldStyle` picks `CityStyle`s. A `CityStyle` picks a `Style` (palette combinator) and building, street and park settings. Buildings pick `Parts`. Parts use a `Palette`. One chain, top to bottom. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

Six asset types composing in a strict order. Break a link and the chain throws, not always where you were standing when you broke it. See [Namespaces](namespaces.md#what-a-reference-into-the-wrong-namespace-actually-does). [game test](../examples/claim-tests.md#ns-4){.v .v-g}

## The chain

| # | Asset [code review](../examples/claim-tests.md#ref-2){.v .v-c} | Picks | Registry folder |
|---|---|---|---|
| 1 | **World Style** | one or more City Styles, by biome and weight | `worldstyles/` |
| 2 | **City Style** | a Style, plus building, street, park and rail settings | `citystyles/` |
| 3 | **Style** | palettes, randomly per slot | `styles/` |
| 4 | **Building** | parts, per floor and cellar, conditionally | `buildings/` |
| 5 | **Building Part** | one palette | `parts/` |
| 6 | **Palette** | blocks, per character | `palettes/` |

## Worked example

A world generates a chunk and decides this is a city, floor 2 of a building. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

1. The dimension's **profile** says `worldStyle: "standard"`.
2. The `standard` **World Style** rolls a biome-weighted pick and lands on `citystyle_standard`.
3. That **City Style** says `style: "standard"` and inherits everything else from `citystyle_common`. It sets no `buildingsettings` of its own, so the building chance stays whatever the profile chose, `0.3` by default.
4. The `standard` **Style** rolls one palette from each of its slots, say one wall-material slot and one roof-material slot, and merges them.
5. The **Building** chosen for this chunk lists a part for floor 2, maybe gated on `inbiome` or `chunkx`.
6. That **Building Part** draws using the merged palette from step 4, unless it sets its own `refpalette` or embeds one, in which case that palette wins. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

Every step is a name lookup, and every name lookup follows the [namespacing](namespaces.md) rules. [code review](../examples/claim-tests.md#ns-3){.v .v-c}

!!! note "A Style is not a visual theme"
    Despite the name, a `Style` describes no look. It is a weighted **palette picker**: each slot resolves to one palette from a list, and the resolved palettes are merged. Full detail on the [Style](../reference/style.md) page. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## See also

- [Your First Custom City](first-city.md) for this chain as six real files
- [Namespaces](namespaces.md)
- [Glossary](../glossary.md)
- [Reference](../reference/index.md) for a key-by-key page on each asset type <!-- noclaim -->
