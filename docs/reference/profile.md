# Profile Reference

!!! tip "TL;DR"
    A profile is `config/lostcities/profiles/<name>.json`. Five sections: `lostcity`, `cities`, `explosions`, `cityspheres`, `client`, plus a root `public` flag. Every field below is optional, omit it and the default applies.

!!! warning "Version note"
    The official docs (checked for comparison while writing this) describe a newer mod version with a hierarchical street/highway grid system (`streetGenerationMode`, `highwayGenerationMode`, hub-based intercity highways, and related fields). **None of that exists in 7.4.12.** Every field below was verified against the actual 7.4.12 class, not copied from the newer docs. If you're not on 7.4.12, check for an addendum before trusting this page.

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

## `lostcity`

### Identity & terrain

| Key | Default | Meaning |
|---|---|---|
| `description` | *(text)* | Shown for the profile in the selector. |
| `extraDescription` | `""` | Extra info text. |
| `warning` | `""` | Warning text shown on selection. |
| `worldStyle` | `"standard"` | The World Style this profile uses. See [Namespaces](../getting-started/namespaces.md). |
| `icon` | `""` | 64×64 icon path for the selector screen. |
| `landscapeType` | `"default"` | One of `default`, `floating`, `space`, `cavern`, `spheres`, `cavernspheres`. |
| `liquidBlock` | `minecraft:water` | Block used as the profile's liquid. Bad ID silently falls back to water. |
| `baseBlock` | `minecraft:stone` | Block used as the worldgen base. Bad ID silently falls back to stone. |
| `groundLevel` | `71` | Base ground Y. |
| `seaLevel` | `-1` | Sea level Y. `-1` uses the world default. |
| `bedrockLayer` | `1` | Bedrock layer height. `0` = vanilla default bedrock. |
| `terrainFixLowerMinOffset` / `MaxOffset` | `-4` / `-3` | Offset range (blocks, relative to city base) for raising adjacent terrain. |
| `terrainFixUpperMinOffset` / `MaxOffset` | `-1` / `1` | Offset range for lowering adjacent terrain. |
| `avoidWater` | `false` | Replace all water with air. |
| `editMode` | `false` | Enables the in-game edit mode. |
| `generateNether` | `false` | Generate the Nether using the cavern-style generator. |

### Spawn

| Key | Default | Meaning |
|---|---|---|
| `spawnBiome` | `""` | Force spawn in this biome. Empty = no restriction. |
| `spawnCity` | `""` | Force spawn in this predefined city. |
| `spawnSphere` | `""` | Force spawn in this predefined sphere. `<in>` = any sphere, `<out>` = outside every sphere. |
| `spawnNotInBuilding` | `false` | Never spawn inside a building. |
| `forceSpawnInBuilding` | `false` | Always spawn inside a building. |
| `forceSpawnBuildings` | `[]` | Restrict to these building names. Empty = any. |
| `forceSpawnParts` | `[]` | Restrict to these part names. Empty = any. |
| `spawnCheckRadius` | `200` | Starting search radius (blocks). |
| `spawnRadiusIncrease` | `100` | Radius growth per failed search pass. |
| `spawnCheckAttempts` | `20000` | Max chunks checked before spawn search fails. |

### Buildings, streets, parks

!!! note "These get overridden by CityStyle"
    `buildingChance`, floor/cellar min/max, `parkChance`, `avoidFoliage`/`parkBorder`/`parkElevation`/`parkStreetThreshold`, `fountainChance`, `buildingFrontChance`, and `corridorChance` all have `CityStyle`-level equivalents. When a `CityStyle` sets its own value, it wins. These profile values are only the fallback.

| Key | Default | Meaning |
|---|---|---|
| `buildingChance` | `0.3` | Chance a city chunk is a building instead of a street. |
| `buildingMinFloors` / `buildingMaxFloors` | `0` / `8` | Floor count bounds (above ground). |
| `buildingMinFloorsChance` / `buildingMaxFloorsChance` | `4` / `6` | See formula below. |
| `buildingMinCellars` / `buildingMaxCellars` | `0` / `3` | Cellar count bounds. |
| `buildingDoorwayChance` | `0.6` | Chance of a doorway per eligible side/level. |
| `buildingFrontChance` | `0.2` | Chance a building uses its "front" part next to a street. |
| `parkChance` | `0.2` | Chance a non-building section is a park. |
| `parkElevation` | `true` | Parks get an extra elevation layer. |
| `parkBorder` | `true` | Park border uses the street block. |
| `parkStreetThreshold` | `3` | Surrounding-street count needed for a park. |
| `fountainChance` | `0.05` | Chance a street section has a fountain. |
| `corridorChance` | `0.7` | Chance a chunk can be a corridor (also needs adjacent corridors). |
| `bridgeChance` | `0.7` | Chance a chunk can be a bridge. |
| `bridgeSupports` | `true` | Generate bridge supports. |
| `multiUseCorner` | `false` | Multi-buildings use only their top-left corner's level, not a surrounding average. |
| `useAvgHeightmap` | `false` | Sample surrounding heightmaps for city level (slower, more accurate). |
| `scatteredChanceMultiplier` | `1.0` | Multiplier on scattered-building chance. `0` disables them. |

!!! example "The floor-count formula"
    ```
    floors = buildingMinFloors + random(
        buildingMinFloorsChance + (cityFactor + 0.1) *
        (buildingMaxFloorsChance - buildingMinFloorsChance)
    )
    ```
    capped at `buildingMaxFloors`. `cityFactor` is how "strong" this particular city is, roughly 0 to 1.

### Decay & overgrowth

| Key | Default | Meaning |
|---|---|---|
| `vineChance` | `0.009` | Chance an exterior block gets a vine. |
| `randomLeafBlockChance` | `0.1` | Chance of leaf blocks at building/street borders. |
| `randomLeafBlockThickness` | `2` | How thick that leaf border looks. |
| `avoidFoliage` | `false` | Remove trees/flowers from parks. |
| `rubbleLayer` | `true` | Enable the overgrown dirt/stone/sand + leaf rubble layer. |
| `rubbleDirtScale` / `rubbleLeaveScale` | `3.0` / `6.0` | Noise scale for each rubble layer. Smaller = broader coverage. `0` disables that layer. |
| `ruinChance` | `0.05` | Chance a building is ruined. |
| `ruinMinlevelPercent` / `ruinMaxlevelPercent` | `0.8` / `1.0` | Height range (as a fraction of building height) where ruin destruction starts. |

### Highways & railways

| Key | Default | Meaning |
|---|---|---|
| `highwayRequiresTwoCities` | `true` | `false` allows a highway with only one valid city end. |
| `highwayLevelFromCities` | `0` | `0` top-left city's height, `1` min of both, `2` max of both, `3` average. |
| `highwayDistanceMask` | `7` | Spacing bitmask, must be a power of two minus one. `0` disables highways. |
| `highwayMainPerlinScale` / `highwaySecondaryPerlinScale` | `50.0` / `10.0` | Noise scale, main and cross axis. |
| `highwayPerlinFactor` | `2.0` | Noise threshold. `0` ≈ 50% chance. Higher suppresses highways. |
| `highwaySupports` | `true` | Generate highway supports. |
| `railwayDungeonChance` | `0.01` | Chance a chunk next to a railway gets a dungeon. |
| `railwaysCanEnd` | `false` | Allow a dead-end rail part where a station would've been. |
| `railwaysEnabled` | `true` | Enable rail lines (stations are separate). |
| `railwayStationsEnabled` | `true` | Enable stations. |
| `railwaySurfaceStationsEnabled` | `true` | Allow surface (not just underground) stations. |

### Loot & misc

| Key | Default | Meaning |
|---|---|---|
| `generateSpawners` | `true` | Buildings can contain spawners. |
| `generateLoot` | `true` | Chests can contain loot. |
| `generateLighting` | `false` | Add minimal building lighting. |
| `chestWithoutLootChance` | `0.2` | Chance an eligible chest is empty. |
| `buildingWithoutLootChance` | `0.2` | Chance a building has neither loot nor spawners. |

## `cities`

| Key | Default | Meaning |
|---|---|---|
| `cityChance` | `0.01` | Chance a chunk is a city center. `-1` switches to Perlin-noise mode. |
| `cityMinRadius` / `cityMaxRadius` | `50` / `128` | City radius bounds (blocks). |
| `cityPerlinScale` / `cityPerlinInnerScale` / `cityPerlinOffset` | `3.0` / `0.1` / `0.1` | Only used when `cityChance` is `-1`. |
| `cityThreshold` | `0.2` | City-factor cutoff for overlapping city circles to count as a city. |
| `citySpawnDistance1` / `citySpawnDistance2` | `0` / `0` | Distances (blocks) from spawn for city-factor scaling. `0` on the second disables scaling. |
| `citySpawnMultiplier1` / `citySpawnMultiplier2` | `1.0` / `1.0` | City factor at each distance. |
| `cityStyleThreshold` | `-1.0` | Below this city factor, use `cityStyleAlternative` instead. `-1` disables the switch. |
| `cityStyleAlternative` | `""` | The alternative city style name. |
| `cityAvoidVoid` | `true` | Floating landscape only: skip cities detected over void. |
| `cityLevel0Height` … `cityLevel7Height` | `75, 83, 91, 99, 107, 115, 123, 131` | Terrain-height cutoffs assigning a city to level 0–7. |
| `cityMinHeight` / `cityMaxHeight` | `50` / `150` | Hard bounds, no cities outside this Y range. |
| `oceanCorrectionBorder` | `4` | Terrain correction offset for ocean chunks next to a city. |

## `explosions`

Normal and mini explosions are independent settings.

| Key | Default | Meaning |
|---|---|---|
| `explosionChance` | `0.002` | Per-chunk chance of a normal explosion. |
| `explosionMinRadius` / `explosionMaxRadius` | `15` / `35` | Radius bounds. |
| `explosionMinHeight` / `explosionMaxHeight` | `75` / `90` | Y bounds. |
| `miniExplosionChance` | `0.03` | Per-chunk chance of a mini explosion. |
| `miniExplosionMinRadius` / `MaxRadius` | `5` / `12` | Radius bounds. |
| `miniExplosionMinHeight` / `MaxHeight` | `60` / `100` | Y bounds. |
| `explosionsInCitiesOnly` | `true` | Blast center must be in a city (blast itself can still reach outside). |
| `debrisToNearbyChunkFactor` | `200` | Debris spillover from nearby damaged chunks. Higher = less spillover. |

## `cityspheres`

Mostly relevant to `space`, `spheres`, and `cavernspheres` landscape types.

| Key | Default | Meaning |
|---|---|---|
| `citySphereFactor` | `1.2` | `space` only: outer sphere radius = city radius × this. |
| `citySphereChance` | `0.7` | Chance a city gets a sphere. |
| `citySphereClearAbove` / `citySphereClearBelow` | `0` / `0` | Blocks cleared above/below the sphere. `0` disables. |
| `citySphereClearAboveUntilAir` / `citySphereClearBelowUntilAir` | `false` / `false` | Keep clearing past the fixed amount until air. |
| `sphereSurfaceVariation` / `outsideSurfaceVariation` | `1.0` / `1.0` | Terrain variation inside / outside spheres. Smaller = more varied. |
| `monorailChance` | `0.8` | Chance a sphere requests a monorail connection each direction (needs a matching neighbor). |
| `monorailOffset` | `-2` | Monorail height offset relative to the sphere. |
| `onlyPredefined` | `false` | Only generate spheres from predefined assets, no random ones. |
| `outsideProfile` | `""` | Profile used for terrain outside the spheres. See [connects page](../getting-started/how-it-connects.md). |
| `outsideGroundLevel` | `-1` | **Deprecated**, use `groundLevel` on `outsideProfile` instead. |
| `grid32` | `false` | Align spheres to a 32×32 grid instead of 16×16. |

## `client`

Only affects players who also have Lost Cities installed. `-1` leaves the default alone.

| Key | Default | Meaning |
|---|---|---|
| `horizon` | `-1` | Client horizon height. |
| `fogRed` / `fogGreen` / `fogBlue` | `-1` | Fog color, `0`–`1` when set explicitly. |
| `fogDensity` | `-1` | Fog density override. |

## See also

- [How It All Connects](../getting-started/how-it-connects.md) for how a profile gets picked at all
- [Glossary](../glossary.md)
