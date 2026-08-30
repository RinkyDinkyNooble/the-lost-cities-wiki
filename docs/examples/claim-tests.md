# Claim tests

Most of this wiki is read out of the mod's compiled code. Reading establishes what
the code says. It does not establish what a world does.

This page is the register of claims that have been checked in a running world, the
packs that check them, and how to run those packs.

Every result below is from Lost Cities **7.4.12** on Minecraft **1.20.1**, Forge,
unless the entry says otherwise. An entry naming another version was produced by
running the same pack against that jar with nothing else changed, which is what
makes the two numbers comparable at all.

Ten versions have been run this way, from **2.0.22** on Minecraft 1.12.2 to
**10.0.1** on Minecraft 26.1.2. `testrig/` in this repository installs any of them
and runs these packs.

## What has been checked in a world

### Buildings and levels

| ID | Claim | Result |
|---|---|---|
| `BLD-1`{#bld-1} | Levels run `0` to `maxfloors` **inclusive**, so `maxfloors: 3` is a four-storey building | Confirmed. `maxfloors: 6` produced 7 storeys, `maxfloors: 2` produced 3. |
| `BLD-2`{#bld-2} | `overrideFloors` replaces the profile's bounds rather than narrowing them | Confirmed. The overriding building generated at 1 storey beside 5-storey towers declaring the same bounds without the key. |
| `BLD-3`{#bld-3} | `minfloors` is a `max()` applied after the maximum, so it can exceed every ceiling | Confirmed. Two buildings declaring `minfloors: 6` and `maxfloors: 6`, one with `overrideFloors` and one without, both generated 6 storeys under a profile allowing 2 to 3. |
| `BLD-4`{#bld-4} | A level that matches no part reference fails the chunk | Confirmed. `Misconfiguration! Floor were generated for a building where no part condition matches!` |
| `BLD-5`{#bld-5} | `parts2` is an overlay placed at the same origin on the same level | Confirmed. Base part 1504 blocks, overlay 8 blocks, both present. |
| `BLD-6`{#bld-6} | `allowDoors: false` leaves the wall as the part draws it | Confirmed. The same three-storey part placed 2240 wall blocks with doors allowed and 2256 with `allowDoors: false`. |
| `BLD-7`{#bld-7} | `filler` and `rubble` resolve against the **building's** palette, not the part's | Confirmed, by 590 failed chunks when they did not. |
| `BLD-8`{#bld-8} | `rubble` is used by the ruin pass | Confirmed. 40 blocks of an otherwise unused character with ruins on, none with ruins off. |

### Conditions and part selection

| ID | Claim | Result |
|---|---|---|
| `CND-1`{#cnd-1} | Test keys chain with AND, never OR | Confirmed. A building gated `ground: false` **and** `top: false` came out banded rather than mixed. |
| `CND-2`{#cnd-2} | `range` includes both ends | Confirmed. |
| `CND-3`{#cnd-3} | A third number in `range` is discarded silently | Confirmed. `"0,2,9"` gave levels 0 to 2, not 0 to 9. |
| `CND-4`{#cnd-4} | `belowpart` tests the **current** part, not the one below | Confirmed, and it is a mod bug. A two-level building whose first entry was gated `belowpart: "<none>"` came out gold on both levels with no diamond. See [Known Issues](../troubleshooting/known-issues.md#belowpart-tests-the-wrong-part-in-every-version-that-has-it). |
| `CND-5`{#cnd-5} | `inpart` and `belowpart` never match from a building's `parts` list | Confirmed. The floor loop passes the literal `<none>` as the current part. |
| `CND-6`{#cnd-6} | `inpart` does work in a Condition reached from a palette | Confirmed. The chest's `LootTable` came out as the table on the `inpart`-gated entry. |
| `CND-7`{#cnd-7} | `range` works there too, and counts storeys | Confirmed. `"0,0"` gave one table on the ground floor, `"1,100"` gave another two storeys up. |

### Palettes

| ID | Claim | Result |
|---|---|---|
| `PAL-1`{#pal-1} | The merge order is style, then building, then part | Confirmed. The same character gave gold from the building palette, diamond from the part palette, and lapis where the building overrode a character the shipped style defines concretely. |
| `PAL-2`{#pal-2} | A part palette **merges** into the building's rather than replacing it | Confirmed. A part palette defining one character still resolved every other character from the building's. |
| `PAL-3`{#pal-3} | A weighted `blocks` list fills 128 slots, and entries after the one that fills the last slot are unreachable | Confirmed. A list of 120 white, 20 black, then 100 red produced **no red block anywhere**. |
| `PAL-4`{#pal-4} | `frompalette` resolves to the aliased character | Confirmed. |
| `PAL-5`{#pal-5} | A concrete definition beats an alias, whatever the order | Confirmed. An alias on a character the shipped style defines concretely lost to that definition. |
| `PAL-6`{#pal-6} | A circular `frompalette` leaves the character undefined, and reports nothing at load | Confirmed. `Could not find entry '<char>' in the palette for part '<part>'!` at generation, nothing at load. |
| `PAL-7`{#pal-7} | A `char` of more than one character keeps the first, silently | Confirmed. `"char": "王zz"` registered `王`. |
| `PAL-8`{#pal-8} | `mob` names a Condition, not an entity | Confirmed. A condition resolving to `minecraft:blaze` produced blaze spawners. |
| `PAL-9`{#pal-9} | `loot` names a Condition, not a loot table | Confirmed, and the page said otherwise. |
| `PAL-10`{#pal-10} | With `generateLoot` on and both loot chances at `0`, every chest is filled | Confirmed. 12 of 12. |
| `PAL-11`{#pal-11} | `tag` places raw NBT | Confirmed. |
| `PAL-12`{#pal-12} | `torch: true` requires `generateLighting`, and without it the character becomes air | Confirmed. |
| `PAL-13`{#pal-13} | `damaged` covers the rubble band, not the ruined section | Confirmed, and the page overstated it. See [the control-chunk note](#counting-needs-a-control). |

### Parts

| ID | Claim | Result |
|---|---|---|
| `PRT-1`{#prt-1} | A layer is one flat string read as `charAt(z * xsize + x)`, so row breaks are formatting | Confirmed in both directions. |
| `PRT-2`{#prt-2} | A layer longer than `xsize * zsize` shifts characters and drops the tail, silently | Confirmed. A 17-character row placed its marker one column along; position 256 was never read. |
| `PRT-3`{#prt-3} | A layer shorter than that fails the chunk | Confirmed. `String index out of range: 255`. |
| `PRT-4`{#prt-4} | `shape=` in a stair block string is discarded and recomputed | Confirmed. Five isolated stairs written `shape=outer_right` all came out straight, and a perpendicular pair produced a corner. |

### City styles, streets and selectors

| ID | Claim | Result |
|---|---|---|
| `CTY-1`{#cty-1} | A multi-building grid is `buildings[x][z]`, outer list X | Confirmed. Red north-west, yellow south-west, blue north-east, green south-east. |
| `CTY-2`{#cty-2} | A street part name accepts a list, sampled per chunk | Confirmed. Both marked variants appear across the road network, mixed. |
| `CTY-3`{#cty-3} | `streetblocks.parts` is all or nothing on inheritance | Confirmed. All 7 shapes restated, all generate. |
| `CTY-4`{#cty-4} | `streetblocks.parts.full` never generates | **Refuted**, and it is a mod bug. See [Streets](../concepts/infrastructure-parts.md#streets). |
| `CTY-5`{#cty-5} | Selector inheritance is additive, so an inherited selector cannot be emptied | Confirmed, indirectly: emptying one required not inheriting at all. |
| `CTY-6`{#cty-6} | An empty `bridges` selector fails even at `bridgeChance: 0` | Confirmed. 1842 failed chunks, `Invalid name given to minecraft:root getOrThrow!`. |
| `CTY-7`{#cty-7} | `parks`, `fountains`, `stairs`, `fronts` and `raildungeons` are safe to leave empty | Confirmed. Zero failed chunks with all five empty. |
| `CTY-8`{#cty-8} | A city style that inherits nothing must define every character the generator dereferences unguarded | Confirmed. Each run reveals only the next missing character. |
| `CTY-9`{#cty-9} | Omitting a selector and writing `[]` are the same thing | Confirmed. Both end at an empty list. |

### Predefined cities

| ID | Claim | Result |
|---|---|---|
| `PRE-1`{#pre-1} | A pinned building's `chunkx` and `chunkz` are offsets from the city centre | Confirmed, and the page said they were world coordinates. |
| `PRE-2`{#pre-2} | A predefined city generates at `cityChance: 0.0` | Confirmed. One city, where it was pinned, in an otherwise empty world. |
| `PRE-3`{#pre-3} | `preventruins` protects a pinned building | Confirmed. Under `ruinChance: 1.0`, 1767 wall blocks on the unprotected copy against 2224 on the protected one. |

### Profiles

| ID | Claim | Result |
|---|---|---|
| `PRF-1`{#prf-1} | A `block` value carrying a 1.12 style `@meta` suffix fails the **whole palette**, not just that character | Confirmed. `minecraft:red_sandstone@2` reaches `ResourceLocation`, whose path rejects `@`, so the palette throws while being built and every character in the file stops resolving. Planted in a working pack, all three of its towers vanished. Lost Cities 7.4.12 ships one such file, `lostcities:bricks_desert_redsand`, unnoticed because assets are built on demand and no shipped style selects it. |
| `PRF-2`{#prf-2} | A profile name containing a digit, an uppercase letter, a hyphen or a dot is read normally but is **not offered on the world creation screen** | **Withdrawn.** Observed once by hand and contradicted by the code. The list is `STANDARD_PROFILES` filtered on `isPublic()`, and nothing tests the characters of a name. |
| `PRF-3`{#prf-3} | A profile is offered unless its own file sets `"public": false` | Confirmed from `LostCitySetup.toggleProfile` and the `LostCityProfile(String, String)` constructor, which reads `public` and treats a missing key as true. That is how the sphere-outside profiles are hidden. |
| `PRF-4`{#prf-4} | A profile is named after everything before the **first dot** in its file name | Confirmed from `ProfileSetup.readProfiles`, which uses `getName().split("\\.")[0]`. `my.thing.json` registers as `my`. |
| `PRF-5`{#prf-5} | One unreadable profile file drops every profile after it | Confirmed from the same method: the `IOException` handler ends in `return`, not `continue`, so the scan stops. Which profiles vanish depends on directory order. |
| `PRF-6`{#prf-6} | The profile list is ordered `default` first, then by `String.compareTo` | Confirmed from the comparator `toggleProfile` sorts with. That is code point order, so a digit sorts before an uppercase letter and an uppercase letter before a lowercase one. It is not case-insensitive alphabetical, and it sorts the key rather than the label shown. |
| `PRF-7`{#prf-7} | A profile key in the wrong section is never read | Confirmed indirectly: a wrong config **section** caused Forge to reset the file to its defaults with no error. |

### Failure behaviour

| ID | Claim | Result |
|---|---|---|
| `FAIL-1`{#fail-1} | A mistake in an asset does not crash the game | Confirmed across every pack. The mod catches it per chunk and logs. |
| `FAIL-2`{#fail-2} | A profile naming a `worldStyle` no loaded datapack defines **does** crash | Confirmed. `Description: Feature placement`, because it resolves before the catch. |
| `FAIL-3`{#fail-3} | A fault raised while building a chunk's `BuildingInfo` spreads to neighbouring chunks | Confirmed. 3 broken buildings produced 77 failed chunks across a 13 by 10 chunk area. |
| `FAIL-4`{#fail-4} | A fault raised while placing blocks stays in its own chunk | Confirmed. A circular palette alias 6 chunks from those three failed exactly 1 chunk. |
| `FAIL-5`{#fail-5} | On a sphere landscape nothing catches either | Confirmed. Same pack, same broken building: `default` gave 35 caught and 0 uncaught, `spheres` gave 18 caught and 21 uncaught, and the server shut down. |
| `FAIL-6`{#fail-6} | `landscapeType` takes lowercase values, and a wrong one stops the game starting | Confirmed. `"SPACE"` gives `Bad landscape type: SPACE!` during mod construction. |
| `FAIL-7`{#fail-7} | A sphere landscape needs `cityspheres.outsideProfile` | Confirmed. Without it, `getOutsideProfile() is null`, uncaught. |

### Version comparison

| ID | Claim | Result |
|---|---|---|
| `VER-1`{#ver-1} | A datapack means the same thing on 7.4.12 and 7.5.1 | Confirmed. The pack written for 7.4.12 gives 28 of 28 on 7.5.1 unchanged. |
| `VER-2`{#ver-2} | 7.5 changed placement, not asset handling | Confirmed. The only counts that moved were wall totals, each by a multiple of 16, which is one doorway. |

## The claim register

Pages carrying verification chips have a numbered entry here for every claim they
make. An entry names how the claim was checked and how to check it again. A claim
marked **unverified** has had neither treatment. That is a statement about the
evidence, not about the claim.

| Status | Means |
|---|---|
| **game test** | Run on a headless Forge server against a named pack, with the blocks read back out of the world |
| **code review** | Read out of the compiled 7.4.12 jar, with the class and method named |
| **unverified** | Neither. The mod's own documentation and the official wiki do not count as either |

A claim may be both game tested and code reviewed. A claim may not be unverified
and anything else at once, and it may not be cited as unverified on one page and
verified on another.

Text that asserts nothing about the mod (navigation, a scope note, a
recommendation) is marked `<!-- noclaim -->` in the source. That records a
decision rather than granting an exemption: the rule is that no block is left
undecided, not that every block is a claim.

`docs/examples/check_claims.py` enforces all of it. It reads every page whose
front matter says `claims: verified`, and fails when a block on one carries
neither a chip nor a `noclaim`, when a chip points at a register entry that does
not exist, when a chip's label and colour disagree, or when a claim's status
contradicts itself across pages.

```bash
python docs/examples/check_claims.py
```

## How a game test on this page is run

Every game test here follows one procedure. It needs a headless server running the
named Lost Cities version and nothing else.

| Step | What |
|---|---|
| 1 | Copy the pack's `data/` and `pack.mcmeta` into `<world>/datapacks/<name>/` |
| 2 | Copy the pack's profile files into `config/lostcities/profiles/` |
| 3 | Point a dimension at the profile: `dimensionsWithProfiles = ["lostcities:lostcity=<profile>"]`, under `[profiles]` in `config/lostcities/common.toml` |
| 4 | Generate the grid with `/execute in lostcities:lostcity run forceload add <x0> <z0> <x1> <z1>`, in **block** coordinates |
| 5 | Count with `/execute in lostcities:lostcity run clone <from> <to> <scratch> filtered <block>`, which reports how many blocks it copied |

The scratch destination has to be loaded as well, and `/clone` caps at 32768 blocks,
which is one chunk footprint 128 levels tall. The traps that each cost a test round
are collected at the end of this page.

The recorded runs were driven over RCON by a script rather than typed by hand. No
result here depends on that script: each one is the five steps above against the
pack and profile its section names.

That script is in the repository, under `testrig/`, and it runs the versions this
page cites. It downloads nothing: point it at server jars and portable Java builds
you fetch yourself, and it reports which versions are ready.

```bash
python testrig/rig.py doctor
python testrig/rig.py run 7.4.12 wiki-test11
```

Minecraft 1.12 has none of `/forceload`, `/execute in <dimension>` or `/data`, so the
file-asset tests use a different route. See [F12-10](#f12-10).


### Namespaces

Source page: [Namespaces](../getting-started/namespaces.md). Pack:
`docs/examples/wiki-test10/`, namespace `nstest`, profiles `wtten` and
`wttenbare`.

#### NS-1 The folder directly under `data/` is the namespace { #ns-1 }

**Game test.** Every asset in `wiki-test10` sits under `data/nstest/` and every
reference to it is written `nstest:`. The control tower generates: 512 gold blocks
in chunk 8,8. Nothing in the pack is under `data/lostcities/`.

**Code review.** `RegistryAssetRegistry.get` looks the name up in the Minecraft
dynamic registry for its key, which is populated by the vanilla datapack loader
from the file path. Lost Cities does no path parsing of its own.

#### NS-2 The middle `lostcities` folder is the registry, not the pack { #ns-2 }

**Game test.** Same pack. Assets resolve from `data/nstest/lostcities/...` while
being named `nstest:...`, so the second path segment cannot be contributing to the
name.

**Code review.** `CustomRegistries` declares each registry key as
`lostcities:worldstyles`, `lostcities:palettes` and so on. The registry's own
namespace supplies that segment.

#### NS-3 A name with no colon is read as `lostcities:` { #ns-3 }

**Code review.** `DataTools.fromName(String)`:

```java
if (name.contains(":")) return new ResourceLocation(name);
return new ResourceLocation("lostcities", name);
```

The inverse, `DataTools.toName(ResourceLocation)`, prints a `lostcities:` name
back out bare, which is why the mod's own files reference each other with no
namespace.

**Game test.** Three buildings in `wiki-test10` differ from the control only in
dropping `nstest:` from one reference each. All three failures name
`lostcities:<thing>` in the log, never `nstest:<thing>`.

#### NS-4 An unresolved reference throws { #ns-4 }

**Code review.** `RegistryAssetRegistry` has three lookups and all three funnel
into `get(CommonLevelAccessor, ResourceLocation)`. That method asks the registry,
gets `null`, and passes the `null` to the asset constructor, which fails. The
`catch (Exception)` around it rethrows as
`RuntimeException("Error getting resource " + name + "!")`. The name-based
`get(level, String)` returns `null` only when the **string** is null, never when
the lookup misses, so it is not the quiet variant its name suggests.

**Game test.** Every failing case in `wiki-test10` produces that message, in the
server crash report and in the `Error generating chunk` lines of the log.

#### NS-5 A profile's unresolved `worldStyle` crashes the server { #ns-5 }

**Game test.** Profile `wttenbare` is `wtten` with one character changed:
`"worldStyle": "test"` in place of `"nstest:test"`. The server died on the first
forced chunk, before any probe could run.

```
Description: Feature placement
java.lang.RuntimeException: Error getting resource lostcities:test!
  at RegistryAssetRegistry.get(RegistryAssetRegistry.java:82)
  at DefaultDimensionInfo.<init>(DefaultDimensionInfo.java:44)
Caused by: java.lang.NullPointerException: Cannot invoke
  "WorldStyleRE.getRegistryName()" because "object" is null
```

**Code review.** `DefaultDimensionInfo`'s constructor resolves the world style
before any chunk is built, and stores it in a `final` field with no null check.
There is no per-chunk `try`/`catch` that far up.

The same behaviour is recorded as [FAIL-2](#fail-2), from an earlier run.

#### NS-6 An unresolved part name in `parts` fails the chunks around the building { #ns-6 }

**Game test.** Building `nstest:barepart` names its part `ns_lapis` rather than
`nstest:ns_lapis`. Result: 0 lapis blocks where the building was pinned, and 41
chunks logged as
`Error generating chunk <x>,<z>: Error getting resource lostcities:ns_lapis!`,
spread over a 4 by 7 chunk area rather than the one chunk that holds the building.

#### NS-7 An unresolved `refpalette` fails only where that palette is needed { #ns-7 }

**Game test.** Two buildings, one difference between them.

| Building | Its part | Result |
|---|---|---|
| `nstest:barepalette` | declares its own `refpalette` | 512 diamond blocks. **The tower generates normally.** Two unrelated chunks fail |
| `nstest:barepalette_only` | declares no palette | 0 emerald blocks. The building is absent |

Both buildings carry the same broken `"refpalette": "test"`. A part's own palette
merges over the building's, so when the part supplies every character used, the
building's palette is never resolved and the bad reference is never reached.

**Code review.** `Building.getPalette` and `BuildingPart.getPalette` both call
`getOrThrow`, but only on first use, and `CompiledPalette` is assembled per
character.

`validate.py` reports both buildings before the game is involved:
`` `filler` is '#', defined in ['nstest:test'], but this building references none
of those ``. The static check catches the case the world hides.

#### NS-8 A profile is named by its file name and takes no namespace { #ns-8 }

**Code review.** `ProfileSetup.readProfiles` builds each profile as
`new LostCityProfile(file.getName().split("\.")[0], contents)`. There is no
namespace anywhere in that path, and `common.toml` matches profiles by that bare
key.

#### NS-9 Override resolution: last pack wins, whole file, no merging { #ns-9 }

**Game test.** Three packs, built for this test. A base pack holds everything
except one palette, and two further packs each define
`data/nsov/lostcities/palettes/shared.json` under the same name. They differ in what
the wall character `W` resolves to, and only one of them also defines a marker
character `M`. A second building drawn entirely in `M` answers the merge question in
blocks rather than by inference.

All three go in `<world>/datapacks/` together. Minecraft enables a newly discovered
pack automatically and orders them by folder name, so the folder names set the load
order. Naming them `base`, `ov-aaa` and `ov-zzz` makes that order explicit, and
running it twice with the two files swapped separates position from content.

| Run | Earlier folder | Later folder | Wall | Marker |
|---|---|---|---|---|
| 1 | gold, defines `M` | diamond | 512 diamond, 0 gold | 0 iron |
| 2 | diamond | gold, defines `M` | 512 gold, 0 diamond | 512 iron |

Three things follow, and the second is the one people get wrong.

The **later** folder wins, and it is position rather than content that decides:
swapping the two files flipped the result exactly.

The win is **whole file**. In run 1 the character `M`, defined only in the losing
file, did not survive into the merged palette at all. It failed its chunk with
`Could not find entry 'M' in the palette for part 'nsov:ov_marker'!`, which is the
same message an undefined character produces. Run 2, where the winning file defines
`M`, had **zero failed chunks**.

Nothing warns that an override happened. Run 1's only output was that one chunk
failure, and it names the character rather than the collision that caused it.

#### NS-10 Assets are read once per world load { #ns-10 }

**Code review.** Lost Cities registers no `ReloadListener` in 7.4.12.
`RegistryAssetRegistry` caches each built asset in its own `assets` map, and
`AssetRegistries.reset()` has exactly two callers: `ModSetup.init`, once at
`FMLCommonSetupEvent`, and `LostCityFeature`. Nothing on the `/reload` path
touches either.

### Fronts, stuff objects and rotation

Source pages: [City Style](../reference/citystyle.md), [Stuff Object](../reference/stuff.md),
[Palette](../reference/palette.md), [The Generation Pipeline](../under-the-hood/generation-pipeline.md).
Pack: `docs/examples/wiki-test11/`, namespace `nstf`, profile `wteleven`.

#### FRT-1 A front is drawn by the adjacent street chunk, never by the building { #frt-1 }

**Game test.** One pinned building with a pinned street on each of its four sides.
The building is white, the front is emerald.

| Chunk | Emerald |
|---|---|
| The building's own chunk | **0** |
| Street to the east | 126 |
| Street to the west | 124 |
| Street to the north | 124 |
| Street to the south | 126 |

So one building's front really is drawn four times, once by each neighbour, and
never in the building's own chunk.

**Code review.** The street branch calls `generateFrontPart` four times, on
`getXmin`, `getZmin`, `getXmax` and `getZmax`, with `ROTATE_NONE`, `ROTATE_90`,
`ROTATE_180` and `ROTATE_270`. Each call passes the **neighbour's** `BuildingInfo`
as the generation context, which is what makes a front resolve against the
building's palette rather than the street's.

#### FRT-2 At `cityChance: 0.0` an unpinned chunk inside a predefined city is not a city chunk { #frt-2 }

**Game test.** Found while the front test was returning nothing. With
`buildingchance` at `0.0` and the streets left unpinned, `/lcdev report` on the
chunk beside the pinned building said:

```
is city: false
building: none, this is a street or open chunk
```

Pinning the four streets flipped it to `is city: true` and the fronts appeared. So
the radius of a predefined city does not by itself make the chunks inside it part
of the city when `cityChance` is `0.0`. A chunk becomes city because it is pinned,
as a building or as a street.

That is why the older test packs pin the streets between their buildings, and it is
worth knowing before concluding that some other feature is broken.

#### FRT-3 Adding a front while inheriting leaves a one-in-four draw { #frt-3 }

**Game test.** `citystyle_common` already ships three fronts, and selector
inheritance is additive, so a city style that inherits it and adds one has four in
the pool. The first three runs of this test drew a shipped front and found no
emerald at all, which reads exactly like the feature not working.

Overriding `lostcities:building_front1`, `2` and `3` at their own paths, which
replaces them outright by [NS-9](#ns-9), made the draw deterministic and the test
passed 7 of 7. A concrete instance of [CTY-5](#cty-5).

#### STF-1 A stuff object's `column` is a palette character, and it is what gets placed { #stf-1 }

**Code review.** `Stuff.actuallyGenerateStuff` takes `getColumn()`, applies
`charAt(0)`, and resolves it through `CompiledPalette.get(char)`. It is not a
filter and not a block name. A multi-character string keeps the first character,
the same rule as `char` in a palette.

The mod's own `chains.json` and `cobweb.json` use `"column": "{"` and
`"column": "\\"`, which are palette characters rather than anything readable as a
block.

**Game test.** A stuff object with `"column": "I"`, where `I` is `iron_block` in
the pack's palette, `inbuilding: true`, `attempts: 30` and counts of 4 to 9, placed
5 iron blocks inside the building. Nothing else in the pack uses `I`.

#### SPH-1 A predefined sphere generates its dome where it is pinned { #sph-1 }

**Game test.** Pack `docs/examples/wiki-test13/`, namespace `nssp`, profile
`wtthirteen` with `landscapeType: spheres`, `onlyPredefined: true` and
`citySphereChance: 0.0`, so nothing random can appear beside it. The sphere is
pinned at `centerx: 136`, `centerz: 136`, `radius: 40`.


Glass counted per chunk, and the pattern is the dome:

| Chunk | Blocks | Glass | Why |
|---|---|---|---|
| 8,8 | 128 to 143 | 513 | The centre. The shell only crosses it above and below |
| 6,8 | 96 to 111 | 1093 | Just inside the western edge, where the shell stands almost vertical |
| 11,8 | 176 to 191 | 0 | Starts exactly at the eastern edge, 136 + 40 |
| 8,11 | z 176 to 191 | 0 | The same on the other axis |

The city pinned at the same spot generated inside it, 1024 blocks. No failed
chunks and no crash, which is worth saying because a sphere landscape has no
per-chunk catch. See [FAIL-5](#fail-5).

`onlyPredefined` and `outsideProfile` are covered by that run. Random sphere
placement, the grid mask, `centerpart`, and monorails between spheres are not.

#### SPH-2 A sphere's glass is one block for the whole dome { #sph-2 }

**Game test.** The shipped `Z` character is a weighted list of four glass types:
plain, gray stained, blue stained and light blue stained. Every glass block in the
dome came back `minecraft:gray_stained_glass`, in both chunks that held any, and
the other three types were absent everywhere.

**Code review.** `CitySphere` holds `private BlockState glassBlock`, one field, set
once through `setBlocks(glass, base, side)`. `Spheres.fillSphere` is handed that
single state and uses it for the whole dome. The character is resolved once per
sphere rather than once per block, so a weighted list gives a dome of one colour
instead of a speckled one.

This is the same shape of surprise as [the rail stripes](../troubleshooting/known-issues.md#railways-come-out-in-flat-16-block-colour-strips),
where `railmain` resolves once per chunk.

#### SCT-1 Scattered structures generate, one per area cell { #sct-1 }

**Game test.** Pack `docs/examples/wiki-test12/`, namespace `nssc`, profile
`wttwelve`. No city anywhere: `cityChance` is `0.0` and nothing is pinned, so every
chunk is open ground and anything that appears came from the scattered pass.


The world style's `scattered` block is tuned to remove the randomness rather than
fight it:

```json
{ "areasize": 1, "chance": 1.0, "weightnone": 0,
  "list": [{ "name": "nssc:sc_tower", "weight": 1, "maxheightdiff": 250 }] }
```

`areasize: 1` makes every chunk its own area, `chance: 1.0` makes every area place
something, and `weightnone: 0` takes "nothing" out of the draw. Chunks 8,8, 10,10
and 12,12 each held 512 gold blocks, the full footprint of the structure, with no
failed chunks.

That covers placement, `terrainheight: average` and `terrainfix: clear`. The other
`terrainheight` and `terrainfix` values, `nearhighway`, `allowvoid`,
`maxheightdiff` as a filter, and `rotatable` being inert are still only read from
the code.

#### LW-1 Lost Cities adapts to terrain, it does not generate it { #lw-1 }

**Code review.** The mod ships no chunk generator class. Its own dimension is
ordinary vanilla noise terrain:

```json title="data/lostcities/dimension/lostcity.json"
{
  "type": "lostcities:lostcity",
  "generator": {
    "type": "minecraft:noise",
    "seed": 0,
    "settings": "minecraft:overworld",
    "biome_source": { "type": "minecraft:multi_noise", "preset": "overworld" }
  }
}
```

Every use of `isFloating`, `isCavern` and `isSpace` in `LostCityTerrainFeature`
reads the existing terrain and adapts to it: avoiding void, seating a building's
filler and border, clearing headroom in a cavern. None of them build the landscape.

So `landscapeType` tells the mod what to **expect** underneath, not what to make. A
`floating` profile over ordinary terrain gets cities placed by floating-island
rules on ground that is not floating.

The mod's own API carries one hook for the other mod, `ILostWorldsChunkGenerator`,
and it exposes a single method, `getOuterSeaLevel()`, read only by the sphere
generator. That is the whole of the coupling.

No world test. Lost Worlds is not on the rig, so what a `floating` profile looks
like without it has not been observed, only what the code does with it.

#### EXP-1 Export collapses two characters that map to one block { #exp-1 }

**Code review.** `EditorInfo` holds
`private final Map<BlockState, Character> reversedPalette`, and
`addPaletteEntry(char, BlockState)` writes into it. Two characters mapping to the
same block state means the second write replaces the first, so only one survives.

`CommandExportPart` asks `getPaleteEntry(BlockState)` for each position and, when
that returns nothing, allocates the next unused character from a fixed alphabet.
Neither path can recover a distinction the reverse map has already lost.

#### ROT-1 Only tagged blocks and rails rotate with a part { #rot-1 }

**Code review.** `LostCityTerrainFeature.transformBlockState(Transform, BlockState)`
is three branches and nothing else:

1. the block is in `lostcities:rotatable`, so `state.rotate(transform)`
2. the state is a rail, so the rail shape property is turned instead
3. neither, so the state is returned **unchanged**

The shipped tag holds one entry, `#minecraft:stairs`. So out of the box stairs
rotate, rails rotate, and everything else keeps the facing it was authored with.

No world test. Rotation reaches parts through highways, railways, monorails and
scattered buildings, none of which the rig has generated.

#### ROT-2 What the tag ships as, per version, and how a pack adds to it { #rot-2 }

**Code review.** The tag was read out of each jar at
`data/lostcities/tags/blocks/rotatable.json`, which is the path in all seven,
including the 1.21 ones:

| Jar | `values` |
|---|---|
| `lostcities-1.20-7.4.12` | `#minecraft:stairs` |
| `lostcities-1.20-7.5.1` | `#minecraft:stairs`, `#minecraft:doors` |
| `lostcities-1.20-7.5.2` | `#minecraft:stairs`, `#minecraft:doors` |
| `lostcities-1.21-8.2.2` | `#minecraft:stairs` |
| `lostcities-1.21-8.4.1` | `#minecraft:stairs`, `#minecraft:doors` |
| `LostCities-1.21.11-9.5.1` | `#minecraft:stairs`, `#minecraft:doors` |
| `LostCities-26.1.2-10.0.1` | `#minecraft:stairs`, `#minecraft:doors` |

None of the seven sets `replace`. So doors arrive in 7.5.1, are absent again in 8.2.2,
and are present from 8.4.1 onward.

**The namespace in the path is the tag's, not the pack author's.** A tag is loaded by
its own id, so every datapack contributing to `lostcities:rotatable` writes
`data/lostcities/tags/blocks/rotatable.json` and the loader merges what it finds. A
file under a different namespace declares a different tag, which nothing reads. That is
Minecraft's tag loader rather than anything Lost Cities does.

`"replace": true` in such a file discards the entries Lost Cities ships, so stairs would
stop rotating. Absent, as in all seven jars, contributions accumulate.

**Being in the tag reaches exactly one call.** ROT-1's first branch is
`state.rotate(transform)`, so the tag decides whether `rotate` is called and the block's
own implementation decides what that does. A block whose `rotate` ignores its facing is
unchanged by being tagged.

No world test. Read from the jars, and from the same method ROT-1 quotes.

### Generation order, damage and ruins

Source pages: [The Generation Pipeline](../under-the-hood/generation-pipeline.md),
[Damage, Ruins & Explosions](../under-the-hood/damage-and-ruins.md),
[How a Chunk Becomes a City](../under-the-hood/city-generation.md).

#### PIPE-1 The per-chunk order of operations { #pipe-1 }

**Code review.** Read off `LostCityTerrainFeature`'s entry point and the methods it
calls in sequence. The order is structure avoidance, city or non-city, sphere centre
piece, railways and rail dungeons, torch fixup, damage and debris, flush.

#### PIPE-2 Ruins run inside the city-chunk pass, explosions run after it { #pipe-2 }

**Code review.** The city-chunk branch calls, in this order, `generateBuilding`,
`generateStreet`, `generateRuins`, the highway levels, `generateStreetDecorations`,
`generateHighways`, `generateRubble`, `generateStuff`. Explosion damage and debris
are applied later, in the top-level chunk pass, after the torch fixup.

Anything called after `generateRuins` therefore lands on an already-ruined building
and is not itself ruined. Explosion damage, being later still, reaches all of it.

#### PIPE-3 A part's air is resolved by the caller, not the part { #pipe-3 }

**Code review.** Parts carry a placeholder for empty space rather than plain air.
What it becomes, real air, water or nothing, is decided by the system placing the
part and the current Y against the world's water level. That is why one basement
floods below sea level and another does not, with no difference in their JSON.

#### CITY-1 A chunk's decisions are made once and written into blocks { #city-1 }

**Code review.** Minecraft asks a chunk generator for a given chunk once, and
`LostCityTerrainFeature` resolves city membership, building choice, floor count and
city style during that call, then writes blocks. Nothing re-reads the profile for an
existing chunk, and the mod registers no reload listener. See [NS-10](#ns-10).

#### CITY-2 Two city-placement modes, chosen by the sign of `cityChance` { #city-2 }

**Code review.** `City.getCityFactor` branches on `cityChance` being negative. At
zero or above it sums a fading factor from every nearby centre and compares the sum
against `cityThreshold`, which is why overlapping radii merge cities. At `-1` it
reads a four-octave Perlin key instead and gates that with the same threshold.
`citySpawnDistance1` and `2` scale the result near spawn in both modes.

#### CITY-3 City level comes from terrain height, and feeds the floor count { #city-3 }

**Code review.** The eight `cityLevel0Height` to `cityLevel7Height` thresholds are
compared against the chunk's real terrain height to produce a level from 0 to 7,
which enters the floor-count formula as `cityFactor`.

#### CITY-4 Sphere candidates sit on a bitmasked grid, and monorails need both sides { #city-4 }

**Code review.** A chunk is a sphere candidate when `chunkX & 15` and `chunkZ & 15`
both equal 8, one every 16 chunks offset to mid-grid, or `& 31` under `grid32`.
Overlapping spheres disable the smaller. Each sphere rolls per direction whether it
wants a monorail, and the line is generated only where both sides rolled true, so
`monorailChance` is a per-sphere want rather than a per-pair guarantee.

#### CITY-5 Highway lines come from two noise keys and a power-of-two mask { #city-5 }

**Code review.** One Perlin key per axis, shaped by `highwayMainPerlinScale`,
`highwaySecondaryPerlinScale` and `highwayPerlinFactor`. `highwayDistanceMask` is
applied as a bitmask, so only a power of two minus one behaves as intended. A line
needs to be at least 5 chunks long and to touch two cities unless
`highwayRequiresTwoCities` is off.

#### CITY-6 Multi-building placement is greedy, per area cell, and style-weighted { #city-6 }

**Code review.** Each `multisettings.areasize` cell rolls a count and places largest
first, where largest is `dimx + dimz` rather than area. `correctstylefactor`,
default `0.8`, rejects a placement whose chunk city style does not match closely
enough.

#### DMG-1 Two block tags decide what survives damage { #dmg-1 }

**Code review.** `lostcities:notbreakable` never breaks, and ships with bedrock,
end portal, end portal frame and end gateway. `lostcities:easybreakable` breaks more
readily and ships with `forge:glass`. An untagged block rolls on distance from the
blast centre and its strength.

#### DMG-2 `debrisToNearbyChunkFactor` is inverse { #dmg-2 }

**Code review.** A higher value produces **less** spillover into neighbouring
chunks, not more. Rubble outside the chunk that rolled the explosion is expected.

#### DMG-3 Nothing exempts an ordinary building from the ruin pass { #dmg-3 }

**Code review.** No Building key protects against ruins: not `preventruins`, not
`noruin`, and nothing under another name. The only per-building exemption in the mod
is `preventruins` on an entry of a predefined city.

**Game test.** Under `ruinChance: 1.0`, the unprotected copy of a building kept 1767
wall blocks against 2224 on the protected copy. See [PRE-3](#pre-3).

#### DMG-4 Ruin chance is profile-wide { #dmg-4 }

**Code review.** A city style can override `explosionchance`. There is no city style
key for ruin chance, so one district cannot be ruined while another stays pristine
through city styles alone. A predefined city is the only per-place control.

### The file-asset era

Source pages: [The File-Asset Era](../file-era/index.md),
[File-Era Assets](../file-era/assets.md),
[Adding Your Own Content](../file-era/adding-content.md).

Read from `lostcities-1.12-2.0.22.jar`, the newest build for Minecraft 1.12.2.
Nothing here has been run: Forge 1.12.2 boots through LaunchWrapper, which needs a
system class loader that is a `URLClassLoader`, and that stopped being true in
Java 9. The rig is installed and waiting on a Java 8 runtime.

#### F12-1 The boundary is the mod version, not the Minecraft version { #f12-1 }

**Code review.** 5.0.4 reads file assets and 5.3.29 reads datapacks, and both are
labelled 1.18. The tell is inside the jar: a file-era build carries
`assets/lostcities/citydata/*.json` and a class named `AbstractAssetRegistry`, and a
datapack build carries `data/lostcities/lostcities/<type>/` and
`RegistryAssetRegistry`.

#### F12-2 Ten asset types, many to a file, each naming itself { #f12-2 }

**Code review.** A file-era asset file is a JSON **array of objects**, and each
object carries its own `type` and `name`. Nothing is derived from the file path, so
one file holds many assets of mixed types.

`AssetRegistries.load` dispatches on `type` and accepts ten values: `building`,
`city`, `citystyle`, `condition`, `multibuilding`, `palette`, `part`, `sphere`,
`style`, `worldstyle`.

The mod's own ten files use eight of them. `city` and `sphere`, the predefined
placements, are supported and unused, the same as in 7.4.12. Counted across the
shipped files: 173 parts, 36 palettes, 25 buildings, 10 multi-buildings, 6 city
styles, 6 styles, 3 conditions, 2 world styles.

Five datapack-era types have no file-era equivalent at all: `variant`, `scattered`,
`stuff`, and the separate `predefinedcities` and `predefinedspheres` registries.

#### F12-3 Assets load from a config list, in order { #f12-3 }

**Code review.** `LostCityConfiguration.ASSETS` is a config option, not a fixed
list. Its description in `general.cfg` reads:

> List of asset libraries loaded in the specified order. If the path starts with
> '/' it is going to be loaded directly from the classpath. If the path starts with
> '$' it is loaded from the config directory

`ModSetup` walks it and branches on the first character:

| Prefix | Resolved as | Example |
|---|---|---|
| `/` | `Class.getResourceAsStream(path)`, so inside a jar | `/assets/lostcities/citydata/library.json` |
| `$` | `<config dir>/` plus the rest | `$lostcities/userassets.json` becomes `config/lostcities/userassets.json` |
| anything else | `RuntimeException: Invalid path for lostcity resource in 'assets' config!` | |

The shipped default is the mod's ten files in a fixed order, with
`$lostcities/userassets.json` **last**.

#### F12-4 A later file replaces an earlier asset of the same name { #f12-4 }

**Code review.** `AbstractAssetRegistry` stores each asset with `Map.put` keyed by
name, so a second asset of the same name and type overwrites the first. Combined
with the load order in [F12-3](#f12-3), and with `userassets.json` sitting last,
anything you define there replaces the mod's version of that name.

That is the file era's whole override mechanism. There is no namespace and no pack
ordering, only position in one config list.

#### F12-5 Config is Forge `.cfg`, and one file per profile { #f12-5 }

**Code review.** `ConfigSetup` builds `config/lostcities/general.cfg` for the main
settings, then one `config/lostcities/profile_<name>.cfg` for each profile. Both are
Forge's old `.cfg` format rather than TOML, and a profile is a whole file rather
than a JSON object.

Three options in `general.cfg` decide what exists:

| Option | Description as the mod writes it |
|---|---|
| `assets` | The load list from [F12-3](#f12-3) |
| `profiles` | `List of all supported profiles (used for world creation). Warning! Make sure there is always a 'default' profile!` |
| `privateProfiles` | `List of privatep profiles that cannot be selected by the player but are only used as a child profile of another one` |

The typo in that last description is the mod's own.

`LostCityProfile` in 2.0.22 registers 116 profile keys, against 131 in 7.4.12.

#### F12-6 The dimension wiring uses a colon, not an equals { #f12-6 }

**Code review.** The option is `additionalDimensions` in the `general` category, and
its description gives the format as `'<id>:<profile>'`.

The datapack era's `dimensionsWithProfiles` uses `<dimension id>=<profile name>`
instead. Carrying the `=` habit backwards produces an entry that does not parse.

#### F12-7 Block names carry a `@meta` suffix { #f12-7 }

**Code review.** File-era palettes are written against Minecraft before the 1.13
flattening, so a block is `minecraft:rail@1`, `minecraft:golden_rail@8` and so on.
The shipped `rails` palette is full of them.

This is the direct ancestor of a bug still shipping in 7.4.12, where the palette
`lostcities:bricks_desert_redsand` carries `minecraft:red_sandstone@2` and cannot be
built at all. See [PRF-1](#prf-1). A file-era palette copied forward without
rewriting every block name breaks the same way.

#### F12-8 The 1.12.2 rig boots, and what it wrote { #f12-8 }

**Game test.** Forge 14.23.5.2859 on
Minecraft 1.12.2, Lost Cities `1.12-2.0.22`, on a portable Temurin **JRE 8** at
a portable Temurin JRE 8. The server reached `Done (6.759s)!` with five mods
loaded and registered dimension **111**.

Java 8 and nothing newer. Forge 1.12.2 boots through LaunchWrapper, which casts the
system class loader to `URLClassLoader`, and Java 9 stopped making it one:

```
java.lang.ClassCastException: jdk.internal.loader.ClassLoaders$AppClassLoader
cannot be cast to java.net.URLClassLoader
  at net.minecraft.launchwrapper.Launch.<init>(Launch.java:34)
```

What first launch produced, all of it read back off disk:

| | |
|---|---|
| `config/lostcities/general.cfg` | 14 options |
| `config/lostcities/profile_<name>.cfg` | **18 files**, 16 public plus 2 private |
| Keys in `profile_default.cfg` | **128**, across six categories |

**Three things this corrected.** The `assets` load order in the generated file is
not the order the bytecode reads in: `conditions.json` is **first**, not fifth, and
`highwayparts.json` comes before `railparts.json`. This page had it wrong from the
disassembly alone.

Profile sections are named `<category>_<profilename>`, so `cities_default` in one
file and `cities_wasteland` in another. Copying a profile file therefore needs all
six headers renamed as well as the file.

One option, `maxcaveheight`, is registered with its name and category swapped. It
lands in a section called `maxcaveheight` holding a key called
`structures_<profilename>`, the reverse of every other option in the file.

**Corrected here too:** this wiki previously put 2.0.22 at 116 profile keys, from an
earlier reading that nothing checked. The file a server writes holds 128.

`general.cfg` also settles the dimension question: `dimensionId` is **111**, a
number rather than a resource location, and `additionalDimensions` takes
`<numeric id>:<profile>`.

#### F12-9 A userassets.json generates, end to end { #f12-9 }

**Game test.** On the rig from [F12-8](#f12-8), driven by a 1.12-specific
procedure because three of the commands the later tests use do not exist there. One `config/lostcities/userassets.json` holding seven assets of
five types, none of which the mod ships:

```json
[ { "type": "palette",   "name": "wt_palette", "...": "..." },
  { "type": "part",      "name": "wt_gold",    "...": "..." },
  { "type": "building",  "name": "wt_gold",    "...": "..." },
  { "type": "citystyle", "name": "wt_style",   "...": "..." },
  { "type": "worldstyle","name": "wt_world",   "...": "..." },
  { "type": "city",      "name": "wt_city",    "...": "..." } ]
```

| Probe | Result |
|---|---|
| Gold at chunk 0,0 | First at y=65, **1856 blocks** |
| Diamond at chunk 2,0 | First at y=53, **1628 blocks** |

The pack is `docs/examples/file-era-test/`, and the counts above are what the test
rig reproduces on the seed it pins. An earlier run on an unpinned seed gave 1372 for
both: the building is the same and the terrain it is cut into is not, which is why
the rig fixes the seed.

Both pinned buildings landed at the chunk offsets the `city` asset gave them, drawn
from a palette that exists only in `userassets.json`. That exercises the whole
chain: the config load list, name-based resolution with no namespaces, and the
`city` type, which the mod ships no example of.

**Three things this took that the pages did not say.**

`level-type=lostcities` in `server.properties`. The mod registers a **world type**
of that name, and `defaultProfile` only says which profile a Lost Cities overworld
uses. Without the world type the overworld is ordinary terrain and `defaultProfile`
does nothing visible.

Two boots. Minecraft 1.12 has no `/forceload`, so a headless server generates only
the region around world spawn. The first boot exists to `setworldspawn 0 64 0`, and
the second generates the pinned city inside that region.

`/clone` needs its destination loaded, and with no way to force a chunk the scratch
area has to sit inside the spawn region too. The later tests park it 992 blocks
out, which cannot work here.

#### F12-10 The 1.12 command set cannot run the datapack-era procedure { #f12-10 }

**Game test.** Three commands the other rigs depend on do not exist in 1.12:

| 1.20.1 | 1.12.2 |
|---|---|
| `/forceload add` | nothing equivalent. Generation follows world spawn |
| `/execute in <dim> ... if block` | `/testforblock <x> <y> <z> <block>` |
| `/data get block` | nothing equivalent |

`/clone ... filtered` survives in both and still reports how many blocks it copied,
which is why counting works the same way on either rig.

### Version and key availability

Source pages: [Key availability](../versions/key-availability.md),
[What changed in 7.5](../versions/7-5.md), [Which version do I have](../versions/index.md),
[The file-asset era](../versions/legacy.md), [The NeoForge line](../versions/neoforge.md).

#### KEY-1 The key sets come from disassembling each jar { #key-1 }

**Code review.** Every version's asset codecs are disassembled and each `fieldOf`,
`optionalFieldOf` and `Tools.listOrStringList` call read for the key name it
registers. The sets are then compared. No release notes are used. The result is
`docs/examples/mod-keys.json`, which `validate.py` checks the reference pages
against on every build. See [REF-1](#ref-1).

`testrig/extract-keys.py` does this, so the export is reproducible rather than
hand-built, and **twelve versions** are recorded rather than two:

```bash
python testrig/extract-keys.py
```

Running it against the two versions that had been built by hand reproduced both
exactly, 253 and 268 codec keys and 131 and 160 profile keys, which is what makes
the ten it added trustworthy.

Profile keys come from `LostCityProfile`'s own `Configuration.get*` calls, which
carry the key, its section, its type and, for numbers, its minimum and maximum.
Defaults are **not** read from a booted server unless asked for: a server install is
shared between mod versions, so the `default.json` sitting in one belongs to
whichever version ran last.

#### KEY-2 An unknown key is ignored, not rejected { #key-2 }

**Game test.** The control building in `wiki-test10`, known to generate 512 gold
blocks, was given two extra keys: `thiskeydoesnotexist`, which no version declares,
and `supportpart`, which is real but arrives in 7.5.1. Run on 7.4.12 the building
generated exactly as before, 512 blocks, and the pack's other three results were
unchanged.

```json
{ "filler": "#", "refpalette": "nstest:test", "...": "...",
  "thiskeydoesnotexist": true, "supportpart": "nstest:ns_gold" }
```

**Code review.** These codecs are `RecordCodecBuilder` maps, which read the fields
they declare and pass over the rest. Nothing in the mod checks for unexpected keys.

An earlier version of the key availability page said an unknown key made the whole
file fail to parse. It does not. The real cost of writing a newer key on an older
version is that the key does nothing, quietly, which is harder to notice than a
parse error would be.

#### KEY-3 A missing required key does fail the file { #key-3 }

**Code review.** A key registered with `fieldOf` rather than `optionalFieldOf`
produces a decode error when absent, and the registry loader drops the entry. This
is the opposite direction from [KEY-2](#key-2) and the two are often confused: an
**extra** key is ignored, a **missing required** key is fatal.

#### KEY-4 `overrideFloors` is missing from 8.2.2, and its absence changes the build { #key-4 }

**Game test.** `wiki-test10`'s control building carries `overrideFloors: true` and
generates 512 gold blocks on 7.4.12. The same pack on 8.2.2 generates **768**. The
cause was isolated on 7.4.12 itself. Take `wiki-test10`, delete `overrideFloors`
from `buildings/full.json` and change nothing else: on 7.4.12 it generates 768 as
well, while `barepalette`, which never carried the key, stays at 512.

| Pack | Version | `full` | `barepalette` |
|---|---|---|---|
| `wiki-test10` | 7.4.12 | 512 | 512 |
| `wiki-test10`, `overrideFloors` deleted | 7.4.12 | **768** | 512 |
| `wiki-test10`, folder renamed for 8.2.2 | 8.2.2 | **768** | 768 |

**Code review.** `BuildingRE` declares `overrideFloors` in 7.4.12, 7.5.1, 7.5.2,
8.4.1, 9.5.1 and 10.0.1, and does not declare it in 5.3.29, 6.0.3, 6.1.6, 6.2.2,
6.2.3 or 8.2.2. Where it is not declared it is an unknown key, so it is ignored
rather than rejected, exactly as [KEY-2](#key-2) describes. The floor count then
comes from the profile instead of from the building, and the building is taller.

This is the clearest demonstration of why KEY-2 matters. Nothing fails, nothing is
logged, and the building is half again as tall as the pack intended.

#### VER-4 The predefined city registry is spelled three different ways { #ver-4 }

**Code review.** `CustomRegistries` builds the registry key that decides the
datapack folder. The spelling is not stable across versions, and a folder that does
not match the version's spelling is never scanned.

| Folder | Versions |
|---|---|
| `predefinedcitites` | 6.0.3 |
| `predefinedcites` | 5.3.29, 6.1.6, 6.2.2, 6.2.3, 8.2.2 |
| `predefinedcities` | 7.4.12, 7.5.1, 7.5.2, 8.4.1, 9.5.1, 10.0.1 |

**Game test.** `wiki-test10` copied to 8.2.2 unchanged produced nothing at any
pinned chunk. Renaming its `predefinedcities` folder to `predefinedcites`, and
changing nothing else, produced 768 gold and 768 diamond.

`predefinedspheres` is spelled the same way everywhere it exists, and 6.0.3 has no
sphere registry at all.

#### VER-5 Four versions read a predefined city and then never place it { #ver-5 }

**Code review.** `City.getPredefinedBuilding` builds its lookup map by iterating
`AssetRegistries.PREDEFINED_CITIES.getIterable()`. That method returns the
`RegistryAssetRegistry`'s own `assets` map, which is a cache filled only by
`get(level, name)`. Nothing ever fetches a predefined city by name, because finding
one is what the iteration is for. The map is therefore empty unless something has
filled the cache from the registry first.

`RegistryAssetRegistry.loadAll(CommonLevelAccessor)` is what fills it, and
`AssetRegistries.load` is what calls it. Both are absent from four versions:

| Version | `loadAll` | Predefined cities and spheres |
|---|---|---|
| 5.3.29 | no | Never placed |
| 6.0.3 | no | Never placed |
| 6.1.6 | no | Never placed |
| 6.2.3 | no | Never placed |
| 6.2.2, 7.4.12, 7.5.1, 7.5.2, 8.2.2, 8.4.1, 9.5.1, 10.0.1 | yes | Work |

The 1.19 line is where this is most confusing: 6.2.2, for Minecraft 1.19, has the
loader, and 6.2.3, for Minecraft 1.19.4, does not.

**Game test, 6.2.2.** Run on a Forge 43.5.0 server for Minecraft 1.19.2, the pinned
buildings generate: 768 gold and 768 diamond, with 41 chunks failing on `ns_lapis`
and 2 on `test`. So the loader's presence is what decides it, and this was predicted
from the code before it was run. 768 rather than 512 because 6.2.2 declares no
`overrideFloors`, and 2 failed chunks rather than 8 because it tolerates an
unresolved `refpalette` as 7.4.12 does.

**Game test.** On the 6.0.3 rig a predefined city in the correct
`predefinedcitites` folder, naming a dimension the profile drives, produced 0 blocks
at all four pinned chunks. The file is read: putting a string where `chunkx` expects
a number stops the server from booting with
`JsonParseException: Error loading registry data: Not a number`. So the asset parses,
validates and registers, and is then never consulted.

`wiki-test10` on 6.0.3 needs one edit before its predefined city is read at all: the
folder renamed to `predefinedcitites`, per [VER-4](#ver-4). With that done:

```
count minecraft:stone       in chunk 8,8   14240   the chunk generated
count minecraft:gold_block  in chunk 8,8       0   the pinned building did not
```

The same pack reaching the world through a city style selector instead of a pin
generated 4496 gold across 6 chunks, so nothing about the building or its
references is at fault. See [VER-8](#ver-8).

`pack_format` is **not** the reason, and an earlier version of this entry said it was.
A dedicated server auto-enables anything in `world/datapacks/` whatever the file
declares. The same pack was run on Minecraft 1.19 declaring `9` and declaring `15`,
and the log reports `Found new data pack ... loading it automatically` both times.
The packs on this site all declare `15` and load unchanged on 1.19, 1.20.1, 1.21,
1.21.11 and 26.1.2. This covers a server picking up a pack from that folder, which is
what these tests do, and says nothing about the client's Data Packs screen.

#### VER-6 6.0.3 has no catch around chunk generation, so a bad reference ends the server { #ver-6 }

**Code review.** `LostCityFeature`'s place method in 6.0.3 compiles with an **empty
exception table**. Every other datapack-era version wraps the generate call, logs
`Error generating chunk <x>,<z>` and carries on. 6.0.3 is alone in this.

| Version | Exception tables in `LostCityFeature` |
|---|---|
| 6.0.3 | **0** |
| 5.3.29, 6.1.6, 6.2.2, 6.2.3, 7.4.12, 8.2.2 | 1 |
| 7.5.1, 7.5.2, 8.4.1, 9.5.1, 10.0.1 | 6 |

**Game test.** On 6.0.3 a city style selecting `nstest:barepart`, whose part name is
written without a namespace, killed the server mid-run:

```
net.minecraft.ReportedException: Feature placement
Caused by: java.lang.RuntimeException: Error getting resource lostcities:ns_lapis!
  at RegistryAssetRegistry.get(RegistryAssetRegistry.java:67)
  at BuildingInfo.<init>(BuildingInfo.java:891)
  at LostCityTerrainFeature.generate(LostCityTerrainFeature.java:261)
  at LostCityFeature.m_142674_(LostCityFeature.java:76)
```

The same fault on 7.4.12 is one line in the log and 41 chunks of empty ground. On
6.0.3 the run does not finish.

#### VER-7 8.2.2 is pre-7.5 code ported to 1.21, not 7.5 code carried forward { #ver-7 }

**Game test and code review.** 8.2.2 carries a higher version number than 7.5.2 and
behaves like 7.4.12 on every point where the two differ. Six signals agree, five of
them read out of the jar and one run in a world.

| Signal | 7.4.12 | 7.5.1 | 8.2.2 | 8.4.1 |
|---|---|---|---|---|
| Unresolvable building `refpalette`, every part carrying its own | Generates | Absent | **Generates** | not run |
| Failed chunks from that pack | 2 | 8 | **2** | not run |
| `overrideFloors` in `BuildingRE` | yes | yes | **no** | yes |
| `AssetRegistries.loadPredefinedStuff` | yes | yes | **no** | yes |
| Registry folder | `predefinedcities` | `predefinedcities` | **`predefinedcites`** | `predefinedcities` |
| Exception tables in `LostCityFeature` | 1 | 6 | **1** | 6 |

That pack on 8.2.2 returned 768 diamond for the building whose
`refpalette` does not resolve, and failed exactly chunks 14,8 and 9,7, the same two
chunks 7.4.12 fails. 7.5.1 and 9.5.1 fail eight and lose the building. See
[VER-3](#ver-3).

The practical reading is that the 7.5 changes reached the 1.21 line at 8.4.1 rather
than at 8.2.2, so a version number alone does not tell you which behaviour you have.

#### VER-8 A fully namespaced datapack building generates on 6.0.3 { #ver-8 }

**Game test.** Take the 6.0.3 build of `wiki-test10` described in
[VER-5](#ver-5), delete the predefined city, since 6.0.3 cannot place one, and point
the city style selector at `nstest:full` alone. Run at `cityChance: 1.0` over a 6 by 6 chunk grid it returned
36 of 36 probes, 4496 gold blocks across 6 chunks, and no failed chunks.

So namespaced references, the datapack registries, the world style and city style
chain, and the profile wiring all work on 6.0.3. What does not work there is pinning,
and any pack that leans on a reference resolving loosely.

A bare `refpalette` is **not** tolerated on 6.0.3: `nstest:barepalette` throws
`Error getting resource lostcities:test!` even though every one of its parts carries
a working palette of its own. That is 7.5 behaviour arriving two major versions
early, which is why [VER-3](#ver-3) describes a window rather than a change of
direction.

#### VER-9 All four packs run on 8.2.2, and three of the four differences are unknown keys { #ver-9 }

**Game test.** The packs are unchanged apart from renaming the predefined city
folder, which [VER-4](#ver-4) covers. Profiles and probes are the same files the
7.4.12 rig uses.

| Pack | 7.4.12 | 8.2.2 | What moved |
|---|---|---|---|
| `wiki-test10` namespaces | 4 of 4 | 3 of 4 | `full` and `barepalette` each 768 rather than 512. Failed chunks identical: 41 on `ns_lapis`, 2 on `test` |
| `wiki-test11` fronts and stuff | 7 of 7 | 6 of 7 | The west front is absent, and the building is 1548 rather than 1036. The stuff object is identical at 5 iron |
| `wiki-test12` scattered | 3 of 3 | 0 of 3 | Nothing placed. See [VER-10](#ver-10) |
| `wiki-test13` predefined sphere | 13 of 13 | 13 of 13 | Every glass count identical, 1093 gray stained in the same chunk. The control building is 1536 rather than 1024 |

Every building in these packs that carries `overrideFloors` comes out larger on
8.2.2, and only those. Three independent instances, one per pack:

| Pack | Building | 7.4.12 | 8.2.2 |
|---|---|---|---|
| `wiki-test10` | `full` | 512 | 768 |
| `wiki-test11` | `tf_main` | 1036 | 1548 |
| `wiki-test13` | `sp_tower` | 1024 | 1536 |

Each is one floor's worth of blocks taller, and each floor count was pinned by the
key 8.2.2 does not declare. Nothing else in any of the three packs moved.

The 7.4.12 figures were re-run rather than quoted, because an earlier note in this
register had the `wiki-test11` number wrong.

The differences are one missing key each, and both are silent:

| Difference | Key 8.2.2 does not declare | Effect |
|---|---|---|
| 768 rather than 512 | `overrideFloors` | The floor count falls back to the profile and the building is taller. See [KEY-4](#key-4) |
| Three fronts rather than four | `frontchance` | `frontchance: 1.0` is ignored, so the draw returns to its default and one of the four street chunks did not get one |

Neither logs anything. A pack looks like it loaded and quietly does something else,
which is [KEY-2](#key-2) with a visible consequence twice over.

The sphere result matters on its own: predefined spheres work on 8.2.2 with the same
counts as 7.4.12, 9.5.1 and 10.0.1, so the predefined machinery is fine there once
the folder name is right.

#### VER-10 Scattered buildings did not place on either version using the older path { #ver-10 }

**Game test.** `wiki-test12` sets `areasize: 1`, `chance: 1.0` and `weightnone: 0`,
which puts one structure in every chunk on 7.4.12. Swept across 49 chunks it produced
**no blocks at all** on 8.2.2 and none on 6.0.3, with no error and no failed chunk in
either run.

| Version | Chunks swept | Chunks holding a structure |
|---|---|---|
| 7.4.12 | 3 probed | 3 |
| 6.0.3 | 49 | 0 |
| 8.2.2 | 49 | 0 |

**Code review.** There are two implementations. From 7.4.12 onward a dedicated
`mcjty.lostcities.worldgen.gen.Scattered` class does the placement and the profile
carries `scatteredChanceMultiplier`. On 5.3.29, 6.0.3, 6.1.6, 6.2.2, 6.2.3 and 8.2.2
that class does not exist; the work happens in
`LostCityTerrainFeature.generateScattered`, reached only from the outside-chunk path
and gated by `avoidScattered`, and there is no `scatteredChanceMultiplier`.

| Version | Placement |
|---|---|
| 5.3.29, 6.0.3, 6.1.6, 6.2.2, 6.2.3, 8.2.2 | `LostCityTerrainFeature`, outside chunks only |
| 7.4.12, 7.5.1, 7.5.2, 8.4.1, 9.5.1, 10.0.1 | `worldgen.gen.Scattered` |

Every key `wiki-test12` uses is declared on both versions, so this is not a key
availability problem. The claim recorded here is narrow and is what was measured:
these settings place nothing on the older path. What would place something there has
not been established.

#### VER-11 8.4.1 is where the 7.5 changes reached the 1.21 line { #ver-11 }

**Game test.** A rig was built for 8.4.1 by copying the 8.2.2 install and swapping
the jar, since both declare NeoForge `[21.0,)` on Minecraft 1.21. All four packs run
there unchanged, with no folder rename, because 8.4.1 spells the registry
`predefinedcities` again.

| Pack | 8.2.2 | 8.4.1 | 7.4.12 |
|---|---|---|---|
| `wiki-test10` namespaces | 3 of 4 | **3 of 4**, and for the opposite reason | 4 of 4 |
| `wiki-test11` fronts and stuff | 6 of 7 | **7 of 7** | 7 of 7 |
| `wiki-test12` scattered | 0 of 3 | **3 of 3**, 512 blocks in each of three chunks | 3 of 3 |
| `wiki-test13` predefined sphere | 13 of 13 | **13 of 13** | 13 of 13 |

Both 8.2.2 and 8.4.1 score 3 of 4 on the namespace pack and the reason is reversed.
8.2.2 generates the building whose `refpalette` does not resolve and gets the count
wrong. 8.4.1 refuses it, which is the [VER-3](#ver-3) behaviour:

| | 8.2.2 | 8.4.1 |
|---|---|---|
| `full` | 768 | **512** |
| `barepalette` | 768 | **0** |
| Chunks failing on `lostcities:test` | 2 | **8** |

512 and 8 are 7.5.1's numbers exactly. `overrideFloors` is honoured again, so
`wiki-test11`'s building returns to 1036 and `wiki-test13`'s to 1024. Scattered
buildings place again, and `frontchance` is back, so all four fronts draw.

This closes the last version that was inferred from its key set rather than run.
Every claim about the split between 8.2.2 and 8.4.1 is now measured.

One count is a genuine 1.21-line difference rather than a version-feature one: the
front is larger on both NeoForge builds, 186 to 189 blocks against 7.4.12's 124 to
126, with the same building and the same pack. The claim being tested, that each
adjacent street chunk draws a front and the building's own chunk never does, holds
on all three.

#### VER-12 Upgrading 8.2.2 to 8.4.1 in place crashes the server on world creation { #ver-12 }

**Game test.** The 8.4.1 rig was built from the 8.2.2 install, which carried the
8.2.2 `config/lostcities-server.toml` forward. Every boot died before the world
existed:

```
java.lang.NullPointerException: Cannot read field "GENERATE_NETHER"
  because the return value of "java.util.Map.get(Object)" is null
    at mcjty.lostcities.setup.Config.getProfileForDimension(Config.java:134)
    at mcjty.lostcities.worldgen.LostCityFeature.getOrCreateDimensionInfo
    at mcjty.lostcities.setup.ForgeEventHandlers.onCreateSpawnPoint
    at net.minecraft.server.MinecraftServer.setInitialSpawn
```

The offending line is one config value:

```toml
selectedProfile = "<CHECK>"
```

Setting it to `""` fixes it and the server boots. Deleting the file entirely also
works: 8.4.1 writes `selectedProfile = ""` into a fresh one.

**Code review.** `<CHECK>` is a sentinel meaning "ask the client which profile it
picked". `Config` carries it in every version up to and including 8.2.2 and does not
carry it in 8.4.1, 9.5.1 or 10.0.1.

| Versions | `<CHECK>` in `Config` | Fresh `selectedProfile` |
|---|---|---|
| 2.0.28 through 8.2.2 | yes | `<CHECK>` on 8.2.2, measured |
| 8.4.1, 9.5.1, 10.0.1 | no | `""` on 8.4.1, measured |

8.4.1 removed the handling and not the value already sitting in installed configs, so
it reads `<CHECK>` as a literal profile name, `standardProfiles.get` returns null, and
the field read throws. A fresh install never sees it. An upgrade always does.

The fix is one line, and it is worth doing before the first boot rather than after
reading a crash report.

### The every-key fixture

Source pack: `docs/examples/every-key/`, namespace `ek`, profile `ekdemo`. Built by
`generate.py` beside it and measured by `docs/examples/key-coverage.py`.

#### EK-1 A pack using every declared key still loads and generates { #ek-1 }

**Game test.** The fixture uses every key the codecs declare, across all thirteen
top-level asset types, and generates: 512 gold from the pinned building's body parts
and 256 diamond from its top part, with no failed chunks on 7.4.12.

```
key names demonstrated   209/209
top-level types checked  13/13
own-key gaps             0
```

Coverage is enforced rather than asserted. `key-coverage.py` fails if any key a
codec declares is absent from an example, and it checks top-level types against
their own folder, so `palette` on a building and `palette` on a part are counted
separately rather than treated as one key that happens to share a name.

The fixture is a **reference**, not a tutorial. Nothing about it is a sensible city.
`docs/examples/first-city/` is the pack to learn from.

#### EK-2 An embedded palette is a whole palette asset, not a list of entries { #ek-2 }

**Code review.** `BuildingPartRE` and `BuildingRE` have no field for a list of
palette entries. Both declare `refPaletteName` for `refpalette`, and both parse
`palette` with **`PaletteRE.CODEC`**, which is the codec for a whole palette file.
A palette file is `{"palette": [ ... ]}`, so an embedded palette nests:

```json
"palette": { "palette": [ { "char": "D", "block": "minecraft:diamond_block" } ] }
```

**Game test.** Written as a bare list, which is the natural guess, the field is not
an error. `optionalFieldOf` yields nothing, the characters resolve to nothing, and
the building's `filler` quietly takes the part's whole volume.

The test has to use a character defined **nowhere else**, or the style's palettes
supply it and both forms appear to work. The fixture's top part draws `Q`, which only
its own embedded palette defines:

| Written as | Emerald placed |
|---|---|
| `"palette": {"palette": [ ... ]}` | **256** |
| `"palette": [ ... ]` | **0**, and nothing logged |

An earlier version of this entry used a character the style also defined, which made
both forms look identical. That is the trap the fixture is for.

The reference pages described this key as "an embedded palette, used instead of
`refpalette`", which is true and does not say the shape. Both now show it.

#### EK-3 A part of a single slice drew nothing { #ek-3 }

**Game test.** The same part, same palette, same building, differing only in height:

| Slices | Diamond placed |
|---|---|
| 1 | **0** |
| 2 | 256 |

No error either way, and the building's filler occupied the space in the failing
case. Reproduced with an embedded palette and again with `refpalette`, so it is not
a palette problem.

Recorded as measured rather than explained. The mechanism has not been traced, and
one slice against two is a narrow enough difference that it is worth knowing before
it is worth theorising about. Every other part in the fixture is two slices or more.

#### EK-6 A profile setting every key still generates the default world { #ek-6 }

**Game test.** `docs/examples/every-key/profile/ekfull.json` sets **all 155**
profile keys the mod declares, across `lostcity`, `cities`, `cityspheres` and
`explosions`. It runs on every version that can pin a city and produces exactly what
the minimal profile beside it produces: 512 gold and 256 emerald, or 768 gold on the
two versions without `overrideFloors`.

That is the point rather than a coincidence. Every key is written at **its own
documented default**, read out of `mod-keys.json`, so a profile that sets everything
behaves identically to one that sets nothing. It demonstrates the shape and the
section of each key without changing what the world builds, which is what makes it
safe to read from.

| | Sets | Generates |
|---|---|---|
| `ekdemo` | 9 keys | 512 gold, 256 emerald |
| `ekfull` | **155 keys** | 512 gold, 256 emerald |

Ten keys have no default, because a null there means unset and demonstrates nothing.
Those are given real values pointing at assets this pack defines: `spawnCity`,
`spawnSphere`, `cityStyleAlternative`, `forceSpawnBuildings`, `forceSpawnParts`,
`outsideProfile`, `spawnBiome`, `icon`, `warning` and `extraDescription`.

The **five `client` keys are absent on purpose**: `fogRed`, `fogGreen`, `fogBlue`,
`fogDensity` and `horizon` exist only on the client, so a headless server can
neither read nor demonstrate them. `key-coverage.py` excludes them from its
denominator rather than reporting a gap that no amount of work would close.

#### EK-5 `inbiome` on a part reference kills chunk generation on 1.21 { #ek-5 }

**Game test.** A part reference carrying `inbiome` made every chunk in the test grid
fail on 8.2.2, 335 of them, with `Exception generating new chunk`. The stack is the
same every time:

```
ConditionContext.parseTest -> BuildingInfo$2.getBiome
  -> LevelReader.getBiome -> WorldGenRegion.getChunk
  ReportedException: Exception generating new chunk
```

The test reads a biome out of a neighbouring chunk while that chunk is still
generating, which 1.21 refuses. 7.4.12 and 7.5.1 run the same pack with no failures
at all.

The same key on a **condition** is fine on every version, because a condition is
evaluated later. The fixture therefore demonstrates `inbiome` on a condition and
deliberately not on a part reference.

`inbiome` is also not a `BiomeMatcher`, despite `biomes` elsewhere being one. It is
one biome name as a plain string, and the accepted shapes differ: 7.5.1 takes a list
or a string, 8.2.2 takes only a string, and 7.4.12 accepted an object and did nothing
with it. A bare string is the only form all of them take.

#### EK-4 The key export was missing three codec types { #ek-4 }

**Code review.** `HighwayParts`, `RailwayParts` and `StreetParts` are real codecs
with real JSON keys, and none of them were in `docs/examples/mod-keys.json`. That is
**37 keys**, so the fixture's first claim of full coverage was measured against a
key set that was short by a sixth.

They were missed because they do not call `fieldOf` at all. All three register their
fields through `Tools.listOrStringList(key, default, fn)`, and an extractor keyed on
`fieldOf` walks straight past them. No other regasset type uses that helper, so this
is the whole of the gap.

| Type | Keys | Where it is used |
|---|---|---|
| `StreetParts` | 9 on 7.5.1, 7 on 7.4.12 | `streetblocks.parts`, `largeparts`, `tertiaryparts` |
| `HighwayParts` | 12 on 7.5.1, 6 on 7.4.12 | A world style's `parts.highways` |
| `RailwayParts` | 16 | A world style's `parts.railways` |

Each value takes either one part name or a list of them, which is what the helper is
for. No shipped world style sets `parts` at all, so the fixture holds the only worked
example of any of them.

### Matchers and world style selection

#### MAT-1 A biome matcher gates the `citystyles` entry it is attached to { #mat-1 }

**Game test.** `docs/examples/matcher-test/` holds three city styles that are
identical apart from the block they build from, reached through three `citystyles`
entries that are identical apart from the matcher on each:

| Entry | Matcher | Builds | Counted |
|---|---|---|---|
| 1 | `if_any: [minecraft:the_void]` | gold | **0** |
| 2 | `if_all: [minecraft:the_void]` | diamond | **0** |
| 3 | `excluding: [minecraft:the_void]` | emerald | **12096** |

Counted over sixteen chunks at full height, on 7.4.12.

The void biome is what an empty world returns and cannot occur in an overworld, so
the expected result is the same on every version and every seed. Naming a real
biome would tie the answer to what the seed put at the test chunk, and biome
generation is not stable across Minecraft versions.

The control is the run that makes this readable. `matcher-control` is the same pack
with one `citystyles` entry carrying **no** `biomes` key, and it builds **12096**
emerald, the same number. So the `excluding` entry produced exactly the world an
ungated entry produces, and the two rejections are rejections rather than an
unbuilt pack.

No predefined city anywhere in this pack, deliberately: a predefined city names its
`citystyle` directly and would bypass the selection list being measured.

**Run on every version.** The pack is unchanged between them, and all nine
datapack-era versions agree: both rejections are total and the `excluding` entry is
the one that builds.

| Version | `if_any` void | `if_all` void | `excluding` void |
|---|---|---|---|
| 5.3.29 | 0 | 0 | 9024 |
| 6.0.3 | 0 | 0 | 4544 |
| 6.2.2 | 0 | 0 | 18064 |
| 7.4.12 | 0 | 0 | 12096 |
| 7.5.1 | 0 | 0 | 6032 |
| 8.2.2 | 0 | 0 | 18028 |
| 8.4.1 | 0 | 0 | 6032 |
| 9.5.1 | 0 | 0 | 6032 |
| 10.0.1 | 0 | 0 | 6032 |

The last column varies because floor heights and street layout differ between
versions, not because the matcher does. What is being measured is which of three
city styles built, and that answer is the same everywhere. 2.0.22 reports `n/a`: the
file-asset era has no world styles.

`BiomeMatcher` declares all three keys in **every** version, including 5.3.29 and
6.0.3. The 6.2.2 requirement noted on [Matchers](../concepts/matchers.md) applies to
the block matcher and the resource location matcher, not to this one.

#### MAT-2 `cityChance: 1.0` makes the highway network refuse every building { #mat-2 }

**Game test.** Found while building [MAT-1](#mat-1), and worth its own entry
because nothing reports it.

At `cityChance: 1.0` the whole world is one city, so the highway network claims
chunk after chunk. A chunk the network has claimed refuses a building unless the
chunk's city level is at least **two above** the highway's level, and on flat
terrain it never is. Every chunk in the grid came back a street. No error, no
warning, and `buildingchance: 1.0` in the city style makes no difference.

`highwayDistanceMask: 0` is the off switch. The highway level lookup returns -1
before it reads anything else when the mask is 0 or less.

| Profile | Buildings in the grid |
|---|---|
| `cityChance: 1.0`, highways at their default | **0** |
| the same with `highwayDistanceMask: 0` | **12096 blocks of building** |

### Behaviour: cellars, lonely buildings and infrastructure

`docs/examples/behaviour/` is one pack behind every entry in this section. Each
result is a **pair**: a profile that turns the feature on, and one that differs by
a single key and turns it off, both counted over the same boxes. These features
place themselves where the generator decides, so a count on its own proves
nothing. The off run is what makes the on run mean something.

All numbers below are 7.4.12 on the public rig.

#### BHV-1 The profile's cellar maximum is a base, not a cap { #bhv-1 }

**Game test.** A building declares a part whose condition is `cellar: true` and
leaves its own cellar bounds unset, so the profile's count is the only thing that
decides whether that part is ever reached.

| Run | `buildingMaxCellars` | City level | Cellar blocks | Above-ground blocks |
|---|---|---|---|---|
| `behaviour-cellars` | 1 | free | **17515** | 17980 |
| `behaviour-cellars-off` | **0** | free | **2352** | 18028 |
| `behaviour-cellars-flat` | **0** | pinned to 0 | **0** | 18064 |

The middle row is the finding. A maximum of 0 still produces cellars, because the
chunk's city level is **added** to that maximum before the count is drawn:
`maxCellars = profile.BUILDING_MAXCELLARS + cityLevel`. The bottom row removes the
addition by pinning every chunk to level 0 with `cityLevel0Height: 384`, and the
maximum then holds exactly.

This confirms what [Building](../reference/building.md#how-floor-and-cellar-counts-are-decided)
already said from the code, with a number against it.

`cityLevel0Height` is in the **`cities`** section, not `lostcity`. Put in the wrong
section it is not read at all, and the run comes back identical to the one without
it, which reads as the setting having no effect.

#### BHV-2 `preferslonely: 1.0` thins a city, it does not empty it { #bhv-2 }

**Game test.** Two runs of the same pack. The only difference is one key on the one
building type the city style selects.

| `preferslonely` | Building blocks over sixteen chunks |
|---|---|
| `0.0` | **18028** |
| `1.0` | **4560** |

The effect is large and it is **not total**. About a quarter of what the control
builds survives.

That matters because reading the code alone suggests it should be total: each chunk
rolls once against each of its four neighbours' `preferslonely`, `Random.nextFloat`
never returns 1.0, and every neighbour here is the same building type. The
measurement disagrees, and the measurement is what this page records. The
mechanism behind the surviving quarter has not been traced.

No inherited buildings are involved. A count of the mod's own building block in the
same run returns 0, so every building measured is this pack's.

#### BHV-3 A world style's highway parts are placed, and the mask switches highways off { #bhv-3 }

**Game test.** Every highway shape in the world style points at one part built from
iron, so any iron in the world came from the highway network.

| `highwayDistanceMask` | Highway blocks over sixty-four chunks |
|---|---|
| `1` | **49152** |
| `0` | **0** |

So the mask is a switch as well as a spacing, and `parts.highways` on a world style
replaces the mod's own highway parts rather than adding to them.

#### BHV-4 `railwaysEnabled: false` leaves every station standing { #bhv-4 }

**Game test.** Three runs, each one key apart.

| Run | Railway blocks |
|---|---|
| Rail and stations both on | **24320** |
| `railwaysEnabled: false` | **13792** |
| and `railwayStationsEnabled: false` as well | **0** |

`railwaysEnabled` is read **only on chunks whose rail type is not a station**.
Stations are governed by `railwayStationsEnabled`, and turning off the first key
alone leaves more than half the network in the ground.

#### BHV-5 A city sphere generates from `citySphereChance` alone { #bhv-5 }

**Game test.** No predefined sphere anywhere in the pack.

| `citySphereChance` | Sphere shell blocks |
|---|---|
| `1.0` | **20835** |
| `0.0` | **0** |

Sphere centres sit on a fixed grid: a chunk is a centre when both its coordinates
are 8 modulo 16, or modulo 32 with `grid32` set.

Two settings are needed and neither is obvious:

- **`outsideProfile` is not optional in a sphere world.** Left unset, the sphere
  feature dereferences a null profile on the first chunk outside a sphere, and
  because that feature has no try/catch the **server goes down** rather than the
  chunk failing. Thirteen caught null pointers and one uncaught one, for one key.
- **`cityChance` still has to be high.** At the mod's default of 0.01 no sphere
  appeared anywhere in the grid, so a sphere needs its chunk to be a city chunk
  first.
- **The shell character has to be defined in the `outsidestyle`**, not only in the
  city style's own style. A chunk that is not a city chunk compiles its palette
  from the world style's `outsidestyle`, and a sphere's shell is drawn on those
  chunks. Pointing `outsidestyle` at the mod's own style while the shell character
  is defined only in the pack left the lookup null, and the sphere feature has no
  null check: the **server goes down** with a bare `NullPointerException` during
  feature placement, naming no file, no part and no character.

#### SPH-3 `citySphereFactor` is not `space` only, and scales less than its name says { #sph-3 }

**Code review.** `CitySphere.getSphereRadius` in 7.4.12. The mod's own config comment
reads *"Only used in 'space' landscape"*. The method contains no landscape check on
any path, so the factor applies on `spheres` and `cavernspheres` as well.

It also multiplies a different thing depending on how the sphere arose:

| Sphere | Radius |
|---|---|
| On a predefined city | `PredefinedCity.getRadius() × CITYSPHERE_FACTOR` |
| Anywhere else | `CITY_MINRADIUS + random(CITY_MAXRADIUS - CITY_MINRADIUS) × CITYSPHERE_FACTOR` |

On the second path the factor never touches `cityMinRadius`, so it cannot take a
sphere below that floor. Lowering it pulls every sphere towards the minimum rather
than scaling it.

Found by reading every profile key's config comment out of the jar and setting it
beside what this wiki says about the key. The comment is the mod's, the behaviour is
the code's, and where they disagree this site documents the code.

#### BHV-6 Monorails were not reproduced { #bhv-6 }

**Unverified.** The monorail parts a world style names were never placed, in any
arrangement tried: both spheres present at `citySphereChance: 1.0`,
`monorailChance: 1.0`, the grid spanning two sphere centres sixteen chunks apart,
and `citySphereFactor` lowered so the two spheres do not touch and the chunks
between them lie outside both.

What the code says, for whoever picks this up. `Monorails.generateMonorails` draws
the `both` part when a chunk has a horizontal **and** a vertical monorail, and
otherwise the `vertical` part, at `groundLevel + monorailOffset`. A chunk fully
inside a sphere takes a different branch that fills to ground with the city style's
border block and never touches a monorail part at all. The four candidate flags on
a sphere are each rolled against `monorailChance`, so at 1.0 all four are set.

Recorded as measured-and-absent rather than left out, because a later attempt
should start from what has already been ruled out.

#### BHV-7 Every letter and digit is already taken by the mod's palettes { #bhv-7 }

**Game test.** A pack that layers its own palette on top of the mod's, which is
what a city style's `style` asset does, takes each character it defines **away**
from every shipped part that used it. The mod's palettes between them use every
letter, every digit, and most punctuation.

Two controls in this pack failed because of it, and both failed quietly:

| Control | Should have counted | Counted | Why |
|---|---|---|---|
| A world with no sphere | 0 shell blocks | **303** | the shell marker was `S`, and shipped parts draw `S` |
| A world with no cellars | 0 cellar blocks | **26** | the cellar marker was `L` |

Both went to exactly 0 when the markers moved to characters no shipped palette
defines. Seven characters are free across every palette the mod ships:

```
"   '   ,   <   >   ?   ]
```

The failure mode is worth the space: nothing errors, nothing is logged, and the
only symptom is that the wrong blocks appear somewhere in the world.

### Whole-page entries

Some claims are made the same way on many pages. Rather than repeat the evidence,
those pages cite one of these.

#### NEO-1 The NeoForge line behaves like the Forge line { #neo-1 }

**Game test.** A second rig: NeoForge 21.11.45 on Minecraft 1.21.11, Java 21, Lost
Cities **9.5.1**. All four namespace and feature packs were run against it
unchanged, no edit to any file.

| Pack | 7.4.12, Forge, 1.20.1 | 9.5.1, NeoForge, 1.21.11 | 10.0.1, NeoForge, 26.1.2 |
|---|---|---|---|
| `wiki-test10`, 4 probes | 3 of 4 | 3 of 4, and see [VER-3](#ver-3) | 3 of 4, the same |
| `wiki-test11`, 7 probes | 7 of 7 | 7 of 7 | 7 of 7 |
| `wiki-test12`, 3 probes | 3 of 3 | 3 of 3 | 3 of 3 |
| `wiki-test13`, 13 probes | 13 of 13 | 13 of 13 | 13 of 13 |

Counts matched exactly nearly everywhere, including the sphere, which returned
1093 gray stained glass in the same chunk and none of the other three glass types
anywhere, the same draw from the same weighted list.

One result moved, and it is **not** a loader difference. Running the same pack on
7.5.1, which is Forge on Minecraft 1.20.1, gives the 9.5.1 answer rather than the
7.4.12 one. The change belongs to 7.5, and 9.5.1 on NeoForge simply carries it. See
[VER-3](#ver-3).

So the claim this entry was opened for holds: at the same feature level the two
loaders agree. Covered by a run: **9.5.1** on Minecraft 1.21.11 and **10.0.1** on
Minecraft 26.1.2, four packs and 27 probes each, both matching 7.5.1 on Forge down
to the counts. The sphere returned 1093 gray stained glass on all three.

That spans two NeoForge majors and two Minecraft versions five releases apart.
8.2.2 and 8.4.1 have since been run as well, so no version on the NeoForge line is
inferred from its key set. See [VER-7](#ver-7) and [VER-11](#ver-11).

The two rigs are NeoForge 21.11.45 on Minecraft 1.21.11 and NeoForge 26.1.2.96 on
Minecraft 26.1.2, on portable Temurin JREs 21 and 25 respectively. Reproducing them
means fetching those installers, since the jars are not ours to redistribute.

#### VER-3 7.5 resolves a building's `refpalette` even when no part needs it { #ver-3 }

**Game test.** The clearest behavioural difference found between 7.4.12 and later
releases, and it is a fix rather than a regression.

`wiki-test10` holds a building whose `refpalette` is written bare, so it resolves to
a namespace where nothing is registered, while each of its parts carries a working
`refpalette` of its own.

| Version | Loader | The building | Chunks failing on that palette |
|---|---|---|---|
| 7.4.12 | Forge, 1.20.1 | **generates**, 512 blocks | 2, neither of them the building's |
| 7.5.1 | Forge, 1.20.1 | **absent**, 0 blocks | 8, including the building's own chunk |
| 9.5.1 | NeoForge, 1.21.11 | **absent**, 0 blocks | 8, the same set |

On 7.4.12 the building's own palette is never needed, because every part supplies
the characters it uses, so the broken reference is never dereferenced and the tower
comes out looking correct. From 7.5 the palette is resolved regardless and the
building fails instead.

The later behaviour is easier to live with. A mistake that produced a correct
looking building on 7.4.12 produces a missing one plus a named error afterwards.
Anything relying on the older leniency stops working on 7.5 and later.

#### REF-1 The key tables match the codecs, and a build says so { #ref-1 }

**Code review.** `docs/examples/mod-keys.json` holds the key set of every codec and
of `LostCityProfile`, read out of each jar. `validate.py` compares it against every
table in `docs/reference/` on every build: a key documented that no version
declares is an error, and so is a key marked optional that the codec requires.

A row's **name, presence and required-or-optional** are therefore checked
mechanically. What a key *means* is not, and any row whose meaning has been tested
carries its own chip.

#### REF-2 Read from the 7.4.12 jar, not run { #ref-2 }

**Code review.** Disassembled with `javap -p -c -constants` from
`lostcities-1.20-7.4.12.jar`. Behaviour follows from the bytecode alone, with no
world involved. Where a version other than 7.4.12 is named, the same was done to
that jar.

#### REF-3 Not checked either way { #ref-3 }

**Unverified.** Neither a run nor a reading covers this. It is written from the
mod's own documentation, the official wiki, or inference from surrounding code,
none of which count. Treat it as the least reliable material on the site.

Almost nothing sits here now. The entry stays because it is the honest home for a
claim that arrives without evidence, and because the home page cites it to show
what an unverified chip looks like.

### How it all connects

Source page: [How It All Connects](../getting-started/how-it-connects.md).

#### HIC-1 A 7.4.12 profile has 131 keys, 7.5.0 onward has 160 { #hic-1 }

**Code review.** Counted off `LostCityProfile`'s fields in each jar and recorded in
`docs/examples/mod-keys.json`, which `validate.py` checks the reference pages
against on every build. See [Key availability](../versions/key-availability.md).

#### HIC-2 Seventeen profile files, three of them private { #hic-2 }

**Game test.** After any run, `config/lostcities/profiles/` holds 18 files:
the 17 the mod ships plus whichever one the pack installed. `grep -l '"public":
false'` returns exactly `bio_wasteland.json`, `biosphere_caves.json` and
`void_outside.json`.

```
ancient atlantis bio_wasteland biosphere biosphere_caves cavern default
floating largecities nodamage onlycities rarecities safe space tallbuildings
void_outside wasteland
```

**Code review.** `ProfileSetup.initStandardProfiles` builds all of them plus
`customized`, which the write loop skips, so it is an eighteenth profile that
never has a file. See [CFG-7](#cfg-7).

#### HIC-3 The dimension, and the bed gateway that reaches it { #hic-3 }

**Code review.** The mod ships the dimension `lostcities:lostcity`, whose terrain
is vanilla noise rather than a generator of the mod's own. See [LW-1](#lw-1). The
gateway is keyed off `Config.SPECIAL_BED_BLOCK`, defined on the server spec with
the default `minecraft:diamond_block`, so it is a per-world setting rather than a
profile key. See [CFG-6](#cfg-6).

#### HIC-4 Two biome modifiers, both on `#minecraft:is_overworld` { #hic-4 }

**Code review.** The jar ships exactly two files under
`data/lostcities/forge/biome_modifier/`:

```json title="lostcities.json"
{ "type": "forge:add_features", "biomes": "#minecraft:is_overworld",
  "features": "lostcities:lostcities", "step": "raw_generation" }
```

```json title="lostcity_spheres.json"
{ "type": "forge:add_features", "biomes": "#minecraft:is_overworld",
  "features": "lostcities:spheres", "step": "top_layer_modification" }
```

#### HIC-5 Non-default landscape types need Lost Worlds { #hic-5 }

**Superseded by [LW-1](#lw-1)**, which settles the same question from the code
rather than leaving it open. The entry stays so older links still land somewhere.

#### CFG-1 Settings are split across three files, one of them per world { #cfg-1 }

**Code review.** `Config`'s static initializer builds three
`ForgeConfigSpec.Builder`s and registers keys against them: three on
`COMMON_BUILDER`, eleven on `SERVER_BUILDER`, none on `CLIENT_BUILDER`. Forge
writes a common spec to `config/<modid>/common.toml` and a server spec into the
save.

**Game test.** After any run, a 7.4.12 server holds
`config/lostcities/common.toml` with exactly `dimensionsWithProfiles`,
`optimizedHeightmap` and `heightSampleSize`, and
`world/serverconfig/lostcities-server.toml` with the other eleven. Deleting the
world deletes the second file and not the first.

#### CFG-2 Both files use `[profiles]`, and a wrong section resets the file { #cfg-2 }

**Code review.** All three builders call `push("profiles")`. The string
`"General settings"` is passed to `comment(...)` immediately before, so it becomes
a comment line rather than a section.

**Game test.** Cost a full test round. Writing the keys under any other section
makes Forge rewrite the file to defaults with no error, which points
`lostcities:lostcity` at `biosphere`, and the run then looks like a generation bug
rather than a config typo.

#### CFG-3 `common.toml` holds three keys, and one contradicts its own comment { #cfg-3 }

**Code review.** `heightSampleSize` is
`defineInRange("heightSampleSize", 3, 1, 100)` under the comment
`Default is 1 which means every chunk is sampled`.

**Game test.** The file the server writes says `heightSampleSize = 3` under that
comment.

#### CFG-4 A bad `dimensionsWithProfiles` entry is logged, not thrown { #cfg-4 }

**Code review.** `Config.getProfileForDimension` splits each entry on `=`. A
missing `=` logs `Bad format for config value: '{}'!`; a name absent from
`STANDARD_PROFILES` logs `Cannot find profile: {} for dimension {}!`. Both are
logger calls and neither throws, so the dimension is simply left without a profile.

#### CFG-5 The world creation screen wires the overworld, not `lostcities:lostcity` { #cfg-5 }

**Game test.** Choosing a profile with the **Cities** button makes the overworld
the Lost Cities world, while `dimensionsWithProfiles` wires the
`lostcities:lostcity` dimension. A predefined city pinned to the wrong one appears
not to generate. The shipped `json5-test` packs pin to both for this reason.

#### CFG-6 Eleven keys are per world { #cfg-6 }

**Code review.** All eleven are defined on `SERVER_BUILDER`.

**Game test.** They appear only in `world/serverconfig/lostcities-server.toml`.
Deleting the world brings the file back at defaults, which is how the defaults
quoted on the page were read.

#### CFG-7 Standard profiles are rewritten to disk on every launch { #cfg-7 }

**Code review.** `ProfileSetup.setupProfiles` runs in this order: build the
standard profiles in code, `mkdirs` the folder, write every standard profile
**except the one named `customized`** through `toJson(true)`, and only then call
`readProfiles` on the folder. So a deleted default returns, an edited default is
overwritten before it is read, and a profile the mod does not define is untouched
because the write loop iterates `STANDARD_PROFILES` rather than the directory.

#### CFG-8 `__readonly__` is written and never read { #cfg-8 }

**Code review.** The only occurrence of the string in the jar is in
`Configuration.toJson(boolean)`, which adds it as a property when the flag is set.
No class reads it. `readProfiles` passes the whole file to the `LostCityProfile`
constructor, which takes the keys it knows and ignores the rest.

**Game test.** Every profile in every test pack omits the key, and all of them
load and are selectable.

### KubeJS integration

Source page: [KubeJS Integration](../advanced/kubejs.md). Tested by moving
`wiki-test10`'s twelve asset files into `kubejs/data/nstest/lostcities/` and running
it again. Reproducing it needs KubeJS, Rhino and Architectury, which are not ours to
redistribute.

#### KJS-1 Lost Cities assets are ordinary dynamic registry entries { #kjs-1 }

**Code review.** `CustomRegistries` declares each asset type as a
`ResourceKey<Registry<...>>` and registers it through Forge's
`DataPackRegistryEvent.NewRegistry`, with a codec per type. Nothing in the mod
opens a file or walks a directory. Loading is done by the vanilla datapack
registry loader, which reads every enabled pack source.

#### KJS-2 Files under `kubejs/data/` are seen by that loader { #kjs-2 }

**Game test.** `wiki-test10`'s twelve asset files were moved from the datapack to
`kubejs/data/nstest/lostcities/`, with KubeJS 2001.6.5, Rhino 2001.2.3 and
Architectury 9.2.14 installed. The datapack that remained held one irrelevant file
and no Lost Cities content at all:

```
world/datapacks/kubejs-test/data/kjsplaceholder/nothing.json
world/datapacks/kubejs-test/pack.mcmeta
```

All four probes came back identical to the datapack run: 512 gold, 512 diamond,
0 lapis, 0 emerald, with the same 41 and 2 failed chunks. Every assertion in this
register's Namespaces section holds unchanged when the files are loaded through
KubeJS.

**Code review.** Consistent with KJS-1: the vanilla registry loader reads through
the `ResourceManager`, and every pack source is one of its inputs.

#### KJS-3 The namespace is the folder, with no default { #kjs-3 }

**Code review.** Lost Cities never sees the file path. It receives a
`ResourceLocation` already built by the loader from `data/<namespace>/<registry
namespace>/<registry path>/<name>.json`, so the namespace can only be the folder.
The mod's own resolution of a bare reference is
`new ResourceLocation("lostcities", name)` in `DataTools.fromName`, which is a
default applied to **references**, not to file locations. Nothing gives a file a
namespace it did not get from its folder.

## What has not been checked in a world

Everything below is documented from the compiled code and has never been generated.
The pages that describe it are not marked differently, so this list is the way to
tell. A claim being here means untested, not suspect.

| Area | Why it is not covered |
|---|---|
| Monorails | Attempted and not placed. What was ruled out is in [BHV-6](#bhv-6). |
| `onlyPredefined` on city spheres | Sphere generation itself is covered by [BHV-5](#bhv-5); this key is not. |
| Part rotation and `lostcities:rotatable` | The claim that an untagged block keeps its facing when a part is rotated. |
| `avoidWater` and `avoidFoliage` | Including the finding that `avoidFoliage` is what controls flooding. |
| The in-game editor | Six commands documented from the code. They need a client, not a headless server. |
| Client-only profile keys | `fogRed`, `fogGreen`, `fogBlue`, `fogDensity` and `horizon`. A headless server can neither read nor show them. |

Everything in this section is counted on **7.4.12**. Where a result is expected to
differ on another version, the probe carries that version's number and the rig
reports it as a pass rather than a difference.

## Corrections this produced

Seven pages were wrong before a world was involved. Each is corrected and linked
from the register above.

| Was documented as | Actually |
|---|---|
| `filler` and `rubble` resolve against the part's palette | They resolve against the **building's** |
| `minfloors` can only make a building shorter | It is applied last and can exceed every maximum |
| Generation errors crash the game and write a crash report | They are caught per chunk. The wiring between profile and datapack is the exception |
| A pinned building's coordinates are world chunk coordinates | They are offsets from the city centre |
| `loot` names a loot table | It names a Condition |
| A bad `loot` value is one of the silent causes of an empty chest | It throws, and leaves invisible chests |
| `damaged` is what a character becomes when a building is ruined | It applies to the rubble band only |

## Bugs this produced

Two, both on [Known Issues](../troubleshooting/known-issues.md) with the evidence:
`streetblocks.parts.full` never generates, and `belowpart` tests the current part.

## The packs

Every pack below ships with this wiki and can be downloaded from the repository.

| Pack | Covers | Read by |
|---|---|---|
| `docs/examples/wiki-test/` | Positive claims about palettes, streets and multi-buildings | Eye |
| `docs/examples/wiki-fail/` | Failure claims. Two of its three profiles are meant to fail | Log |
| `docs/examples/wiki-test7/` | The pinned grid: 21 assets, 28 probes | Eye or block count |
| `docs/examples/wiki-test8/` | Ruins, damage, row length, `parts2` | Block count |
| `docs/examples/wiki-test10/` | Namespace resolution, and what an unresolved reference does | Block count |
| `docs/examples/wiki-test11/` | Building fronts, stuff objects, and what a predefined city does not make a city chunk | Block count |
| `docs/examples/wiki-test12/` | Scattered structures, with the placement randomness tuned out | Block count |
| `docs/examples/wiki-test13/` | A predefined sphere, and what its glass character resolves to | Block count |
| `docs/examples/matcher-test/` | Whether a biome matcher gates the world style entry it sits on, with an ungated control | Block count |
| `docs/examples/behaviour/` | Cellars, `preferslonely`, highways, railways and city spheres, each against a control that turns the feature off | Block count |
| `docs/examples/every-key/` | Every key the codecs declare, in a pack that loads. A reference, not a tutorial | Block count |
| `docs/examples/json5-test/` | Three packs building the same three towers, for the DevTool's `.json5` handling | Block count |
| `docs/examples/file-era-test/` | The file-asset era: one `userassets.json`, no datapack | Block count |

Four more were built for single claims and are described where they are used rather
than shipped, because each is a small edit to one of the packs above or needs mod
jars that are not ours to redistribute.

| Built for | What it is |
|---|---|
| [KJS-2](#kjs-2) | `wiki-test10`'s twelve files moved to `kubejs/data/nstest/lostcities/`, with KubeJS, Rhino and Architectury installed |
| [NS-9](#ns-9) | A base pack plus two packs claiming the same asset, run twice with the two files swapped |
| [KEY-4](#key-4) | `wiki-test10` with `overrideFloors` deleted from `buildings/full.json` |
| [VER-4](#ver-4), [VER-5](#ver-5) | `wiki-test10` with its predefined city folder renamed to whichever spelling the version compiled in |

Three packs in the folder are superseded and kept only because results above were
produced on them: `wiki-test5` and `wiki-test6` are earlier builds of the grid that
`wiki-test7` replaced, and `wiki-test9` is an earlier JSON5 test that `json5-test`
replaced. Nothing on this page needs them, and a new test should start from one of
the packs in the table instead.

### The pinned grid

A [predefined city](../reference/predefined.md) pins one city to world chunk
**8, 8** with a radius of 8, and pins every test building to a fixed chunk inside
it. `cityChance` is `0.0`, so that city is the only one in the world. Each test has
a block address rather than needing to be found.

| Block corner | Building | Tests |
|---|---|---|
| 128, 128 | `origin` | Pinned coordinates are relative |
| 160, 128 | `rangetest` | A third number in `range` |
| 192, 128 | `andtest` | AND, never OR |
| 224, 128 | `belowsem` | `belowpart` semantics |
| 128, 160 | `prectest` | Palette precedence, all three levels |
| 160, 160 | `slottest` | The 128-slot cutoff |
| 192, 160 | `stairtest` | `shape=` is discarded |
| 224, 160 | `torchtest` | The `torch` attachment pass |
| 128, 192 | `loottest` | `loot` through a Condition |
| 160, 192 | `mobtest` | `mob` through a Condition |
| 192, 192 | `tagtest` | Raw NBT |
| 224, 192 | `chartest` | A `char` longer than one character |
| 128, 224 | `circulartest` | A circular alias. **This chunk is meant to fail** |
| 160, 224 | `doors_on` | `allowDoors` default |
| 192, 224 | `doors_off` | `allowDoors: false` |
| 128, 256 | `lootcond` | `inpart` and `range` on the loot path |

Grey buildings are backdrop. The gaps between test buildings are pinned streets.

## Installing a pack by hand

The datapack and the profile go in different places.

**1. The datapack.** Copy the pack folder into the world, keeping the folder:

```
<world>/datapacks/wiki-test7/
  pack.mcmeta
  data/wt7/lostcities/...
```

The **Data Packs** button on the world creation screen also works, and is easier,
because the pack has to be present before the world generates.

**2. The profile.** This is config, not datapack:

```
config/lostcities/profiles/wtseven.json
```

**3. The wiring.** In `config/lostcities/common.toml`, under `[profiles]`:

```toml
dimensionsWithProfiles = [ "lostcities:lostcity=wtseven" ]
```

**4. Restart**, create a new world, enter the Lost City dimension, then travel to
the grid:

```
/execute in lostcities:lostcity run tp @s 136 120 136
```

### If nothing generates

```
/lostcities locate wt7:origin
```

A hit means the whole chain resolved. If it reports nothing, stand in a city chunk
and run `/lostcities debug`, which dumps the generator's decisions for that chunk to
the **server console**, not to chat. Then work through
[When nothing happens](../getting-started/first-city.md#when-nothing-happens).

### The failure pack needs one profile at a time

`wiki-fail` ships three profiles and two of them are meant to fail. Run them one at
a time by changing a single line in `common.toml` and restarting, using a throwaway
world for each. A failure in the first would hide anything after it.

Its three city styles deliberately do **not** inherit `citystyle_common`, because
selector inheritance is additive and emptying a selector is the point of the first
test. A standalone city style then has to define every character the generator
dereferences without a null check. The full list is in
[City Style](../reference/citystyle.md).

## Running a pack without a player

The pinned grid also runs on a headless Forge server. The server force loads the
grid so generation happens with no player, then the result is read back over RCON.

The command set has no block counter, so counts come from a **filtered clone**,
which reports how many blocks it copied:

```
execute in lostcities:lostcity run clone 160 40 160 175 167 175 992 40 992 filtered minecraft:red_concrete
```

`/clone` caps at 32768 blocks, which is exactly one chunk footprint by 128 levels,
so a count box is one chunk and 128 levels tall. The destination has to be loaded
as well, so a scratch chunk well clear of the grid is force loaded too.

`/data get block` covers what a count cannot: a chest's `LootTable`, a spawner's
entity, a `CustomName`, an exact stair `shape=`.

## Traps when testing

### `/forceload` takes block coordinates

Not chunk coordinates. Passing chunk numbers loads chunk 0,0 and nothing else, and
every probe then answers `That position is not loaded`, which reads as an empty
world rather than as an error.

### The config section is `[profiles]`

Not `[general]`. Forge does not reject a wrong section: it rewrites the file to the
mod's defaults, which point the lost city dimension at `biosphere`. A predefined
city is consulted whatever the profile is, so the pack half works and the failure
looks like a generation bug.

### Counting needs a control

`damaged` maps a character to another block when a building is ruined. Measured on
a three-storey building made entirely of one character mapped `iron_block` to
`cobweb`, with `ruinChance: 1.0` and explosions off:

| | |
|---|---|
| Iron left standing | 587 of 2256 |
| Cobweb from the swap | 2 |
| Cobweb in a control chunk containing no iron | 5 |

The control holds more than the swap produced. Without it, ordinary decoration
reads as the result, and it reads in the direction the test was hoping for.

### `explosionChance: 0` does not turn explosions off

`miniExplosionChance` is a separate roll and its default, `0.03`, is fifteen times
larger. A profile that zeroes only the first still gets damaged buildings.

### A wall count is not comparable across versions

Doorways are cut toward adjacent **city** chunks, and the 7.5 road planner changes
which neighbours those are. On an identical pinned grid, four wall totals moved
between 7.4.12 and 7.5.1, each by a multiple of 16:

| Probe | 7.4.12 | 7.5.1 |
|---|---|---|
| `origin-tower` | 3760 | 3744 |
| `char-truncate` | 708 | 720 |
| `doors-on` | 2240 | 2256 |
| `doors-off` | 2256 | 2256 |

Count an interior block or a block entity instead. Both give the same number on
both versions.

## What the validator predicts

`validate.py` reproduces four of the in-game outcomes before the game starts:

```
ERROR  rangetest.json: levels [6] match no part. Levels run from -0 to 6 INCLUSIVE,
       so 'maxfloors': 6 is a 7-storey building.
ERROR  prectest.json:  levels [3] match no part.
ERROR  belowsem.json:  part reference uses 'belowpart', which never matches from a
       building's parts list
ERROR  test.json: char 'loot' on 'c': 'minecraft:chests/simple_dungeon' is a loot
       table ID, but 'loot' names a Condition
```

Its earlier rule was that a building needs one part entry with no conditions on it.
That rejected a building which generates correctly and explained none of the three
that failed. It now computes level coverage instead.

## Reporting a result

A run that disagrees with this page is the most useful outcome available, not a
failed exercise. Note which claim, what the world did, and the mod version, then
open an issue. See
[Contributing](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki#contributing).
