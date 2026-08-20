---
claims: verified
---

# Lost Cities Wiki

This is an in-depth guide to building custom cities with [Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Minecraft world-generation mod that produces ruined, overgrown cities. It has Forge releases up to 7.5.x and NeoForge releases from 8.0 onward. <!-- noclaim -->

!!! note "This is not the official wiki"
    The mod's own documentation is at [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities). Read it as well. This site covers what that documentation does not: why a setting appears to do nothing, why a key copied from an example does not work in your own file, and how any of this reaches a world in the first place.

## Who this is for

Anyone building a custom city for their own modpack or server. You do not need Java. <!-- noclaim -->

**Before you start, you need to know:** <!-- noclaim -->

- How a datapack is laid out, that is a `data/<namespace>/...` folder inside a world's `datapacks` folder or inside a mod
- How to find the `config` folder of your Minecraft instance
- How to read and write JSON by hand <!-- noclaim -->

## Scope

Pages are written against Lost Cities **7.4.12** for **Minecraft 1.20.1** on Forge, and most claims were read out of that version's own code and shipped content. A growing number have also been run in a world, and those are listed on [Claim Tests](examples/claim-tests.md). [code review](examples/claim-tests.md#ref-2){.v .v-c}

The claim-test pack written for 7.4.12 also passes unchanged on **7.5.1**, so the two share the same datapack behaviour even though 7.5 changed where cities put things. [game test](examples/claim-tests.md#ver-1){.v .v-g}

The NeoForge line is no longer inferred. Every version below has been booted on the [test rig](examples/claim-tests.md#how-a-game-test-on-this-page-is-run) and had its blocks read back out of the world, so a version-specific statement here rests on a run rather than on a key set. [game test](examples/claim-tests.md#neo-1){.v .v-g}

| Target | State |
|---|---|
| 7.4.12, Minecraft 1.20.1, Forge | Primary. Every page here is written against it, and every claim pack was authored on it. [game test](examples/claim-tests.md#ver-1){.v .v-g} |
| 7.5.1, Minecraft 1.20.1, Forge | Runs the same packs unchanged, with one documented difference in how a building's palette is resolved. [game test](examples/claim-tests.md#ver-3){.v .v-g} |
| 8.2.2, Minecraft 1.21, NeoForge | Run in a world. A higher number than 7.5 and a **smaller** feature set, because it is pre-7.5 code ported forward. [game test](examples/claim-tests.md#ver-9){.v .v-g} |
| 8.4.1, Minecraft 1.21, NeoForge | Run in a world. This is where the 7.5 changes reached the 1.21 line. [game test](examples/claim-tests.md#ver-11){.v .v-g} |
| 9.5.1 and 10.0.1, Minecraft 1.21.11 and 26.1.2, NeoForge | Run in a world, all four packs, identical counts to Forge. [game test](examples/claim-tests.md#neo-1){.v .v-g} |
| 6.2.2, Minecraft 1.19 | Run in a world. Builds a floor taller than 7.4.12 from the same file, because it has no `overrideFloors`. [game test](examples/claim-tests.md#key-4){.v .v-g} |
| 5.3.29 and 6.0.3, Minecraft 1.18 and 1.19 | Run in a world, and neither can place a predefined city at all. Datapack content still loads. [game test](examples/claim-tests.md#ver-5){.v .v-g} |
| 2.0.22 and earlier | A different asset system entirely, run on its own rig and covered in [The File-Asset Era](file-era/index.md). [game test](examples/claim-tests.md#f12-9){.v .v-g} |

The [Versions](versions/index.md) section covers the mod's history from Minecraft 1.11.2 to Minecraft 26.1, which asset system each release uses, and which pages here apply to it. [code review](examples/claim-tests.md#key-1){.v .v-c}

### How claims are checked

Every claim on this site carries a chip saying how it was checked, and the chip is
a link to the evidence in [the claim register](examples/claim-tests.md#the-claim-register). <!-- noclaim -->

| Chip | Means |
|---|---|
| [game test](examples/claim-tests.md#ref-1){.v .v-g} | Run on a headless Forge server against a named pack, with the blocks read back out of the world. The strongest evidence here |
| [code review](examples/claim-tests.md#ref-2){.v .v-c} | Read out of the compiled jar of the named version, with the class and method named |
| [unverified](examples/claim-tests.md#ref-3){.v .v-u} | Neither. Not a synonym for false, and not a synonym for unknown: it is a statement about the evidence |

A claim may be both game tested and code reviewed. It may not be unverified and
anything else at once. **The mod's own documentation and the official wiki count as
neither**, which is why several pages here disagree with them. <!-- noclaim -->

`docs/examples/check_claims.py` enforces it on every build: a block with no chip
fails, a chip pointing at a register entry that does not exist fails, and a claim
cited as unverified on one page and verified on another fails. <!-- noclaim -->

Two rules follow from that, and this site is written to both: <!-- noclaim -->

- A claim checked on one version is not restated as true of all versions.
- The mod's own code is the authority on what happens, and the mod's documentation
  is the authority on what is intended and supported. Where a config comment and
  the code disagree, this site documents the code and says so. <!-- noclaim -->

!!! warning "On 7.5.0 or later, read the 7.5 page before anything else"
    Version 7.5.0 added a planned road system and an inter-city highway network,
    and **both are on by default**. A setup that worked on 7.4.12 generates
    different cities after the upgrade, with no change to your config.

    The clearest symptom: the mod refuses a building in any chunk the road planner
    has claimed, and it does so **before** it rolls `buildingchance`. Setting
    `buildingchance` to `1.0` no longer fills every eligible chunk. [code review](examples/claim-tests.md#ref-2){.v .v-c}

    [What changed in 7.5](versions/7-5.md) documents this, verified against the
    7.5.1 jar. The same system is in 8.4.1, 9.5.1 and 10.0.1, unchanged. [code review](examples/claim-tests.md#ref-2){.v .v-c}

    Not sure which version you have? See
    [Which version do I have](versions/index.md). <!-- noclaim -->

## The mod's own documentation

Read it alongside this site. There are three places, and they are not the same: <!-- noclaim -->

| Source | What it is <!-- noclaim --> |
|---|---|
| [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities) | The general mod documentation. |
| [mcjty.eu asset-datapack page](https://www.mcjty.eu/docs/mods/lost-cities/asset-datapack) | The deeper page on the datapack asset system. |
| [`docs/asset_structure.md` on GitHub](https://github.com/McJtyMods/LostCities/blob/1.20/docs/asset_structure.md) | A newer and much longer reference covering the datapack assets key by key. |

Those are the authoritative sources. This site adds depth on top of them and shows
its working: each behaviour claim names the version it was checked against, and
most were read out of the mod's own code or run in a world. <!-- noclaim -->

## Where to start

| You want to | Go to <!-- noclaim --> |
|---|---|
| Understand how any of this reaches a world | [How It All Connects](getting-started/how-it-connects.md) |
| Get your own building generating today | [Your First Custom City](getting-started/first-city.md) |
| Look up a key | [Reference](reference/index.md) |
| Fix an error you are looking at | [Error Messages](troubleshooting/errors.md) |
| Work out why nothing happens at all | [When nothing happens](getting-started/first-city.md#when-nothing-happens) |

If you are new to the mod, read [How It All Connects](getting-started/how-it-connects.md) first, then follow the tutorial. The rest of this wiki assumes you know how a dimension reaches a world style. <!-- noclaim -->

[Examples](examples/index.md) holds complete working files for everything the tutorial builds, and a validator that checks a datapack against the rules documented here. <!-- noclaim -->
