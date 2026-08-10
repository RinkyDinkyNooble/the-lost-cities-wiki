# How a Chunk Becomes a City

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This section explains *why* the generator behaves the way it does, for readers who want the mental model behind the fields they are already setting, or who are debugging something that does not look right.

!!! tip "TL;DR"
    Every chunk's city/building decision is made once, the first time that chunk generates, from the world seed and chunk coordinates. It is cached for that chunk forever after. Changing a profile or city style has zero effect on chunks that already exist, only on chunks generated from then on.

## Decisions are permanent per chunk

Minecraft only ever asks a chunk generator to generate a given chunk once. Everything on this page, is-it-a-city, which building, how many floors, which city style, happens exactly once for that chunk and gets written into the actual placed blocks. Editing your profile or city style JSON afterward changes nothing about chunks that were already generated, only chunks generated after the change see it.

This is the actual explanation behind "I changed a setting and nothing happened": the setting works, but the chunks you are looking at already existed before you changed it. Testing a change properly means generating into brand-new terrain, or using a tool that force-regenerates specific chunks.

## Two ways a chunk becomes part of a city

Controlled by the sign of a profile's `cityChance` (see [Profile Reference](../reference/profile.md#cities)):

=== "Discrete cities (cityChance ≥ 0)"

    Each chunk independently rolls a chance to become a **city center**, then gets a random radius between `cityMinRadius` and `cityMaxRadius`. A chunk counts as "in a city" based on its distance to every nearby center: each center contributes a factor that fades out toward its edge, and overlapping centers' factors **add together**. `cityThreshold` is the cutoff those summed factors need to clear.

    This is why bumping `cityMaxRadius` up does not just make individual cities bigger, past a point, neighboring cities' fade zones start overlapping and summing past the threshold, and what were meant to be separate cities merge into one sprawling one.

=== "Continuous noise (cityChance = -1)"

    No discrete centers or radius at all. A 4-octave Perlin noise field, shaped by `cityPerlinScale`/`cityPerlinOffset`/`cityPerlinInnerScale`, covers the whole map, and `cityThreshold` gates it the same way. The result reads as organic, uneven city coverage instead of clean circles, useful for a wasteland/sprawl theme where "the whole region is basically city, with pockets that are not" is the goal rather than distinct, separated cities.

Either mode, being near spawn can also scale the effective city factor down via `citySpawnDistance1`/`2` and `citySpawnMultiplier1`/`2`, e.g. to keep the immediate spawn area less city-dense.

### Blending city styles at the edges

`cityStyleThreshold` and `cityStyleAlternative` let a city's outer, weaker-factor edge use a **different, usually sparser** city style than its dense core, one city, two looks, a believable transition from downtown to outskirts instead of a hard edge. Leave `cityStyleThreshold` at `-1` (default) to disable this and use one style throughout.

## City level: terrain height decides building scale

Every city chunk gets assigned a **city level**, 0 through 7, by comparing the real terrain height under it against the eight `cityLevel0Height`…`cityLevel7Height` thresholds. Taller natural terrain → higher city level.

City level then feeds directly into the [floor-count formula](../reference/profile.md#buildings-streets-parks) documented on the Profile page, specifically the `cityFactor` term. Practical effect: buildings on naturally elevated terrain tend to roll taller than buildings on low terrain, by design, not coincidence. If you want uniformly tall (or uniformly short) buildings regardless of terrain, `overrideFloors` on a [Building](../reference/building.md) is the way to force it per-building rather than fighting terrain height.

## City spheres

Relevant to `space`, `spheres`, and `cavernspheres` [landscape types](../reference/profile.md#identity-terrain). Candidate sphere centers sit on a fixed grid (every 16 chunks, or every 32 with `grid32`), each independently chance-gated by `citySphereChance`. Overlapping spheres resolve by disabling the smaller one. A [Predefined Sphere](../reference/predefined.md) always wins over a randomly-generated one at the same spot.

**Monorails need agreement from both sides**: each sphere independently rolls, per direction, whether it wants a monorail connection that way. A line only actually generates between two spheres if **both** rolled true facing each other. Setting `monorailChance: 1.0` does not mean every possible connection appears, it means every sphere always wants one, which is different from every pair of neighbors agreeing (it does mean every geometrically possible connection appears, since both sides are guaranteed to roll true, but it is worth knowing the check is per-pair, not global).

## Highways

Two independent Perlin noise fields, one per axis, decide where highway lines run, shaped by `highwayMainPerlinScale`/`highwaySecondaryPerlinScale`/`highwayPerlinFactor`. `highwayDistanceMask` is a bitmask (must be `0`, `1`, `3`, `7`, `15`, and so on, a power of two minus one) that spaces candidate lines to regular intervals rather than letting the noise field produce them anywhere, this is why it jumps in specific increments rather than scaling smoothly. A candidate line only actually generates if it is at least 5 chunks long and touches two cities (unless `highwayRequiresTwoCities` is `false`), and its level (height) comes from whichever endpoint-combination rule `highwayLevelFromCities` selects.

## Multi-chunk buildings

[Multi-Building](../reference/multibuilding.md) placement is greedy and area-grid-based: each grid cell (`multisettings.areasize` on a [World Style](../reference/worldstyle.md)) rolls a random count of multibuildings to place, biggest footprint first, weighted toward whichever city style dominates that area. `correctstylefactor` (default `0.8`) can reject a placement into a chunk whose city style does not match closely enough, even if the area otherwise had room. If a multibuilding you added is not showing up where you expect, a style mismatch in that specific spot is a likely reason, not a placement-chance issue.

## See also

- [Profile Reference](../reference/profile.md) for every field named above
- [The Generation Pipeline](generation-pipeline.md) for what happens once a chunk's decisions are made
- [Damage, Ruins & Explosions](damage-and-ruins.md)
