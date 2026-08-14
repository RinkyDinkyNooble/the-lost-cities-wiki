# Key availability

This wiki documents the 224 datapack keys that exist in 7.4.12. **158 of them exist
in every datapack-era version.** The other 66 do not.

If you write a file against this wiki and run it on a different version, a key that
does not exist there is what breaks first. This page lists exactly which keys those
are.

Use it when a file that matches the reference pages fails to load anyway.

!!! note "This covers the datapack era only"
    Versions before 5.3.29 have no datapack keys at all. See
    [The file-asset era](legacy.md).

## What happens when a key does not exist

The codec rejects the whole file. The asset does not load. The behaviour depends on
whether the key was required:

| Situation | Result |
|---|---|
| An optional key the version does not know | The file fails to parse. An unknown key is not ignored. |
| A required key the version does not know | The same failure. |

See [Error Messages](../troubleshooting/errors.md) for the text you will see.

## Version numbers are not ordered across Minecraft branches

Before reading the groups below, know this: **6.2.2 has keys that 6.2.3 does not.**

The two were built on different Minecraft branches, 6.2.2 for Minecraft 1.19 and
6.2.3 for Minecraft 1.19.4. A higher mod version does not imply a newer feature set
unless both are on the same branch. The same is true of 8.2.2 against 7.5.1.

## Group 1: added in 6.2.2

Absent in 5.3.29, 6.0.3, 6.1.6 and 6.2.3. Present in 6.2.2, 7.4.12 and later.

26 keys. This group includes the entire **stuff object** asset.

| Wiki page | Keys |
|---|---|
| [Stuff Object](../reference/stuff.md) | `attempts`, `biomes`, `blocks`, `buildings`, `column`, `inbuilding`, `maxcount`, `maxheight`, `mincount`, `minheight`, `seesky`, `tags`, `upperblocks` |
| [City Style](../reference/citystyle.md) | `stuff_tags` |
| [World Style](../reference/worldstyle.md) | `multisettings`, and inside multi settings: `areasize`, `attempts`, `correctstylefactor`, `maximum`, `minimum` |
| [City Style](../reference/citystyle.md), inside `streetblocks` | `parts` |
| [Matchers](../concepts/matchers.md) | Block matcher: `if_all`, `if_any`, `excluding`. Resource location matcher: `if_any`, `excluding` |

!!! warning "The stuff object does not exist before 6.2.2"
    Every key of the asset is in this group. On 5.3.29, 6.0.3, 6.1.6 or 6.2.3 the
    asset type itself is unavailable, not merely reduced.

    The block matcher goes with it. All 3 of its keys arrive in 6.2.2, because the
    stuff object is what introduced it.

## Group 2: added in 7.4.12

Absent in every 5.x and 6.x version, and also absent in **8.2.2**. Present in
7.4.12, 7.5.1, 8.4.1 and later.

23 keys. This is the group that catches an upgrade to 8.2.2, whose version number
looks newer than 7.4.12 but whose feature set is older.

| Wiki page | Keys |
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

## Group 3: missing in 6.0.3 only

Present in 5.3.29, then absent in 6.0.3, then present again from 6.1.6 onward.

16 keys. 6.0.3 is the weakest version in the datapack era, with 180 keys against
7.4.12's 224.

| Wiki page | Keys |
|---|---|
| [Building](../reference/building.md) | `allowDoors`, `allowFillers` |
| [Palette](../reference/palette.md) | `tag` |
| [World Style](../reference/worldstyle.md) | `cityspheres`, and inside city sphere settings `centerpart`, `centerpartoffset`, `centerpartorigin`, `centertype` |
| [City Style](../reference/citystyle.md), inside `generalblocks` | `leaves`, `rubbledirt` |
| [Predefined City & Sphere](../reference/predefined.md) | `centerx`, `centerz`, `chunkx`, `chunkz`, `dimension`, `radius` |

## Group 4: added in 7.4.12, present in 8.2.2

1 key. Absent in every 5.x and 6.x version.

| Wiki page | Key |
|---|---|
| [Scattered Building](../reference/scattered.md) | `allowvoid` |

## Keys added after 7.4.12

Version 7.5.1 adds 7 keys that 7.4.12 does not have. If you are reading this wiki
and running 7.4.12, they do not exist for you. See
[What changed in 7.5](7-5.md#new-datapack-keys).

## Summary by version

| Version | Datapack keys | Groups it lacks |
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

Each version's asset codecs were disassembled, and every `fieldOf` and
`optionalFieldOf` call was read to get the key name it registers. The sets were
then compared. No release notes were used.
