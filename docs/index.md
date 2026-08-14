# Lost Cities Wiki

This is an in-depth guide to building custom cities with [Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Minecraft world-generation mod that produces ruined, overgrown cities. It has Forge releases up to 7.5.x and NeoForge releases from 8.0 onward.

!!! note "This is not the official wiki"
    The mod's own documentation is at [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities). Read it as well. This site covers what that documentation does not: why a setting appears to do nothing, why a key copied from an example does not work in your own file, and how any of this reaches a world in the first place.

## Who this is for

Anyone building a custom city for their own modpack or server. You do not need Java.

**Before you start, you need to know:**

- How a datapack is laid out, that is a `data/<namespace>/...` folder inside a world's `datapacks` folder or inside a mod
- How to find the `config` folder of your Minecraft instance
- How to read and write JSON by hand

## Scope

Pages are written against Lost Cities **7.4.12** for **Minecraft 1.20.1** on Forge, and most claims were read out of that version's own code and shipped content. A growing number have also been run in a world, and those are listed on [Claim Tests](examples/claim-tests.md).

The claim-test pack written for 7.4.12 also passes unchanged on **7.5.1**, so the two share the same datapack behaviour even though 7.5 changed where cities put things.

The NeoForge line is **in progress**. Its keys, defaults and bounds are mapped, but its behaviour has not been tested the same way, so treat anything version-specific there as unconfirmed until a page says otherwise.

| Target | State |
|---|---|
| 7.4.12, Minecraft 1.20.1, Forge | Primary. Read from the mod and run in a world. |
| 7.5.1, Minecraft 1.20.1, Forge | Read from the mod and run in a world. |
| 8.x, 9.x, 10.x, NeoForge | In progress. Keys and defaults mapped. |
| Before 5.3.29 | Out of scope. Content lives inside the jar, not in datapacks. |

The [Versions](versions/index.md) section covers the mod's history from Minecraft 1.11.2 to Minecraft 26.1, which asset system each release uses, and which pages here apply to it.

### How claims are checked

A claim on this site carries one of these levels. Pages name the version they were
checked against, and the level is stated wherever it is not the page default.

| Level | Meaning |
|---|---|
| **Run in a world** | The behaviour was reproduced in game and the result is on [Claim Tests](examples/claim-tests.md). The strongest evidence here. |
| **Read from the mod** | The behaviour was traced through the compiled code of the named version. This is the default for most pages. |
| **Schema checked** | The key, its type, default and bounds were extracted from the jar and are machine-compared on every build. Applies to every reference table. |
| **Not checked** | Documented but neither run nor traced. Listed on [what has not been checked in a world](examples/claim-tests.md#what-has-not-been-checked-in-a-world). |

Two rules follow from this, and both are in [STYLE.md](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/blob/main/STYLE.md):

- A claim checked on one version is not restated as true of all versions.
- The mod's own code is the authority on what happens. The mod's documentation is
  the authority on what is intended and supported. Where a config comment and the
  code disagree, this site documents the code and says so.

!!! warning "On 7.5.0 or later, read the 7.5 page before anything else"
    Version 7.5.0 added a planned road system and an inter-city highway network,
    and **both are on by default**. A setup that worked on 7.4.12 generates
    different cities after the upgrade, with no change to your config.

    The clearest symptom: the mod refuses a building in any chunk the road planner
    has claimed, and it does so **before** it rolls `buildingchance`. Setting
    `buildingchance` to `1.0` no longer fills every eligible chunk.

    [What changed in 7.5](versions/7-5.md) documents this, verified against the
    7.5.1 jar. The same system is in 8.4.1, 9.5.1 and 10.0.1, unchanged.

    Not sure which version you have? See
    [Which version do I have](versions/index.md).

## The mod's own documentation

Read it alongside this site. There are three places, and they are not the same:

| Source | What it is |
|---|---|
| [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities) | The general mod documentation. |
| [mcjty.eu asset-datapack page](https://www.mcjty.eu/docs/mods/lost-cities/asset-datapack) | The deeper page on the datapack asset system. |
| [`docs/asset_structure.md` on GitHub](https://github.com/McJtyMods/LostCities/blob/1.20/docs/asset_structure.md) | A newer and much longer reference covering the datapack assets key by key. |

Those are the authoritative sources. This site adds depth on top of them and shows
its working: each behaviour claim names the version it was checked against, and
most were read out of the mod's own code or run in a world.

## Where to start

| You want to | Go to |
|---|---|
| Understand how any of this reaches a world | [How It All Connects](getting-started/how-it-connects.md) |
| Get your own building generating today | [Your First Custom City](getting-started/first-city.md) |
| Look up a key | [Reference](reference/index.md) |
| Fix an error you are looking at | [Error Messages](troubleshooting/errors.md) |
| Work out why nothing happens at all | [When nothing happens](getting-started/first-city.md#when-nothing-happens) |

If you are new to the mod, read [How It All Connects](getting-started/how-it-connects.md) first, then follow the tutorial. The rest of this wiki assumes you know how a dimension reaches a world style.

[Examples](examples/index.md) holds complete working files for everything the tutorial builds, and a validator that checks a datapack against the rules documented here.
