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
| KubeJS loading | The path is documented, the load has not been observed. |

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
