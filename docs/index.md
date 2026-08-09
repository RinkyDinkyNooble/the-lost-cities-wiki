# Lost Cities Wiki

This is an in-depth guide to building custom cities with [Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Forge mod that generates ruined, overgrown cities during world generation.

!!! note "This is not the official wiki"
    The mod's real docs live at [mcjty.eu/docs/mods/lost-cities](https://mcjty.eu/docs/mods/lost-cities). Worth checking there too. This site exists to go further: the parts you only find out about by reading the source, breaking things, or asking around. Why a setting doesn't seem to do anything, why a key you copied from an example doesn't work in your own file, how any of this gets triggered in a world at all, that's what's covered here.

## Who this is for

Anyone building a custom city profile for their own modpack or server. No Java needed.

**Before you start, you should know:**

- Basic datapack structure (a `data/<namespace>/...` folder inside a world or resource pack)
- How to find your Minecraft instance's `config` folder
- How to read and write JSON by hand

## Scope

Everything in this wiki is verified against Lost Cities **7.4.12** for **Minecraft 1.20.1**. Version differences are called out explicitly wherever they matter, and later mod versions get their own changes-only notes rather than silently overwriting what's here.

## Where to start

| You want to | Go to |
|---|---|
| Understand how any of this reaches a world | [How It All Connects](getting-started/how-it-connects.md) |
| Get a building of your own generating, today | [Your First Custom City](getting-started/first-city.md) |
| Look up a field | the **Reference** section |
| Fix an error you're staring at | [Error Messages](troubleshooting/errors.md) |
| Work out why nothing happens at all | [When nothing happens](getting-started/first-city.md#when-nothing-happens) |

New to this entirely? Read [How It All Connects](getting-started/how-it-connects.md) first, then follow the tutorial. Nothing else in this wiki will make much sense until you understand that first piece.

Complete working files for everything the tutorial builds are in [`examples/`](https://github.com/RinkyDinkyNooble/lostcities-wiki/tree/main/examples), along with a validator that checks a datapack against the rules documented here.
