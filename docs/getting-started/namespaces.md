---
claims: verified
---

# Namespaces

!!! tip "TL;DR"
    Every Lost Cities asset has a full name, `namespace:path`. Leave the namespace off when *referencing* something and the mod reads it as `lostcities:`. A reference that lands in a namespace where nothing is registered does not fall back and does not pass quietly: it throws, and where the throw lands decides whether you lose one chunk or the whole server.

Every claim on this page carries a chip saying how it was checked. Follow the chip for the evidence.

## What a name is

A resource location, `namespace:path`. Examples:

- `minecraft:stone`
- `lostcities:standard` (the built-in world style)
- `apocalypse:wasteland_city` (a custom world style in your own namespace)

File location decides the name. A file at:

```
data/apocalypse/lostcities/worldstyles/wasteland_city.json
```

registers as `apocalypse:wasteland_city`. The folder right after `data/` **is** the namespace. [game test](../examples/claim-tests.md#ns-1){.v .v-g} [code review](../examples/claim-tests.md#ns-1){.v .v-c}

### The exact folder layout

Lost Cities assets are datapack registries, so the path is always:

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

**Rule of thumb:** if your file lives under `data/lostcities/...`, you can reference it bare. If it lives under `data/<your namespace>/...`, you must include that namespace everywhere you reference it.

## What a reference into the wrong namespace actually does

It throws. Every lookup, including the ones whose method name suggests otherwise, ends in the same place: the registry is asked for the name, returns nothing, and the asset constructor is handed that nothing and fails. The failure comes back as:

```
java.lang.RuntimeException: Error getting resource lostcities:wasteland_city!
Caused by: java.lang.NullPointerException: Cannot invoke
    "mcjty.lostcities.worldgen.lost.regassets.WorldStyleRE.getRegistryName()"
    because "object" is null
```

[code review](../examples/claim-tests.md#ns-4){.v .v-c} [game test](../examples/claim-tests.md#ns-4){.v .v-g}

What you see depends only on **when** the reference is first needed:

| Reference | First read | Result |
|---|---|---|
| A profile's `worldStyle` | Building the dimension, before any chunk exists | **Server crash** on the first chunk generated, reported as `Feature placement` [game test](../examples/claim-tests.md#ns-5){.v .v-g} |
| A part name in a building's `parts` | The floor loop, every time that building is considered | Chunks around the building fail and generate empty, logged as `Error generating chunk` [game test](../examples/claim-tests.md#ns-6){.v .v-g} |
| A building's or part's `refpalette` | Only when a character has to be resolved out of *that* palette | Nothing at all, if every part carries its own palette. The building still generates [game test](../examples/claim-tests.md#ns-7){.v .v-g} |

That last row is the one that costs an evening. A bare `refpalette` on a building whose parts each declare their own `refpalette` generated a complete, correct tower, and surfaced only as two unrelated-looking chunk failures elsewhere in the city. Give the same building a part with no palette of its own and it disappears. [game test](../examples/claim-tests.md#ns-7){.v .v-g}

!!! warning "The message names the resolved name, not what you typed"
    `Error getting resource lostcities:wasteland_city!` is what a missing namespace looks like. If you did not expect to see `lostcities:` in front of your own asset's name, the reference that produced it was written bare. [game test](../examples/claim-tests.md#ns-4){.v .v-g}

## A worked example

A profile is a config file, not a datapack file, so it has no namespace of its own. It is named by its file name and it lives outside `data/` entirely. The `worldStyle` value inside it is the point where config crosses into datapack space, and that value **is** a namespaced reference.

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

    Put your file under your own namespace:

    ```
    data/apocalypse/lostcities/worldstyles/wasteland_city.json
    ```

    Nothing collides. But **every reference to it, everywhere, needs the full `apocalypse:wasteland_city` name.**

=== "Override the defaults"

    Put your file at the **exact same path** as a built-in one:

    ```
    data/lostcities/lostcities/worldstyles/standard.json
    ```

    Your version replaces the mod's shipped one entirely. Simple, but global: anything else that expects the original `lostcities:standard` behaviour gets your version instead.

Most modpacks should default to their own namespace. Override only when you deliberately want to replace a specific built-in.

### How an override resolves

Ordinary datapack rules, with one consequence worth spelling out:

- The pack **latest in load order wins**, and it wins **whole file**. There is no key-by-key merging between two files with the same name, unlike block tags (which do merge) or a city style's own [`inherit`](../reference/citystyle.md#inheritance) (which merges within one file's chain).
- So overriding `citystyle_config` to change one setting means restating everything else that file contained, not just the key you care about.
- Nothing warns you when an override happens. The losing file is simply never seen.

[unverified](../examples/claim-tests.md#ns-9){.v .v-u}

!!! warning "`/reload` does not pick up Lost Cities asset changes"
    These registries are read **once, when the world loads**. In 7.4.12 the mod registers no reload listener, and vanilla does not reload datapack registries on `/reload` either. Editing a part or palette and running `/reload` changes nothing. [code review](../examples/claim-tests.md#ns-10){.v .v-c}

    In single player, leaving the world and rejoining does clear the mod's asset cache, so the next chunks generated use your edits. On a dedicated server it takes a full server restart. See [Seeing your changes](../tooling/commands.md#seeing-your-changes). [code review](../examples/claim-tests.md#ns-10){.v .v-c}

## See also

- [Your First Custom City](first-city.md) for these paths in a working datapack
- [KubeJS Integration](../advanced/kubejs.md) for the same rules under `kubejs/data/`
- [Glossary](../glossary.md) for `namespace`, `resource location`, and `registry` if any of those were new.
