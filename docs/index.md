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

Everything in this wiki is verified against Lost Cities **7.4.12** for **Minecraft 1.20.1**. Pages state version differences wherever they matter. A later mod version gets its own changes-only notes. It does not silently overwrite what is here.

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
