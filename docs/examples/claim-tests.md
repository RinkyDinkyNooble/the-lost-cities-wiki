# Claim tests

Most of this wiki is read out of the mod's compiled code. Reading establishes what
the code says. It does not establish what a world does.

This page is the register of claims that have been checked in a running world, the
packs that check them, and how to run those packs.

Every result below is from Lost Cities **7.4.12** on Minecraft **1.20.1**, Forge,
unless a row says otherwise. Results marked 7.5.1 were produced by running the same
pack against that jar with nothing else changed.

## What has been checked in a world

### Buildings and levels

| Claim | Result |
|---|---|
| Levels run `0` to `maxfloors` **inclusive**, so `maxfloors: 3` is a four-storey building | Confirmed. `maxfloors: 6` produced 7 storeys, `maxfloors: 2` produced 3. |
| `overrideFloors` replaces the profile's bounds rather than narrowing them | Confirmed. The overriding building generated at 1 storey beside 5-storey towers declaring the same bounds without the key. |
| `minfloors` is a `max()` applied after the maximum, so it can exceed every ceiling | Confirmed. Two buildings declaring `minfloors: 6` and `maxfloors: 6`, one with `overrideFloors` and one without, both generated 6 storeys under a profile allowing 2 to 3. |
| A level that matches no part reference fails the chunk | Confirmed. `Misconfiguration! Floor were generated for a building where no part condition matches!` |
| `parts2` is an overlay placed at the same origin on the same level | Confirmed. Base part 1504 blocks, overlay 8 blocks, both present. |
| `allowDoors: false` leaves the wall as the part draws it | Confirmed. The same three-storey part placed 2240 wall blocks with doors allowed and 2256 with `allowDoors: false`. |
| `filler` and `rubble` resolve against the **building's** palette, not the part's | Confirmed, by 590 failed chunks when they did not. |
| `rubble` is used by the ruin pass | Confirmed. 40 blocks of an otherwise unused character with ruins on, none with ruins off. |

### Conditions and part selection

| Claim | Result |
|---|---|
| Test keys chain with AND, never OR | Confirmed. A building gated `ground: false` **and** `top: false` came out banded rather than mixed. |
| `range` includes both ends | Confirmed. |
| A third number in `range` is discarded silently | Confirmed. `"0,2,9"` gave levels 0 to 2, not 0 to 9. |
| `belowpart` tests the **current** part, not the one below | Confirmed, and it is a mod bug. A two-level building whose first entry was gated `belowpart: "<none>"` came out gold on both levels with no diamond. See [Known Issues](../troubleshooting/known-issues.md#belowpart-tests-the-wrong-part-in-every-version-that-has-it). |
| `inpart` and `belowpart` never match from a building's `parts` list | Confirmed. The floor loop passes the literal `<none>` as the current part. |
| `inpart` does work in a Condition reached from a palette | Confirmed. The chest's `LootTable` came out as the table on the `inpart`-gated entry. |
| `range` works there too, and counts storeys | Confirmed. `"0,0"` gave one table on the ground floor, `"1,100"` gave another two storeys up. |

### Palettes

| Claim | Result |
|---|---|
| The merge order is style, then building, then part | Confirmed. The same character gave gold from the building palette, diamond from the part palette, and lapis where the building overrode a character the shipped style defines concretely. |
| A part palette **merges** into the building's rather than replacing it | Confirmed. A part palette defining one character still resolved every other character from the building's. |
| A weighted `blocks` list fills 128 slots, and entries after the one that fills the last slot are unreachable | Confirmed. A list of 120 white, 20 black, then 100 red produced **no red block anywhere**. |
| `frompalette` resolves to the aliased character | Confirmed. |
| A concrete definition beats an alias, whatever the order | Confirmed. An alias on a character the shipped style defines concretely lost to that definition. |
| A circular `frompalette` leaves the character undefined, and reports nothing at load | Confirmed. `Could not find entry '<char>' in the palette for part '<part>'!` at generation, nothing at load. |
| A `char` of more than one character keeps the first, silently | Confirmed. `"char": "王zz"` registered `王`. |
| `mob` names a Condition, not an entity | Confirmed. A condition resolving to `minecraft:blaze` produced blaze spawners. |
| `loot` names a Condition, not a loot table | Confirmed, and the page said otherwise. |
| With `generateLoot` on and both loot chances at `0`, every chest is filled | Confirmed. 12 of 12. |
| `tag` places raw NBT | Confirmed. |
| `torch: true` requires `generateLighting`, and without it the character becomes air | Confirmed. |
| `damaged` covers the rubble band, not the ruined section | Confirmed, and the page overstated it. See [the control-chunk note](#counting-needs-a-control). |

### Parts

| Claim | Result |
|---|---|
| A layer is one flat string read as `charAt(z * xsize + x)`, so row breaks are formatting | Confirmed in both directions. |
| A layer longer than `xsize * zsize` shifts characters and drops the tail, silently | Confirmed. A 17-character row placed its marker one column along; position 256 was never read. |
| A layer shorter than that fails the chunk | Confirmed. `String index out of range: 255`. |
| `shape=` in a stair block string is discarded and recomputed | Confirmed. Five isolated stairs written `shape=outer_right` all came out straight, and a perpendicular pair produced a corner. |

### City styles, streets and selectors

| Claim | Result |
|---|---|
| A multi-building grid is `buildings[x][z]`, outer list X | Confirmed. Red north-west, yellow south-west, blue north-east, green south-east. |
| A street part name accepts a list, sampled per chunk | Confirmed. Both marked variants appear across the road network, mixed. |
| `streetblocks.parts` is all or nothing on inheritance | Confirmed. All 7 shapes restated, all generate. |
| `streetblocks.parts.full` never generates | **Refuted**, and it is a mod bug. See [Streets](../concepts/infrastructure-parts.md#streets). |
| Selector inheritance is additive, so an inherited selector cannot be emptied | Confirmed, indirectly: emptying one required not inheriting at all. |
| An empty `bridges` selector fails even at `bridgeChance: 0` | Confirmed. 1842 failed chunks, `Invalid name given to minecraft:root getOrThrow!`. |
| `parks`, `fountains`, `stairs`, `fronts` and `raildungeons` are safe to leave empty | Confirmed. Zero failed chunks with all five empty. |
| A city style that inherits nothing must define every character the generator dereferences unguarded | Confirmed. Each run reveals only the next missing character. |
| Omitting a selector and writing `[]` are the same thing | Confirmed. Both end at an empty list. |

### Predefined cities

| Claim | Result |
|---|---|
| A pinned building's `chunkx` and `chunkz` are offsets from the city centre | Confirmed, and the page said they were world coordinates. |
| A predefined city generates at `cityChance: 0.0` | Confirmed. One city, where it was pinned, in an otherwise empty world. |
| `preventruins` protects a pinned building | Confirmed. Under `ruinChance: 1.0`, 1767 wall blocks on the unprotected copy against 2224 on the protected one. |

### Profiles

| Claim | Result |
|---|---|
| A `block` value carrying a 1.12 style `@meta` suffix fails the **whole palette**, not just that character | Confirmed. `minecraft:red_sandstone@2` reaches `ResourceLocation`, whose path rejects `@`, so the palette throws while being built and every character in the file stops resolving. Planted in a working pack, all three of its towers vanished. Lost Cities 7.4.12 ships one such file, `lostcities:bricks_desert_redsand`, unnoticed because assets are built on demand and no shipped style selects it. |
| A profile name containing a digit, an uppercase letter, a hyphen or a dot is read normally but is **not offered on the world creation screen** | **Withdrawn.** Observed once by hand and contradicted by the code. The list is `STANDARD_PROFILES` filtered on `isPublic()`, and nothing tests the characters of a name. |
| A profile is offered unless its own file sets `"public": false` | Confirmed from `LostCitySetup.toggleProfile` and the `LostCityProfile(String, String)` constructor, which reads `public` and treats a missing key as true. That is how the sphere-outside profiles are hidden. |
| A profile is named after everything before the **first dot** in its file name | Confirmed from `ProfileSetup.readProfiles`, which uses `getName().split("\\.")[0]`. `my.thing.json` registers as `my`. |
| One unreadable profile file drops every profile after it | Confirmed from the same method: the `IOException` handler ends in `return`, not `continue`, so the scan stops. Which profiles vanish depends on directory order. |
| The profile list is ordered `default` first, then by `String.compareTo` | Confirmed from the comparator `toggleProfile` sorts with. That is code point order, so a digit sorts before an uppercase letter and an uppercase letter before a lowercase one. It is not case-insensitive alphabetical, and it sorts the key rather than the label shown. |
| A profile key in the wrong section is never read | Confirmed indirectly: a wrong config **section** caused Forge to reset the file to its defaults with no error. |

### Failure behaviour

| Claim | Result |
|---|---|
| A mistake in an asset does not crash the game | Confirmed across every pack. The mod catches it per chunk and logs. |
| A profile naming a `worldStyle` no loaded datapack defines **does** crash | Confirmed. `Description: Feature placement`, because it resolves before the catch. |
| A fault raised while building a chunk's `BuildingInfo` spreads to neighbouring chunks | Confirmed. 3 broken buildings produced 77 failed chunks across a 13 by 10 chunk area. |
| A fault raised while placing blocks stays in its own chunk | Confirmed. A circular palette alias 6 chunks from those three failed exactly 1 chunk. |
| On a sphere landscape nothing catches either | Confirmed. Same pack, same broken building: `default` gave 35 caught and 0 uncaught, `spheres` gave 18 caught and 21 uncaught, and the server shut down. |
| `landscapeType` takes lowercase values, and a wrong one stops the game starting | Confirmed. `"SPACE"` gives `Bad landscape type: SPACE!` during mod construction. |
| A sphere landscape needs `cityspheres.outsideProfile` | Confirmed. Without it, `getOutsideProfile() is null`, uncaught. |

### Version comparison

| Claim | Result |
|---|---|
| A datapack means the same thing on 7.4.12 and 7.5.1 | Confirmed. The pack written for 7.4.12 gives 28 of 28 on 7.5.1 unchanged. |
| 7.5 changed placement, not asset handling | Confirmed. The only counts that moved were wall totals, each by a multiple of 16, which is one doorway. |

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


### Namespaces

Source page: [Namespaces](../getting-started/namespaces.md). Pack:
`docs/examples/wiki-test10/`, namespace `nstest`, profiles `wtten` and
`wttenbare`.

```bash
python harness.py --pack ../../docs/examples/wiki-test10 --profile wtten --probes probes/wt10.json
```

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

**Game test.** Every failing case in `wiki-test10` produces that message.
Evidence: `research/claim-evidence/crash-2026-08-18_18.17.07-server.txt`, and the
harness `failed chunks` summary.

#### NS-5 A profile's unresolved `worldStyle` crashes the server { #ns-5 }

**Game test.** Profile `wttenbare` is `wtten` with one character changed:
`"worldStyle": "test"` in place of `"nstest:test"`. The server died on the first
forced chunk and the harness lost its RCON connection.

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

**Unverified.** No pack has been run with two datapacks defining the same Lost
Cities asset. The behaviour stated on the page is inherited from vanilla dynamic
registry loading and has not been confirmed for these registries specifically, in
either the code or a world. Checking it needs a two-pack run with a controlled
load order.

#### NS-10 Assets are read once per world load { #ns-10 }

**Code review.** Lost Cities registers no `ReloadListener` in 7.4.12.
`RegistryAssetRegistry` caches each built asset in its own `assets` map, and
`AssetRegistries.reset()` has exactly two callers: `ModSetup.init`, once at
`FMLCommonSetupEvent`, and `LostCityFeature`. Nothing on the `/reload` path
touches either.

### Configuration

Source page: [Configuration Reference](../reference/config.md). Evidence is the
rig's own config files, which a real server wrote, plus `mcjty.lostcities.setup.Config`.

#### CFG-1 Settings are split across three files, one of them per world { #cfg-1 }

**Code review.** `Config`'s static initializer builds three
`ForgeConfigSpec.Builder`s and registers keys against them: three on
`COMMON_BUILDER`, eleven on `SERVER_BUILDER`, none on `CLIENT_BUILDER`. Forge
writes a common spec to `config/<modid>/common.toml` and a server spec into the
save.

**Game test.** After any harness run, `research/server-1.20.1-7.4.12/` holds
`config/lostcities/common.toml` with exactly `dimensionsWithProfiles`,
`optimizedHeightmap` and `heightSampleSize`, and
`world/serverconfig/lostcities-server.toml` with the other eleven. Deleting the
world deletes the second file and not the first.

#### CFG-2 Both files use `[profiles]`, and a wrong section resets the file { #cfg-2 }

**Code review.** All three builders call `push("profiles")`. The string
`"General settings"` is passed to `comment(...)` immediately before, so it becomes
a comment line rather than a section.

**Game test.** Cost a full test round before the harness was fixed. The harness
now writes the section explicitly, and `harness.py` carries the note: a wrong
section makes Forge rewrite the file to defaults with no error, which points
`lostcities:lostcity` at `biosphere`, and the run looks like a generation bug
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
The harness wipes the world between runs, and the file comes back at defaults each
time, which is how the defaults quoted on the page were read.

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

Source page: [KubeJS Integration](../advanced/kubejs.md). No pack yet. The mod jars
needed to run one are held privately; installing KubeJS, Rhino and Architectury on
the test rig is the outstanding step.

#### KJS-1 Lost Cities assets are ordinary dynamic registry entries { #kjs-1 }

**Code review.** `CustomRegistries` declares each asset type as a
`ResourceKey<Registry<...>>` and registers it through Forge's
`DataPackRegistryEvent.NewRegistry`, with a codec per type. Nothing in the mod
opens a file or walks a directory. Loading is done by the vanilla datapack
registry loader, which reads every enabled pack source.

#### KJS-2 Files under `kubejs/data/` are seen by that loader { #kjs-2 }

**Unverified.** Consistent with KJS-1, because the vanilla loader reads from the
`ResourceManager` and every pack source is one of its inputs, and reported to work
in practice. Neither the rig nor the code has been used to confirm that KubeJS
registers its `data` folder as such a source in
`kubejs-forge-2001.6.5-build.26`. Confirming it needs KubeJS on the rig and a
`wiki-test10` variant relocated under `kubejs/data/nstest/`.

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
| Cellars | Every pack so far runs with `mincellars` and `maxcellars` at 0. Negative level indices, `cellar: true`, and the city level added to the cellar maximum are all untraced in a world. |
| Highways, railways, monorails | Only streets have been generated. Infrastructure parts need a much wider force-loaded area than the pinned grid uses. |
| City spheres | Sphere generation itself, `onlyPredefined`, and monorail agreement between spheres. One bug has already been found in this area by accident. |
| Scattered buildings and `stuff` | Both asset types are documented from their codecs and neither has been placed. |
| Building fronts | `fronts`, `buildingFrontChance`, and the claim that a front is drawn by the adjacent street chunk. |
| `preferslonely` | Needs a count over many chunks rather than a pinned grid. |
| Part rotation and `lostcities:rotatable` | The claim that an untagged block keeps its facing when a part is rotated. |
| `avoidWater` and `avoidFoliage` | Including the finding that `avoidFoliage` is what controls flooding. |
| `isbuilding`, `issphere`, `chunkx`, `chunkz` | Four condition keys with no coverage. |
| Predefined spheres | The city half is covered, the sphere half is not. |
| The in-game editor | Six commands documented from the code. They need a client, not a headless server. |
| KubeJS loading | The path is documented, the load has not been observed. See [KJS-2](#kjs-2). |

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

| Pack | Covers | Read by |
|---|---|---|
| `docs/examples/wiki-test/` | Positive claims about palettes, streets and multi-buildings | Eye |
| `docs/examples/wiki-fail/` | Failure claims. Two of its three profiles are meant to fail | Log |
| `docs/examples/wiki-test7/` | The pinned grid: 21 assets, 28 probes | Eye or harness |
| `docs/examples/wiki-test8/` | Ruins, damage, row length, `parts2` | Harness |
| `docs/examples/wiki-test10/` | Namespace resolution, and what an unresolved reference does | Harness |

`wiki-test7` supersedes `wiki-test5` and `wiki-test6`, which are earlier builds of
the same grid kept only because their failures are documented above.

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
