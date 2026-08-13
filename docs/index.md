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

!!! warning "Newer versions exist, and 7.5.0 changed street generation"
    The mod has moved on. At the time of writing the author states that **7.5.1** is current, and that **7.5.0** introduced a hierarchical street and highway system, internally named `HIERARCHICAL_GRID_V1`, along with new open-lot parks. The author describes the change as compatible with existing worlds.

    That system does not exist in 7.4.12, so this wiki does not document it.

    One consequence is worth knowing even if you never read further. Under the new system, planned roads take precedence over normal building selection, so the technique of setting `buildingchance` to `1.0` to fill every eligible chunk with your own building no longer does that. Chunks the planner has claimed as streets stay streets.

    **This wiki has not verified any 7.5.x behaviour.** The statements above come from the mod author in support discussion, not from reading 7.5.x code. Treat them as a pointer, not as documentation.

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
