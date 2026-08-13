# The NeoForge line

Minecraft 1.21 and later require **NeoForge**. There is no Forge build of the mod
for those versions, and there is no way to load one. The switch happens at mod
version 8.0.

| Mod versions | Loader |
|---|---|
| 1.0.1 through 7.5.1 | Forge |
| 8.2.2 and later | NeoForge |

This page covers what a reader on 1.21 or later needs that the rest of the wiki
does not say. Everything else on this site applies unchanged.

## The versions

| Version | Label | Loader requirement | Has hierarchical roads |
|---|---|---|---|
| 8.2.2 | 1.21 | NeoForge `[21.0,)` | No |
| 8.4.1 | 1.21 | NeoForge `[21.0,)` | Yes |
| 9.5.1 | 1.21.11 | NeoForge `[21.11,)` | Yes |
| 10.0.1 | 26.1.2 | NeoForge `[26.1.2.0-beta,)` | Yes |

## 8.4.1 and later match 7.5.1 exactly

This is the useful part. If you are on 8.4.1, 9.5.1 or 10.0.1, the mod's
configuration surface is identical to 7.5.1 on Minecraft 1.20.1.

Verified by comparing complete key sets:

| Surface | Result |
|---|---|
| Profile keys | The same 160 names, with identical types, defaults, minimums and maximums. Zero differences across 7.5.1, 8.4.1, 9.5.1 and 10.0.1. |
| Datapack keys | The same 231 keys, each required or optional in the same way. |

So read this wiki, then read [What changed in 7.5](7-5.md), and you have the whole
picture. The hierarchical road system and its 29 profile keys behave the same way
here.

### The one internal rename

In 9.5.1 the class `ResourceLocationMatcher` became `IdentifierMatcher`. This is a
Java class name. The JSON keys it carries, `if_any` and `excluding`, did not
change. Your files do not need editing.

## 8.2.2 is behind 7.4.12, not ahead of it

The version number is higher. The feature set is smaller.

8.2.2 is missing **23 datapack keys** and **19 profile keys** that 7.4.12 has, and
it adds none. It also still carries `libraryChance` and `dataCenterChance`, two
profile keys that 7.4.12 had already removed.

!!! warning "A datapack written against this wiki may fail to load on 8.2.2"
    23 of the keys this wiki documents do not exist in 8.2.2. A required key that
    the codec does not know is a load failure. Move to 8.4.1 or later, or check
    each key against the list below.

Datapack keys present in 7.4.12 and absent in 8.2.2:

| Asset | Keys |
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

Profile keys present in 7.4.12 and absent in 8.2.2:

`cityLevel4Height`, `cityLevel5Height`, `cityLevel6Height`, `cityLevel7Height`,
`citySpawnDistance1`, `citySpawnDistance2`, `citySpawnMultiplier1`,
`citySpawnMultiplier2`, `forceSpawnBuildings`, `forceSpawnParts`, `grid32`,
`multiUseCorner`, `parkStreetThreshold`, `railwaySurfaceStationsEnabled`,
`scatteredChanceMultiplier`, `spawnCheckAttempts`, `spawnCheckRadius`,
`spawnRadiusIncrease`, `useAvgHeightmap`.

## The loot table directory was renamed

Minecraft renamed its registry folder from `loot_tables` to `loot_table`. The mod
follows, so the path depends on your version.

| Versions | Path inside a datapack |
|---|---|
| Up to and including 8.2.2 | `data/<namespace>/loot_tables/chests/<name>.json` |
| 8.4.1, 9.5.1, 10.0.1 | `data/<namespace>/loot_table/chests/<name>.json` |

This affects any loot table you write, including one you point a building part at.
Using the wrong folder means Minecraft never registers the table, and the mod then
fails to find it by name.

The path to the mod's **own** assets is not affected. That stays
`data/<namespace>/lostcities/<type>/<name>.json` on every version in the datapack
era.

## Blocks, not keys, are the real upgrade risk

The asset format stopped changing after 7.5.1. Minecraft did not. A palette that
names a block which was renamed or removed between Minecraft 1.20.1 and Minecraft
26.1 fails on the newer version, even though the file is structurally valid.

Check your palettes against the target Minecraft version before assuming a
datapack carries over.
