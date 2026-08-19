---
claims: verified
---

# File-Era Assets

!!! tip "TL;DR"
    An asset file is a JSON **array of objects**. Each object carries its own `type` and `name`, so one file holds many assets of mixed types and nothing is derived from the file path. Ten types exist. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## The shape of a file

```json title="The pattern every file-era asset file follows"
[
  { "type": "palette", "name": "rails", "palette": [ ] },
  { "type": "part",    "name": "top4_1", "xsize": 16, "zsize": 16, "slices": [ ] },
  { "type": "building","name": "center00", "filler": "#", "parts": [ ] }
]
```

That is the whole naming system. There is no namespace, no folder meaning, and no path parsing. Two assets collide when they share a `type` and a `name`, and the one loaded later wins. See [Adding Your Own Content](adding-content.md#overriding-something-the-mod-ships). [code review](../examples/claim-tests.md#f12-4){.v .v-c}

## The ten types

`AssetRegistries.load` dispatches on `type` and accepts these and nothing else. An unrecognised `type` is not an asset. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

| Type | Shipped | Holds |
|---|---|---|
| `part` | 173 | `xsize`, `zsize`, `slices`, and optionally `meta` and `palette` |
| `palette` | 36 | `palette`, a list of character entries |
| `building` | 25 | `filler`, `parts`, and optionally `parts2`, `minfloors`, `maxfloors`, `maxcellars`, `preferslonely` |
| `multibuilding` | 10 | `dimx`, `dimz`, `buildings` |
| `citystyle` | 6 | `inherit`, `style`, the block groups, and the selectors |
| `style` | 6 | `randompalettes` |
| `condition` | 3 | `values` |
| `worldstyle` | 2 | `outsidestyle`, `citystyles` |
| `city` | 0 | A predefined city. Supported, and the mod ships none |
| `sphere` | 0 | A predefined sphere. Supported, and the mod ships none |
[code review](../examples/claim-tests.md#f12-2){.v .v-c}

Five datapack-era types have no equivalent here at all: `variant`, `scattered`, `stuff`, and the separate predefined city and sphere registries. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## Where the shipped content lives

Ten files inside the jar, under `assets/lostcities/citydata/`: [code review](../examples/claim-tests.md#f12-3){.v .v-c}

| File | Holds |
|---|---|
| `library.json` | Most of it. Buildings, multi-buildings, city styles, world styles, and many parts and palettes |
| `buildingparts.json` | Parts, and the largest file at about 320 KB |
| `palette.json` | Styles and palettes |
| `palette_desert.json`, `palette_chisel.json`, `palette_chisel_desert.json` | Palette and style variants |
| `railparts.json`, `highwayparts.json`, `monorailparts.json` | Infrastructure parts |
| `conditions.json` | The three conditions |
[code review](../examples/claim-tests.md#f12-3){.v .v-c}

Reading `library.json` is the fastest way to learn the format, because it holds one of nearly everything. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## A city style keeps its selectors flat

This is the difference most likely to catch someone moving between eras. A datapack city style nests its selectors under `selectors` and names each entry's target `value`. A file-era city style puts them at the top level and names each entry after its own type. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

```json title="File era: flat, and the entry key is the type"
{
  "type": "citystyle",
  "name": "citystyle_common",
  "inherit": "citystyle_config",
  "streetblocks": { "border": "y", "wall": "w", "street": "S" },
  "buildings": [ { "factor": 0.4, "building": "building1" } ],
  "multibuildings": [ { "factor": 0.3, "multibuilding": "multi1" } ]
}
```

```json title="Datapack era, for comparison"
{
  "selectors": {
    "buildings": [ { "factor": 0.4, "value": "building1" } ]
  }
}
```

The block groups themselves survived: `streetblocks`, `parkblocks`, `corridorblocks`, `railblocks` and `sphereblocks` carry the same character keys in both eras. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## A palette entry

Eight keys appear across the 36 shipped palettes, counted by how often each is used: [code review](../examples/claim-tests.md#f12-2){.v .v-c}

| Key | Uses | Meaning |
|---|---|---|
| `char` | 202 | The character this entry defines |
| `block` | 175 | One block, in `modid:name@meta` form |
| `damaged` | 79 | What the block becomes in the rubble band |
| `blocks` | 25 | A weighted list, each entry `{random, block}` |
| `frompalette` | 2 | An alias to another character |
| `mob` | 2 | Names a Condition rather than an entity |
| `facing` | 1 | A facing value |
| `loot` | 1 | Names a Condition rather than a loot table |
[code review](../examples/claim-tests.md#f12-2){.v .v-c}

`variant`, `tag` and `torch` do not exist here. They are datapack-era additions. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

!!! danger "Every block name carries a `@meta` suffix"
    `minecraft:rail@1`, `minecraft:golden_rail@8`, `minecraft:rail@6`. This is Minecraft before the 1.13 flattening, where a block plus a metadata number identified a state. [code review](../examples/claim-tests.md#f12-7){.v .v-c}

    Moving one of these palettes to a modern version means rewriting every block name. Leaving a single `@` behind fails the **whole palette**, not that one entry, because the name reaches `ResourceLocation` whose path rejects `@`. A leftover of exactly this kind still ships in 7.4.12. [code review](../examples/claim-tests.md#f12-7){.v .v-c} [game test](../examples/claim-tests.md#prf-1){.v .v-g}

## A part

Same idea as the datapack era: `xsize`, `zsize`, and `slices` holding one entry per Y layer, each a list of strings. A part may carry a `palette` of its own and a `meta` list. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

`meta` entries are a `key` plus exactly one typed value, and three types are used across the shipped parts: `boolean` 17 times, `char` 8 times, `integer` 8 times. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## A world style selects on plain biome names

```json
{
  "type": "worldstyle",
  "name": "standard",
  "outsidestyle": "outside",
  "citystyles": [
    { "factor": 0.5, "citystyle": "citystyle_standard" },
    { "factor": 9.0, "citystyle": "citystyle_desert",
      "biomes": ["desert", "desert_hills", "mesa", "mesa_rock", "mesa_clear_rock"] }
  ]
}
```

`biomes` here is a flat list of bare biome names. It is not a [Matcher](../concepts/matchers.md) object, it takes no `if_any` or `excluding`, and the names carry no namespace. Tags are not available. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## A condition

```json
{
  "type": "condition",
  "name": "easymobs",
  "values": [
    { "factor": 1, "value": "Zombie" },
    { "factor": 1, "value": "Skeleton" },
    { "factor": 1, "value": "Spider" }
  ]
}
```

A weighted table, the same idea as the datapack era. The values are old-style capitalised entity names rather than resource locations. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## A multi-building

```json
{
  "type": "multibuilding",
  "name": "library",
  "dimx": 2, "dimz": 2,
  "buildings": [["library00", "library01"], ["library10", "library11"]]
}
```

The naming convention in the shipped content is `<name><x><z>`, which matches the datapack era's grid order of `buildings[x][z]`, outer list X. [code review](../examples/claim-tests.md#f12-2){.v .v-c} [game test](../examples/claim-tests.md#cty-1){.v .v-g}

## See also

- [The File-Asset Era](index.md)
- [Adding Your Own Content](adding-content.md) <!-- noclaim -->
