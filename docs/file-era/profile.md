---
claims: verified
---

# File-Era Profile Reference

!!! tip "TL;DR"
    A file-era profile is a whole file, `config/lostcities/profile_<name>.cfg`, in Forge's old `.cfg` format rather than JSON. Version 2.0.22 writes **128 keys** across six categories, and every default is inherited from a parent profile rather than listed in one place. [game test](../examples/claim-tests.md#f12-8){.v .v-g}


!!! info "Read from a file a real server wrote"
    Every key, type, default, range and description below is taken from the `profile_default.cfg` that Forge 1.12.2 with Lost Cities 2.0.22 generated on first launch. The descriptions are the mod's own. Generation itself has not been run yet, so this page covers the profile surface rather than what each key does to a world. [game test](../examples/claim-tests.md#f12-8){.v .v-g}


## How a profile is put together

Two steps, not one. Write `config/lostcities/profile_<name>.cfg`, then add that name
to the `profiles` list in `general.cfg`. A profile file that nothing lists is never
offered. See [Adding Your Own Content](adding-content.md#config-and-one-file-per-profile). [game test](../examples/claim-tests.md#f12-8){.v .v-g}


!!! danger "Every section is named after the profile, so copying a file is not enough"
    The section headers are not `cities` and `lostcity`. They are `cities_<profilename>` and `lostcity_<profilename>`:

    ```
    cities_default { ... }          in profile_default.cfg
    cities_wasteland { ... }        in profile_wasteland.cfg
    ```

    Copying `profile_default.cfg` to `profile_mycity.cfg` therefore leaves every section still called `..._default`. Rename the file **and** all six headers inside it. [game test](../examples/claim-tests.md#f12-8){.v .v-g}


!!! bug "`maxcaveheight` has its name and category swapped"
    One option is registered with its two first arguments the wrong way round, so it lands in a section of its own named after the key, holding a key named after the category: [game test](../examples/claim-tests.md#f12-8){.v .v-g}

    ```
    maxcaveheight {
        # Maximum height at which vanilla caves can generate. Default is 128.
        I:structures_default=128
    }
    ```

    To change it you edit `structures_<profilename>` inside a section called `maxcaveheight`, which is the reverse of every other option in the file. It follows the profile name like the rest, so the wasteland profile holds `I:structures_wasteland`. [game test](../examples/claim-tests.md#f12-8){.v .v-g}


!!! note "Defaults are inherited, not tabulated"
    Each key is registered as `inheritFrom.orElse(this).<field>`, so a profile's default is whatever its parent holds. That is what `privateProfiles` in `general.cfg` is for: a profile nobody can pick, existing only to be a parent. The defaults below are the ones `default` itself ships with. [code review](../examples/claim-tests.md#f12-8){.v .v-c}


## The six categories

| Category | Keys | Covers |
|---|---|---|
| `lostcity_<profile>` | 74 | The bulk of it: terrain, buildings, streets, ruins, highways, railways and loot |
| `cities_<profile>` | 10 | Where cities appear, how big they get, and how terrain height becomes city level |
| `explosions_<profile>` | 15 | Explosions, mini explosions, and the debris they leave behind |
| `cityspheres_<profile>` | 11 | Glass spheres, used by the sphere landscapes |
| `structures_<profile>` | 12 | Which vanilla structures may generate inside a Lost Cities world |
| `client_<profile>` | 5 | Fog and horizon, applied only for a player who also has the mod |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## `lostcity_<profile>`

The bulk of it: terrain, buildings, streets, ruins, highways, railways and loot. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

| Key | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `allowedBiomeFactors` | text | *(list)* |  | List of biomes that are allowed in the world. Empty list is default all biomes. The factor controls how much that biome is favored over the others (higher means less favored!). |
| `avoidFoliage` | true/false | `false` |  | If this is true then parks will have no foliage (trees and flowers currently). |
| `avoidGeneratedCactii` | true/false | `false` |  | This will prevent biomes from generating cactii. |
| `avoidGeneratedDesertWell` | true/false | `false` |  | This will prevent the generation of desert wells. |
| `avoidGeneratedFlowers` | true/false | `false` |  | This will prevent biomes from generating flowers. |
| `avoidGeneratedFossils` | true/false | `false` |  | This will prevent the generation of fossils. |
| `avoidGeneratedGrass` | true/false | `false` |  | This will prevent biomes from generating grass. |
| `avoidGeneratedLakewater` | true/false | `false` |  | This will prevent the generation of water in lakes. |
| `avoidGeneratedLilypads` | true/false | `false` |  | This will prevent biomes from generating lilypads. |
| `avoidGeneratedMushrooms` | true/false | `false` |  | This will prevent biomes from generating mushrooms. |
| `avoidGeneratedPumpkins` | true/false | `false` |  | This will prevent biomes from generating pumpkins. |
| `avoidGeneratedReeds` | true/false | `false` |  | This will prevent biomes from generating reeds. |
| `avoidGeneratedTrees` | true/false | `false` |  | This will prevent biomes from generating trees. |
| `avoidWater` | true/false | `false` |  | If true then all water will be avoided (replaced with air). |
| `baseBlock` | text | `minecraft:stone` |  | Block to use as the worldgen base. |
| `bedrockLayer` | integer | `1` | 0 ~ 10 | The height of the bedrock layer that is generated at the bottom of some world types. Set to 0 to disable this and get default bedrock generation. |
| `biomeSelectionStrategy` | text | `original` |  | This is used in combination with allowedBiomeFactors. 'original' is the old strategy. 'randomized' is a new strategy that tries to randomize the biomes better. 'varied' is similar but has a more relaxed biome distance function. |
| `bridgeChance` | text | `0.7` | 0.0 ~ 1.0 | The chance that a chunk can possibly contain a bridge. There actually being a bridge also depends on the presence of adjacent bridges and other conditions. |
| `bridgeSupports` | true/false | `true` |  | If true bridges get supports when needed. You can disable this if you have bridges that span void chunks. |
| `building2x2Chance` | text | `0.03` | 0.0 ~ 1.0 | The chance that a chunk can possibly be the top-left chunk of 2x2 building. There actually being a 2x2 building also depends on the condition of those other chunks. |
| `buildingChance` | text | `0.3` | 0.0 ~ 1.0 | The chance that a chunk in a city will have a building. Otherwise it will be a street. |
| `buildingDoorwayChance` | text | `0.6` | 0.0 ~ 1.0 | The chance that a doorway will be generated at a side of a building (on any level). Only when possible. |
| `buildingFrontChance` | text | `0.2` | 0.0 ~ 1.0 | The chance that a building will have a 'front' part if this is possible (i.e. adjacent street). |
| `buildingMaxCellars` | integer | `4` | 0 ~ 7 | The maximum number of cellars (below ground). 0 means no cellar. |
| `buildingMaxFloors` | integer | `9` | 0 ~ 30 | A cap for the amount of floors a city can have (above ground). |
| `buildingMaxFloorsChance` | integer | `6` | 1 ~ 30 | The amount of floors of a building is equal to: MINFLOORS + random(MINFLOORS_CHANCE + (cityFactor + .1f) * (MAXFLOORS_CHANCE - MINFLOORS_CHANCE)). |
| `buildingMinCellars` | integer | `0` | 0 ~ 7 | The minimum number of cellars (below ground). 0 means no cellar. |
| `buildingMinFloors` | integer | `0` | 0 ~ 30 | The minimum number of floors (above ground) for a building (0 means the first floor only). |
| `buildingMinFloorsChance` | integer | `4` | 1 ~ 30 | The amount of floors of a building is equal to: MINFLOORS + random(MINFLOORS_CHANCE + (cityFactor + .1f) * (MAXFLOORS_CHANCE - MINFLOORS_CHANCE)). |
| `buildingWithoutLootChance` | text | `0.2` | 0.0 ~ 1.0 | The chance that a building will have no loot and no spawners. |
| `chestWithoutLootChance` | text | `0.2` | 0.0 ~ 1.0 | The chance that a chest will have no loot. |
| `corridorChance` | text | `0.7` | 0.0 ~ 1.0 | The chance that a chunk can possibly contain a corridor. There actually being a corridor also depends on the presence of adjacent corridors. |
| `dataCenterChance` | text | `0.1` | 0.0 ~ 1.0 | The chance that a 2x2 building will be a data center. |
| `description` | text | `Default generation, common cities, explosions` |  | The description of this profile. |
| `extraDescription` | text | *(list)* |  | Additional information. |
| `fountainChance` | text | `0.05` | 0.0 ~ 1.0 | The chance that a street section contains a fountain. |
| `generateLighting` | true/false | `false` |  | If true then there will be minimal lighting in the buildings. |
| `generateLoot` | true/false | `true` |  | If true the chests in the buildings will contain loot. |
| `generateSpawners` | true/false | `true` |  | If true then the buildings will be full of spawners. |
| `generatorOptions` | text | *(list)* |  | A json with generator options for the chunk generator. |
| `groundLevel` | integer | `71` | 2 ~ 256 | Ground level. |
| `highwayDistanceMask` | integer | `7` | 0 ~ 2147483647 | Mask to control how far highways can generate. Must be a power of 2 (minus 1). If 0 there are no highways at all. |
| `highwayLevelFromCities` | integer | `0` | 0 ~ 3 | 0 (take height from top-left city), 1 (take minimum height from both cities), 2 (take maximum height from both cities), 3 (take average height). |
| `highwayMainPerlinScale` | text | `50.0` | 1.0 ~ 1000.0 | For highways on a certain axis, this value is used to scale the perlin noise generator on the main axis. Increasing this value will increase the frequency of highways but make them smaller. |
| `highwayPerlinFactor` | text | `2.0` | -100.0 ~ 100.0 | The highway perlin noise is compared to this value. Setting this to 0 would give 50% chance of a highway being at a spot. Note that highways only generate on chunks a multiple of 8. Setting this very high will prevent highways from generating. |
| `highwayRequiresTwoCities` | true/false | `true` |  | If true then a highway will only generate if both sides have a valid city. If false then one city is sufficient. |
| `highwaySecondaryPerlinScale` | text | `10.0` | 1.0 ~ 1000.0 | For highways on a certain axis, this value is used to scale the perlin noise generator on the secondary axis. Increasing this value will increase the variation of nearby highways. |
| `highwaySupports` | true/false | `true` |  | If true highways get supports when needed. You can disable this if you have highways that span void chunks. |
| `icon` | text | `textures/gui/icon_default.png` |  | The icon to use in the configuration screen (64x64). |
| `landscapeType` | text | `default` |  | Type of landscape. |
| `libraryChance` | text | `0.1` | 0.0 ~ 1.0 | The chance that a 2x2 building will be a library. |
| `liquidBlock` | text | `minecraft:water` |  | Block to use as a liquid. |
| `manualBiomeMappings` | text | *(list)* |  | Use in combination with 'allowedBiomeFactors' to manually map some biomes to others. This is a list of the format oldbiome=newbiome. |
| `parkChance` | text | `0.2` | 0.0 ~ 1.0 | The chance that a non-building section can be a park section. |
| `railwayDungeonChance` | text | `0.01` | 0.0 ~ 1.0 | The chance that a chunk next to a railway will have a railway dungeon. |
| `railwaysCanEnd` | true/false | `false` |  | If true the a place where a station would have been if there was a city above will have an 'ending' rail part if one side of the 'station' has no connections. Useful in case cities are rare. |
| `railwaysEnabled` | true/false | `true` |  | If true then railways are enabled. If false they are not (but stations will still generate). |
| `railwayStationsEnabled` | true/false | `true` |  | If true then railway stations are enabled. |
| `randomLeafBlockChance` | text | `0.1` | 0.0 ~ 1.0 | Chance that leafblocks will be generated at the border of a building and a street. |
| `randomLeafBlockThickness` | integer | `2` | 1 ~ 8 | Frequency of leafblocks as seen from the sides of buildings. |
| `rubbleDirtScale` | text | `3.0` | 0.0 ~ 100.0 | The scale of the dirt layer. Smaller values make the layer larger. Use 0 to disable. |
| `rubbleLayer` | true/false | `true` |  | If this is true an alternative way to generate dirt/stone/sand + leave blocks is used that makes the city appear more overgrown. |
| `rubbleLeaveScale` | text | `6.0` | 0.0 ~ 100.0 | The scale of the leave layer. Smaller values make the layer larger. Use 0 to disable. |
| `ruinChance` | text | `0.05` | 0.0 ~ 1.0 | If ruines are enabled this gives the chance that a building is ruined. |
| `ruinMaxlevelPercent` | text | `1.0` | 0.0 ~ 1.0 | If a building is ruined this indicates the maximum start height for the ruin destruction layer. |
| `ruinMinlevelPercent` | text | `0.8` | 0.0 ~ 1.0 | If a building is ruined this indicates the minimum start height for the ruin destruction layer. |
| `ruins` | true/false | `true` |  | If true there is a chance a building is ruined from the top (not caused by explosion damage). |
| `spawnBiome` | text | *(list)* |  | When this is set the player will always spawn in the given biome. |
| `spawnCity` | text | *(list)* |  | When this is set the player will always spawn in the given predefined city. |
| `spawnNotInBuilding` | true/false | `false` |  | If this is true the player will not spawn in a building. This can be used in combination with the other spawn settings. |
| `spawnSphere` | text | *(list)* |  | When this is set the player will always spawn in the given predefined sphere. If you use <in> the player will always spawn in a random sphere. If you use <out> the player will always spawn outside a sphere. |
| `vineChance` | text | `0.009` | 0.0 ~ 1.0 | The chance that a block on the outside of a building will be covered with a vine. |
| `waterLevelOffset` | integer | `8` | -100 ~ 100 | How much lower the water level is compared to the ground level (63). |
| `worldStyle` | text | `standard` |  | The worldstyle used by this profile (defined in the assets). |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## `cities_<profile>`

Where cities appear, how big they get, and how terrain height becomes city level. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

| Key | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `cityBiomeFactorDefault` | text | `1.0` | 0.0 ~ 1.0 | The default biome factor which is used if your biome is not specified in 'cityBiomeFactors'. |
| `cityBiomeFactors` | text | *(list)* |  | List of biomes with a factor to affect the city factor in that biome. Using the value 0 you can disable city generation in biomes , [frozen_river=0], [ocean=.7], [frozen_ocean=.7], [deep_ocean=.4]]. |
| `cityChance` | text | `0.02` | 0.0 ~ 1.0 | The chance this chunk will be the center of a city. |
| `cityLevel0Height` | integer | `75` | 1 ~ 255 | Below this chunk height cities will be level 0. |
| `cityLevel1Height` | integer | `83` | 1 ~ 255 | Below this chunk height cities will be level 1. |
| `cityLevel2Height` | integer | `91` | 1 ~ 255 | Below this chunk height cities will be level 2. |
| `cityLevel3Height` | integer | `99` | 1 ~ 255 | Below this chunk height cities will be level 3. |
| `cityMaxRadius` | integer | `128` | 1 ~ 10000 | The maximum radius of a city. |
| `cityMinRadius` | integer | `50` | 1 ~ 10000 | The minimum radius of a city. |
| `cityThresshold` | text | `0.2` | 0.0 ~ 1.0 | The center and radius of a city define a sphere. This thresshold indicates from which point a city is considered a city. This is important for calculating where cities are based on overlapping city circles (where the city thressholds are added). |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## `explosions_<profile>`

Explosions, mini explosions, and the debris they leave behind. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

| Key | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `debrisToNearbyChunkFactor` | integer | `200` | 1 ~ 10000 | A factor that determines how much debris will overflow from nearby damaged chunks. Bigger numbers mean less debris. |
| `destroyLoneBlocksFactor` | text | `0.05` | 0.0 ~ 1.0 | When a section of blocks in in an explosion the generator will count the number of blocks that are connected. The number of connections divided by the total number of blocks in a connected section is compared with this number. If it is smaller then the section of blocks is destroyed or moved down with gravity. |
| `destroyOrMoveChance` | text | `0.4` | 0.0 ~ 1.0 | When a section of blocks is to be moved or destroyed this chance gives the chance of removal (as opposed to moving with gravity). |
| `destroySmallSectionsSize` | integer | `50` | 1 ~ 5000 | A section of blocks that is about to be moved or destroyed is always destroyed if it is smaller then this size. |
| `explosionChance` | text | `0.002` | 0.0 ~ 1.0 | The chance that a chunk will contain an explosion. |
| `explosionMaxHeight` | integer | `90` | 1 ~ 256 | The maximum height of an explosion. |
| `explosionMaxRadius` | integer | `35` | 1 ~ 3000 | The maximum radius of an explosion. |
| `explosionMinHeight` | integer | `75` | 1 ~ 256 | The minimum height of an explosion. |
| `explosionMinRadius` | integer | `15` | 1 ~ 1000 | The minimum radius of an explosion. |
| `explosionsInCitiesOnly` | true/false | `true` |  | If this is true the center of an explosion can only be in a city (the blast can still affect non-city chunks). |
| `miniExplosionChance` | text | `0.03` | 0.0 ~ 1.0 | The chance that a chunk will contain a mini explosion. |
| `miniExplosionMaxHeight` | integer | `100` | 1 ~ 256 | The maximum height of a mini explosion. |
| `miniExplosionMaxRadius` | integer | `12` | 1 ~ 3000 | The maximum radius of a mini explosion. |
| `miniExplosionMinHeight` | integer | `60` | 1 ~ 256 | The minimum height of a mini explosion. |
| `miniExplosionMinRadius` | integer | `5` | 1 ~ 1000 | The minimum radius of a mini explosion. |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## `cityspheres_<profile>`

Glass spheres, used by the sphere landscapes. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

| Key | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `citySphereChance` | text | `0.7` | 0.0 ~ 1.0 | The chance that a city sphere will be generated. |
| `citySphereFactor` | text | `1.2` | 0.1 ~ 10.0 | Only used in 'space' landscape. This factor will be multiplied with the radius of the city to calculate the radius of the outer sphere. |
| `landscapeOutside` | true/false | `false` |  | If this is true then there will be a landscape outside the city spheres. |
| `monorailChance` | text | `0.8` | 0.0 ~ 1.0 | The chance that a city will have a monorail connection in a certain direction. There will only be an actual connection if there is a city in that direction that also wants a monorail. |
| `monorailOffset` | integer | `-2` | -100 ~ 100 | Offset compared to main height. |
| `onlyPredefined` | true/false | `false` |  | If this is true then only predefined spheres are generated. |
| `outsideGroundLevel` | integer | `-1` | -1 ~ 256 | Ground level for outside city spheres (DEPRECATED, USE GROUNDLEVEL OF OTHER PROFILE). |
| `outsideProfile` | text | *(list)* |  | An optional profile to use for the outside world. |
| `outsideSurfaceVariation` | text | `1.0` | 0.0 ~ 1.0 | Smaller numbers make the surface outside a city sphere more varied. |
| `singleBiome` | true/false | `false` |  | If this is true then every city sphere will be limited to one (random) biome. |
| `sphereSurfaceVariation` | text | `1.0` | 0.0 ~ 1.0 | Smaller numbers make the surface inside a city sphere more varied. |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## `structures_<profile>`

Which vanilla structures may generate inside a Lost Cities world. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

| Key | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `generateCaves` | true/false | `true` |  | Generate caves. |
| `generateDungeons` | true/false | `true` |  | Generate dungeons. |
| `generateLakes` | true/false | `true` |  | Generate lakes (lava/water). |
| `generateMansions` | true/false | `true` |  | Generate mansions. |
| `generateMineshafts` | true/false | `true` |  | Generate mineshafts. |
| `generateOceanMonuments` | true/false | `true` |  | Generate ocean monuments. |
| `generateRavines` | true/false | `true` |  | Generate ravines. |
| `generateScattered` | true/false | `true` |  | Generate scattered features (swamphunts, desert temples, ...). |
| `generateStrongholds` | true/false | `true` |  | Generate strongholds. |
| `generateVillages` | true/false | `true` |  | Generate villages. |
| `preventLakesRavinesInCities` | true/false | `false` |  | If true then no lakes and ravines will be generated in cities. |
| `preventVillagesInCities` | true/false | `true` |  | If true then an attempt will be made to prevent villages in cities. Note that enabling this option will likely require a low city density in order to actually get a reasonable chance for villages. |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## `client_<profile>`

Fog and horizon, applied only for a player who also has the mod. [game test](../examples/claim-tests.md#f12-8){.v .v-g}

| Key | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `fogBlue` | text | `-1.0` | -1.0 ~ 1.0 | This is used client-side (but only if the client has this mod) for the fog color. |
| `fogDensity` | text | `-1.0` | -1.0 ~ 1.0 | This is used client-side (but only if the client has this mod) for the fog density. |
| `fogGreen` | text | `-1.0` | -1.0 ~ 1.0 | This is used client-side (but only if the client has this mod) for the fog color. |
| `fogRed` | text | `-1.0` | -1.0 ~ 1.0 | This is used client-side (but only if the client has this mod) for the fog color. |
| `horizon` | text | `-1.0` | -1.0 ~ 256.0 | This is used client-side (but only if the client has this mod) to set the height of the horizon. |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

## Against the datapack era

| | 2.0.22 | 7.4.12 |
|---|---|---|
| Profile keys | 128 | 131 |
| Format | Forge `.cfg`, one file per profile | JSON, one file per profile |
| Section names | `<category>_<profilename>` | Plain category names |
| Defaults | Inherited from a parent profile | Written into the generated file |
| Dimension wiring | `additionalDimensions`, `<numeric id>:<profile>` | `dimensionsWithProfiles`, `<dimension id>=<profile>` |
[game test](../examples/claim-tests.md#f12-8){.v .v-g}

Key names overlap heavily between the eras and the file holding them does not, so
treat a matching name as worth checking rather than as a guarantee. [code review](../examples/claim-tests.md#f12-8){.v .v-c}

## See also

- [The File-Asset Era](index.md)
- [Adding Your Own Content](adding-content.md)
- [Profile Reference](../reference/profile.md) for the datapack era's 131 keys <!-- noclaim -->

