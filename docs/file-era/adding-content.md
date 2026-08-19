---
claims: verified
---

# Adding Your Own Content

!!! tip "TL;DR"
    Write your assets into `config/lostcities/userassets.json`, which the mod already loads and loads **last**. Anything you define there with the same type and name as something the mod ships replaces it. [code review](../examples/claim-tests.md#f12-3){.v .v-c} [code review](../examples/claim-tests.md#f12-4){.v .v-c}

## The load list

The set of asset files is a config option, not a fixed list. `general.cfg` describes it in the mod's own words: [code review](../examples/claim-tests.md#f12-3){.v .v-c}

> List of asset libraries loaded in the specified order. If the path starts with '/' it is going to be loaded directly from the classpath. If the path starts with '$' it is loaded from the config directory [code review](../examples/claim-tests.md#f12-3){.v .v-c}

The first character of each entry decides where it is read from: [code review](../examples/claim-tests.md#f12-3){.v .v-c}

| Prefix | Resolved as | Example |
|---|---|---|
| `/` | A resource inside a jar, through `getResourceAsStream` | `/assets/lostcities/citydata/library.json` |
| `$` | The config directory, plus the rest of the path | `$lostcities/userassets.json` becomes `config/lostcities/userassets.json` |
| anything else | Nothing. The mod throws `Invalid path for lostcity resource in 'assets' config!` | |
[code review](../examples/claim-tests.md#f12-3){.v .v-c}

A path with no prefix is a hard failure at startup rather than a skipped entry, so a plain `userassets.json` without the `$` stops the game. [code review](../examples/claim-tests.md#f12-3){.v .v-c}

## Where your file goes

The default list is the mod's ten files in a fixed order, with one config entry after them: [game test](../examples/claim-tests.md#f12-8){.v .v-g}

```title="general.cfg, S:assets, exactly as a first launch writes it"
/assets/lostcities/citydata/conditions.json
/assets/lostcities/citydata/palette.json
/assets/lostcities/citydata/palette_desert.json
/assets/lostcities/citydata/palette_chisel.json
/assets/lostcities/citydata/palette_chisel_desert.json
/assets/lostcities/citydata/highwayparts.json
/assets/lostcities/citydata/railparts.json
/assets/lostcities/citydata/monorailparts.json
/assets/lostcities/citydata/buildingparts.json
/assets/lostcities/citydata/library.json
$lostcities/userassets.json
```

So `config/lostcities/userassets.json` is already wired and already last. Creating it is the whole setup step, and the file is an array in the same [shape as any other](assets.md#the-shape-of-a-file): [code review](../examples/claim-tests.md#f12-3){.v .v-c}

```json title="config/lostcities/userassets.json"
[
  {
    "type": "palette",
    "name": "mypalette",
    "palette": [
      { "char": "#", "block": "minecraft:concrete@8" },
      { "char": "_", "block": "minecraft:air" }
    ]
  },
  {
    "type": "part",
    "name": "mytower",
    "xsize": 16, "zsize": 16,
    "palette": "mypalette",
    "slices": [ ]
  }
]
```

Adding a further file means adding an entry to `assets`, and its position in the list is what decides who wins a collision. [code review](../examples/claim-tests.md#f12-3){.v .v-c}

## Overriding something the mod ships

Each asset is stored under its name, and a later load of the same name replaces the earlier one. Since `userassets.json` sits last, defining `citystyle_common` there gives you the mod's city style with your version in its place. [code review](../examples/claim-tests.md#f12-4){.v .v-c}

The replacement is the **whole asset**, not a merge of keys, so an override has to restate everything the original held that you still want. [code review](../examples/claim-tests.md#f12-4){.v .v-c}

That is the entire override mechanism. There is no namespace to avoid a collision with and no pack ordering, only position in one config list. [code review](../examples/claim-tests.md#f12-4){.v .v-c}

## Config, and one file per profile

The config is Forge's old `.cfg`, not TOML, and a profile is a whole file rather than a JSON object: [code review](../examples/claim-tests.md#f12-5){.v .v-c}

| Path | Holds |
|---|---|
| `config/lostcities/general.cfg` | 14 options, including the three below |
| `config/lostcities/profile_<name>.cfg` | One profile. **128 keys** in 2.0.22, against 131 in 7.4.12. 18 files ship, 16 public and 2 private |
| `config/lostcities/userassets.json` | Your assets |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

Every key of a profile is on its own page: [File-Era Profile Reference](profile.md). [game test](../examples/claim-tests.md#f12-8){.v .v-g}

Three options in `general.cfg` decide what exists at all: [code review](../examples/claim-tests.md#f12-5){.v .v-c}

| Option | What it does |
|---|---|
| `assets` | The load list above |
| `profiles` | Which profiles the world creation screen offers. The mod warns that one of them must be `default` |
| `privateProfiles` | Profiles a player cannot pick, used only as another profile's child |
[code review](../examples/claim-tests.md#f12-5){.v .v-c}

A new profile therefore takes two steps rather than one: write `profile_<name>.cfg`, then add that name to `profiles`. Writing the file alone leaves it unoffered. [code review](../examples/claim-tests.md#f12-5){.v .v-c}

!!! danger "The dimension wiring uses a colon, not an equals"
    The option is `additionalDimensions` in the `general` category, and its format is `'<id>:<profile>'`. The id is a **number**: `general.cfg` ships `dimensionId=111`, because 1.12 identifies a dimension by integer rather than by resource location. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

    The datapack era's `dimensionsWithProfiles` uses `<dimension id>=<profile name>` instead. Carrying the `=` backwards gives an entry that does not parse, and carrying the `:` forwards does the same. [code review](../examples/claim-tests.md#f12-6){.v .v-c} [code review](../examples/claim-tests.md#cfg-4){.v .v-c}

## Moving content to a modern version

The concepts carry over. The files do not, and renaming will not do it. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

| What has to change | From | To |
|---|---|---|
| File layout | One array holding many assets | One file per asset |
| Naming | A `name` key | The file path |
| Type | A `type` key | The folder |
| Block names | `minecraft:rail@1` | `minecraft:rail[shape=north_south]` |
| References | Bare names | `namespace:path`, or bare meaning `lostcities:` |
| City style selectors | Flat, entry key is the type | Nested under `selectors`, entry key is `value` |
| Biome selection | A flat list of bare names | A [Matcher](../concepts/matchers.md) taking tags |
[code review](../examples/claim-tests.md#f12-2){.v .v-c} [code review](../examples/claim-tests.md#f12-7){.v .v-c}

The block names are the part that fails loudest. A single `@` left behind takes the whole palette down rather than that one entry. [game test](../examples/claim-tests.md#prf-1){.v .v-g}

## See also

- [The File-Asset Era](index.md)
- [File-Era Assets](assets.md)
- [Namespaces](../getting-started/namespaces.md) for the system that replaced bare names <!-- noclaim -->
