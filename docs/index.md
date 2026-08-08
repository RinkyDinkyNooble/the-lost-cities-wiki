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

New to this entirely? Start with [How It All Connects](getting-started/how-it-connects.md). Nothing else in this wiki will make much sense until you understand that piece.
