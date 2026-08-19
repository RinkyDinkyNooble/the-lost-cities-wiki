---
claims: verified
---

# The NeoForge line

Minecraft 1.21 and later require **NeoForge**. There is no Forge build of the mod
for those versions and no way to load one. The switch happens at mod version 8.0. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Mod versions | Loader |
|---|---|
| 1.0.1 through 7.5.1 | Forge |
| 8.2.2 and later | NeoForge |
[code review](../examples/claim-tests.md#key-1){.v .v-c}

This page covers what a reader on 1.21 or later needs that the rest of the wiki
does not say. <!-- noclaim -->

!!! info "What 'unchanged' covers, and what it does not"
    The comparison below is of the **configuration and datapack surface**: profile
    key names, types, defaults, minimums and maximums, and datapack codec keys with
    their required or optional status. Those are machine-compared and identical. [code review](../examples/claim-tests.md#key-1){.v .v-c}

    Runtime behaviour on the NeoForge line **has** now been run, on 9.5.1 with
    NeoForge 21.11.45 and Minecraft 1.21.11. Four packs and 27 probes came back
    matching the Forge line at the same feature level, counts included. Versions
    8.2.2, 8.4.1 and 10.0.1 are still inferred from their key sets rather than run. [game test](../examples/claim-tests.md#neo-1){.v .v-g}

## The versions

| Version [code review](../examples/claim-tests.md#key-1){.v .v-c} | Label | Loader requirement | Has hierarchical roads |
|---|---|---|---|
| 8.2.2 | 1.21 | NeoForge `[21.0,)` | No |
| 8.4.1 | 1.21 | NeoForge `[21.0,)` | Yes |
| 9.5.1 | 1.21.11 | NeoForge `[21.11,)` | Yes |
| 10.0.1 | 26.1.2 | NeoForge `[26.1.2.0-beta,)` | Yes |

## 8.4.1 and later match 7.5.1 exactly

On 8.4.1, 9.5.1 or 10.0.1 the mod's configuration surface is identical to 7.5.1 on
Minecraft 1.20.1. [code review](../examples/claim-tests.md#key-1){.v .v-c}

Compared by extracting every key from each jar and diffing the complete sets. The
extraction is `docs/examples/mod-keys.json` and the comparison runs on every build,
so this claim fails the CI gate if it stops being true. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Surface | Result |
|---|---|
| Profile keys | The same 160 names, with identical types, defaults, minimums and maximums. Zero differences across 7.5.1, 8.4.1, 9.5.1 and 10.0.1 |
| Datapack keys | The same 231 keys, each required or optional in the same way |
[code review](../examples/claim-tests.md#key-1){.v .v-c}

Read this wiki, then [What changed in 7.5](7-5.md), and the picture is complete.
The hierarchical road system and its 29 profile keys are declared the same way
here. [code review](../examples/claim-tests.md#key-1){.v .v-c} [game test](../examples/claim-tests.md#neo-1){.v .v-g}

### The one internal rename

In 9.5.1 the class `ResourceLocationMatcher` became `IdentifierMatcher`. That is a
Java class name. The JSON keys it carries, `if_any` and `excluding`, did not change,
so no file needs editing. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## 8.2.2 is behind 7.4.12, not ahead of it

The version number is higher and the feature set is smaller. [code review](../examples/claim-tests.md#key-1){.v .v-c}

8.2.2 is missing **23 datapack keys** and **19 profile keys** that 7.4.12 has, and
adds none. It also still carries `libraryChance` and `dataCenterChance`, two profile
keys 7.4.12 had already dropped. [code review](../examples/claim-tests.md#key-1){.v .v-c}

!!! warning "A datapack written against this wiki loads on 8.2.2 and does less"
    23 of the keys this wiki documents do not exist there. They are **ignored**
    rather than rejected, so the pack loads, no message appears, and the behaviour
    those keys asked for never happens. Move to 8.4.1 or later, or check each key
    against the list below. [game test](../examples/claim-tests.md#key-2){.v .v-g} [code review](../examples/claim-tests.md#key-1){.v .v-c}

Datapack keys present in 7.4.12 and absent in 8.2.2: <!-- noclaim -->

| Asset [code review](../examples/claim-tests.md#key-1){.v .v-c} | Keys |
|---|---|
| Building | `overrideFloors` |
| Part reference | `belowpart` |
| Condition part | `belowpart` |
| World style | `settings` |
| World settings | `railpartheight6`, `railwayavoidance`, `vinenorth`, `vinesouth`, `vineeast`, `vinewest` |
| Park settings | `parkchance`, `parkborder`, `parkelevation`, `parkstreetthreshold`, `avoidfoliage` |
| Street settings | `frontchance`, `fountainchance` |
| Corridor settings | `corridorchance` |
| Object selector | `feather`, `minSpawnDistance`, `maxSpawnDistance` |
| Scattered building | `rotatable` |
| Scattered reference | `nearhighway` |

Profile keys present in 7.4.12 and absent in 8.2.2: [code review](../examples/claim-tests.md#key-1){.v .v-c}

`cityLevel4Height`, `cityLevel5Height`, `cityLevel6Height`, `cityLevel7Height`,
`citySpawnDistance1`, `citySpawnDistance2`, `citySpawnMultiplier1`,
`citySpawnMultiplier2`, `forceSpawnBuildings`, `forceSpawnParts`, `grid32`,
`multiUseCorner`, `parkStreetThreshold`, `railwaySurfaceStationsEnabled`,
`scatteredChanceMultiplier`, `spawnCheckAttempts`, `spawnCheckRadius`,
`spawnRadiusIncrease`, `useAvgHeightmap`. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## The loot table directory was renamed

Minecraft renamed its registry folder from `loot_tables` to `loot_table`, and the
mod follows, so the path depends on the version. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Versions [code review](../examples/claim-tests.md#key-1){.v .v-c} | Path inside a datapack |
|---|---|
| Up to and including 8.2.2 | `data/<namespace>/loot_tables/chests/<name>.json` |
| 8.4.1, 9.5.1, 10.0.1 | `data/<namespace>/loot_table/chests/<name>.json` |

This affects any loot table you write, including one a building part points at.
The wrong folder means Minecraft never registers the table, and the mod then fails
to find it by name. [code review](../examples/claim-tests.md#key-1){.v .v-c}

!!! note "The two jars labelled 1.21 do not target the same Minecraft release"
    8.2.2 and 8.4.1 carry the same `1.21` label and the same NeoForge requirement,
    `[21.0,)`. They disagree about this folder: 8.2.2 uses the plural form and 8.4.1
    the singular. Minecraft adopted the singular in a later 1.21 release, so 8.4.1
    targets that release or newer whatever its label says. Check the CurseForge
    listing before assuming either runs on your exact version. [code review](../examples/claim-tests.md#key-1){.v .v-c}

The path to the mod's **own** assets is unaffected and stays
`data/<namespace>/lostcities/<type>/<name>.json` on every version in the datapack
era. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Blocks, not keys, are the real upgrade risk

The asset format stopped changing after 7.5.1. Minecraft did not. A palette naming
a block that was renamed or removed between Minecraft 1.20.1 and Minecraft 26.1
fails on the newer version even though the file is structurally valid. [code review](../examples/claim-tests.md#key-1){.v .v-c}

That failure is not gentle. A block name the game cannot resolve takes the **whole
palette** down, not the one entry, which is the same mechanism as the `@meta`
suffix bug. Check palettes against the target Minecraft version before assuming a
datapack carries over. [game test](../examples/claim-tests.md#prf-1){.v .v-g}
