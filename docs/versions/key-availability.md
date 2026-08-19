---
claims: verified
---

# Key availability

This wiki documents the 224 datapack keys that exist in 7.4.12. **158 of them exist
in every datapack-era version.** The other 66 do not. [code review](../examples/claim-tests.md#key-1){.v .v-c}

Write a file against this wiki, run it on a different version, and a key that does
not exist there is what changes the result. This page lists which keys those are. [code review](../examples/claim-tests.md#key-1){.v .v-c}

!!! note "This covers the datapack era only"
    Versions before 5.3.29 have no datapack keys at all. See
    [The file-asset era](legacy.md). [code review](../examples/claim-tests.md#key-1){.v .v-c}

## What happens when a key does not exist

**Nothing visible.** The key is ignored and the rest of the file loads normally. [game test](../examples/claim-tests.md#key-2){.v .v-g}

| Situation | Result |
|---|---|
| A key this version does not know | Ignored. The file loads, the asset works, and the behaviour that key would have controlled is simply absent [game test](../examples/claim-tests.md#key-2){.v .v-g} |
| A **required** key that is missing | The file fails to decode and the asset does not load at all [code review](../examples/claim-tests.md#key-3){.v .v-c} |

Those two are easy to confuse and they fail in opposite directions. An extra key
costs nothing at load and everything at generation, because the behaviour it asked
for never happens and no message says so. A missing required key is loud. [game test](../examples/claim-tests.md#key-2){.v .v-g} [code review](../examples/claim-tests.md#key-3){.v .v-c}

!!! danger "This is why the running version is worth checking first"
    A datapack written for 7.4.12 loads without complaint on 6.0.3. It quietly stops
    doing 44 things. See [Error Messages](../troubleshooting/errors.md) for the
    failures that do produce text. [game test](../examples/claim-tests.md#key-2){.v .v-g}

## Version numbers are not ordered across Minecraft branches

**6.2.2 has keys that 6.2.3 does not.** [code review](../examples/claim-tests.md#key-1){.v .v-c}

The two were built on different Minecraft branches, 6.2.2 for Minecraft 1.19 and
6.2.3 for Minecraft 1.19.4. A higher mod version implies a newer feature set only
when both sit on the same branch. The same holds for 8.2.2 against 7.5.1. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Group 1: added in 6.2.2

Absent in 5.3.29, 6.0.3, 6.1.6 and 6.2.3. Present in 6.2.2, 7.4.12 and later.
26 keys, including the entire **stuff object** asset. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Wiki page [code review](../examples/claim-tests.md#key-1){.v .v-c} | Keys |
|---|---|
| [Stuff Object](../reference/stuff.md) | `attempts`, `biomes`, `blocks`, `buildings`, `column`, `inbuilding`, `maxcount`, `maxheight`, `mincount`, `minheight`, `seesky`, `tags`, `upperblocks` |
| [City Style](../reference/citystyle.md) | `stuff_tags` |
| [World Style](../reference/worldstyle.md) | `multisettings`, and inside multi settings: `areasize`, `attempts`, `correctstylefactor`, `maximum`, `minimum` |
| [City Style](../reference/citystyle.md), inside `streetblocks` | `parts` |
| [Matchers](../concepts/matchers.md) | Block matcher: `if_all`, `if_any`, `excluding`. Resource location matcher: `if_any`, `excluding` |

!!! warning "The stuff object does not exist before 6.2.2"
    Every key of the asset is in this group. On 5.3.29, 6.0.3, 6.1.6 or 6.2.3 the
    asset type itself is unavailable, not merely reduced. [code review](../examples/claim-tests.md#key-1){.v .v-c}

    The block matcher goes with it. All three of its keys arrive in 6.2.2, because
    the stuff object is what introduced it. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Group 2: added in 7.4.12

Absent in every 5.x and 6.x version, and also absent in **8.2.2**. Present in
7.4.12, 7.5.1, 8.4.1 and later. 23 keys, and the group that catches an upgrade to
8.2.2, whose version number looks newer than 7.4.12 while its feature set is older. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Wiki page [code review](../examples/claim-tests.md#key-1){.v .v-c} | Keys |
|---|---|
| [Building](../reference/building.md) | `overrideFloors` |
| [Building](../reference/building.md), part reference | `belowpart` |
| [Condition](../reference/condition.md) | `belowpart` |
| [World Style](../reference/worldstyle.md) | `settings` |
| [World Style](../reference/worldstyle.md), inside `settings` | `railpartheight6`, `railwayavoidance`, `vinenorth`, `vinesouth`, `vineeast`, `vinewest` |
| [City Style](../reference/citystyle.md), inside `parkblocks` | `parkchance`, `parkborder`, `parkelevation`, `parkstreetthreshold`, `avoidfoliage` |
| [City Style](../reference/citystyle.md), inside `streetblocks` | `frontchance`, `fountainchance` |
| [City Style](../reference/citystyle.md), inside `corridorblocks` | `corridorchance` |
| [City Style](../reference/citystyle.md), inside `selectors` | `feather`, `minSpawnDistance`, `maxSpawnDistance` |
| [Scattered Building](../reference/scattered.md) | `rotatable`, `nearhighway` |

!!! danger "Measured: one key from this group changes a building by half its height"
    The wiki's control building carries `overrideFloors: true` and generates 512
    gold blocks on 7.4.12. The identical pack on 8.2.2 generates **768**. Deleting
    that one key on 7.4.12 gives 768 there as well, which isolates the cause. The
    building is not broken and nothing is logged. It is simply taller than the pack
    asked for, because the floor count fell back to the profile. [game test](../examples/claim-tests.md#key-4){.v .v-g} [code review](../examples/claim-tests.md#key-4){.v .v-c}

## Group 3: missing in 6.0.3 only

Present in 5.3.29, then absent in 6.0.3, then present again from 6.1.6 onward.
16 keys. 6.0.3 is the thinnest version in the datapack era, with 180 keys against
the 224 of 7.4.12. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Wiki page [code review](../examples/claim-tests.md#key-1){.v .v-c} | Keys |
|---|---|
| [Building](../reference/building.md) | `allowDoors`, `allowFillers` |
| [Palette](../reference/palette.md) | `tag` |
| [World Style](../reference/worldstyle.md) | `cityspheres`, and inside city sphere settings `centerpart`, `centerpartoffset`, `centerpartorigin`, `centertype` |
| [City Style](../reference/citystyle.md), inside `generalblocks` | `leaves`, `rubbledirt` |
| [Predefined City & Sphere](../reference/predefined.md) | `centerx`, `centerz`, `chunkx`, `chunkz`, `dimension`, `radius` |

## Group 4: added in 7.4.12, present in 8.2.2

1 key. Absent in every 5.x and 6.x version. [code review](../examples/claim-tests.md#key-1){.v .v-c}

| Wiki page [code review](../examples/claim-tests.md#key-1){.v .v-c} | Key |
|---|---|
| [Scattered Building](../reference/scattered.md) | `allowvoid` |

## Keys added after 7.4.12

Version 7.5.1 adds 7 keys that 7.4.12 does not have. On 7.4.12 they do not exist,
and writing one is ignored rather than reported. See
[What changed in 7.5](7-5.md#new-datapack-keys). [code review](../examples/claim-tests.md#key-1){.v .v-c} [game test](../examples/claim-tests.md#key-2){.v .v-g}

## Summary by version

| Version [code review](../examples/claim-tests.md#key-1){.v .v-c} | Datapack keys | Groups it lacks |
|---|---|---|
| 5.3.29 | 196 | 1, 2, 4 |
| 6.0.3 | 180 | 1, 2, 3, 4 |
| 6.1.6 | 196 | 1, 2, 4 |
| 6.2.2 | 200 | 2, 4 |
| 6.2.3 | 196 | 1, 2, 4 |
| 7.4.12 | 224 | none |
| 7.5.1 | 231 | none, plus 7 extra |
| 8.2.2 | 201 | 2 |
| 8.4.1, 9.5.1, 10.0.1 | 231 | none, plus 7 extra |

## How this was checked

Each version's asset codecs were disassembled and every `fieldOf` and
`optionalFieldOf` call read for the key name it registers, then the sets were
compared. No release notes were used. [code review](../examples/claim-tests.md#key-1){.v .v-c}
