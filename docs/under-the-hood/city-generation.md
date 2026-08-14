# How a Chunk Becomes a City

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This section explains *why* the generator behaves the way it does. It is background for the keys documented elsewhere, and a starting point when a world does not look the way the settings say it should.

!!! tip "TL;DR"
    Every chunk's city/building decision is made once, the first time that chunk generates, from the world seed and chunk coordinates. It is cached for that chunk forever after. Changing a profile or city style has zero effect on chunks that already exist, only on chunks generated from then on.

## Decisions are permanent per chunk

Minecraft only ever asks a chunk generator to generate a given chunk once. Everything on this page, is-it-a-city, which building, how many floors, which city style, happens exactly once for that chunk and gets written into the actual placed blocks. Editing your profile or city style JSON afterward changes nothing about chunks that were already generated, only chunks generated after the change see it.

This is why a changed setting appears to do nothing. The setting works, and the chunks being looked at were written to disk before it changed. Testing a change means generating into new terrain, or force-regenerating the chunks.

## Two ways a chunk becomes part of a city

Controlled by the sign of a profile's `cityChance` (see [Profile Reference](../reference/profile.md#cities)):

=== "Discrete cities (cityChance ≥ 0)"

    Each chunk independently rolls a chance to become a **city center**, then gets a random radius between `cityMinRadius` and `cityMaxRadius`. A chunk counts as "in a city" based on its distance to every nearby center: each center contributes a factor that fades out toward its edge, and overlapping centers' factors **add together**. `cityThreshold` is the cutoff those summed factors need to clear.

    This is why bumping `cityMaxRadius` up does not just make individual cities bigger, past a point, neighbouring cities' fade zones start overlapping and summing past the threshold, and what were meant to be separate cities merge into one sprawling one.

=== "Continuous noise (cityChance = -1)"

    No discrete centers or radius at all. A 4-octave Perlin noise key, shaped by `cityPerlinScale`/`cityPerlinOffset`/`cityPerlinInnerScale`, covers the whole map, and `cityThreshold` gates it the same way. The result reads as organic, uneven city coverage instead of clean circles, useful for a wasteland or sprawl theme, where the goal is a region that is mostly city with pockets that are not, rather than distinct separated cities.

Either mode, being near spawn can also scale the effective city factor down via `citySpawnDistance1`/`2` and `citySpawnMultiplier1`/`2`, e.g. to keep the immediate spawn area less city-dense.

### Blending city styles at the edges

`cityStyleThreshold` and `cityStyleAlternative` let a city's outer, weaker-factor edge use a **different, usually sparser** city style than its dense core, one city, two looks, a believable transition from downtown to outskirts instead of a hard edge. Leave `cityStyleThreshold` at `-1` (default) to disable this and use one style throughout.

## City level: terrain height decides building scale

Every city chunk gets assigned a **city level**, 0 through 7, by comparing the real terrain height under it against the eight `cityLevel0Height`…`cityLevel7Height` thresholds. Taller natural terrain → higher city level.

City level then feeds directly into the [floor-count formula](../reference/profile.md#buildings-streets-parks) documented on the Profile page, specifically the `cityFactor` term. Practical effect: buildings on naturally elevated terrain tend to roll taller than buildings on low terrain, by design, not coincidence. If you want uniformly tall (or uniformly short) buildings regardless of terrain, `overrideFloors` on a [Building](../reference/building.md) is the way to force it per-building rather than fighting terrain height.

## City spheres

Relevant to the `space`, `spheres` and `cavernspheres` [landscape types](../reference/profile.md#landscape-types). Candidate sphere centres sit on a fixed grid, each independently chance-gated by `citySphereChance`.

The grid test is a bitmask on the chunk coordinate. By default a chunk is a candidate when both `chunkX & 15` and `chunkZ & 15` equal 8, which is one candidate every 16 chunks, offset to the middle of each block of 16. With `grid32` the mask becomes 31, giving one every 32 chunks. The offset of 8 is why candidates sit mid-grid rather than on the corners. Overlapping spheres resolve by disabling the smaller one. A [Predefined Sphere](../reference/predefined.md) always wins over a randomly-generated one at the same spot.

**Monorails need agreement from both sides**: each sphere independently rolls, per direction, whether it wants a monorail connection that way. A line only actually generates between two spheres if **both** rolled true facing each other. Setting `monorailChance: 1.0` means every sphere always wants one, which is not the same as every pair agreeing. At `1.0` both sides do roll true, so every geometrically possible connection appears, but the check remains per-pair rather than global.

## Highways

Two independent Perlin noise keys, one per axis, decide where highway lines run, shaped by `highwayMainPerlinScale`/`highwaySecondaryPerlinScale`/`highwayPerlinFactor`. `highwayDistanceMask` is a bitmask (must be `0`, `1`, `3`, `7`, `15`, and so on, a power of two minus one) that spaces candidate lines to regular intervals rather than letting the noise key produce them anywhere, this is why it jumps in specific increments rather than scaling smoothly. A candidate line only actually generates if it is at least 5 chunks long and touches two cities (unless `highwayRequiresTwoCities` is `false`), and its level (height) comes from whichever endpoint-combination rule `highwayLevelFromCities` selects.

## Multi-chunk buildings

[Multi-Building](../reference/multibuilding.md) placement is greedy and area-grid-based: each grid cell (`multisettings.areasize` on a [World Style](../reference/worldstyle.md)) rolls a random count of multibuildings to place, largest first, weighted toward whichever city style dominates that area. "Largest" is measured as `dimx + dimz`, not area, so a 1 by 5 multi-building sorts level with a 3 by 3. `correctstylefactor` (default `0.8`) can reject a placement into a chunk whose city style does not match closely enough, even if the area otherwise had room. If a multibuilding you added is not showing up where you expect, a style mismatch in that specific spot is a likely reason, not a placement-chance issue.

## See also

- [Profile Reference](../reference/profile.md) for every key named above
- [The Generation Pipeline](generation-pipeline.md) for what happens once a chunk's decisions are made
- [Damage, Ruins & Explosions](damage-and-ruins.md)
