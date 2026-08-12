# The Content Model

!!! tip "TL;DR"
    `WorldStyle` picks `CityStyle`s. A `CityStyle` picks a `Style` (palette combinator) and building/street/park settings. Buildings pick `Parts`. Parts use a `Palette`. One chain, top to bottom.

Six asset types, composing in a strict order. Miss a link and the chain breaks silently, same rule as [Namespaces](namespaces.md).

## The chain

| # | Asset | Picks | Registry folder |
|---|---|---|---|
| 1 | **World Style** | one or more City Styles, by biome/weight | `worldstyles/` |
| 2 | **City Style** | a Style, plus building/street/park/rail settings | `citystyles/` |
| 3 | **Style** | palettes, randomly per "slot" | `styles/` |
| 4 | **Building** | parts, per floor/cellar, conditionally | `buildings/` |
| 5 | **Building Part** | one palette | `parts/` |
| 6 | **Palette** | blocks, per character | `palettes/` |

## Worked example

Say a world generates a chunk and decides "this is a city, floor 2 of a building."

1. The dimension's **profile** says `worldStyle: "standard"`.
2. `standard` **World Style** rolls a biome-weighted pick and lands on `citystyle_standard`.
3. `citystyle_standard` **City Style** says `style: "standard"` and inherits everything else from `citystyle_common`. It sets no `buildingsettings` of its own, so the building chance stays whatever the profile chose, `0.3` by default.
4. `standard` **Style** rolls one palette from each of its slots (say, one wall-material slot, one roof-material slot) and merges them.
5. The **Building** chosen for this chunk lists a part for floor 2, maybe conditioned on `"inbiome"` or `"chunkx"`.
6. That **Building Part** renders using the merged palette from step 4, unless it sets its own `refpalette` or embeds one directly, in which case that palette wins instead.

Every step above is a name lookup. Every name lookup respects [namespacing](namespaces.md) rules.

!!! note "Style ≠ visual theme"
    Despite the name, a `Style` does not describe a look. It is a weighted **palette picker**: each "slot" in a style randomly resolves to one palette from a list, then all the resolved palettes get merged. Full reference on the Style page.

## See also

- [Your First Custom City](first-city.md) for this chain as six real files
- [Namespaces](namespaces.md)
- [Glossary](../glossary.md)
- [Reference](../reference/index.md) for a key-by-key page on each asset type
