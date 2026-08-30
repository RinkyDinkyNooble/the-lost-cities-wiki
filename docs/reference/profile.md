---
claims: verified
---

# Profile Reference

!!! tip "Every key of this page, in one runnable file"
    `docs/examples/every-key/profile/ekfull.json` sets all 155 profile keys at their
    documented defaults, in the section each one belongs to. It runs, and it builds
    the same world as a profile that sets none of them. Useful when you want to see
    where a key goes rather than what it does. [game test](../examples/claim-tests.md#ek-6){.v .v-g}

!!! tip "TL;DR"
    A profile is `config/lostcities/profiles/<name>.json`. Five sections: `lostcity`, `cities`, `explosions`, `cityspheres`, `client`, plus a root `public` flag. Every key below is optional, omit it and the default applies.

!!! warning "This page is the 131 keys of 7.4.12. Version 7.5 has 160."
    Every key below was verified against the 7.4.12 class itself. On 7.5.0 or later,
    29 keys are missing from this page and 3 of the keys that are here behave
    differently.

    | If you are on | Read [code review](../examples/claim-tests.md#key-1){.v .v-c} |
    |---|---|
    | 7.4.12 | This page, as written. |
    | 7.5.x, 8.4.1, 9.5.1 or 10.0.1 | This page, plus [What changed in 7.5](../versions/7-5.md). Those four versions share one identical set of 160 keys. |
    | 8.2.2 | This page, minus 19 keys it does not have. See [Key availability](../versions/key-availability.md). |

    Two changes here matter most. `streetGenerationMode` defaults to the new road
    planner, which refuses a building on any planned road chunk **before** it rolls
    `buildingchance`. And `highwayLevelFromCities` changed its default from `0` to
    `3`. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## The file name is the profile name

The mod reads every file in `config/lostcities/profiles/` whose name ends in
`.json`, and takes the profile name from the file name. It does not read a name
from inside the file. [code review](../examples/claim-tests.md#cfg-7){.v .v-c}

The name is everything **before the first dot**, because the mod splits the file
name on `.` and keeps the first piece. [game test](../examples/claim-tests.md#prf-4){.v .v-g}

| File name | Profile name | Notes [game test](../examples/claim-tests.md#prf-4){.v .v-g} |
|---|---|---|
| `mycity.json` | `mycity` | |
| `mycity2.json` | `mycity2` | Digits are fine. |
| `MyCity.json` | `MyCity` | Case is kept. Match it exactly in `common.toml`. |
| `my.city.json` | `my` | **Truncated at the first dot.** |
| `mycity.JSON` | not read | The extension test is case sensitive. |

!!! danger "Two files whose names share everything before the first dot collide silently"
    `city.a.json` and `city.b.json` both become the profile `city`. The mod stores
    profiles in a map keyed by that name, so the second file read replaces the
    first. There is no warning, and which one survives depends on directory order.

    Keep dots out of profile file names. <!-- noclaim -->

The name is used as a plain map key. It is not a resource location, so it is not
restricted to lowercase, and it does not need a namespace. What matters is that the
name in `dimensionsWithProfiles` matches the file name exactly, including case. [code review](../examples/claim-tests.md#cfg-4){.v .v-c}

!!! warning "Loading a profile and being offered it are two different things"
    The rules above govern whether the mod **reads** the file. Whether it is
    *offered* on the world creation screen is a separate test, and it is not about
    the characters in the name.

    The screen lists `STANDARD_PROFILES` filtered on `isPublic()`. A profile is
    offered unless its own file sets `"public": false`, which is how the
    outside-sphere profiles are hidden. Nothing anywhere inspects the characters of
    a name. An earlier version of this page said a digit, an uppercase letter, a
    hyphen or a dot kept a profile off the screen; that was observed once by hand,
    is contradicted by the code, and is withdrawn. [code review](../examples/claim-tests.md#prf-3){.v .v-c}

    The list is ordered `default` first, then by `String.compareTo`, which is code
    point order: digits before uppercase, uppercase before lowercase. It sorts the
    key rather than the label shown. [code review](../examples/claim-tests.md#prf-6){.v .v-c}

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

`public` is root-level, not inside a category. Defaults to `true`. Set `false` to hide a profile from the in-game selector (used for the "private" outside-sphere profiles mentioned on the [connects page](../getting-started/how-it-connects.md)). [code review](../examples/claim-tests.md#prf-3){.v .v-c}

Tables below: **Range** is the window the mod was designed and tested against, and the window the in-game screen enforces. A blank Range means it is not a number (text, block ID, list, or true/false). [code review](../examples/claim-tests.md#ref-1){.v .v-c}

!!! danger "Nothing validates a JSON profile"
    The ranges below are **not enforced** when a profile is loaded from `config/lostcities/profiles/`. `"buildingMaxFloors": 9999` or `"cityChance": -50` load without a warning and are used exactly as written, which shows up as broken generation rather than a clear error.

    Only the in-game config screen clamps: the clamp function has three callers, all of them GUI slider widgets. The load path never calls it, and the real bounds are not even registered by then, since the raw JSON values are read in first. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    Treat every range on this page as a rule you have to follow yourself. <!-- noclaim -->

!!! tip "There is also an in-game screen for this"
    The "Cities" button on the world-creation screen exposes about 40 of the more common keys from `lostcity`, `explosions`, and `cityspheres` below (chances, floor/cellar counts, explosion tuning, highway/rail toggles) without touching JSON. It is session-only: nothing is written to `config/lostcities/profiles/` until the world is created. Anything not shown there, including every `spawn*` key, is JSON-only.

## `lostcity`

### Identity & terrain

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `description` | *(text)* | | Shown for the profile in the selector. |
| `extraDescription` | `""` | | Extra info text. |
| `warning` | `""` | | Warning text shown on selection. |
| `worldStyle` | `"standard"` | | The World Style this profile uses. See [Namespaces](../getting-started/namespaces.md). |
| `icon` | `""` | | 64×64 icon path for the selector screen. |
| `landscapeType` | `"default"` | | Which terrain generator the profile uses, and therefore what the world outside the cities looks like. See [Landscape types](#landscape-types) for what each of the six values does. |
| `liquidBlock` | `minecraft:water` | | Block used as the profile's liquid. Bad ID silently falls back to water. |
| `baseBlock` | `minecraft:stone` | | Block used as the worldgen base. Bad ID silently falls back to stone. |
| `groundLevel` | `71` | 2 to 256 | The Y coordinate of city level 0. Every city level above it sits 6 blocks higher, so this is the anchor the whole vertical layout is measured from. |
| `seaLevel` | `-1` | -1 to 256 | Sea level Y. `-1` uses the world default. |
| `bedrockLayer` | `1` | 0 to 10 | Bedrock layer height. `0` = vanilla default bedrock. |
| `terrainFixLowerMinOffset` | `-4` | -40 to 40 | Lower-mesh offset (blocks) for raising adjacent terrain. |
| `terrainFixLowerMaxOffset` | `-3` | -40 to 40 | Upper end of that same offset range. |
| `terrainFixUpperMinOffset` | `-1` | -40 to 40 | Upper-mesh offset for lowering adjacent terrain. |
| `terrainFixUpperMaxOffset` | `1` | -40 to 40 | Upper end of that same offset range. |
| `avoidWater` | `false` | | If `true`, any block a **part** places that is the profile's liquid becomes air instead. Narrower than it sounds, see the note below. |
| `editMode` | `false` | | If `true`, the world records which part it placed where, enabling the [editor commands](../tooling/editing.md). Must be set before the world is created. |
| `generateNether` | `false` | | If `true`, the Nether is generated with the cavern-style generator instead of vanilla. |

!!! warning "`avoidWater` is narrower than its name and its official description"
    The mod's own config comment says *"all water will be avoided (replaced with air)"*. In 7.4.12 it has **exactly one** effect: while a part is being placed, a block that resolves to the profile's liquid becomes air instead.

    | | [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
    |---|---|
    | Palette characters mapping to water, inside your parts | **Removed** |
    | Natural oceans, rivers, lakes, aquifers | **Untouched** |
    | The water that fills "hard air" below sea level | **Untouched by this flag**, see below |

    So it drains *your buildings*, not *the world*. If you want a dry world you need terrain settings, not this. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! warning "`avoidFoliage` also controls water, which its name does not suggest"
    "Hard air" is a special palette result that becomes water when it sits below the chunk's water level, which is what floods the lower storeys of a coastal building.

    The check that decides this reads **`avoidFoliage`**, not `avoidWater`: [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    - `avoidFoliage: true` → hard air stays air, even below sea level
    - `avoidFoliage: false` → hard air floods, regardless of `avoidWater` [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    That looks like a mix-up in the mod rather than a deliberate design, but it is what 7.4.12 does. If you are trying to stop buildings flooding, `avoidFoliage: true` is the flag that works, at the cost of trees and flowers in parks. The per-part [`nowater` meta](part.md#nowater) does the same thing for one part without that cost. <!-- noclaim -->

### Landscape types

`landscapeType` accepts exactly six values. It decides what the world outside the cities is made of, and several other keys are only consulted on some of them. [game test](../examples/claim-tests.md#fail-6){.v .v-g}

| Value | What you get [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| `default` | Ordinary terrain, with cities sitting on it. This is the baseline every other type is a departure from. |
| `floating` | Islands floating in empty space, with cities on the islands. `cityAvoidVoid` matters here, because a city can otherwise hang off an island edge. |
| `space` | Everything inside glass bubbles in a void. The `cityspheres` section drives this. |
| `cavern` | Cities inside a large enclosed cave system rather than on an open surface. |
| `spheres` | Spheres on otherwise normal terrain, rather than in a void. |
| `cavernspheres` | Spheres inside a cavern. This is the hybrid: the mod treats it as **both** a cavern and a sphere type. |

!!! note "`cavernspheres` satisfies two checks at once"
    The mod's internal tests are not one-per-value. `isCavern()` is true for both `cavern` and `cavernspheres`, and `isSpheres()` is true for both `spheres` and `cavernspheres`. So anything gated on either check applies to `cavernspheres`.

    There is one test that separates them. `isVoidSpheres()` is true for `spheres` only, never for `cavernspheres`, which is what distinguishes spheres standing in open terrain from spheres enclosed in rock. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! warning "The terrain itself is not generated by this mod"
    Choosing anything other than `default` expects matching terrain to already exist. Lost Cities places cities, it does not generate floating islands or cavern systems. That is **Lost Worlds**, a separate mod by the same author. See [How It All Connects](../getting-started/how-it-connects.md).

### Spawn

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `spawnBiome` | `""` | | Force spawn in this biome. Empty = no restriction. |
| `spawnCity` | `""` | | Force spawn in this predefined city. |
| `spawnSphere` | `""` | | Force spawn in this predefined sphere. `<in>` = any sphere, `<out>` = outside every sphere. |
| `spawnNotInBuilding` | `false` | | If `true`, the spawn search rejects any position inside a building. |
| `forceSpawnInBuilding` | `false` | | If `true`, the spawn search only accepts positions inside a building. |
| `forceSpawnBuildings` | `[]` | | Restrict to these building names. Empty = any. |
| `forceSpawnParts` | `[]` | | Restrict to these part names. Empty = any. |
| `spawnCheckRadius` | `200` | 1 to 100000 | Starting search radius (blocks). |
| `spawnRadiusIncrease` | `100` | 1 to 100000 | Radius growth per failed search pass. |
| `spawnCheckAttempts` | `20000` | 1 to 1000000 | Max chunks checked before spawn search fails. |

!!! warning "A bad combination of these keys is a hard error, not a fallback"
    Setting any of `spawnBiome`/`spawnCity`/`spawnSphere`/`spawnNotInBuilding`/`forceSpawnInBuilding`/`forceSpawnBuildings`/`forceSpawnParts` replaces vanilla's spawn search entirely, it does not layer on top of it. If the combination you set cannot actually be satisfied anywhere within `spawnCheckAttempts` chunks (a `spawnCity`/`spawnSphere` name that does not match any [Predefined City/Sphere](predefined.md), or filters that contradict each other), world creation throws and fails outright instead of silently picking an imperfect spot. If a world with custom spawn settings will not generate, check these keys first.

### Buildings, streets, parks

!!! note "These get overridden by CityStyle"
    `buildingChance`, floor/cellar min/max, `parkChance`, `avoidFoliage`/`parkBorder`/`parkElevation`/`parkStreetThreshold`, `fountainChance`, `buildingFrontChance`, and `corridorChance` all have `CityStyle`-level equivalents. When a `CityStyle` sets its own value, it wins. These profile values are only the fallback.

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `buildingChance` | `0.3` | 0 to 1 | Chance a city chunk is a building instead of a street. |
| `buildingMinFloors` | `0` | 0 to 60 | The fewest floors above ground a building may be given. `0` means the ground floor only. |
| `buildingMaxFloors` | `8` | 0 to 60 | The most floors above ground. This is the top floor index, so `8` allows nine storeys counting the ground floor. |
| `buildingMinFloorsChance` | `4` | 1 to 60 | See formula below. |
| `buildingMaxFloorsChance` | `6` | 1 to 60 | See formula below. |
| `buildingMinCellars` | `0` | 0 to 20 | The fewest cellar levels. `0` means no cellar. |
| `buildingMaxCellars` | `3` | 0 to 20 | The most cellar levels. The chunk's city level is added to this, so buildings on higher terrain may go deeper. |
| `buildingDoorwayChance` | `0.6` | 0 to 1 | Chance of a doorway per eligible side/level. |
| `buildingFrontChance` | `0.2` | 0 to 1 | Chance that a building is given a front part. The front is then drawn by each adjacent street chunk, not by the building itself. See [City Style](citystyle.md#what-a-building-front-is). |
| `parkChance` | `0.2` | 0 to 1 | Chance a non-building section is a park. |
| `parkElevation` | `true` | | If `true`, parks get an extra layer of elevation. `false` leaves them flush with the street. |
| `parkBorder` | `true` | | If `true`, a park's border uses the street block as its base. |
| `parkStreetThreshold` | `3` | 0 to 8 | Surrounding-street count needed for a park. |
| `fountainChance` | `0.05` | 0 to 1 | Chance a street section has a fountain. |
| `corridorChance` | `0.7` | 0 to 1 | Chance a chunk can be a corridor (also needs adjacent corridors). |
| `bridgeChance` | `0.7` | 0 to 1 | The chance a chunk is eligible to carry a bridge. Terrain still has to suit one, so the visible rate is lower than this number. |
| `bridgeSupports` | `true` | | If `true`, bridges get support pillars where needed. Set `false` for bridges that span void. |
| `multiUseCorner` | `false` | | If `true`, a multi-building takes its level from its top-left corner only. `false` averages the surrounding level. |
| `useAvgHeightmap` | `false` | | If `true`, city level is averaged from surrounding heightmaps. More accurate, and slower, since it has to fetch neighbouring chunks. |
| `scatteredChanceMultiplier` | `1.0` | 0 to 100 | Multiplier on scattered-building chance. `0` disables them. |

!!! example "The floor-count formula"
    ```
    floors = buildingMinFloors + random(
        buildingMinFloorsChance + (cityFactor + 0.1) *
        (buildingMaxFloorsChance - buildingMinFloorsChance)
    )
    ```
    capped at `buildingMaxFloors`. `cityFactor` is how "strong" this particular city is, roughly 0 to 1. [code review](../examples/claim-tests.md#city-3){.v .v-c}

### Decay & overgrowth

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `vineChance` | `0.009` | 0 to 1 | Chance an exterior block gets a vine. |
| `randomLeafBlockChance` | `0.1` | 0 to 1 | Chance of leaf blocks at building/street borders. |
| `randomLeafBlockThickness` | `2` | 1 to 8 | How thick that leaf border looks. |
| `avoidFoliage` | `false` | | If `true`, parks generate with no trees or flowers. **Also stops hard-air filling with water**, see the note below. |
| `rubbleLayer` | `true` | | If `true`, the alternative dirt/stone/sand plus leaves layer generates, making cities look more overgrown. |
| `rubbleDirtScale` | `3.0` | 0 to 100 | Noise scale for the dirt rubble layer. Smaller = broader coverage. `0` disables it. |
| `rubbleLeaveScale` | `6.0` | 0 to 100 | Same, for the leaf rubble layer. |
| `ruinChance` | `0.05` | 0 to 1 | The chance a building is ruined, meaning its upper levels are partly destroyed. See [Damage, Ruins and Explosions](../under-the-hood/damage-and-ruins.md). |
| `ruinMinlevelPercent` | `0.8` | 0 to 1 | Fraction of building height where ruin destruction can start, low end. |
| `ruinMaxlevelPercent` | `1.0` | 0 to 1 | Same, high end. |

### Highways & railways

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `highwayRequiresTwoCities` | `true` | | If `true`, a highway needs a valid city at **both** ends. `false` lets one city be enough. |
| `highwayLevelFromCities` | `0` | 0 to 3 | `0` top-left city's height, `1` min of both, `2` max of both, `3` average. |
| `highwayDistanceMask` | `7` | ≥ 0 | Spacing bitmask, must be a power of two minus one (`0`, `1`, `3`, `7`, `15`...). `0` disables highways outright: the level lookup returns -1 before reading anything else, and no highway part is placed anywhere. [game test](../examples/claim-tests.md#bhv-3){.v .v-g} |
| `highwayMainPerlinScale` | `50.0` | 1 to 1000 | Noise scale, main axis. |
| `highwaySecondaryPerlinScale` | `10.0` | 1 to 1000 | Noise scale, cross axis. |
| `highwayPerlinFactor` | `2.0` | -100 to 100 | Noise threshold. `0` ≈ 50% chance on an eligible chunk. Higher suppresses highways. Only chunks at a multiple of 8 are eligible at all, so this thins an already sparse grid rather than placing highways anywhere. |
| `highwaySupports` | `true` | | If `true`, highways get support pillars where needed. Set `false` for highways that span void. |
| `railwayDungeonChance` | `0.01` | 0 to 1 | Chance a chunk next to a railway gets a dungeon. |
| `railwaysCanEnd` | `false` | | If `true`, a spot that would have been a station but has no city above gets a dead-end rail part instead. Useful when cities are rare. |
| `railwaysEnabled` | `true` | | If `false`, no rail lines generate. **Stations still do**, and they are more than half the network: turning this off alone left 13792 of 24320 railway blocks standing. `railwayStationsEnabled` has to go too. [game test](../examples/claim-tests.md#bhv-4){.v .v-g} |
| `railwayStationsEnabled` | `true` | | If `false`, no railway stations generate. |
| `railwaySurfaceStationsEnabled` | `true` | | If `false`, only underground stations generate, never surface ones. |

### Loot & misc

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `generateSpawners` | `true` | | If `false`, no spawners are placed even where a palette asks for them. |
| `generateLoot` | `true` | | If `false`, chests generate empty even where a palette sets a `loot` table. |
| `generateLighting` | `false` | | If `true`, torch palette entries are actually placed. **If `false`, every `torch` entry becomes air**, so buildings are unlit. |
| `chestWithoutLootChance` | `0.2` | 0 to 1 | Chance an eligible chest is empty. |
| `buildingWithoutLootChance` | `0.2` | 0 to 1 | Chance a building has neither loot nor spawners. |

## `cities`

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `cityChance` | `0.01` | -1 to 1 | Chance a chunk is a city center. Exactly `-1` switches to Perlin-noise mode. Raising it to `1.0` does not give you a world of buildings: the highway network then claims chunk after chunk, and a claimed chunk refuses a building whatever `buildingchance` says, so the whole grid comes back streets. Set `highwayDistanceMask` to `0` alongside it. [game test](../examples/claim-tests.md#mat-2){.v .v-g} |
| `cityMinRadius` | `50` | 1 to 2000 | The smallest radius, in blocks, a city circle can roll. |
| `cityMaxRadius` | `128` | 1 to 2000 | The largest radius, in blocks. Each city rolls a radius between the two. |
| `cityPerlinScale` | `3.0` | huge range, effectively unbounded | Noise scale for Perlin city placement. Larger values stretch the noise, so cities become broader and further apart. Ignored unless `cityChance` is exactly `-1`. |
| `cityPerlinInnerScale` | `0.1` | huge range, effectively unbounded | A second, finer noise scale layered on the first. Larger values smooth the city edges. Ignored unless `cityChance` is `-1`. |
| `cityPerlinOffset` | `0.1` | huge range, effectively unbounded | Shifts the noise threshold. Raising it makes cities rarer, lowering it makes them more common. Ignored unless `cityChance` is `-1`. |
| `cityThreshold` | `0.2` | 0 to 1 | City-factor cutoff for overlapping city circles to count as a city. |
| `citySpawnDistance1` | `0` | 0 to 10000000 | Distance (blocks) from spawn for city-factor scaling, first point. |
| `citySpawnDistance2` | `0` | 0 to 10000000 | Second point. `0` disables spawn-distance scaling entirely. |
| `citySpawnMultiplier1` | `1.0` | 0 to 1 | City factor at the first distance. |
| `citySpawnMultiplier2` | `1.0` | 0 to 1 | City factor at the second distance. |
| `cityStyleThreshold` | `-1.0` | disabled at -1, else 0 to 1 | Below this city factor, use `cityStyleAlternative` instead. |
| `cityStyleAlternative` | `""` | | The city style to use instead of the normal one wherever the city factor falls below `cityStyleThreshold`. Empty means no substitution. This is how a dense centre fades into sparse outskirts. |
| `cityAvoidVoid` | `true` | | `floating` landscape only. If `true`, a chunk detected as void gets no city, which stops cities hanging off island edges. |
| `cityLevel0Height` … `cityLevel7Height` | `75, 83, 91, 99, 107, 115, 123, 131` | 1 to 384 each | Terrain-height cutoffs assigning a city to level 0 to 7. |
| `cityMinHeight` | `50` | -1024 to 2048 | No cities below this Y. |
| `cityMaxHeight` | `150` | -1024 to 2048 | No cities above this Y. |
| `oceanCorrectionBorder` | `4` | -255 to 255 | Terrain correction offset for ocean chunks next to a city. |

## `explosions`

Normal and mini explosions are independent settings. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `explosionChance` | `0.002` | 0 to 1 | Per-chunk chance of a normal explosion. **Setting this to `0` does not turn explosions off.** `miniExplosionChance` is a separate roll, and its default is 15 times larger. |
| `explosionMinRadius` | `15` | 1 to 1000 | The smallest blast radius, in blocks, that a normal explosion can roll. |
| `explosionMaxRadius` | `35` | 1 to 3000 | The largest blast radius, in blocks. The mod rolls a radius between this and the minimum for each explosion. |
| `explosionMinHeight` | `75` | 1 to 256 | The lowest Y the **centre** of a normal explosion can be placed at. The blast still reaches below it. |
| `explosionMaxHeight` | `90` | 1 to 256 | The highest Y the centre can be placed at. |
| `miniExplosionChance` | `0.03` | 0 to 1 | Per-chunk chance of a mini explosion. This is the one that actually fires: at 15 times `explosionChance`, most damage in a default world comes from here. A test profile that wants undamaged buildings has to zero **both**. |
| `miniExplosionMinRadius` | `5` | 1 to 1000 | The smallest blast radius, in blocks, for a mini explosion. |
| `miniExplosionMaxRadius` | `12` | 1 to 3000 | The largest blast radius for a mini explosion. |
| `miniExplosionMinHeight` | `60` | 1 to 256 | The lowest Y a mini explosion centre can be placed at. |
| `miniExplosionMaxHeight` | `100` | 1 to 256 | The highest Y a mini explosion centre can be placed at. |
| `explosionsInCitiesOnly` | `true` | | If `true`, an explosion's centre can only be in a city chunk. The blast radius reaches outside it either way. |
| `debrisToNearbyChunkFactor` | `200` | 1 to 10000 | Debris spillover from nearby damaged chunks. Higher = less spillover. |

## `cityspheres`

Mostly relevant to `space`, `spheres`, and `cavernspheres` landscape types. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Default | Range | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `citySphereFactor` | `1.2` | 0.1 to 10 | Scales every city sphere's radius, on **any** sphere landscape. Not `space` only, whatever the config comment says. See the note below. [code review](../examples/claim-tests.md#sph-3){.v .v-c} |
| `citySphereChance` | `0.7` | 0 to 1 | The chance a given city is enclosed in a sphere. Only consulted on the sphere landscape types, and only on a chunk that is already a city chunk: at the default `cityChance` of `0.01` no sphere appeared anywhere in a 225 chunk grid. `0.0` places none. [game test](../examples/claim-tests.md#bhv-5){.v .v-g} |
| `citySphereClearAbove` | `0` | 0 to 1024 | Blocks cleared above the sphere. `0` disables. |
| `citySphereClearBelow` | `0` | 0 to 1024 | Blocks cleared below the sphere. `0` disables. |
| `citySphereClearAboveUntilAir` | `false` | | If `true`, clearing continues above whatever `citySphereClearAbove` removed, until it reaches air. |
| `citySphereClearBelowUntilAir` | `false` | | If `true`, the same downward, continuing past `citySphereClearBelow` until it reaches air. |
| `sphereSurfaceVariation` | `1.0` | 0 to 1 | Terrain variation inside spheres. Smaller = more varied. |
| `outsideSurfaceVariation` | `1.0` | 0 to 1 | The same terrain variation, applied outside the spheres instead of inside. Smaller values give more varied ground. |
| `monorailChance` | `0.8` | 0 to 1 | Chance a sphere requests a monorail connection each direction (needs a matching neighbour). |
| `monorailOffset` | `-2` | -100 to 100 | Monorail height offset relative to the sphere. |
| `onlyPredefined` | `false` | | If `true`, only [predefined](predefined.md) spheres generate and none are placed randomly. |
| `outsideProfile` | `""` | | Profile used for terrain outside the spheres. **Effectively required on a sphere landscape**: leave it empty and the first chunk that asks about the outside world throws `getOutsideProfile() is null`, uncaught. See [connects page](../getting-started/how-it-connects.md). |
| `outsideGroundLevel` | `-1` | -1 to 256 | **Deprecated**, use `groundLevel` on `outsideProfile` instead. |
| `grid32` | `false` | | If `true`, city spheres align to a 32×32 chunk grid. `false` uses 16×16. |

!!! warning "`citySphereFactor` is not `space` only, and it does not scale the whole radius"
    The mod's config comment reads *"Only used in 'space' landscape"*. `getSphereRadius` reads it on every path, with no landscape check anywhere in the method, so it applies on `spheres` and `cavernspheres` too. [code review](../examples/claim-tests.md#sph-3){.v .v-c}

    It also multiplies less than the name suggests. For a sphere on a predefined city the whole radius is scaled, but for an ordinary one only the random part is: [code review](../examples/claim-tests.md#sph-3){.v .v-c}

    | Sphere | Radius [code review](../examples/claim-tests.md#sph-3){.v .v-c} |
    |---|---|
    | On a predefined city | `radius × citySphereFactor` |
    | Anywhere else | `cityMinRadius + random(cityMaxRadius - cityMinRadius) × citySphereFactor` |

    So on an ordinary sphere the factor can never take the radius below `cityMinRadius`, and lowering it pulls every sphere towards that floor rather than shrinking it proportionally. [code review](../examples/claim-tests.md#sph-3){.v .v-c}


## `client`

!!! danger "All five of these do nothing on 7.4.12"
    They parse, land in fields and get copied between profiles, and **nothing ever applies them**. Setting them has no effect a player can see. [game test](../examples/claim-tests.md#prf-8){.v .v-g} [code review](../examples/claim-tests.md#prf-8){.v .v-c}

    `javap` over every class in the 7.4.12 jar finds no subscriber to `ViewportEvent`, `RenderFog` or `ComputeFogColor`, and no use of `FogRenderer` at all. The only classes touching `FOG_RED` are `ProfileSetup` and `LostCityProfile`, where the single read is a copy constructor. [code review](../examples/claim-tests.md#prf-8){.v .v-c}

    Confirmed at a client rather than inferred: same seed and position, two profiles differing only in this section, one of them with `fogRed` 1.0, `fogDensity` 0.9 and `horizon` 200. Sky, fog colour, fog density and horizon were identical in both, while the city generated from the profile in each. [game test](../examples/claim-tests.md#prf-8){.v .v-g}

    **This was read from 7.4.12 only.** Whether a later version wired the fog up has not been checked, so treat the table below as what the keys are declared to mean rather than what they do. [code review](../examples/claim-tests.md#prf-8){.v .v-c}

The table records the mod's own declared meaning for each key. `-1` is the "leave it alone" value throughout. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Default | Range | Declared meaning, not observed behaviour [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|---|
| `horizon` | `-1` | -1 to 256 | Overrides the client-side horizon height, which is where the sky meets the fog. `-1` leaves Minecraft's own value alone. |
| `fogRed` | `-1` | -1 to 1 | Red fog component, `0`to`1` when set explicitly. |
| `fogGreen` | `-1` | -1 to 1 | The green channel of the fog colour, `0` to `1`. `-1` leaves it alone. |
| `fogBlue` | `-1` | -1 to 1 | The blue channel of the fog colour, `0` to `1`. `-1` leaves it alone. |
| `fogDensity` | `-1` | -1 to 1 | How thick the fog is, `0` to `1`, where higher is thicker. `-1` leaves it alone. |

!!! info "Where the file lives, and what rewrites it"
    `config/lostcities/profiles/` is rewritten on every launch: the mod writes each
    profile it ships back to disk before reading the folder. Deleting or editing a
    shipped profile does not last, `__readonly__` is inert, and profiles of your own
    are untouched. See [Configuration](config.md#the-profiles-folder).

## See also

- [How It All Connects](../getting-started/how-it-connects.md) for how a profile gets picked at all
- [Glossary](../glossary.md) <!-- noclaim -->
