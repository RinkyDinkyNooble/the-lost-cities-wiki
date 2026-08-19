---
claims: verified
---

# Key Interactions

Most keys are independent. The ones on this page are not: setting one correctly
still produces nothing, because a second key elsewhere overrides it, gates it, or
is applied after it. <!-- noclaim -->

Every entry names the version it was checked against and how. These are the cases
behind most reports of a setting that "does nothing". <!-- noclaim -->

## One key silently defeats another

### `torch` needs `generateLighting`

| | [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| Set | A palette entry with `torch: true` |
| Defeated by | `lostcity.generateLighting`, default `false` |
| Result | The character resolves to **air**. The `block` value is discarded and nothing is logged. |
| Checked | Run in a world, 7.4.12 |

The mod's own `common` palette marks `T` this way, which is why shipped buildings
are unlit under a default profile. See [Palette](palette.md#torch-requires-generatelighting). [game test](../examples/claim-tests.md#pal-11){.v .v-g}

### `explosionChance: 0` does not stop explosions

| | [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| Set | `explosions.explosionChance: 0.0` |
| Defeated by | `explosions.miniExplosionChance`, default `0.03` |
| Result | Buildings are still damaged. The mini roll is **15 times** more likely than the one that was turned off. |
| Checked | Run in a world, 7.4.12 |

A profile that wants undamaged buildings has to zero both. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

### `avoidWater` does not stop buildings flooding

| | [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| Set | `lostcity.avoidWater: true` |
| Actually controlled by | `lostcity.avoidFoliage` |
| Result | `avoidWater` only removes liquid a **part** places. Whether "hard air" floods below sea level is read from `avoidFoliage`, whose name does not suggest it. |
| Checked | Read from the mod, 7.4.12 |

The per-part [`nowater` meta](part.md#nowater) does the same job for one part without
losing foliage. See [Profile](profile.md). [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### `buildingchance: 1.0` does not fill every chunk on 7.5.0 or later

| | [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| Set | `buildingchance: 1.0` on a city style |
| Defeated by | `streetGenerationMode`, default `HIERARCHICAL_GRID_V1` from 7.5.0 |
| Result | The road planner claims chunks **before** `buildingchance` is rolled, so a claimed chunk never reaches the roll. |
| Checked | Read from the mod, 7.5.1 |

`streetGenerationMode: LEGACY` restores the 7.4.12 ordering. See
[What changed in 7.5](../versions/7-5.md). [code review](../examples/claim-tests.md#key-1){.v .v-c}

### `preventruins` is on the pinned building, not the Building asset

| | [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| Looking for | A key on a [Building](building.md) that protects it from ruins |
| Where it is | `preventruins` on a **pinned building inside a predefined city** |
| Result | A Building asset has no such key. Ruin protection is only reachable by pinning. |
| Checked | Run in a world, 7.4.12 |

## Order of application matters

### `minfloors` is applied after `maxfloors`

The floor count is clamped to the maximum, then raised to the minimum. The minimum
is a `max()`, so it wins. [game test](../examples/claim-tests.md#bld-3){.v .v-g}

| Declared | Result [game test](../examples/claim-tests.md#bld-3){.v .v-g} |
|---|---|
| `maxfloors: 3`, `minfloors: 6` | **6 floors.** The minimum overrides the maximum it was just clamped to. |
| `maxfloors: 3` alone | At most 3, subject to the profile and city style. |

`overrideFloors` changes which sources are consulted, not the order. Checked in a
world on 7.4.12. See [Building](building.md#how-floor-and-cellar-counts-are-decided). [game test](../examples/claim-tests.md#bld-2){.v .v-g}

### A palette is merged in three layers

Style, then Building, then Part. Each layer overwrites the one before it for the
same character, and a part palette **merges into** the building's rather than
replacing it. [game test](../examples/claim-tests.md#pal-1){.v .v-g}

One exception inverts the rule: a **concrete definition beats an alias** whatever
the order, so a `frompalette` entry cannot override a character that any palette in
the set defines with a real block. [game test](../examples/claim-tests.md#pal-5){.v .v-g}

Checked in a world on 7.4.12. See [Palette](palette.md#collisions-and-merge-order). [game test](../examples/claim-tests.md#pal-1){.v .v-g}

## Chains where every link must hold

### A chest is filled only if four things agree

| Gate | Default | Effect when it fails [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|
| `generateLoot` | `true` | Every chest is empty. |
| `buildingWithoutLootChance` | `0.2` | One building in five gets neither loot nor spawners. |
| `chestWithoutLootChance` | `0.2` | One surviving chest in five is still empty. |
| The `loot` value names a Condition | | Throws, and leaves invisible chests. |

At the defaults a chest in a randomly chosen building has roughly a **64%** chance
of being filled. Two empty chests in a row is not evidence of a broken palette.
Checked in a world on 7.4.12. See [Palette](palette.md#why-a-chest-generates-empty). [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### A profile reaches a datapack through four names

`dimensionsWithProfiles` names a profile, the profile names a `worldStyle`, the
world style names city styles, and a city style names buildings. [code review](../examples/claim-tests.md#cfg-4){.v .v-c}

A wrong name at the first three is not equal in consequence: [game test](../examples/claim-tests.md#ns-4){.v .v-g}

| Wrong name in | Result [game test](../examples/claim-tests.md#ns-5){.v .v-g} |
|---|---|
| `dimensionsWithProfiles` | The dimension generates with a default profile. |
| The profile's `worldStyle` | **The server crashes.** It is resolved before the generation try/catch. |
| A city style or building reference | Failed chunks, logged per chunk. |

Checked in a world on 7.4.12. See
[Error Messages](../troubleshooting/errors.md#thrown-during-chunk-generation). [game test](../examples/claim-tests.md#ns-5){.v .v-g}

### A sphere landscape needs a second profile

`landscapeType: spheres` or `cavernspheres` requires `cityspheres.outsideProfile`.
It is documented as optional with an empty default, and that default resolves to
null, so the first chunk that asks about the world outside a sphere throws. [game test](../examples/claim-tests.md#fail-7){.v .v-g}

On those landscape types nothing catches it, because `LostCitySphereFeature` has no
`try`. Checked in a world on 7.4.12. [game test](../examples/claim-tests.md#fail-5){.v .v-g}

## Keys that override generation wholesale

### A predefined city ignores the values that would otherwise choose

| Normally decided by | Inside a predefined city [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|
| `cityChance` | Ignored. The centre chunk is a city centre even at `0.0`. |
| The city radius roll | Fixed to `radius`. |
| The world style's weighted city style pick | Fixed to `citystyle`. |
| `buildingchance`, per chunk | Ignored on any chunk holding a pinned building or street. |

Checked in a world on 7.4.12. See [Predefined City](predefined.md). [game test](../examples/claim-tests.md#pre-1){.v .v-g}

## Two keys that cannot work at all

`inpart` and `belowpart` never match from a Building's `parts` list, whatever else
is set, because the floor loop has no current part yet and passes the literal
`<none>`. `belowpart` additionally tests the current part rather than the one below
it in every version that declares the key. [game test](../examples/claim-tests.md#cnd-5){.v .v-g}

Both work in a Condition reached from a palette's `loot` or `mob`, where the part is
real. Checked in a world on 7.4.12. See
[Condition](condition.md#belowpart-and-inpart-in-a-building). [game test](../examples/claim-tests.md#cnd-6){.v .v-g}

## See also

- [Known Issues](../troubleshooting/known-issues.md) for behaviour with no key at all
- [Claim Tests](../examples/claim-tests.md) for how each entry above was checked
- [Profile Reference](profile.md) for the keys themselves <!-- noclaim -->
