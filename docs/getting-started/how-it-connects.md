---
claims: verified
---

# How It All Connects

!!! tip "TL;DR"
    A dimension points at a **profile** (config). A profile picks a **world style** (datapack). A world style picks **city styles**, which pull in **buildings, parts, and palettes**. A wrong name anywhere along that chain throws, and how badly depends on where in it you were. [game test](../examples/claim-tests.md#ns-4){.v .v-g} [code review](../examples/claim-tests.md#ns-4){.v .v-c}

Asset files have no effect until the active profile references a world style that reaches them. This page documents that chain. The official documentation describes the asset types individually rather than the dependency between them. <!-- noclaim -->

## The three layers

| Layer | Where it lives | What it does |
|---|---|---|
| **Content** | `data/<namespace>/lostcities/` | Your buildings, parts, palettes, city styles, world styles. Loaded as normal datapack JSON. See [Namespaces](namespaces.md#the-exact-folder-layout) for the exact layout [game test](../examples/claim-tests.md#ns-2){.v .v-g} |
| **Profile** | `config/lostcities/profiles/<name>.json` | Picks *one* world style. Also holds the behaviour settings: city frequency, building height, ruin damage, landscape type. 131 keys in 7.4.12, 160 from 7.5.0 onward [code review](../examples/claim-tests.md#hic-1){.v .v-c} |
| **Dimension wiring** | `config/lostcities/common.toml` | One line mapping a dimension to a profile by name. This is the actual switch [code review](../examples/claim-tests.md#cfg-4){.v .v-c} |

```toml title="config/lostcities/common.toml"
dimensionsWithProfiles = [
    "lostcities:lostcity=biosphere",
    "lostworlds:abyss=biosphere_caves"
]
```

Format: `<dimension id>=<profile name>`. Change this line and that dimension starts using a different profile, which points at a different world style, which pulls in different city styles, buildings, and palettes. See [Configuration](../reference/config.md#dimensionswithprofiles-in-detail) for what happens when either side is wrong. [code review](../examples/claim-tests.md#cfg-4){.v .v-c}

**Full chain:** <!-- noclaim -->

```
dimension → profile (config) → world style name → World Style (datapack) → city styles → buildings, parts, palettes
```

Everything left of "World Style" is config. Everything right of it is the content this wiki's reference section covers. The profile's `worldStyle` value is the join, and it is the one reference in the chain that takes a namespace. [game test](../examples/claim-tests.md#ns-5){.v .v-g} [code review](../examples/claim-tests.md#ns-8){.v .v-c}

!!! tip "Fastest way to test"
    Copy an existing profile, change its `worldStyle` key, point `dimensionsWithProfiles` at your copy. No need to touch datapack content just to check the wiring works. <!-- noclaim -->

## Profiles: read the built-in ones first

The mod writes its built-in profiles to `config/lostcities/profiles/`, 17 files in 7.4.12, then reads back whatever is in that folder. They are live files the mod ships and maintains, not examples left for you to edit. [game test](../examples/claim-tests.md#hic-2){.v .v-g} [code review](../examples/claim-tests.md#hic-2){.v .v-c}

!!! danger "Do not edit them in place, your changes will vanish"
    That write happens on **every launch**, not just the first, and it overwrites unconditionally. Any edit to `wasteland.json`, `default.json`, or any other shipped profile is silently gone next time the game starts. [code review](../examples/claim-tests.md#cfg-7){.v .v-c}

    Files the mod does not ship are read and left alone, so **always use your own file name**. `/lostcities saveprofile <name>` is the intended way to get a fully populated starting point. [code review](../examples/claim-tests.md#cfg-7){.v .v-c}

Four worth opening first, because each one changes something different: [game test](../examples/claim-tests.md#hic-2){.v .v-g}

- **wasteland**: no water, high ruin chance
- **atlantis**: drowned cities, sea level raised
- **biosphere**: jungle in glass domes on barren land
- **space**: glass bubbles floating in a void [game test](../examples/claim-tests.md#hic-2){.v .v-g}

Three of the 17 set `"public": false` and do not appear in the in-game selector: `bio_wasteland` and `void_outside`, which only define what generates *outside* the glass spheres in sphere-based profiles, and `biosphere_caves`, which is a full profile wired to a Lost Worlds dimension rather than chosen by hand. A spheres profile of your own will likely want a private outside-profile too. [game test](../examples/claim-tests.md#hic-2){.v .v-g}

!!! note "An eighteenth profile exists with no file"
    `customized` is a standard profile the write loop skips, so it never appears in the folder while still being a name `dimensionsWithProfiles` accepts. It is what the world creation screen's customise button writes into. [code review](../examples/claim-tests.md#cfg-7){.v .v-c} [game test](../examples/claim-tests.md#hic-2){.v .v-g}

## Attaching to a world: two options

=== "Dedicated dimension"

    The mod ships its own dimension, `lostcities:lostcity`. Its terrain is ordinary vanilla noise using the `minecraft:overworld` settings, not a generator of the mod's own, and Lost Cities is added to it as a feature exactly as it is added to a normal world. Clean if you want cities kept separate. [code review](../examples/claim-tests.md#lw-1){.v .v-c}

    **Getting players in and out**: the mod includes its own two-way gateway, no portal item or command needed. A bed sitting on the block named by `specialBedBlock`, surrounded by skull blocks on both sides and both far corners (any skull type), works as a sleep-to-teleport gateway. Sleeping in it while in the Lost Cities dimension sends you to the Overworld; sleeping in it anywhere else sends you into the Lost Cities dimension, which must already be loaded on the server. That block is [a per-world config key](../reference/config.md#lostcities-servertoml), not a profile key, and it defaults to `minecraft:diamond_block`. [code review](../examples/claim-tests.md#hic-3){.v .v-c}

=== "Inject into the existing world"

    Two Forge biome modifiers ship with the mod, each adding a Lost Cities feature to every biome in `#minecraft:is_overworld`. No custom dimension needed. This is almost certainly what you want if the goal is "ruined cities in my normal world" rather than "a separate dimension players travel to". [code review](../examples/claim-tests.md#hic-4){.v .v-c}

    | Modifier | Feature | Generation step |
    |---|---|---|
    | `lostcities:lostcities` | `lostcities:lostcities` | `raw_generation` |
    | `lostcities:lostcity_spheres` | `lostcities:spheres` | `top_layer_modification` |
    [code review](../examples/claim-tests.md#hic-4){.v .v-c}

## Landscape type needs a matching terrain mod

A profile's landscape type (`floating`, `space`, `cavern`, and the rest) says what terrain the mod should **expect** underneath, not what it should build. Lost Cities ships no chunk generator: its own dimension is vanilla noise terrain with the overworld settings, and every landscape branch in the generator reads the existing heightmap and adapts to it. [code review](../examples/claim-tests.md#lw-1){.v .v-c}

Making the terrain match is **Lost Worlds**, a separate mod by the same author, so anything but the default landscape means pairing both. Set `floating` without it and cities are placed by floating-island rules on ground that is not floating. [code review](../examples/claim-tests.md#lw-1){.v .v-c}

## See also

- [Configuration](../reference/config.md) for the three files these settings are split across
- [Your First Custom City](first-city.md) for the whole chain above, built one file at a time
- [Namespaces](namespaces.md) for how a name like `worldStyle` actually resolves
- [Glossary](../glossary.md) for quick definitions of any term above <!-- noclaim -->
