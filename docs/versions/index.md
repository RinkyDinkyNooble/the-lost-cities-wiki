---
claims: verified
---

# Versions

The mod has run on Minecraft 1.11.2 through Minecraft 26.1, across two mod loaders
and three asset systems. A file that works on one of them can be meaningless on
another. [code review](../examples/claim-tests.md#key-1){.v .v-c}

This page states which version you have, what its asset system is, and which pages
of this wiki apply. Every number comes from the jar itself; the method is in
[How these versions were checked](#how-these-versions-were-checked). [code review](../examples/claim-tests.md#key-1){.v .v-c}

## The short answer

| You are on [code review](../examples/claim-tests.md#key-1){.v .v-c} | Read |
|---|---|
| 7.4.12, Minecraft 1.20.1 | This wiki, as written. It is the documented version. |
| 7.5.0 or later on Minecraft 1.20.1 | This wiki, plus [What changed in 7.5](7-5.md). Read that page first. |
| 8.4.1 or later on Minecraft 1.21 or later | This wiki, plus [What changed in 7.5](7-5.md), plus [The NeoForge line](neoforge.md). |
| 8.2.2 on Minecraft 1.21 | This wiki. Ignore the 7.5 page. See [The NeoForge line](neoforge.md). |
| 5.3.29 through 6.2.3 | Most of this wiki. Some keys do not exist yet. See [Key availability](#key-availability). |
| Anything before 5.3.29 | Almost none of it. See [The file-asset era](legacy.md). |

## The boundary that matters

The mod changed how it loads city assets in **5.3.29**, and that one change decides
whether this wiki applies at all. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| [code review](../examples/claim-tests.md#key-1){.v .v-c} | Before 5.3.29 | 5.3.29 and later |
|---|---|---|
| Where assets live | `assets/lostcities/citydata/*.json` inside the jar | `data/<namespace>/lostcities/<type>/<name>.json` in a datapack |
| How you add your own | One combined file, `config/lostcities/userassets.json` | One file per asset, in a datapack |
| Loader class | `AbstractAssetRegistry` | `RegistryAssetRegistry` |
| This wiki applies | No | Yes |

Everything this wiki documents about buildings, parts, palettes, city styles and
world styles describes the datapack system. On an earlier version those files are
never read. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Version matrix

The Minecraft version below is the label the author put in the file name. The
loader requirement is what the jar declares in its own metadata. [code review](../examples/claim-tests.md#key-1){.v .v-c}

!!! note "One jar often runs on more than one Minecraft release"
    A jar declares a loader range, not a Minecraft range. Which Minecraft versions
    a release supports lives on CurseForge rather than inside the file, and this
    table reports only what the file states. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Mod version [code review](../examples/claim-tests.md#key-1){.v .v-c} | Label | Loader requirement | Asset system | Profile keys | Datapack keys |
|---|---|---|---|---|---|
| 1.0.2 | 1.1x | Forge, Minecraft 1.11.2 | File | 72 | 0 |
| 1.0.1 | 1.12 | Forge, Minecraft 1.12.2 | File | 71 | 0 |
| 1.0.2 | 1.12 | Forge, Minecraft 1.12.2 | File | 72 | 0 |
| 2.0.22 | 1.12 | Forge, Minecraft 1.12.2 | File | 116 | 0 |
| 2.0.28-alpha | 1.14 | Forge `[28,)`, Minecraft `[1.14]` | File | 131 | 0 |
| 3.0.2-alpha | 1.15 | Forge `[31,)` | File | 131 | 0 |
| 4.0.5-alpha | 1.16 | Forge `[31,)` | File | 132 | 0 |
| 4.0.12-beta | 1.16 | Forge `[31,)` | File | 132 | 0 |
| 5.0.4 | 1.18 | Forge `[31,)` | File | 132 | 0 |
| 5.3.29 | 1.18 | Forge `[40.1.50,)` | Datapack | 111 | 196 |
| 6.0.3 | 1.19 | Forge `[31,)` | Datapack | 111 | 180 |
| 6.1.6 | 1.19.3 | Forge `[43.1.30,)` | Datapack | 107 | 196 |
| 6.2.2 | 1.19 | Forge `[43.1.30,)` | Datapack | 110 | 200 |
| 6.2.3 | 1.19.4 | Forge `[43.1.30,)` | Datapack | 107 | 196 |
| **7.4.12** | **1.20** | **Forge `[47,)`** | **Datapack** | **131** | **224** |
| 7.5.1 | 1.20 | Forge `[47,)` | Datapack, hierarchical roads | 160 | 231 |
| 8.2.2 | 1.21 | NeoForge `[21.0,)` | Datapack | 114 | 201 |
| 8.4.1 | 1.21 | NeoForge `[21.0,)` | Datapack, hierarchical roads | 160 | 231 |
| 9.5.1 | 1.21.11 | NeoForge `[21.11,)` | Datapack, hierarchical roads | 160 | 231 |
| 10.0.1 | 26.1.2 | NeoForge `[26.1.2.0-beta,)` | Datapack, hierarchical roads | 160 | 231 |

The bold row is the version this wiki documents. <!-- noclaim -->

!!! warning "A higher mod version does not always mean a newer feature set"
    8.2.2 has a higher mod version than 7.5.1 and does **not** have the hierarchical
    road system 7.5.1 has. The 1.20 line and the 1.21 line advanced in parallel, so
    compare the asset system column rather than the version number. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Loader

Minecraft 1.21 and later require **NeoForge**. There is no Forge build. The change
happens at mod version 8.0 and it does not go both ways: a NeoForge jar does not
load on Forge, and a Forge jar does not load on NeoForge. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Mod versions | Loader |
|---|---|
| 1.0.1 through 7.5.1 | Forge |
| 8.2.2 and later | NeoForge |
[code review](../examples/claim-tests.md#key-1){.v .v-c}

## Key availability

The datapack asset format is not fixed across the datapack era. Key counts by
version: [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Version [code review](../examples/claim-tests.md#key-1){.v .v-c} | Datapack keys | Against 7.4.12 |
|---|---|---|
| 5.3.29 | 196 | 28 fewer |
| 6.0.3 | 180 | 44 fewer |
| 6.1.6 | 196 | 28 fewer |
| 6.2.2 | 200 | 24 fewer |
| 6.2.3 | 196 | 28 fewer |
| 7.4.12 | 224 | documented baseline |
| 7.5.1 | 231 | 7 more |
| 8.2.2 | 201 | 23 fewer |
| 8.4.1, 9.5.1, 10.0.1 | 231 | 7 more |

A key used on a version that predates it is **ignored**, not rejected. The file
loads, nothing is logged, and the behaviour that key asked for never happens. That
is quieter than a load failure and harder to spot. See
[Key availability](key-availability.md#what-happens-when-a-key-does-not-exist). [game test](../examples/claim-tests.md#key-2){.v .v-g}

## One reference covers 7.5.1 through 10.0.1

The datapack format and the profile keys stopped changing after 7.5.1, compared by
diffing the full key sets rather than reading release notes. [code review](../examples/claim-tests.md#key-1){.v .v-c}

- **Profile keys.** 7.5.1, 8.4.1, 9.5.1 and 10.0.1 declare the same 160 keys, with
  identical types, defaults, minimums and maximums. Zero differences.
- **Datapack keys.** The same 231 keys, with the same required or optional status on
  each. The only change is a Java class rename in 9.5.1, from
  `ResourceLocationMatcher` to `IdentifierMatcher`. The JSON keys that class carries,
  `if_any` and `excluding`, are unchanged. [code review](../examples/claim-tests.md#key-1){.v .v-c}

As far as the asset format goes, a datapack written for 7.5.1 on Minecraft 1.20.1
loads unchanged on 10.0.1 on Minecraft 26.1. Block names inside the palettes are a
separate problem, because Minecraft renames blocks between releases. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## The config file moved in 4.0.5

| Versions [code review](../examples/claim-tests.md#key-1){.v .v-c} | Path |
|---|---|
| 2.0.28 and 3.0.2 | `config/lostcities-common.toml` |
| 4.0.5 and later | `config/lostcities/common.toml` |

The older path still turns up in support threads and guides, and has been wrong
since Minecraft 1.16. Every version this wiki covers uses
`config/lostcities/common.toml`, which holds three keys. See
[Configuration](../reference/config.md). [game test](../examples/claim-tests.md#cfg-1){.v .v-g}

## How these versions were checked

Every jar was disassembled with `javap` and the numbers read from the mod's own
constants rather than from documentation. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Number [code review](../examples/claim-tests.md#key-1){.v .v-c} | Source |
|---|---|
| Profile keys | Each `Configuration.get*` registration call in `LostCityProfile`. Up to 2.0.22 that is Forge's own config class, writing `lostcities.cfg`. From 2.0.28 it is the mod's class, writing a `.toml` file. |
| Datapack keys | Each `fieldOf` and `optionalFieldOf` call in the asset codecs. |
| Loader requirement | `META-INF/mods.toml` or `META-INF/neoforge.mods.toml`. |
| Asset system | Presence of `RegistryAssetRegistry` against `AbstractAssetRegistry`. |

`pack.mcmeta` is **not** used. The mod left its `pack_format` at 6 from Minecraft
1.16 through Minecraft 1.19, so that number cannot date a jar. [code review](../examples/claim-tests.md#key-1){.v .v-c}
