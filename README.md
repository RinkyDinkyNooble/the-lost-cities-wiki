# The Lost Cities Wiki

An in-depth, unofficial guide to building custom cities with [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities), a Minecraft mod by McJty.

**Read it at [rinkydinkynooble.github.io/the-lost-cities-wiki](https://rinkydinkynooble.github.io/the-lost-cities-wiki/)**

## What this is

The mod has its own documentation at [mcjty.eu](https://mcjty.eu/docs/mods/lost-cities). Read it first. This site covers what that documentation does not: the behaviour you otherwise find only by reading the decompiled source or by breaking a world and working out why.

Every claim here is verified against **Lost Cities 7.4.12, Minecraft 1.20.1, Forge**. The source of truth is the mod's own code and shipped content, not other documentation. Where a page states a behaviour, it also states what happens when you get it wrong.

Some things you will not find elsewhere:

- Why a building crashes world generation with `Misconfiguration! Floor were generated for a building where no part condition matches!`, and the rule behind it
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

`--strict` turns any broken internal link into a build failure. The validator checks that the example datapack still satisfies every rule the wiki states. Together they stop the docs and the example from drifting apart.

## Contributing

Corrections are welcome, especially ones backed by observed behaviour. If a page is wrong, state **what you observed** and **which mod version** you observed it on. That is more useful than anything else you can send.

Read [STYLE.md](STYLE.md) before writing prose. The wiki uses one approved term per concept and a deliberately plain register, so a correction written in a different voice needs rewriting before it can be merged.

Four pages are marked in-progress in the navigation. Each one states what is still missing.

## Licence

[CC0 1.0](LICENSE). Use it however you like. No attribution required.

Not affiliated with or endorsed by McJty. The Lost Cities is McJty's work. This is an independent guide to it.
