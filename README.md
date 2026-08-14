# The Lost Cities Wiki

An in-depth, unofficial guide to building custom cities with [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Minecraft mod by McJty.

**Read it at [rinkydinkynooble.github.io/the-lost-cities-wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/)**

## What this is

The mod has its own documentation in three places: the [general docs](https://mcjty.eu/docs/mods/lost-cities), the [asset-datapack page](https://www.mcjty.eu/docs/mods/lost-cities/asset-datapack), and a newer, much longer [`asset_structure.md`](https://github.com/McJtyMods/LostCities/blob/1.20/docs/asset_structure.md) on GitHub that the author points people to in support and states was AI generated. Read them alongside this site.

This site covers what they do not: the behaviour you otherwise find only by reading the decompiled source or by breaking a world and working out why.

Every claim here is verified against **Lost Cities 7.4.12, Minecraft 1.20.1, Forge**. The source of truth is the mod's own code and shipped content, not other documentation. Where a page states a behaviour, it also states what happens when you get it wrong.

**On other versions:** the [Versions](https://rinkydinkynooble.github.io/the-lost-cities-wiki/versions/) section covers the mod's full history, from Minecraft 1.11.2 to Minecraft 26.1, checked the same way. It states which release uses which asset system, and which pages here apply to it.

Two findings from that work are worth naming here:

- **7.5.0 turned on a planned road system by default.** The mod refuses a building in any chunk the road planner claims, and it does so before it rolls `buildingchance`. Setting `buildingchance` to `1.0` therefore stopped filling every eligible chunk. This is verified against the 7.5.1 jar, not inferred from release notes.
- **7.5.1 through 10.0.1 are one documentation target.** Those four releases declare the same 160 profile keys and the same 231 datapack keys, with identical defaults and bounds. A datapack written for Minecraft 1.20.1 is structurally valid on Minecraft 26.1.

Claims here are traced to the code that implements them, and a growing number have also been run in a world. See [Claim Tests](https://rinkydinkynooble.github.io/the-lost-cities-wiki/examples/claim-tests/) for what has been verified in game, including the documentation errors and the mod bug that testing found. The largest of those: **a mistake in your assets does not crash the game.** The mod catches it per chunk and logs, so no crash report is written and the world simply comes out wrong. The exception is the wiring between a profile and its datapack, which is resolved outside that catch: a profile naming a `worldStyle` no loaded datapack defines crashes the server outright. Both boundaries were established by crashing a world on purpose, not by reading release notes.

Some things you will not find elsewhere:

- Why a building fails every chunk with `Misconfiguration! Floor were generated for a building where no part condition matches!`, and the rule behind it
- That a city style inherits selectors **additively**, so a child style cannot narrow the building list it inherits
- That street part names accept a **list**, and that no shipped file uses one
- What a palette `char` may legally be, and why an emoji fails in two separate ways
- An [index of every error message](https://rinkydinkynooble.github.io/the-lost-cities-wiki/troubleshooting/errors/) the mod throws, with the cause and the fix for each

## Layout

| Path | Contents |
|---|---|
| `docs/` | The wiki itself, built with MkDocs Material |
| `docs/examples/first-city/` | A complete example datapack that loads as it is |
| `docs/examples/validate.py` | Checks a datapack against the rules the wiki documents |
| `STYLE.md` | The writing rules this wiki follows |
| `CONTRIBUTING.md` | How to report or send a correction, and the gates to run |
| `docs/examples/mod-keys.json` | The mod's real codec and profile keys, extracted from the jars |
| `.github/workflows/docs.yml` | Strict build gate, then deploy to Pages |

## Running it locally

```bash
pip install -r requirements.txt
```

```bash
mkdocs serve
```

Then open <http://127.0.0.1:8000>.

To run the same checks CI runs:

```bash
mkdocs build --strict && python docs/examples/validate.py
```

`--strict` turns any broken internal link into a build failure. The validator does three things:

- Checks that the example datapack still satisfies every rule the wiki states, and that any page inlining a whole example file still matches it byte for byte.
- Checks every key in the reference tables against `docs/examples/mod-keys.json`, which holds the keys the mod's own codecs declare, extracted from the jars. A key the wiki documents that the mod does not have is an error, and so is a key marked optional that the codec requires.
- Checks that every key the version pages attribute to a reference page actually appears on that page.

Together they stop the docs, the example, and the mod's real schema from drifting apart.

## Contributing

Corrections are welcome, especially ones backed by observed behaviour. If a page is wrong, state **what you observed** and **which mod version** you observed it on. That is more useful than anything else you can send.

Full guidance is in [CONTRIBUTING.md](CONTRIBUTING.md). Read [STYLE.md](STYLE.md) before writing prose. The wiki uses one approved term per concept and a deliberately plain register, so a correction written in a different voice needs rewriting before it can be merged.

Four pages are marked in-progress in the navigation. Each one states what is still missing.

## Licence

[CC0 1.0](LICENSE). Use it however you like. No attribution required.

Not affiliated with or endorsed by McJty. The Lost Cities is McJty's work. This is an independent guide to it.
