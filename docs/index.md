# Lost Cities Wiki

This is an in-depth guide to building custom cities with [Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Forge mod that generates ruined, overgrown cities during world generation.

!!! note "This is not the official wiki"
    The mod's own documentation is at [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities). Read it as well. This site covers what that documentation does not: why a setting appears to do nothing, why a key copied from an example does not work in your own file, and how any of this reaches a world in the first place.

## Who this is for

Anyone building a custom city for their own modpack or server. You do not need Java.

**Before you start, you need to know:**

- How a datapack is laid out, that is a `data/<namespace>/...` folder inside a world's `datapacks` folder or inside a mod
- How to find the `config` folder of your Minecraft instance
- How to read and write JSON by hand

## Scope

Everything in this wiki is verified against Lost Cities **7.4.12** for **Minecraft 1.20.1**, by reading that version's own code and shipped content.

The [Versions](versions/index.md) section covers the rest of the mod's history, checked the same way: every release from Minecraft 1.11.2 to Minecraft 26.1, which asset system each one uses, and which pages here apply to it.

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
| [`docs/asset_structure.md` on GitHub](https://github.com/McJtyMods/LostCities/blob/1.20/docs/asset_structure.md) | A newer and much longer reference, which the author points people to in support. He states that it was AI generated. |

This site exists to go further than all three, and to be checkable: every behaviour claim here was traced to the code that implements it, in the version named above.

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
