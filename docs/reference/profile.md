# Profile Reference

!!! tip "TL;DR"
    A profile is `config/lostcities/profiles/<name>.json`. Five sections: `lostcity`, `cities`, `explosions`, `cityspheres`, `client`, plus a root `public` flag. Every field below is optional, omit it and the default applies.

!!! warning "Version note"
    The official docs (checked for comparison while writing this) describe a newer mod version with a hierarchical street/highway grid system (`streetGenerationMode`, `highwayGenerationMode`, hub-based intercity highways, and related fields). **None of that exists in 7.4.12.** Every field below was verified against the actual 7.4.12 class, not copied from the newer docs. On a different version, check for a changes-only update to this page before trusting it.

## File shape

```json
{
  "public": true,
  "lostcity": { "worldStyle": "standard" },
  "cities": {},
  "explosions": {},
  "cityspheres": {},
  "client": {}
}
```

`public` is root-level, not inside a category. Defaults to `true`. Set `false` to hide a profile from the in-game selector (used for the "private" outside-sphere profiles mentioned on the [connects page](../getting-started/how-it-connects.md)).

Tables below: **Range** is the valid input window, values outside it get clamped or rejected. A blank Range means it's not a number (text, block ID, list, or true/false).

## `lostcity`

### Identity & terrain

| Key | Default | Range | Meaning |
|---|---|---|---|
| `description` | *(text)* | | Shown for the profile in the selector. |
| `extraDescription` | `""` | | Extra info text. |
| `warning` | `""` | | Warning text shown on selection. |
| `worldStyle` | `"standard"` | | The World Style this profile uses. See [Namespaces](../getting-started/namespaces.md). |
| `icon` | `""` | | 64×64 icon path for the selector screen. |
| `landscapeType` | `"default"` | | One of `default`, `floating`, `space`, `cavern`, `spheres`, `cavernspheres`. |
| `liquidBlock` | `minecraft:water` | | Block used as the profile's liquid. Bad ID silently falls back to water. |
| `baseBlock` | `minecraft:stone` | | Block used as the worldgen base. Bad ID silently falls back to stone. |
| `groundLevel` | `71` | 2 – 256 | Base ground Y. |
| `seaLevel` | `-1` | -1 – 256 | Sea level Y. `-1` uses the world default. |
| `bedrockLayer` | `1` | 0 – 10 | Bedrock layer height. `0` = vanilla default bedrock. |
| `terrainFixLowerMinOffset` | `-4` | -40 – 40 | Lower-mesh offset (blocks) for raising adjacent terrain. |
| `terrainFixLowerMaxOffset` | `-3` | -40 – 40 | Upper end of that same offset range. |
| `terrainFixUpperMinOffset` | `-1` | -40 – 40 | Upper-mesh offset for lowering adjacent terrain. |
| `terrainFixUpperMaxOffset` | `1` | -40 – 40 | Upper end of that same offset range. |
| `avoidWater` | `false` | | Replace all water with air. |
| `editMode` | `false` | | Enables the in-game edit mode. |
| `generateNether` | `false` | | Generate the Nether using the cavern-style generator. |

### Spawn

| Key | Default | Range | Meaning |
|---|---|---|---|
| `spawnBiome` | `""` | | Force spawn in this biome. Empty = no restriction. |
| `spawnCity` | `""` | | Force spawn in this predefined city. |
| `spawnSphere` | `""` | | Force spawn in this predefined sphere. `<in>` = any sphere, `<out>` = outside every sphere. |
| `spawnNotInBuilding` | `false` | | Never spawn inside a building. |
| `forceSpawnInBuilding` | `false` | | Always spawn inside a building. |
| `forceSpawnBuildings` | `[]` | | Restrict to these building names. Empty = any. |
| `forceSpawnParts` | `[]` | | Restrict to these part names. Empty = any. |
| `spawnCheckRadius` | `200` | 1 – 100000 | Starting search radius (blocks). |
| `spawnRadiusIncrease` | `100` | 1 – 100000 | Radius growth per failed search pass. |
| `spawnCheckAttempts` | `20000` | 1 – 1000000 | Max chunks checked before spawn search fails. |

### Buildings, streets, parks

!!! note "These get overridden by CityStyle"
    `buildingChance`, floor/cellar min/max, `parkChance`, `avoidFoliage`/`parkBorder`/`parkElevation`/`parkStreetThreshold`, `fountainChance`, `buildingFrontChance`, and `corridorChance` all have `CityStyle`-level equivalents. When a `CityStyle` sets its own value, it wins. These profile values are only the fallback.

| Key | Default | Range | Meaning |
|---|---|---|---|
| `buildingChance` | `0.3` | 0 – 1 | Chance a city chunk is a building instead of a street. |
| `buildingMinFloors` | `0` | 0 – 60 | Min floor count (above ground). |
| `buildingMaxFloors` | `8` | 0 – 60 | Max floor count. |
| `buildingMinFloorsChance` | `4` | 1 – 60 | See formula below. |
| `buildingMaxFloorsChance` | `6` | 1 – 60 | See formula below. |
| `buildingMinCellars` | `0` | 0 – 20 | Min cellar count. |
| `buildingMaxCellars` | `3` | 0 – 20 | Max cellar count. |
| `buildingDoorwayChance` | `0.6` | 0 – 1 | Chance of a doorway per eligible side/level. |
| `buildingFrontChance` | `0.2` | 0 – 1 | Chance a building uses its "front" part next to a street. |
| `parkChance` | `0.2` | 0 – 1 | Chance a non-building section is a park. |
| `parkElevation` | `true` | | Parks get an extra elevation layer. |
| `parkBorder` | `true` | | Park border uses the street block. |
| `parkStreetThreshold` | `3` | 0 – 8 | Surrounding-street count needed for a park. |
| `fountainChance` | `0.05` | 0 – 1 | Chance a street section has a fountain. |
| `corridorChance` | `0.7` | 0 – 1 | Chance a chunk can be a corridor (also needs adjacent corridors). |
| `bridgeChance` | `0.7` | 0 – 1 | Chance a chunk can be a bridge. |
| `bridgeSupports` | `true` | | Generate bridge supports. |
| `multiUseCorner` | `false` | | Multi-buildings use only their top-left corner's level, not a surrounding average. |
| `useAvgHeightmap` | `false` | | Sample surrounding heightmaps for city level (slower, more accurate). |
| `scatteredChanceMultiplier` | `1.0` | 0 – 100 | Multiplier on scattered-building chance. `0` disables them. |

!!! example "The floor-count formula"
    ```
    floors = buildingMinFloors + random(
        buildingMinFloorsChance + (cityFactor + 0.1) *
        (buildingMaxFloorsChance - buildingMinFloorsChance)
    )
    ```
    capped at `buildingMaxFloors`. `cityFactor` is how "strong" this particular city is, roughly 0 to 1.

### Decay & overgrowth

| Key | Default | Range | Meaning |
|---|---|---|---|
| `vineChance` | `0.009` | 0 – 1 | Chance an exterior block gets a vine. |
| `randomLeafBlockChance` | `0.1` | 0 – 1 | Chance of leaf blocks at building/street borders. |
| `randomLeafBlockThickness` | `2` | 1 – 8 | How thick that leaf border looks. |
| `avoidFoliage` | `false` | | Remove trees/flowers from parks. |
| `rubbleLayer` | `true` | | Enable the overgrown dirt/stone/sand + leaf rubble layer. |
| `rubbleDirtScale` | `3.0` | 0 – 100 | Noise scale for the dirt rubble layer. Smaller = broader coverage. `0` disables it. |
| `rubbleLeaveScale` | `6.0` | 0 – 100 | Same, for the leaf rubble layer. |
| `ruinChance` | `0.05` | 0 – 1 | Chance a building is ruined. |
| `ruinMinlevelPercent` | `0.8` | 0 – 1 | Fraction of building height where ruin destruction can start, low end. |
| `ruinMaxlevelPercent` | `1.0` | 0 – 1 | Same, high end. |

### Highways & railways

| Key | Default | Range | Meaning |
|---|---|---|---|
| `highwayRequiresTwoCities` | `true` | | `false` allows a highway with only one valid city end. |
| `highwayLevelFromCities` | `0` | 0 – 3 | `0` top-left city's height, `1` min of both, `2` max of both, `3` average. |
| `highwayDistanceMask` | `7` | ≥ 0 | Spacing bitmask, must be a power of two minus one (`0`, `1`, `3`, `7`, `15`...). `0` disables highways. |
| `highwayMainPerlinScale` | `50.0` | 1 – 1000 | Noise scale, main axis. |
| `highwaySecondaryPerlinScale` | `10.0` | 1 – 1000 | Noise scale, cross axis. |
| `highwayPerlinFactor` | `2.0` | -100 – 100 | Noise threshold. `0` ≈ 50% chance. Higher suppresses highways. |
| `highwaySupports` | `true` | | Generate highway supports. |
| `railwayDungeonChance` | `0.01` | 0 – 1 | Chance a chunk next to a railway gets a dungeon. |
| `railwaysCanEnd` | `false` | | Allow a dead-end rail part where a station would've been. |
| `railwaysEnabled` | `true` | | Enable rail lines (stations are separate). |
| `railwayStationsEnabled` | `true` | | Enable stations. |
| `railwaySurfaceStationsEnabled` | `true` | | Allow surface (not just underground) stations. |

### Loot & misc

| Key | Default | Range | Meaning |
|---|---|---|---|
| `generateSpawners` | `true` | | Buildings can contain spawners. |
| `generateLoot` | `true` | | Chests can contain loot. |
| `generateLighting` | `false` | | Add minimal building lighting. |
| `chestWithoutLootChance` | `0.2` | 0 – 1 | Chance an eligible chest is empty. |
| `buildingWithoutLootChance` | `0.2` | 0 – 1 | Chance a building has neither loot nor spawners. |

## `cities`

| Key | Default | Range | Meaning |
|---|---|---|---|
| `cityChance` | `0.01` | -1 – 1 | Chance a chunk is a city center. Exactly `-1` switches to Perlin-noise mode. |
| `cityMinRadius` | `50` | 1 – 2000 | Min city radius (blocks). |
| `cityMaxRadius` | `128` | 1 – 2000 | Max city radius. |
| `cityPerlinScale` | `3.0` | huge range, effectively unbounded | Only used when `cityChance` is `-1`. |
| `cityPerlinInnerScale` | `0.1` | huge range, effectively unbounded | Same. |
| `cityPerlinOffset` | `0.1` | huge range, effectively unbounded | Same. |
| `cityThreshold` | `0.2` | 0 – 1 | City-factor cutoff for overlapping city circles to count as a city. |
| `citySpawnDistance1` | `0` | 0 – 10000000 | Distance (blocks) from spawn for city-factor scaling, first point. |
| `citySpawnDistance2` | `0` | 0 – 10000000 | Second point. `0` disables spawn-distance scaling entirely. |
| `citySpawnMultiplier1` | `1.0` | 0 – 1 | City factor at the first distance. |
| `citySpawnMultiplier2` | `1.0` | 0 – 1 | City factor at the second distance. |
| `cityStyleThreshold` | `-1.0` | disabled at -1, else 0 – 1 | Below this city factor, use `cityStyleAlternative` instead. |
| `cityStyleAlternative` | `""` | | The alternative city style name. |
| `cityAvoidVoid` | `true` | | Floating landscape only: skip cities detected over void. |
| `cityLevel0Height` … `cityLevel7Height` | `75, 83, 91, 99, 107, 115, 123, 131` | 1 – 384 each | Terrain-height cutoffs assigning a city to level 0–7. |
| `cityMinHeight` | `50` | -1024 – 2048 | No cities below this Y. |
| `cityMaxHeight` | `150` | -1024 – 2048 | No cities above this Y. |
| `oceanCorrectionBorder` | `4` | -255 – 255 | Terrain correction offset for ocean chunks next to a city. |

## `explosions`

Normal and mini explosions are independent settings.

| Key | Default | Range | Meaning |
|---|---|---|---|
| `explosionChance` | `0.002` | 0 – 1 | Per-chunk chance of a normal explosion. |
| `explosionMinRadius` | `15` | 1 – 1000 | Min radius. |
| `explosionMaxRadius` | `35` | 1 – 3000 | Max radius. |
| `explosionMinHeight` | `75` | 1 – 256 | Min Y. |
| `explosionMaxHeight` | `90` | 1 – 256 | Max Y. |
| `miniExplosionChance` | `0.03` | 0 – 1 | Per-chunk chance of a mini explosion. |
| `miniExplosionMinRadius` | `5` | 1 – 1000 | Min radius. |
| `miniExplosionMaxRadius` | `12` | 1 – 3000 | Max radius. |
| `miniExplosionMinHeight` | `60` | 1 – 256 | Min Y. |
| `miniExplosionMaxHeight` | `100` | 1 – 256 | Max Y. |
| `explosionsInCitiesOnly` | `true` | | Blast center must be in a city (blast itself can still reach outside). |
| `debrisToNearbyChunkFactor` | `200` | 1 – 10000 | Debris spillover from nearby damaged chunks. Higher = less spillover. |

## `cityspheres`

Mostly relevant to `space`, `spheres`, and `cavernspheres` landscape types.

| Key | Default | Range | Meaning |
|---|---|---|---|
| `citySphereFactor` | `1.2` | 0.1 – 10 | `space` only: outer sphere radius = city radius × this. |
| `citySphereChance` | `0.7` | 0 – 1 | Chance a city gets a sphere. |
| `citySphereClearAbove` | `0` | 0 – 1024 | Blocks cleared above the sphere. `0` disables. |
| `citySphereClearBelow` | `0` | 0 – 1024 | Blocks cleared below the sphere. `0` disables. |
| `citySphereClearAboveUntilAir` | `false` | | Keep clearing above past the fixed amount until air. |
| `citySphereClearBelowUntilAir` | `false` | | Same, below. |
| `sphereSurfaceVariation` | `1.0` | 0 – 1 | Terrain variation inside spheres. Smaller = more varied. |
| `outsideSurfaceVariation` | `1.0` | 0 – 1 | Same, outside spheres. |
| `monorailChance` | `0.8` | 0 – 1 | Chance a sphere requests a monorail connection each direction (needs a matching neighbor). |
| `monorailOffset` | `-2` | -100 – 100 | Monorail height offset relative to the sphere. |
| `onlyPredefined` | `false` | | Only generate spheres from predefined assets, no random ones. |
| `outsideProfile` | `""` | | Profile used for terrain outside the spheres. See [connects page](../getting-started/how-it-connects.md). |
| `outsideGroundLevel` | `-1` | -1 – 256 | **Deprecated**, use `groundLevel` on `outsideProfile` instead. |
| `grid32` | `false` | | Align spheres to a 32×32 grid instead of 16×16. |

## `client`

Only affects players who also have Lost Cities installed. `-1` leaves the default alone.

| Key | Default | Range | Meaning |
|---|---|---|---|
| `horizon` | `-1` | -1 – 256 | Client horizon height. |
| `fogRed` | `-1` | -1 – 1 | Red fog component, `0`–`1` when set explicitly. |
| `fogGreen` | `-1` | -1 – 1 | Green fog component. |
| `fogBlue` | `-1` | -1 – 1 | Blue fog component. |
| `fogDensity` | `-1` | -1 – 1 | Fog density override. |

## See also

- [How It All Connects](../getting-started/how-it-connects.md) for how a profile gets picked at all
- [Glossary](../glossary.md)
