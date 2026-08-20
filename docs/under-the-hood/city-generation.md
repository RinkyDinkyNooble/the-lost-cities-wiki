---
claims: verified
---

# How a Chunk Becomes a City

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This section covers why the generator behaves as it does: background for the keys documented elsewhere, and a starting point when a world does not look the way the settings say it should. <!-- noclaim -->

!!! tip "TL;DR"
    Every chunk's city and building decision is made once, the first time that chunk generates, from the world seed and the chunk coordinates. Changing a profile or city style has no effect on chunks that already exist, only on chunks generated afterwards. [code review](../examples/claim-tests.md#city-1){.v .v-c}

## Decisions are permanent per chunk

Minecraft asks a chunk generator to generate a given chunk once. Everything on this page, is it a city, which building, how many floors, which city style, happens exactly once for that chunk and is written into the placed blocks. Editing profile or city style JSON afterwards changes nothing about chunks that already exist. [code review](../examples/claim-tests.md#city-1){.v .v-c}

That is why a changed setting appears to do nothing. The setting works, and the chunks being looked at were written to disk before it changed. Testing a change means generating into new terrain, or force-regenerating those chunks. See [Seeing your changes](../tooling/commands.md#seeing-your-changes). [code review](../examples/claim-tests.md#ns-10){.v .v-c}

## Two ways a chunk becomes part of a city

Decided by the sign of a profile's `cityChance`, documented on the [Profile Reference](../reference/profile.md#cities). [code review](../examples/claim-tests.md#city-2){.v .v-c}

=== "Discrete cities, `cityChance` 0 or above"

    Each chunk independently rolls a chance to become a **city centre**, then takes a random radius between `cityMinRadius` and `cityMaxRadius`. Whether a chunk counts as in a city comes from its distance to every nearby centre: each centre contributes a factor that fades towards its edge, and overlapping centres' factors **add together**. `cityThreshold` is the cutoff those summed factors have to clear. [code review](../examples/claim-tests.md#city-2){.v .v-c}

    That is why raising `cityMaxRadius` does more than make individual cities bigger. Past a point, neighbouring fade zones overlap and sum past the threshold, and cities meant to be separate merge into one sprawl. [code review](../examples/claim-tests.md#city-2){.v .v-c}

=== "Continuous noise, `cityChance` of -1"

    No discrete centres and no radius. A four-octave Perlin noise key, shaped by `cityPerlinScale`, `cityPerlinOffset` and `cityPerlinInnerScale`, covers the whole map, and `cityThreshold` gates it the same way. The result reads as uneven, organic coverage rather than clean circles, which suits a wasteland or a sprawl: a region that is mostly city with pockets that are not, rather than distinct separated cities. [code review](../examples/claim-tests.md#city-2){.v .v-c}

In either mode, being near spawn can scale the effective city factor down through `citySpawnDistance1` and `2` with `citySpawnMultiplier1` and `2`, which is how the immediate spawn area is kept less dense. [code review](../examples/claim-tests.md#city-2){.v .v-c}

### Blending city styles at the edges

`cityStyleThreshold` and `cityStyleAlternative` let a city's outer, weaker-factor edge use a **different, usually sparser** city style than its dense core. One city, two looks, and a transition from downtown to outskirts instead of a hard edge. Leaving `cityStyleThreshold` at its default of `-1` disables this and uses one style throughout. [code review](../examples/claim-tests.md#city-2){.v .v-c}

## City level: terrain height decides building scale

Every city chunk is assigned a **city level** from 0 to 7, by comparing the real terrain height under it against the eight `cityLevel0Height` to `cityLevel7Height` thresholds. Taller natural terrain gives a higher city level. [code review](../examples/claim-tests.md#city-3){.v .v-c}

City level then feeds the [floor-count formula](../reference/profile.md#buildings-streets-parks) through its `cityFactor` term, so buildings on naturally elevated terrain tend to roll taller than buildings on low ground. That is by design. For uniform height regardless of terrain, `overrideFloors` on a [Building](../reference/building.md) forces it per building rather than fighting the terrain. [code review](../examples/claim-tests.md#city-3){.v .v-c} [game test](../examples/claim-tests.md#bld-2){.v .v-g}

## City spheres

Relevant to the `space`, `spheres` and `cavernspheres` [landscape types](../reference/profile.md#landscape-types). Candidate sphere centres sit on a fixed grid, each independently gated by `citySphereChance`. [code review](../examples/claim-tests.md#city-4){.v .v-c}

The grid test is a bitmask on the chunk coordinate. By default a chunk is a candidate when both `chunkX & 15` and `chunkZ & 15` equal 8, which is one candidate every 16 chunks, offset to the middle of each block of 16. `grid32` changes the mask to 31, giving one every 32 chunks. The offset of 8 is why candidates sit mid-grid rather than on the corners. Overlapping spheres resolve by disabling the smaller one, and a [Predefined Sphere](../reference/predefined.md) always beats a randomly generated one at the same spot. [code review](../examples/claim-tests.md#city-4){.v .v-c}

!!! warning "Monorails need agreement from both sides"
    Each sphere independently rolls, per direction, whether it wants a monorail connection that way, and a line generates between two spheres only where **both** rolled true facing each other. `monorailChance: 1.0` means every sphere always wants one, which is not the same as every pair agreeing. At `1.0` both sides do roll true, so every geometrically possible connection appears, but the check stays per pair rather than global. [code review](../examples/claim-tests.md#city-4){.v .v-c}

    All of that is read from the code. **No monorail has been placed in a test.** Sphere generation itself has been, and monorails have not, in any arrangement tried. [unverified](../examples/claim-tests.md#bhv-6){.v .v-u}

## Highways

Two independent Perlin noise keys, one per axis, decide where highway lines run, shaped by `highwayMainPerlinScale`, `highwaySecondaryPerlinScale` and `highwayPerlinFactor`. [code review](../examples/claim-tests.md#city-5){.v .v-c}

`highwayDistanceMask` is a bitmask, so it takes `0`, `1`, `3`, `7`, `15` and so on, a power of two minus one. It spaces candidate lines at regular intervals rather than letting the noise key put them anywhere, which is why it jumps in fixed increments instead of scaling smoothly. **`0` is not the tightest spacing, it is off**: the level lookup returns -1 before it reads anything else, and no highway generates anywhere. [game test](../examples/claim-tests.md#bhv-3){.v .v-g} A candidate line generates only where it is at least 5 chunks long and touches two cities, unless `highwayRequiresTwoCities` is `false`, and its height comes from whichever endpoint rule `highwayLevelFromCities` selects. [code review](../examples/claim-tests.md#city-5){.v .v-c}

## Multi-chunk buildings

[Multi-Building](../reference/multibuilding.md) placement is greedy and area-grid based. Each grid cell, sized by `multisettings.areasize` on a [World Style](../reference/worldstyle.md), rolls a random count of multi-buildings to place, largest first, weighted towards whichever city style dominates that area. [code review](../examples/claim-tests.md#city-6){.v .v-c}

Largest is measured as `dimx + dimz` rather than area, so a 1 by 5 multi-building sorts level with a 3 by 3. `correctstylefactor`, default `0.8`, can reject a placement into a chunk whose city style does not match closely enough even where the area had room. A multi-building not showing up where you expect is more often a style mismatch in that spot than a placement-chance problem. [code review](../examples/claim-tests.md#city-6){.v .v-c}

## See also

- [Profile Reference](../reference/profile.md) for every key named above
- [The Generation Pipeline](generation-pipeline.md) for what happens once a chunk's decisions are made
- [Damage, Ruins & Explosions](damage-and-ruins.md) <!-- noclaim -->
