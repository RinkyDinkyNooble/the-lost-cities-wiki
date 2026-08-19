---
claims: verified
---

# Namespaces

!!! tip "TL;DR"
    Every Lost Cities asset has a full name, `namespace:path`. Leave the namespace off when *referencing* something and the mod reads it as `lostcities:`. A reference that lands in a namespace where nothing is registered does not fall back and does not pass quietly: it throws, and where the throw lands decides whether you lose one chunk or the whole server. [game test](../examples/claim-tests.md#ns-4){.v .v-g} [code review](../examples/claim-tests.md#ns-4){.v .v-c}

Every claim on this page carries a chip saying how it was checked. Follow the chip for the evidence. <!-- noclaim -->

## What a name is

An asset name is a resource location, `namespace:path`. [code review](../examples/claim-tests.md#ns-1){.v .v-c}

- `minecraft:stone`
- `lostcities:standard` (the built-in world style)
- `apocalypse:wasteland_city` (a custom world style in your own namespace) [code review](../examples/claim-tests.md#ns-1){.v .v-c}

File location decides the name. The folder right after `data/` **is** the namespace, so a file at `data/apocalypse/lostcities/worldstyles/wasteland_city.json` registers as `apocalypse:wasteland_city`. [game test](../examples/claim-tests.md#ns-1){.v .v-g} [code review](../examples/claim-tests.md#ns-1){.v .v-c}

### The exact folder layout

Lost Cities assets are datapack registries, so the path is always the same four segments. [code review](../examples/claim-tests.md#ns-2){.v .v-c}

```
data/<your namespace>/lostcities/<asset type>/<name>.json
     └── becomes the      └── fixed, this is  └── buildings, parts, palettes,
         namespace            the registry's      citystyles, worldstyles,
                              own namespace       styles, variants, conditions,
                                                  multibuildings, scattered,
                                                  stuff, predefinedcities,
                                                  predefinedspheres
```

The `lostcities` in the middle is **not** your namespace, it is part of the registry's identity, and it is there no matter whose pack the file is in. That is why the mod's own files sit at `data/lostcities/lostcities/parts/...`: the first `lostcities` is the pack, the second is the registry. Only the mod's own files get that doubled-up look. Yours will not. [game test](../examples/claim-tests.md#ns-2){.v .v-g} [code review](../examples/claim-tests.md#ns-2){.v .v-c}

## A bare name means `lostcities:`

Anywhere the mod expects a *name* (a profile's `worldStyle` key, a world style's list of city styles, a building's `refpalette`, and so on), the string is turned into a resource location by one rule: if it contains a colon it is parsed as written, and if it does not, the namespace becomes `lostcities`. There is no search across namespaces and no fallback to the pack the file came from. [code review](../examples/claim-tests.md#ns-3){.v .v-c} [game test](../examples/claim-tests.md#ns-3){.v .v-g}

```json title="Reads as lostcities:wasteland_city, whatever pack the file is in"
{
  "worldStyle": "wasteland_city"
}
```

```json title="Reads as apocalypse:wasteland_city"
{
  "worldStyle": "apocalypse:wasteland_city"
}
```

**Rule of thumb:** a file under `data/lostcities/...` can be referenced bare. A file under `data/<your namespace>/...` needs that namespace everywhere it is referenced. [code review](../examples/claim-tests.md#ns-3){.v .v-c}

## What a reference into the wrong namespace actually does

It throws. Every lookup, including the ones whose method name suggests otherwise, ends in the same place: the registry is asked for the name, returns nothing, and the asset constructor is handed that nothing and fails. [code review](../examples/claim-tests.md#ns-4){.v .v-c} [game test](../examples/claim-tests.md#ns-4){.v .v-g}

```
java.lang.RuntimeException: Error getting resource lostcities:wasteland_city!
Caused by: java.lang.NullPointerException: Cannot invoke
    "mcjty.lostcities.worldgen.lost.regassets.WorldStyleRE.getRegistryName()"
    because "object" is null
```

What you see depends only on **when** the reference is first needed. [game test](../examples/claim-tests.md#ns-4){.v .v-g}

| Reference | First read | Result |
|---|---|---|
| A profile's `worldStyle` | Building the dimension, before any chunk exists | **Server crash** on the first chunk generated, reported as `Feature placement` [game test](../examples/claim-tests.md#ns-5){.v .v-g} |
| A part name in a building's `parts` | The floor loop, every time that building is considered | Chunks around the building fail and generate empty, logged as `Error generating chunk` [game test](../examples/claim-tests.md#ns-6){.v .v-g} |
| A building's or part's `refpalette` | Only when a character has to be resolved out of *that* palette | Nothing at all, if every part carries its own palette. The building still generates [game test](../examples/claim-tests.md#ns-7){.v .v-g} |

That last row is the one that costs an evening. A bare `refpalette` on a building whose parts each declare their own `refpalette` generated a complete, correct tower, and surfaced only as two unrelated-looking chunk failures elsewhere in the city. Give the same building a part with no palette of its own and it disappears. [game test](../examples/claim-tests.md#ns-7){.v .v-g}

!!! warning "The message names the resolved name, not what you typed"
    `Error getting resource lostcities:wasteland_city!` is what a missing namespace looks like. A `lostcities:` prefix in front of an asset that is not the mod's own means the reference that produced it was written bare. [game test](../examples/claim-tests.md#ns-4){.v .v-g}

## A worked example

A profile is a config file, not a datapack file, so it has no namespace of its own. It is named by its file name and it lives outside `data/` entirely. The `worldStyle` value inside it is the point where config crosses into datapack space, and that value **is** a namespaced reference. [code review](../examples/claim-tests.md#ns-8){.v .v-c}

```title="Two separate places, one reference between them"
config/lostcities/profiles/apocalypse.json
└── the profile is named after its file name: "apocalypse"

<world>/datapacks/apocalypse-pack/
├── pack.mcmeta
└── data/apocalypse/lostcities/
         │           └── the registry, fixed
         └── the namespace, yours to choose
    ├── worldstyles/wasteland.json    registers as apocalypse:wasteland
    └── citystyles/downtown.json      registers as apocalypse:downtown
```

```json title="config/lostcities/profiles/apocalypse.json"
{
  "lostcity": {
    "worldStyle": "apocalypse:wasteland"
  }
}
```

```json title="data/apocalypse/lostcities/worldstyles/wasteland.json"
{
  "outsidestyle": "outside",
  "citystyles": [
    { "factor": 1.0, "citystyle": "apocalypse:downtown" }
  ]
}
```

Two references, and both need the namespace. `"wasteland"` on the profile crashes the server on the first chunk. `"downtown"` inside the world style fails every chunk that tries to place a city. `"outside"` is correct bare, because `lostcities:outside` is a style the mod itself ships. [game test](../examples/claim-tests.md#ns-5){.v .v-g}

The profile's own file name never takes a namespace. `apocalypse.json` makes a profile called `apocalypse`, and `config/lostcities/common.toml` wires it to a dimension by that bare name. [code review](../examples/claim-tests.md#ns-8){.v .v-c}

## Two real strategies

=== "Use your own namespace"

    A file under your own namespace collides with nothing, and **every reference to it, everywhere, needs the full name.** [game test](../examples/claim-tests.md#ns-1){.v .v-g}

    ```
    data/apocalypse/lostcities/worldstyles/wasteland_city.json
    ```

=== "Override the defaults"

    A file at the **exact same path** as a built-in one replaces the mod's shipped version of it entirely, so anything expecting the original `lostcities:standard` behaviour gets yours instead. [game test](../examples/claim-tests.md#ns-9){.v .v-g}

    ```
    data/lostcities/lostcities/worldstyles/standard.json
    ```

Most modpacks are better off with their own namespace, and overriding is worth it only to replace a specific built-in deliberately. <!-- noclaim -->

### How an override resolves

The pack **latest in load order wins**, and it wins the **whole file**. Two packs were given the same palette, one of them defining an extra character the other did not, and the extra character did not survive into the result. Swapping which pack held which file flipped the outcome exactly, so it is position that decides rather than content. [game test](../examples/claim-tests.md#ns-9){.v .v-g}

That is different from how two other things in this system behave, and the difference catches people: [game test](../examples/claim-tests.md#ns-9){.v .v-g}

| | Merges | Replaces | [game test](../examples/claim-tests.md#ns-9){.v .v-g}
|---|---|---|
| Two datapacks, same asset name | | **yes, whole file** [game test](../examples/claim-tests.md#ns-9){.v .v-g} |
| Block tags | yes | |
| A city style's [`inherit`](../reference/citystyle.md#inheritance) chain | yes, within one file's chain | |
| A part palette over a building palette | yes, per character | [game test](../examples/claim-tests.md#pal-2){.v .v-g} |

So overriding `citystyle_config` to change one setting means restating everything else that file held, not only the key you came for. [game test](../examples/claim-tests.md#ns-9){.v .v-g}

!!! warning "Nothing tells you an override happened"
    The losing file is never seen and no message names it. In the test above, the only sign was one failed chunk reporting `Could not find entry 'M' in the palette for part '<part>'!`, which is the same message an ordinary undefined character produces. It names the character, not the collision that removed it. [game test](../examples/claim-tests.md#ns-9){.v .v-g}

!!! warning "`/reload` does not pick up Lost Cities asset changes"
    These registries are read **once, when the world loads**. In 7.4.12 the mod registers no reload listener, and vanilla does not reload datapack registries on `/reload` either. Editing a part or palette and running `/reload` changes nothing. [code review](../examples/claim-tests.md#ns-10){.v .v-c}

    In single player, leaving the world and rejoining does clear the mod's asset cache, so the next chunks generated use your edits. On a dedicated server it takes a full server restart. See [Seeing your changes](../tooling/commands.md#seeing-your-changes). [code review](../examples/claim-tests.md#ns-10){.v .v-c}

## See also

- [Your First Custom City](first-city.md) for these paths in a working datapack
- [KubeJS Integration](../advanced/kubejs.md) for the same rules under `kubejs/data/`
- [Glossary](../glossary.md) for `namespace`, `resource location`, and `registry` if any of those were new. <!-- noclaim -->
